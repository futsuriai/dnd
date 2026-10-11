#!/usr/bin/env python3
"""Compare ASR engines on one session without a human reference transcript.

Reads <work-dir>/<engine>/<track>.json (dnd-asr-v1) for two or more engines and
writes a Markdown + JSON report covering:

- coverage: VAD speech time vs time covered by recognized words
- agreement: windowed word-level disagreement between engines, with hotspots
- one-sided speech: windows only one engine transcribed (missed vs hallucinated)
- names: canonical campaign-name hits vs near-miss spellings per engine
- loops/confidence: repeated-phrase loops and low-confidence word rates
- throughput: speech minutes processed and local realtime factor
- optional audio judge: Gemini (via the agy CLI) listens to the worst hotspot
  clips and transcribes them; the engine closer to its reading wins the clip

Example:
    python asr_diagnostics.py --work-dir "session-21/asr" --session 21 \
        --primary gladia --judge agy --judge-samples 16
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import asr_common

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = SCRIPT_DIR.parent.parent
WORDLIST = Path("/usr/share/dict/words")
FILLERS = {"um", "uh", "erm", "hmm", "mm", "mhm", "ah", "uh-huh", "mm-hmm"}
NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
    "thirteen": "13", "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}


def fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def norm_tokens(words: list[str]) -> list[str]:
    tokens = []
    for word in words:
        for token in re.findall(r"[a-z0-9']+", fold(word)):
            token = token.strip("'")
            if token and token not in FILLERS:
                tokens.append(NUMBER_WORDS.get(token, token))
    return tokens


def edit_distance(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, token_a in enumerate(a, 1):
        current = [i] + [0] * len(b)
        for j, token_b in enumerate(b, 1):
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (token_a != token_b))
        previous = current
    return previous[-1]


def windows_for(track: dict, window: float) -> dict[int, list[dict]]:
    buckets: dict[int, list[dict]] = defaultdict(list)
    for word in track["words"]:
        buckets[int(word["s"] // window)].append(word)
    return buckets


def covered_seconds(words: list[dict], pad: float = 0.25, max_word: float = 1.5) -> float:
    """Seconds of audio covered by recognized words (word spans capped so a word
    remapped across removed silence does not count minutes of coverage)."""
    total, end = 0.0, -1.0
    for word in sorted(words, key=lambda w: w["s"]):
        start, stop = word["s"] - pad, min(word["e"], word["s"] + max_word) + pad
        if start > end:
            total += stop - start
        elif stop > end:
            total += stop - end
        end = max(end, stop)
    return total


def loop_count(words: list[dict]) -> int:
    tokens = norm_tokens([w["w"] for w in words])
    loops, i = 0, 0
    while i < len(tokens):
        found = False
        for size in range(1, 7):
            gram = tokens[i:i + size]
            if len(gram) < size:
                break
            repeats = 1
            while tokens[i + repeats * size: i + (repeats + 1) * size] == gram:
                repeats += 1
            if repeats >= (4 if size == 1 else 3):
                loops += 1
                i += repeats * size
                found = True
                break
        if not found:
            i += 1
    return loops


def campaign_names(session: str | None, common: set[str] | None = None) -> list[str]:
    sys.path.insert(0, str(SCRIPT_DIR))
    import transcribe_gladia  # light import; transcribe.py itself pulls torch lazily via spec

    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    terms = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, session, module)
    names = set()
    for term in terms + ["Berridin", "Ellara", "Nyx", "Ysidor", "Witty", "Meri", "Din"]:
        for word in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", term):
            word = word.replace("'s", "")
            if len(word) >= 3 and word[0].isupper() and (not common or word.lower() not in common or word in {"Witty", "Din"}):
                names.add(word)
    return sorted(names)


def name_stats(track_words: list[str], names: list[str], common: set[str]) -> dict:
    folded_names = {fold(n): n for n in names}
    hits: Counter = Counter()
    near: Counter = Counter()
    for raw in track_words:
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", raw):
            base = token[:-2] if token.lower().endswith("'s") else token
            key = fold(base)
            if len(key) < 3:
                continue
            if key in folded_names:
                hits[folded_names[key]] += 1
                continue
            if key in common or len(key) < 4:
                continue
            match = difflib.get_close_matches(key, list(folded_names), n=1, cutoff=0.72)
            if match:
                near[f"{base} -> {folded_names[match[0]]}"] += 1
    return {"hits": sum(hits.values()), "near_misses": sum(near.values()), "top_hits": hits.most_common(12), "top_near": near.most_common(15)}


def clip_audio(audio: Path, start: float, end: float, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, start):.2f}", "-t", f"{end - start:.2f}",
         "-i", str(audio), "-ac", "1", "-ar", "16000", "-b:a", "48k", str(dest)],
        check=True,
    )


def judge_clip(sample: dict, names: list[str], model: str | None) -> dict:
    sys.path.insert(0, str(SCRIPT_DIR))
    import agent_cli

    with tempfile.TemporaryDirectory(prefix="asr-judge-") as tmp:
        clip = Path(tmp) / f"clip_{int(sample['start'])}.mp3"
        clip_audio(Path(sample["audio_file"]), sample["start"] - 0.4, sample["end"] + 0.4, clip)
        prompt = (
            "You are checking a speech-recognition transcript of a Dungeons & Dragons session.\n"
            f"Listen to the attached audio clip ({clip.name}) and transcribe verbatim what the main, "
            "closest speaker says. Ignore faint background voices. Use these campaign spellings when you "
            f"hear them: {', '.join(names[:60])}.\n"
            "Output only the transcript text on one line. If there is no intelligible speech, output NO_SPEECH."
        )
        try:
            heard = agent_cli.run_agy(prompt, Path(tmp), model, write=False, attachments=[clip], timeout=300)
        except Exception as exc:  # noqa: BLE001 - keep the report going
            return {**sample, "judge_text": None, "judge_error": str(exc)[:300]}

    heard = heard.strip().splitlines()[-1] if heard.strip() else ""
    ref = norm_tokens(heard.split()) if "NO_SPEECH" not in heard else []
    scores = {}
    for engine, text in sample["texts"].items():
        hyp = norm_tokens(text.split())
        scores[engine] = edit_distance(ref, hyp) / max(1, len(ref)) if ref else (0.0 if not hyp else 1.0)
    best = min(scores.values())
    winners = [e for e, s in scores.items() if s - best < 0.05]
    return {**sample, "judge_text": heard, "judge_wer": scores, "judge_winner": winners[0] if len(winners) == 1 else "tie"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-dir", required=True, help="Directory containing <engine>/<track>.json")
    parser.add_argument("--session")
    parser.add_argument("--engines", help="Comma list; default: every engine dir present")
    parser.add_argument("--primary", default="gladia")
    parser.add_argument("--window", type=float, default=15.0)
    parser.add_argument("--hotspots", type=int, default=25)
    parser.add_argument("--judge", choices=["agy"], help="Listen to hotspot clips with Gemini via agy")
    parser.add_argument("--judge-model")
    parser.add_argument("--judge-samples", type=int, default=16)
    parser.add_argument("--judge-workers", type=int, default=3)
    parser.add_argument("--out-md", help="Default: <work-dir>/ASR Diagnostics.md")
    args = parser.parse_args()

    work_dir = Path(args.work_dir).expanduser().resolve()
    engine_names = (
        [e.strip() for e in args.engines.split(",")]
        if args.engines
        else sorted(p.name for p in work_dir.iterdir() if p.is_dir() and any(p.glob("*.json")))
    )
    engines = {name: asr_common.load_engine_dir(work_dir / name) for name in engine_names}
    engines = {k: v for k, v in engines.items() if v}
    if len(engines) < 1:
        raise SystemExit(f"no engine outputs under {work_dir}")
    primary = args.primary if args.primary in engines else next(iter(engines))
    others = [e for e in engines if e != primary]
    tracks = sorted(set().union(*[set(v) for v in engines.values()]))
    common = {l.strip() for l in WORDLIST.read_text(errors="ignore").splitlines() if l.strip().islower()} if WORDLIST.exists() else set()
    names = campaign_names(args.session, common)
    sys.path.insert(0, str(SCRIPT_DIR))
    from name_normalizer import NameNormalizer

    normalizer = NameNormalizer()

    report: dict = {"session": args.session, "primary": primary, "engines": {}, "tracks": {}, "hotspots": [], "one_sided": []}

    for engine, data in engines.items():
        words = [w for t in data.values() for w in t["words"]]
        confidences = [w["p"] for w in words if w.get("p") is not None]
        speech = sum(t.get("speech_seconds") or 0 for t in data.values())
        elapsed = sum((t.get("params") or {}).get("elapsed_seconds") or 0 for t in data.values())
        report["engines"][engine] = {
            "tracks": len(data),
            "words": len(words),
            "speech_minutes": round(speech / 60, 1),
            "covered_minutes": round(sum(covered_seconds(t["words"]) for t in data.values()) / 60, 1),
            "low_conf_rate": round(sum(p < 0.5 for p in confidences) / len(confidences), 3) if confidences else None,
            "mean_conf": round(sum(confidences) / len(confidences), 3) if confidences else None,
            "loops": sum(loop_count(t["words"]) for t in data.values()),
            "elapsed_minutes": round(elapsed / 60, 1) if elapsed else None,
            # Names are scored after the pipeline's own deterministic name fixes,
            # so engines are compared on the errors that would actually survive.
            "names": name_stats([normalizer.normalize(s["text"]) for t in data.values() for s in t["segments"]], names, common),
        }

    for other in others:
        edits_total = tokens_total = 0
        for track in tracks:
            a, b = engines[primary].get(track), engines[other].get(track)
            if not a or not b:
                continue
            wa, wb = windows_for(a, args.window), windows_for(b, args.window)
            partial = bool((b.get("params") or {}).get("partial"))
            track_edits = track_tokens = 0
            for index in sorted(set(wa) | set(wb)):
                ta = norm_tokens([w["w"] for w in wa.get(index, [])])
                tb = norm_tokens([w["w"] for w in wb.get(index, [])])
                if partial and not tb:
                    continue  # partial engines (Gemini on disputed lines) only cover some windows
                edits = edit_distance(ta, tb)
                track_edits += edits
                track_tokens += len(ta)
                start = index * args.window
                sample = {
                    "track": track,
                    "audio_file": a["audio_file"],
                    "start": start,
                    "end": start + args.window,
                    "edits": edits,
                    "texts": {
                        primary: " ".join(w["w"] for w in wa.get(index, [])),
                        other: " ".join(w["w"] for w in wb.get(index, [])),
                    },
                }
                if (len(ta) >= 5 and not tb) or (len(tb) >= 5 and not ta):
                    sample["only"] = primary if ta else other
                    report["one_sided"].append(sample)
                elif edits >= 5 and edits / max(1, max(len(ta), len(tb))) >= 0.3:
                    report["hotspots"].append(sample)
            report["tracks"].setdefault(track, {})[f"{primary}_vs_{other}"] = {
                "disagreement": round(track_edits / max(1, track_tokens), 3),
                "primary_tokens": track_tokens,
            }
            edits_total += track_edits
            tokens_total += track_tokens
        report["engines"][other]["disagreement_vs_primary"] = round(edits_total / max(1, tokens_total), 3)

    report["hotspots"].sort(key=lambda s: s["edits"], reverse=True)
    report["one_sided"].sort(key=lambda s: -max(len(t.split()) for t in s["texts"].values()))

    if args.judge and others:
        pool_samples = report["hotspots"][: args.judge_samples] + report["one_sided"][: max(4, args.judge_samples // 4)]
        print(f"Judging {len(pool_samples)} clips with agy...", flush=True)
        with ThreadPoolExecutor(max_workers=args.judge_workers) as pool:
            judged = list(pool.map(lambda s: judge_clip(s, names, args.judge_model), pool_samples))
        report["judged"] = judged
        report["judge_tally"] = dict(Counter(j.get("judge_winner", "error") for j in judged))

    out_md = Path(args.out_md) if args.out_md else work_dir / "ASR Diagnostics.md"
    (out_md.with_suffix(".json")).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report, args.hotspots), encoding="utf-8")
    print(f"Wrote {out_md}")
    return 0


def render_markdown(report: dict, hotspot_limit: int) -> str:
    primary = report["primary"]
    out = [f"# ASR Diagnostics — Session {report.get('session') or '?'}", "", f"Primary engine: `{primary}`", ""]
    out += ["## Engines", "", "Low-conf rate uses each engine's own confidence scale (not comparable across engines). Name counts are after name_corrections.json is applied.", ""]
    out += ["| engine | speech min | covered min | words | low-conf rate | loops | names hit | near-miss names | disagreement vs primary | local runtime min |", "|---|---|---|---|---|---|---|---|---|---|"]
    for engine, stats in report["engines"].items():
        out.append(
            f"| {engine} | {stats['speech_minutes']} | {stats['covered_minutes']} | {stats['words']} | "
            f"{stats['low_conf_rate'] if stats['low_conf_rate'] is not None else '-'} | {stats['loops']} | "
            f"{stats['names']['hits']} | {stats['names']['near_misses']} | {stats.get('disagreement_vs_primary', '-')} | "
            f"{stats['elapsed_minutes'] or '-'} |"
        )
    if report.get("judge_tally"):
        out += ["", "## Audio judge (Gemini listened to hotspot clips)", "", f"Wins: {report['judge_tally']}", ""]
        out += ["| track | time | winner | judge heard | " + " | ".join(report["engines"]) + " |", "|---|---|---|---|" + "---|" * len(report["engines"])]
        for j in report.get("judged", []):
            texts = " | ".join((j["texts"].get(e) or "")[:120].replace("|", "/") for e in report["engines"])
            heard = (j.get("judge_text") or j.get("judge_error") or "")[:120].replace("|", "/")
            out.append(f"| {j['track']} | {asr_common.format_ts(j['start'])} | {j.get('judge_winner', 'error')} | {heard} | {texts} |")
    out += ["", "## Names", ""]
    for engine, stats in report["engines"].items():
        near = ", ".join(f"{k} ({v})" for k, v in stats["names"]["top_near"]) or "none"
        hits = ", ".join(f"{k} ({v})" for k, v in stats["names"]["top_hits"])
        out += [f"**{engine}** — hits: {hits}", "", f"near misses: {near}", ""]
    out += ["## Per-track disagreement", ""]
    for track, comps in report["tracks"].items():
        out.append(f"- {track}: " + ", ".join(f"{k} {v['disagreement']:.1%} over {v['primary_tokens']} words" for k, v in comps.items()))
    out += ["", f"## Top disagreement hotspots ({len(report['hotspots'])} total)", ""]
    for sample in report["hotspots"][:hotspot_limit]:
        out.append(f"### {sample['track']} @ {asr_common.format_ts(sample['start'])} ({sample['edits']} edits)")
        for engine, text in sample["texts"].items():
            out.append(f"- **{engine}**: {text}")
        out.append("")
    out += [f"## One-sided windows ({len(report['one_sided'])} total; missed speech or hallucination)", ""]
    for sample in report["one_sided"][:15]:
        out.append(f"- {sample['track']} @ {asr_common.format_ts(sample['start'])} only **{sample['only']}**: {sample['texts'][sample['only']][:200]}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
