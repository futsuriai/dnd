#!/usr/bin/env python3
"""Compare ASR engines on one session without a human reference transcript.

Reads <work-dir>/<engine>/<track>.json (dnd-asr-v1) for two or more engines and
writes a Markdown + JSON report plus `hotspot_segments.json` (directly
consumable by `asr_gemini_windows.py --hotspots-json`):

- coverage: VAD speech time vs time covered by recognized words
- agreement: utterance-aligned word-level disagreement between engines, with
  separate dice/number and campaign-entity disagreement metrics
- multi-engine hotspots: all engines' readings populated side-by-side (fixes
  missing columns when 3+ engines are present)
- one-sided speech: utterances only one engine transcribed
- names: canonical campaign-name hits vs near-miss spellings + candidate
  `name_corrections_draft`
- loops/confidence: repeated-phrase loops and low-confidence word rates
- optional audio judge: Gemini 4 Neon (`gemini-4-neon-high`) with `--json-schema`
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

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent
WORDLIST = Path("/usr/share/dict/words")
FILLERS = {"um", "uh", "erm", "hmm", "mm", "mhm", "ah", "uh-huh", "mm-hmm"}
NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
    "thirteen": "13", "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50",
}
DICE_CONTEXT_WORDS = {
    "roll", "rolled", "nat", "natural", "crit", "dc", "check", "save", "damage", "hit",
    "d20", "d12", "d10", "d8", "d6", "d4", "d100", "initiative", "stealth", "perception",
    "insight", "persuasion", "deception", "arcana", "athletics", "acrobatics",
}

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["speech", "mic_bleed", "no_speech"]},
        "text": {"type": "string"},
    },
    "required": ["status", "text"],
}


def fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def norm_tokens(words: list[str]) -> list[str]:
    raw: list[str] = []
    for word in words:
        for token in re.findall(r"[a-z0-9']+", fold(word)):
            token = token.strip("'")
            if token and token not in FILLERS:
                raw.append(NUMBER_WORDS.get(token, token))
    tokens: list[str] = []
    i = 0
    while i < len(raw):
        if raw[i] in {"20", "30", "40", "50"} and i + 1 < len(raw) and raw[i + 1].isdigit() and len(raw[i + 1]) == 1:
            tokens.append(str(int(raw[i]) + int(raw[i + 1])))
            i += 2
            continue
        tokens.append(raw[i])
        i += 1
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
    """Legacy fixed-grid bucketing (kept for external callers)."""
    buckets: dict[int, list[dict]] = defaultdict(list)
    for word in track["words"]:
        buckets[int(word["s"] // window)].append(word)
    return buckets


def build_utterance_windows(
    primary_track: dict,
    other_track: dict | None = None,
    *,
    max_window: float = 15.0,
    split_gap: float = 1.2,
) -> list[tuple[float, float]]:
    """Build natural utterance-aligned time spans instead of cutting mid-sentence on a fixed grid."""
    all_words = sorted(
        (primary_track.get("words") or []) + ((other_track or {}).get("words") or []),
        key=lambda w: float(w["s"]),
    )
    if not all_words:
        return []

    spans: list[tuple[float, float]] = []
    cur_start = float(all_words[0]["s"])
    cur_end = min(float(all_words[0]["e"]), cur_start + 1.5)

    for word in all_words[1:]:
        ws = float(word["s"])
        we = min(float(word["e"]), ws + 1.5)
        gap = ws - cur_end
        span_len = we - cur_start
        if gap > split_gap or span_len > max_window:
            spans.append((round(cur_start, 3), round(max(cur_end, cur_start + 0.1), 3)))
            cur_start, cur_end = ws, max(ws, we)
        else:
            cur_end = max(cur_end, we)

    spans.append((round(cur_start, 3), round(max(cur_end, cur_start + 0.1), 3)))
    return spans


def words_in_span(track: dict | None, start: float, end: float, pad: float = 0.2) -> list[dict]:
    if not track:
        return []
    out = []
    for w in track.get("words", []):
        ws = float(w["s"])
        we = min(float(w["e"]), ws + 1.5)
        mid = 0.5 * (ws + we)
        if start - pad <= mid <= end + pad:
            out.append(w)
    return out


def covered_seconds(words: list[dict], pad: float = 0.25, max_word: float = 1.5) -> float:
    """Seconds of audio covered by recognized words."""
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
            gram = tokens[i : i + size]
            if len(gram) < size:
                break
            repeats = 1
            while tokens[i + repeats * size : i + (repeats + 1) * size] == gram:
                repeats += 1
            if repeats >= (4 if size == 1 else 3):
                loops += 1
                i += repeats * size
                found = True
                break
        if not found:
            i += 1
    return loops


def _party_names_from_metadata() -> list[str]:
    meta = DND_DIR / "scripts" / "transcription" / "entity_metadata.json"
    if not meta.exists():
        return ["Berridin", "Ellara", "Nyx", "Ysidor", "Witty", "Meri", "Din"]
    try:
        entities = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["Berridin", "Ellara", "Nyx", "Ysidor", "Witty", "Meri", "Din"]
    names = []
    for e in entities:
        if e.get("type") == "Characters":
            names.append(str(e.get("name", "")))
    return names + ["Meri", "Din"]


def campaign_names(session: str | None, common: set[str] | None = None) -> list[str]:
    sys.path.insert(0, str(SCRIPT_DIR))
    import transcribe_gladia

    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    terms = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, session, module)
    names = set()
    for term in terms + _party_names_from_metadata():
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
    return {
        "hits": sum(hits.values()),
        "near_misses": sum(near.values()),
        "top_hits": hits.most_common(12),
        "top_near": near.most_common(15),
    }


def _collect_all_engine_texts(
    engines: dict[str, dict[str, dict]], track: str, start: float, end: float
) -> dict[str, str]:
    """Populate texts for EVERY engine in the report (fixes 3+ engine table blank columns)."""
    texts: dict[str, str] = {}
    for eng_name, eng_tracks in engines.items():
        track_data = eng_tracks.get(track)
        texts[eng_name] = " ".join(w["w"] for w in words_in_span(track_data, start, end))
    return texts


def _dedupe_samples(samples: list[dict], overlap_tol: float = 1.0) -> list[dict]:
    """Keep the highest-edit sample when multiple engine pairs flag the same utterance."""
    samples_sorted = sorted(samples, key=lambda s: (-s.get("edits", 0), s["track"], s["start"]))
    kept: list[dict] = []
    for sample in samples_sorted:
        dup = any(
            k["track"] == sample["track"]
            and k["start"] <= sample["end"] + overlap_tol
            and k["end"] >= sample["start"] - overlap_tol
            for k in kept
        )
        if not dup:
            kept.append(sample)
    return kept


def clip_audio(audio: Path, start: float, end: float, dest_stem: Path) -> Path:
    duration = max(0.1, end - max(0.0, start))
    ogg_dest = dest_stem.with_suffix(".ogg")
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, start):.2f}", "-t", f"{duration:.2f}",
            "-i", str(audio), "-ac", "1", "-ar", "16000", "-c:a", "libopus", "-b:a", "48k",
            "-application", "voip", str(ogg_dest),
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0 and ogg_dest.exists() and ogg_dest.stat().st_size > 0:
        return ogg_dest
    wav_dest = dest_stem.with_suffix(".wav")
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, start):.2f}", "-t", f"{duration:.2f}",
            "-i", str(audio), "-ac", "1", "-ar", "16000", str(wav_dest),
        ],
        check=True,
    )
    return wav_dest


def judge_clip(sample: dict, names: list[str], hints: str, model: str | None) -> dict:
    sys.path.insert(0, str(SCRIPT_DIR))
    import agent_cli

    resolved_model = agent_cli.resolve_model("agy", model or agent_cli.AGY_TIERS["strong"])
    with tempfile.TemporaryDirectory(prefix="asr-judge-") as tmp:
        clip = clip_audio(Path(sample["audio_file"]), sample["start"] - 0.4, sample["end"] + 0.4, Path(tmp) / f"clip_{int(sample['start'])}")
        prompt = (
            "You are checking a speech-recognition transcript of a Dungeons & Dragons session.\n"
            f"Listen to the attached audio clip ({clip.name}) for track `{sample['track']}` and transcribe "
            "verbatim what the main, closest speaker says. Ignore faint background voices from other microphones.\n"
            f"Use these campaign spellings when you hear them: {', '.join(names[:100])}.\n"
            f"{hints}\n\n"
            'Return JSON matching the schema: {"status": "speech"|"mic_bleed"|"no_speech", "text": "<verbatim text or empty>"}'
        )
        try:
            raw = agent_cli.run_agent(
                prompt,
                provider="agy",
                model=resolved_model,
                workspace=Path(tmp),
                write=False,
                attachments=[clip],
                json_schema=JUDGE_SCHEMA,
                timeout=300,
                retries=1,
            )
            parsed = agent_cli.extract_json(raw)
            status = str(parsed.get("status", "speech")).lower()
            heard = str(parsed.get("text", "")).strip() if status == "speech" else status.upper()
        except Exception as exc:  # noqa: BLE001 - keep the report going
            return {**sample, "judge_text": None, "judge_error": str(exc)[:300]}

    ref = norm_tokens(heard.split()) if status == "speech" and heard else []
    scores = {}
    for engine, text in sample["texts"].items():
        hyp = norm_tokens(text.split())
        scores[engine] = edit_distance(ref, hyp) / max(1, len(ref)) if ref else (0.0 if not hyp else 1.0)
    best = min(scores.values())
    winners = [e for e, s in scores.items() if s - best < 0.05]
    return {
        **sample,
        "judge_status": status,
        "judge_text": heard,
        "judge_wer": scores,
        "judge_winner": winners[0] if len(winners) == 1 else "tie",
    }


def _draft_name_corrections(report: dict) -> dict[str, str]:
    """Build candidate name_corrections.json entries from recurring near-misses."""
    counts: Counter = Counter()
    for stats in report["engines"].values():
        for pair, cnt in stats["names"]["top_near"]:
            counts[pair] += cnt
    draft: dict[str, str] = {}
    for pair, cnt in counts.most_common():
        if cnt < 2 or " -> " not in pair:
            continue
        wrong, right = pair.split(" -> ", 1)
        if wrong != right and wrong not in draft:
            draft[wrong] = right
    return draft


def compute_diagnostics(
    engines: dict[str, dict[str, dict]],
    primary: str,
    *,
    session: str | None = None,
    window: float = 15.0,
    names: list[str] | None = None,
    common: set[str] | None = None,
    normalizer=None,
) -> dict:
    """Compute diagnostics report dict across 1..N engines (unit-testable core)."""
    others = [e for e in engines if e != primary]
    tracks = sorted(set().union(*[set(v) for v in engines.values()]))
    common_set = common or set()
    names_list = names if names is not None else campaign_names(session, common_set)
    folded_entities = {fold(n) for n in names_list}

    if normalizer is None:
        sys.path.insert(0, str(SCRIPT_DIR))
        from name_normalizer import NameNormalizer

        normalizer = NameNormalizer()

    report: dict = {
        "session": session,
        "primary": primary,
        "engines": {},
        "tracks": {},
        "hotspots": [],
        "one_sided": [],
    }

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
            "names": name_stats([normalizer.normalize(s["text"]) for t in data.values() for s in t["segments"]], names_list, common_set),
        }

    raw_hotspots: list[dict] = []
    raw_one_sided: list[dict] = []

    for other in others:
        edits_total = tokens_total = 0
        dice_edits_total = dice_tokens_total = 0
        entity_edits_total = entity_tokens_total = 0

        for track in tracks:
            a, b = engines[primary].get(track), engines[other].get(track)
            if not a or not b:
                continue
            partial = bool((b.get("params") or {}).get("partial"))
            spans = build_utterance_windows(a, b, max_window=window)
            track_edits = track_tokens = 0

            for start, end in spans:
                wa = words_in_span(a, start, end)
                wb = words_in_span(b, start, end)
                ta = norm_tokens([w["w"] for w in wa])
                tb = norm_tokens([w["w"] for w in wb])
                if partial and not tb:
                    continue
                edits = edit_distance(ta, tb)
                track_edits += edits
                track_tokens += len(ta)

                # Separate dice/number metrics.
                da = [t for t in ta if t.isdigit() or t in DICE_CONTEXT_WORDS]
                db = [t for t in tb if t.isdigit() or t in DICE_CONTEXT_WORDS]
                if da or db:
                    dice_edits_total += edit_distance(da, db)
                    dice_tokens_total += max(len(da), len(db))

                # Separate campaign-entity metrics.
                ea = [t for t in ta if t in folded_entities]
                eb = [t for t in tb if t in folded_entities]
                if ea or eb:
                    entity_edits_total += edit_distance(ea, eb)
                    entity_tokens_total += max(len(ea), len(eb))

                if (len(ta) >= 4 and not tb) or (len(tb) >= 4 and not ta):
                    all_texts = _collect_all_engine_texts(engines, track, start, end)
                    raw_one_sided.append({
                        "track": track,
                        "audio_file": a["audio_file"],
                        "start": start,
                        "end": end,
                        "edits": edits,
                        "only": primary if ta else other,
                        "compared_pair": [primary, other],
                        "texts": all_texts,
                    })
                elif edits >= 4 and edits / max(1, max(len(ta), len(tb))) >= 0.25:
                    all_texts = _collect_all_engine_texts(engines, track, start, end)
                    raw_hotspots.append({
                        "track": track,
                        "audio_file": a["audio_file"],
                        "start": start,
                        "end": end,
                        "edits": edits,
                        "compared_pair": [primary, other],
                        "texts": all_texts,
                    })

            report["tracks"].setdefault(track, {})[f"{primary}_vs_{other}"] = {
                "disagreement": round(track_edits / max(1, track_tokens), 3),
                "primary_tokens": track_tokens,
            }
            edits_total += track_edits
            tokens_total += track_tokens

        report["engines"][other]["disagreement_vs_primary"] = round(edits_total / max(1, tokens_total), 3)
        report["engines"][other]["dice_number_disagreement"] = (
            round(dice_edits_total / dice_tokens_total, 3) if dice_tokens_total else None
        )
        report["engines"][other]["entity_disagreement"] = (
            round(entity_edits_total / entity_tokens_total, 3) if entity_tokens_total else None
        )

    report["hotspots"] = _dedupe_samples(raw_hotspots)
    report["one_sided"] = sorted(
        _dedupe_samples(raw_one_sided),
        key=lambda s: -max((len(t.split()) for t in s["texts"].values()), default=0),
    )
    report["name_corrections_draft"] = _draft_name_corrections(report)
    return report


def export_hotspot_segments(report: dict, out_path: Path, limit: int = 200) -> Path:
    """Export hotspots + one-sided segments in the schema consumed by `asr_gemini_windows.py --hotspots-json`."""
    segments = []
    for sample in report["hotspots"][:limit]:
        segments.append({
            "track": sample["track"],
            "audio_file": sample["audio_file"],
            "start": sample["start"],
            "end": sample["end"],
            "reason": "hotspot",
            "edits": sample["edits"],
            "texts": sample["texts"],
        })
    for sample in report["one_sided"][:limit]:
        segments.append({
            "track": sample["track"],
            "audio_file": sample["audio_file"],
            "start": sample["start"],
            "end": sample["end"],
            "reason": f"one_sided:{sample.get('only', '')}",
            "edits": sample["edits"],
            "texts": sample["texts"],
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"session": report.get("session"), "segments": segments}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-dir", required=True, help="Directory containing <engine>/<track>.json")
    parser.add_argument("--session")
    parser.add_argument("--engines", help="Comma list; default: every engine dir present")
    parser.add_argument("--primary", default="gladia")
    parser.add_argument("--window", type=float, default=15.0, help="Target max utterance window duration in seconds")
    parser.add_argument("--hotspots", type=int, default=25)
    parser.add_argument("--judge", choices=["agy"], help="Listen to hotspot clips with Gemini 4 Neon via agy")
    parser.add_argument("--judge-model", help="Default: gemini-4-neon-high")
    parser.add_argument("--judge-samples", type=int, default=16)
    parser.add_argument("--judge-workers", type=int, default=3)
    parser.add_argument("--out-md", help="Default: <work-dir>/ASR Diagnostics.md")
    parser.add_argument("--out-hotspots", help="Default: <work-dir>/hotspot_segments.json")
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
    common = (
        {l.strip() for l in WORDLIST.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip().islower()}
        if WORDLIST.exists()
        else set()
    )
    names = campaign_names(args.session, common)

    sys.path.insert(0, str(SCRIPT_DIR))
    from name_normalizer import NameNormalizer

    normalizer = NameNormalizer()
    report = compute_diagnostics(
        engines,
        primary,
        session=args.session,
        window=args.window,
        names=names,
        common=common,
        normalizer=normalizer,
    )

    if args.judge and others:
        pool_samples = report["hotspots"][: args.judge_samples] + report["one_sided"][: max(4, args.judge_samples // 4)]
        hints = normalizer.llm_hint_block()
        print(f"Judging {len(pool_samples)} clips with agy ({args.judge_model or 'gemini-4-neon-high'})...", flush=True)
        with ThreadPoolExecutor(max_workers=args.judge_workers) as pool:
            judged = list(pool.map(lambda s: judge_clip(s, names, hints, args.judge_model), pool_samples))
        report["judged"] = judged
        report["judge_tally"] = dict(Counter(j.get("judge_winner", "error") for j in judged))

    out_md = Path(args.out_md) if args.out_md else work_dir / "ASR Diagnostics.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.with_suffix(".json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report, args.hotspots), encoding="utf-8")

    hotspots_path = Path(args.out_hotspots) if args.out_hotspots else work_dir / "hotspot_segments.json"
    export_hotspot_segments(report, hotspots_path)
    print(f"Wrote {out_md} and {hotspots_path}")
    return 0


def render_markdown(report: dict, hotspot_limit: int) -> str:
    primary = report["primary"]
    engine_list = list(report["engines"].keys())
    out = [f"# ASR Diagnostics — Session {report.get('session') or '?'}", "", f"Primary engine: `{primary}`", ""]
    out += [
        "## Engines",
        "",
        "Low-conf rate uses each engine's own confidence scale. Disagreement is computed over utterance-aligned spans.",
        "",
        "| engine | speech min | covered min | words | low-conf rate | loops | names hit | near-miss | disagree vs primary | dice/num disagree | entity disagree | runtime min |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for engine, stats in report["engines"].items():
        out.append(
            f"| {engine} | {stats['speech_minutes']} | {stats['covered_minutes']} | {stats['words']} | "
            f"{stats['low_conf_rate'] if stats['low_conf_rate'] is not None else '-'} | {stats['loops']} | "
            f"{stats['names']['hits']} | {stats['names']['near_misses']} | {stats.get('disagreement_vs_primary', '-')} | "
            f"{stats.get('dice_number_disagreement') if stats.get('dice_number_disagreement') is not None else '-'} | "
            f"{stats.get('entity_disagreement') if stats.get('entity_disagreement') is not None else '-'} | "
            f"{stats['elapsed_minutes'] or '-'} |"
        )
    if report.get("judge_tally"):
        out += ["", "## Audio judge (Gemini 4 Neon listened to hotspot clips)", "", f"Wins: {report['judge_tally']}", ""]
        out += [
            "| track | time | winner | judge heard | " + " | ".join(engine_list) + " |",
            "|---|---|---|---|" + "---|" * len(engine_list),
        ]
        for j in report.get("judged", []):
            texts = " | ".join((j["texts"].get(e) or "")[:120].replace("|", "/") for e in engine_list)
            heard = (j.get("judge_text") or j.get("judge_error") or "")[:120].replace("|", "/")
            out.append(f"| {j['track']} | {asr_common.format_ts(j['start'])} | {j.get('judge_winner', 'error')} | {heard} | {texts} |")
    out += ["", "## Names", ""]
    for engine, stats in report["engines"].items():
        near = ", ".join(f"{k} ({v})" for k, v in stats["names"]["top_near"]) or "none"
        hits = ", ".join(f"{k} ({v})" for k, v in stats["names"]["top_hits"])
        out += [f"**{engine}** — hits: {hits}", "", f"near misses: {near}", ""]
    if report.get("name_corrections_draft"):
        out += ["### Candidate `name_corrections.json` additions", ""]
        for wrong, right in list(report["name_corrections_draft"].items())[:20]:
            out.append(f"- `{wrong}` -> `{right}`")
        out.append("")
    out += ["## Per-track disagreement", ""]
    for track, comps in report["tracks"].items():
        out.append(f"- {track}: " + ", ".join(f"{k} {v['disagreement']:.1%} over {v['primary_tokens']} words" for k, v in comps.items()))
    out += ["", f"## Top disagreement hotspots ({len(report['hotspots'])} total)", ""]
    for sample in report["hotspots"][:hotspot_limit]:
        out.append(f"### {sample['track']} @ {asr_common.format_ts(sample['start'])}–{asr_common.format_ts(sample['end'])} ({sample['edits']} edits)")
        for engine in engine_list:
            out.append(f"- **{engine}**: {sample['texts'].get(engine, '')}")
        out.append("")
    out += [f"## One-sided windows ({len(report['one_sided'])} total; missed speech or hallucination)", ""]
    for sample in report["one_sided"][:15]:
        only = sample["only"]
        out.append(f"- {sample['track']} @ {asr_common.format_ts(sample['start'])} only **{only}**: {sample['texts'].get(only, '')[:200]}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
