#!/usr/bin/env python3
"""Gemini (agy CLI) as an extra transcription reference on a primary engine's timings.

Gemini's own timestamps drift, and in long clips it loses track of which numbered
utterance is which. This engine avoids both problems:

1. take the reference engine's (normally Gladia's) per-track segments, pooled
   across tracks in spoken order
2. optionally keep only *disputed* segments: where the second engine
   (normally Whisper) heard something materially different
3. pack them into small blocks (~15 segments / ~90 s of speech); each block is
   one clip with every segment from its own speaker's isolated track, separated
   by short beeps, sent in parallel calls
4. ask Gemini for one numbered line per segment, with campaign spellings and the
   table's preceding lines as context
5. map Gemini's words back to segments by *content*: its text is aligned against
   the reference words of the block, so a slipped line number no longer shifts
   text onto the wrong utterance; blocks whose text barely matches the
   reference (wrong audio, hallucination) are dropped

Output: dnd-asr-v1 JSON per track under --out-dir, containing only the segments
Gemini covered (params.partial says so); word times are spread evenly inside each
segment because Gemini gives none. fuse_transcript.py uses it as a third reading.
"""

from __future__ import annotations

import argparse
import difflib
import math
import re
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import asr_common

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = SCRIPT_DIR.parent.parent
SAMPLE_RATE = 16000
LINE_RE = re.compile(r"^\s*(\d+)\s*[|:.)\]-]\s?(.*)$")
FILLERS = {"um", "uh", "erm", "hmm", "mm", "mhm", "ah"}


def norm(word: str) -> str:
    folded = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode("ascii").lower()
    return "".join(re.findall(r"[a-z0-9']+", folded)).strip("'")


def tokens(text: str) -> list[str]:
    return [t for t in (norm(w) for w in text.split()) if t and t not in FILLERS]


def beep(seconds: float = 0.1, freq: float = 880.0, gap: float = 0.3) -> bytes:
    silence = b"\x00\x00" * int(gap * SAMPLE_RATE)
    tone = b"".join(
        struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)))
        for i in range(int(seconds * SAMPLE_RATE))
    )
    return silence + tone + silence


def read_pcm(audio: str, start: float, end: float) -> bytes:
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, start):.3f}", "-t", f"{end - start:.3f}", "-i", audio,
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout


def collect_segments(tracks: dict[str, dict], speaker_of) -> list[dict]:
    pool = []
    for track, data in tracks.items():
        for seg in data["segments"]:
            if seg["text"].strip():
                pool.append({**seg, "track": track, "speaker": speaker_of(track), "audio": data["audio_file"]})
    pool.sort(key=lambda s: (s["s"], s["e"]))
    for index, seg in enumerate(pool):
        seg["idx"] = index
    return pool


def disputed(segments: list[dict], alt_tracks: dict[str, dict], threshold: float) -> list[dict]:
    """Segments where the second engine's words for the same span differ materially."""
    chosen = []
    for seg in segments:
        alt = alt_tracks.get(seg["track"])
        alt_words = [w["w"] for w in alt["words"] if seg["s"] - 0.35 <= w["s"] <= seg["e"] + 0.2] if alt else []
        a, b = tokens(seg["text"]), tokens(" ".join(alt_words))
        if not a:
            continue
        ratio = 1 - difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        if ratio >= threshold:
            seg["alt_text"] = " ".join(alt_words)
            chosen.append(seg)
    return chosen


def build_blocks(segments: list[dict], max_segments: int, max_speech: float, max_span: float) -> list[list[dict]]:
    blocks, current, speech = [], [], 0.0
    for seg in segments:
        duration = seg["e"] - seg["s"]
        if current and (
            len(current) >= max_segments
            or speech + duration > max_speech
            or seg["s"] - current[0]["s"] > max_span
        ):
            blocks.append(current)
            current, speech = [], 0.0
        current.append(seg)
        speech += duration
    if current:
        blocks.append(current)
    return blocks


def write_block_wav(block: list[dict], dest: Path) -> None:
    separator = beep()
    parts = [read_pcm(seg["audio"], seg["s"] - 0.15, seg["e"] + 0.15) for seg in block]
    with wave.open(str(dest), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(separator.join(parts))


def block_prompt(clip: str, block: list[dict], before: list[dict], names: list[str], hints: str) -> str:
    listing = "\n".join(f"{n} — {seg['speaker']}" for n, seg in enumerate(block, 1))
    previous = "\n".join(f"{s['speaker']}: {s['text']}" for s in before) or "(start of session)"
    return f"""Transcribe the attached audio clip {clip} from a Dungeons & Dragons session recorded over Discord.
It contains {len(block)} short speech segments in order, separated by beeps; each segment is one person:
{listing}

Return one line per segment, `<segment number>|<verbatim text>`, in order, and nothing else.
Verbatim: keep in-character voices, jokes, numbers and dice results; drop only um/uh. Faint voices from
other microphones may leak in; write only the listed speaker. If a segment is unintelligible, leave it empty.

Campaign spellings to use when you hear them: {', '.join(names)}.
{hints}

What the table said just before this clip (rough machine transcript, context only):
{previous}
"""


def gemini_words(reply: str) -> list[tuple[str, int]]:
    """(word, line number) pairs in reply order; tolerant of missing/odd numbering."""
    words = []
    line_no = 0
    for raw in reply.splitlines():
        if not raw.strip():
            continue
        match = LINE_RE.match(raw)
        line_no = int(match.group(1)) if match else line_no + 1
        text = match.group(2) if match else raw
        for word in text.split():
            words.append((word, line_no))
    return words


def realign(block: list[dict], reply: str) -> tuple[dict[int, str], float]:
    """Align against the primary text and the second engine's text; keep the better fit.

    Disputed segments are exactly where the primary text is unreliable, so the
    second engine's hearing is often the better anchor.
    """
    best: tuple[dict[int, str], float] = ({}, 0.0)
    for key in ("text", "alt_text"):
        if key == "alt_text" and not any(seg.get("alt_text") for seg in block):
            continue
        result = realign_against(block, reply, key)
        if result[1] > best[1]:
            best = result
    return best


def realign_against(block: list[dict], reply: str, key: str) -> tuple[dict[int, str], float]:
    """Assign Gemini's words to the block's segments by aligning against one reference."""
    ref, ref_seg = [], []
    for position, seg in enumerate(block):
        for tok in tokens(seg.get(key) or seg["text"]):
            ref.append(tok)
            ref_seg.append(position)
    gem = gemini_words(reply)
    gem_norm = [norm(w) for w, _ in gem]
    if not ref or not gem:
        return {}, 0.0

    assign: list[int | None] = [None] * len(gem)
    matcher = difflib.SequenceMatcher(None, ref, gem_norm, autojunk=False)
    matched = 0
    for a, b, size in matcher.get_matching_blocks():
        for k in range(size):
            assign[b + k] = ref_seg[a + k]
        matched += size

    # Unmatched words sit between two matched anchors: keep them with the anchor
    # on the same Gemini line, otherwise with the following anchor.
    anchors = [i for i, s in enumerate(assign) if s is not None]
    if not anchors:
        return {}, 0.0
    for i in range(len(gem)):
        if assign[i] is not None:
            continue
        prev_a = max((a for a in anchors if a < i), default=None)
        next_a = min((a for a in anchors if a > i), default=None)
        if prev_a is not None and (next_a is None or gem[prev_a][1] == gem[i][1]):
            assign[i] = assign[prev_a]
        else:
            assign[i] = assign[next_a]

    texts: dict[int, list[str]] = {}
    for (word, _), position in zip(gem, assign):
        texts.setdefault(position, []).append(word)
    coverage = matched / max(1, len(ref))
    return {block[p]["idx"]: " ".join(words) for p, words in texts.items()}, coverage


def spread_words(seg: dict, text: str) -> list[dict]:
    toks = text.split()
    if not toks:
        return []
    step = (seg["e"] - seg["s"]) / len(toks)
    return [{"s": seg["s"] + i * step, "e": seg["s"] + (i + 1) * step, "w": tok, "p": None} for i, tok in enumerate(toks)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference-dir", required=True, help="Primary engine dir, e.g. <session>/asr/gladia")
    parser.add_argument("--out-dir", required=True, help="Output engine dir, e.g. <session>/asr/gemini")
    parser.add_argument("--alt-dir", help="Second engine dir; with --select disputed, only disagreements go to Gemini")
    parser.add_argument("--select", choices=["all", "disputed"], default="disputed")
    parser.add_argument("--dispute-threshold", type=float, default=0.25, help="Token mismatch ratio that counts as disputed")
    parser.add_argument("--session")
    parser.add_argument("--model", help="agy model (default gemini-3.8-flash-high)")
    parser.add_argument("--block-segments", type=int, default=15)
    parser.add_argument("--block-speech-seconds", type=float, default=90.0)
    parser.add_argument("--block-span-seconds", type=float, default=600.0, help="Max table time one block may span")
    parser.add_argument("--min-match", type=float, default=0.3, help="Drop blocks whose text matches less of the reference")
    parser.add_argument("--context-lines", type=int, default=8)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit-blocks", type=int, help="Only process the first N blocks (testing)")
    parser.add_argument("--start-at", type=float, default=0.0, help="Skip segments before this many seconds (testing)")
    args = parser.parse_args()

    sys.path.insert(0, str(SCRIPT_DIR))
    import agent_cli
    import assemble_transcript
    import transcribe_gladia
    from name_normalizer import NameNormalizer

    tracks = asr_common.load_engine_dir(Path(args.reference_dir))
    speaker_map = assemble_transcript.load_speaker_map()
    pool = collect_segments(tracks, lambda t: assemble_transcript.identify_speaker(t, speaker_map))
    selected = [s for s in pool if s["s"] >= args.start_at]
    if args.select == "disputed":
        if not args.alt_dir:
            raise SystemExit("--select disputed needs --alt-dir")
        selected = disputed(selected, asr_common.load_engine_dir(Path(args.alt_dir)), args.dispute_threshold)
    blocks = build_blocks(selected, args.block_segments, args.block_speech_seconds, args.block_span_seconds)
    if args.limit_blocks:
        blocks = blocks[: args.limit_blocks]
    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    names = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, args.session, module)[:80]
    hints = NameNormalizer().llm_hint_block()
    speech = sum(s["e"] - s["s"] for b in blocks for s in b)
    print(f"{len(pool)} segments, {len(selected)} selected ({args.select}) -> {len(blocks)} blocks, {speech / 60:.1f} min of speech", flush=True)

    texts: dict[int, str] = {}
    stats = {"ok": 0, "dropped": 0, "errors": 0, "seconds": []}
    started = time.monotonic()

    def transcribe(block: list[dict]) -> None:
        first = block[0]["idx"]
        before = pool[max(0, first - args.context_lines): first]
        with tempfile.TemporaryDirectory(prefix="gemini-block-") as tmp:
            clip = Path(tmp) / f"block_{int(block[0]['s']):06d}.wav"
            write_block_wav(block, clip)
            t0 = time.monotonic()
            try:
                reply = agent_cli.run_agy(
                    block_prompt(clip.name, block, before, names, hints), Path(tmp), args.model,
                    write=False, attachments=[clip], timeout=900,
                )
            except Exception as exc:  # noqa: BLE001
                stats["errors"] += 1
                print(f"  block @{asr_common.format_ts(block[0]['s'])}: agy error {str(exc)[:200]}", flush=True)
                return
        elapsed = time.monotonic() - t0
        stats["seconds"].append(elapsed)
        aligned, coverage = realign(block, reply)
        if coverage < args.min_match:
            stats["dropped"] += 1
            print(f"  block @{asr_common.format_ts(block[0]['s'])}: dropped (matched {coverage:.0%} of reference) {elapsed:.0f}s", flush=True)
            return
        texts.update(aligned)
        stats["ok"] += 1
        print(f"  block @{asr_common.format_ts(block[0]['s'])}: {len(block)} segments, matched {coverage:.0%}, {elapsed:.0f}s", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool_exec:
        list(pool_exec.map(transcribe, blocks))

    covered = {s["idx"] for b in blocks for s in b}
    out_dir = Path(args.out_dir)
    for track, data in tracks.items():
        out_segments, words = [], []
        for seg in pool:
            if seg["track"] != track or seg["idx"] not in covered or seg["idx"] not in texts:
                continue
            out_segments.append({"s": seg["s"], "e": seg["e"], "text": texts[seg["idx"]]})
            words.extend(spread_words(seg, texts[seg["idx"]]))
        asr_common.write_engine_json(
            out_dir / f"{track}.json",
            engine="gemini",
            model=args.model or agent_cli.DEFAULT_MODELS["agy"],
            audio_file=Path(data["audio_file"]),
            words=words,
            segments=out_segments,
            duration=data.get("duration"),
            speech_seconds=data.get("speech_seconds"),
            params={
                "reference_engine": data.get("engine"),
                "select": args.select,
                "partial": True,
                "blocks": len(blocks),
                "word_times": "spread evenly within reference segments",
                "elapsed_seconds": round(time.monotonic() - started, 1),
            },
        )
        asr_common.write_segment_txt(out_dir / f"{track}.txt", out_segments)
    per_call = sorted(stats["seconds"])
    median = per_call[len(per_call) // 2] if per_call else 0
    print(
        f"done in {time.monotonic() - started:.0f}s: {stats['ok']} blocks ok, {stats['dropped']} dropped, "
        f"{stats['errors']} errors; {len(texts)} segments covered; median call {median:.0f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
