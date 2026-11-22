#!/usr/bin/env python3
"""Audio-grounded Gemini 4 Neon arbitration over disputed / high-risk ASR segments.

Upgraded from blind transcription to structured audio-grounded arbitration:

1. Pools primary-engine segments (e.g. Gladia) AND one-sided secondary-engine
   segments (e.g. Whisper speech missed by Gladia VAD), plus optional external
   hotspots from `asr_diagnostics.py` (`hotspot_segments.json`).
2. Selects high-leverage segments using normalized diffing (`NUMBER_WORDS`),
   low word confidence (`p < 0.50`), spoken dice/numbers, hallucination loops,
   campaign-entity near-misses, and one-sided speech.
3. Packs segments into compact blocks encoded as 48 kbps mono `.ogg` (Opus,
   falling back to `.wav` if ffmpeg lacks libopus), caching completed blocks
   on disk for resumability.
4. Sends each block to `agy` (`gemini-4-neon-medium` by default, escalating to
   `gemini-4-neon-high` on parse/empty failures) with `--json-schema`, giving
   candidate primary/alt readings, preceding context, and concurrent
   overlapping-speaker lines (for mic-bleed rejection).
5. Parses per-segment structured verdicts `{idx, status, text, source}` instead
   of fragile whole-block `realign()` drops.

Outputs under --out-dir:
    <track>.json     dnd-asr-v1 JSON with Gemini-verified speech segments
    <track>.txt      per-track text transcript
    verdicts.json    all per-segment verdicts (speech, mic_bleed, no_speech)
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
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
from functools import lru_cache
from pathlib import Path

import asr_common

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent
SAMPLE_RATE = 16000
LINE_RE = re.compile(r"^\s*(\d+)\s*[|:.)\]-]\s?(.*)$")
FILLERS = {"um", "uh", "erm", "hmm", "mm", "mhm", "ah", "uh-huh", "mm-hmm"}
ENGLISH_WORDLIST = Path("/usr/share/dict/words")

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
    "forty": "40", "fifty": "50",
}

DICE_KEYWORDS = {
    "roll", "rolled", "rolling", "nat", "natural", "crit", "critical",
    "check", "save", "saving", "dc", "damage", "hit", "hits", "ac", "hp",
    "initiative", "stealth", "perception", "insight", "persuasion",
    "deception", "intimidation", "investigation", "arcana", "athletics",
    "acrobatics", "survival", "religion", "history", "nature", "medicine",
    "performance", "sleight", "d20", "d12", "d10", "d8", "d6", "d4", "d100",
}

ARBITRATION_SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "idx": {"type": "integer"},
                    "status": {"type": "string", "enum": ["speech", "mic_bleed", "no_speech"]},
                    "text": {"type": "string"},
                    "source": {
                        "type": "string",
                        "enum": ["primary", "alt", "combined", "audio_corrected", "none"],
                    },
                },
                "required": ["idx", "status", "text", "source"],
            },
        }
    },
    "required": ["segments"],
}


def norm(word: str) -> str:
    folded = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode("ascii").lower()
    cleaned = "".join(re.findall(r"[a-z0-9']+", folded)).strip("'")
    return NUMBER_WORDS.get(cleaned, cleaned)


def tokens(text: str) -> list[str]:
    """Normalized content tokens with compound number words collapsed."""
    raw = [norm(w) for w in text.split()]
    out: list[str] = []
    i = 0
    while i < len(raw):
        tok = raw[i]
        if not tok or tok in FILLERS:
            i += 1
            continue
        if tok in {"20", "30", "40", "50"} and i + 1 < len(raw) and raw[i + 1].isdigit() and len(raw[i + 1]) == 1:
            out.append(str(int(tok) + int(raw[i + 1])))
            i += 2
            continue
        out.append(tok)
        i += 1
    return out


def has_loop(text: str) -> bool:
    toks = tokens(text)
    n = len(toks)
    i = 0
    while i < n:
        for size in range(1, 5):
            gram = toks[i : i + size]
            if len(gram) < size:
                break
            repeats = 1
            while toks[i + repeats * size : i + (repeats + 1) * size] == gram:
                repeats += 1
            if repeats >= (4 if size == 1 else 3):
                return True
        i += 1
    return False


def has_dice_or_number_risk(primary_text: str, alt_text: str) -> bool:
    a, b = tokens(primary_text), tokens(alt_text)
    nums_a = [t for t in a if t.isdigit()]
    nums_b = [t for t in b if t.isdigit()]
    if nums_a != nums_b and (nums_a or nums_b):
        return True
    combined_set = set(a) | set(b)
    if (nums_a or nums_b) and (combined_set & DICE_KEYWORDS):
        return True
    return False


def has_entity_near_miss(text: str, entity_folded: set[str], common_words: set[str]) -> bool:
    if not entity_folded:
        return False
    entity_list = sorted(entity_folded)
    for raw in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text):
        base = raw[:-2] if raw.lower().endswith("'s") else raw
        key = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii").lower()
        if len(key) < 4 or key in entity_folded or key in common_words:
            continue
        if difflib.get_close_matches(key, entity_list, n=1, cutoff=0.76):
            return True
    return False


def beep(seconds: float = 0.1, freq: float = 880.0, gap: float = 0.3) -> bytes:
    silence = b"\x00\x00" * int(gap * SAMPLE_RATE)
    tone = b"".join(
        struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)))
        for i in range(int(seconds * SAMPLE_RATE))
    )
    return silence + tone + silence


def read_pcm(audio: str, start: float, end: float) -> bytes:
    duration = max(0.05, end - max(0.0, start))
    return subprocess.run(
        [
            "ffmpeg", "-v", "error", "-ss", f"{max(0.0, start):.3f}", "-t", f"{duration:.3f}",
            "-i", audio, "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-",
        ],
        check=True,
        capture_output=True,
    ).stdout


@lru_cache(maxsize=1)
def has_libopus() -> bool:
    try:
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            check=False,
            capture_output=True,
            text=True,
        )
        return "libopus" in proc.stdout
    except OSError:
        return False


def write_block_wav(block: list[dict], dest: Path) -> Path:
    separator = beep()
    parts = [read_pcm(seg["audio"], seg["s"] - 0.15, seg["e"] + 0.15) for seg in block]
    with wave.open(str(dest), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(separator.join(parts))
    return dest


def write_block_audio(block: list[dict], dest_stem: Path, prefer_opus: bool = True) -> Path:
    """Encode concatenated segment clip as 48 kbps mono .ogg (Opus), falling back to .wav."""
    separator = beep()
    pcm = separator.join(read_pcm(seg["audio"], seg["s"] - 0.15, seg["e"] + 0.15) for seg in block)
    if prefer_opus and has_libopus():
        ogg_path = dest_stem.with_suffix(".ogg")
        proc = subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "pipe:0",
                "-c:a", "libopus", "-b:a", "48k", "-application", "voip",
                str(ogg_path),
            ],
            input=pcm,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0 and ogg_path.exists() and ogg_path.stat().st_size > 0:
            return ogg_path

    wav_path = dest_stem.with_suffix(".wav")
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)
    return wav_path


def _words_in_span(track_data: dict | None, start: float, end: float, pad: float = 0.25) -> list[dict]:
    if not track_data:
        return []
    out = []
    for w in track_data.get("words", []):
        w_start = float(w["s"])
        w_end = min(float(w["e"]), w_start + 1.5)
        mid = 0.5 * (w_start + w_end)
        if start - pad <= mid <= end + pad:
            out.append(w)
    return out


def collect_segments(tracks: dict[str, dict], speaker_of) -> list[dict]:
    """Collect primary-engine segments (kept for backwards compatibility)."""
    return collect_union_segments(tracks, {}, speaker_of)


def collect_union_segments(
    ref_tracks: dict[str, dict],
    alt_tracks: dict[str, dict] | None,
    speaker_of,
    min_alt_tokens: int = 2,
) -> list[dict]:
    """Pool primary-engine segments PLUS Whisper/alt one-sided segments missed by primary."""
    pool: list[dict] = []
    for track, data in ref_tracks.items():
        for seg in data.get("segments", []):
            text = seg.get("text", "").strip()
            if not text:
                continue
            words = _words_in_span(data, seg["s"], seg["e"], pad=0.1)
            confs = [w["p"] for w in words if w.get("p") is not None]
            pool.append({
                "s": float(seg["s"]),
                "e": float(seg["e"]),
                "text": text,
                "track": track,
                "speaker": speaker_of(track),
                "audio": data["audio_file"],
                "origin": "reference",
                "mean_conf": (sum(confs) / len(confs)) if confs else None,
                "min_conf": min(confs) if confs else None,
            })

    if alt_tracks:
        for track, alt_data in alt_tracks.items():
            ref_data = ref_tracks.get(track)
            audio_file = (ref_data or alt_data).get("audio_file")
            if not audio_file:
                continue
            ref_segments = (ref_data or {}).get("segments", [])
            for seg in alt_data.get("segments", []):
                alt_text = seg.get("text", "").strip()
                if not alt_text:
                    continue
                s, e = float(seg["s"]), float(seg["e"])
                # Check if primary has any words or overlapping segment here.
                ref_words = _words_in_span(ref_data, s, e, pad=0.4)
                has_ref_seg = any(
                    float(rs["s"]) <= e + 0.4 and float(rs["e"]) >= s - 0.4
                    for rs in ref_segments
                )
                if ref_words or has_ref_seg:
                    continue
                toks = tokens(alt_text)
                has_digit_or_dice = any(t.isdigit() or t in DICE_KEYWORDS for t in toks)
                if len(toks) < min_alt_tokens and not has_digit_or_dice:
                    continue
                pool.append({
                    "s": s,
                    "e": e,
                    "text": "",
                    "alt_text": alt_text,
                    "track": track,
                    "speaker": speaker_of(track),
                    "audio": audio_file,
                    "origin": "alt_only",
                    "mean_conf": None,
                    "min_conf": None,
                })

    pool.sort(key=lambda s: (s["s"], s["e"], s["track"]))
    for index, seg in enumerate(pool):
        seg["idx"] = index
    return pool


def select_segments(
    segments: list[dict],
    alt_tracks: dict[str, dict] | None,
    *,
    threshold: float = 0.25,
    low_conf_threshold: float = 0.50,
    entity_names: list[str] | None = None,
    common_words: set[str] | None = None,
    external_hotspots: list[dict] | None = None,
    select_all: bool = False,
) -> list[dict]:
    """Select segments for audio arbitration using rich multi-signal triggers."""
    alt_tracks = alt_tracks or {}
    common = common_words or set()
    entity_folded = {
        unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode("ascii").lower()
        for name in (entity_names or [])
        for w in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", name)
        if len(w) >= 4
    }
    hotspots_by_track: dict[str, list[tuple[float, float]]] = {}
    for hs in external_hotspots or []:
        hotspots_by_track.setdefault(hs.get("track", ""), []).append(
            (float(hs.get("start", 0.0)), float(hs.get("end", 0.0)))
        )

    chosen: list[dict] = []
    for seg in segments:
        if seg.get("origin") == "alt_only":
            seg["reasons"] = ["one_sided_alt"]
            chosen.append(seg)
            continue

        alt = alt_tracks.get(seg["track"])
        alt_words = [w["w"] for w in _words_in_span(alt, seg["s"], seg["e"], pad=0.25)]
        alt_text = " ".join(alt_words).strip()
        seg["alt_text"] = alt_text

        a, b = tokens(seg["text"]), tokens(alt_text)
        reasons: list[str] = []

        if select_all:
            reasons.append("all")
        else:
            if alt is not None:
                if a and not b and len(a) >= 2:
                    reasons.append("one_sided_ref")
                elif a:
                    ratio = 1.0 - difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
                    if ratio >= threshold:
                        reasons.append(f"disagreement:{ratio:.2f}")

            min_conf = seg.get("min_conf")
            mean_conf = seg.get("mean_conf")
            if (min_conf is not None and min_conf < low_conf_threshold) or (
                mean_conf is not None and mean_conf < low_conf_threshold
            ):
                reasons.append("low_conf")

            if has_dice_or_number_risk(seg["text"], alt_text):
                reasons.append("dice_number")

            if has_loop(seg["text"]) or (alt_text and has_loop(alt_text)):
                reasons.append("loop")

            if has_entity_near_miss(seg["text"], entity_folded, common) or (
                alt_text and has_entity_near_miss(alt_text, entity_folded, common)
            ):
                reasons.append("entity_near_miss")

            for hs_s, hs_e in hotspots_by_track.get(seg["track"], []):
                if seg["s"] <= hs_e + 0.5 and seg["e"] >= hs_s - 0.5:
                    reasons.append("hotspot")
                    break

        if reasons:
            seg["reasons"] = reasons
            chosen.append(seg)

    return chosen


def disputed(segments: list[dict], alt_tracks: dict[str, dict], threshold: float) -> list[dict]:
    """Backwards-compatible wrapper around select_segments()."""
    return select_segments(segments, alt_tracks, threshold=threshold)


def build_blocks(segments: list[dict], max_segments: int, max_speech: float, max_span: float) -> list[list[dict]]:
    blocks, current, speech = [], [], 0.0
    for seg in segments:
        duration = max(0.1, seg["e"] - seg["s"])
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


def concurrent_speakers(seg: dict, pool: list[dict], pad: float = 0.5) -> list[dict]:
    """Return overlapping lines from OTHER speakers around seg's timestamp."""
    overlaps = []
    s, e = seg["s"] - pad, seg["e"] + pad
    for other in pool:
        if other["track"] == seg["track"]:
            continue
        if other["s"] > e:
            break
        if other["e"] >= s:
            text = other.get("text") or other.get("alt_text") or ""
            if text.strip():
                overlaps.append(other)
    return overlaps


def preceding_context(seg: dict, pool: list[dict], limit: int = 3) -> list[dict]:
    idx = seg.get("idx", 0)
    out = []
    for cand in reversed(pool[max(0, idx - 12) : idx]):
        text = cand.get("text") or cand.get("alt_text") or ""
        if text.strip():
            out.append(cand)
            if len(out) >= limit:
                break
    out.reverse()
    return out


def block_prompt(
    clip: str,
    block: list[dict],
    pool: list[dict],
    names: list[str],
    hints: str,
    context_lines: int = 3,
) -> str:
    """Build an audio-grounded arbitration prompt with candidate readings & overlap context."""
    items: list[str] = []
    for n, seg in enumerate(block, 1):
        ts = asr_common.format_ts(seg["s"], millis=True)
        reasons = ", ".join(seg.get("reasons") or ["check"])
        primary_txt = seg.get("text") or "(silence / not detected)"
        alt_txt = seg.get("alt_text") or "(silence / not detected)"
        lines_for_seg = [
            f"Segment {n} [{ts}] Speaker: {seg['speaker']} (triggers: {reasons})",
            f"  Primary ASR: {primary_txt}",
            f"  Alt ASR:     {alt_txt}",
        ]
        prev = preceding_context(seg, pool, limit=context_lines)
        if prev:
            prev_str = " | ".join(
                f"{p['speaker']}: {(p.get('text') or p.get('alt_text') or '')[:120]}" for p in prev
            )
            lines_for_seg.append(f"  Preceding table context: {prev_str}")
        overlaps = concurrent_speakers(seg, pool)
        if overlaps:
            ov_str = " | ".join(
                f"{o['speaker']}: {(o.get('text') or o.get('alt_text') or '')[:120]}" for o in overlaps[:4]
            )
            lines_for_seg.append(f"  Concurrent OTHER speakers (check for mic bleed!): {ov_str}")
        items.append("\n".join(lines_for_seg))

    listing = "\n\n".join(items)
    return f"""You are an audio-grounded speech arbitration judge for a Dungeons & Dragons session recorded over Discord (one isolated track per speaker).

Listen carefully to the attached audio clip ({clip}). It contains {len(block)} short speech segments in order, separated by short 880 Hz beeps.
For each segment `idx` from 1 to {len(block)}, verify what the listed track speaker ACTUALLY said in the audio, using the candidate ASR readings and table context as guides.

Rules:
- Trust your ears over the candidate ASR text whenever the audio clearly disagrees.
- Mic-bleed rejection: If you only hear a faint/distant voice matching one of the listed "Concurrent OTHER speakers" (and NOT the listed track speaker), set `status` to `"mic_bleed"`, `text` to `""`, `source` to `"none"`.
- Silence / non-speech noise (cough, keyboard, breathing, hallucination): set `status` to `"no_speech"`, `text` to `""`, `source` to `"none"`.
- Real speech by the listed speaker: set `status` to `"speech"`, write verbatim text (keep jokes, numbers, dice results, slang; drop only um/uh), and set `source` to `"primary"`, `"alt"`, `"combined"`, or `"audio_corrected"`.
- Return JSON matching the schema with EXACTLY one entry per segment `idx` (1..{len(block)}).

Campaign spellings to use when you hear them: {', '.join(names)}.
{hints}

Segments to arbitrate:
{listing}
"""


def parse_structured_reply(block: list[dict], reply: str) -> dict[int, dict]:
    """Parse structured JSON arbitration output into {global_idx: verdict_dict}."""
    import agent_cli

    try:
        payload = agent_cli.extract_json(reply)
    except ValueError:
        return {}

    items = payload.get("segments") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return {}

    by_global = {seg["idx"]: seg for seg in block}
    verdicts: dict[int, dict] = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        raw_idx = entry.get("idx")
        if not isinstance(raw_idx, int):
            try:
                raw_idx = int(raw_idx)
            except (TypeError, ValueError):
                continue

        # Accept 1-based block index (preferred) or global segment idx.
        if 1 <= raw_idx <= len(block):
            seg = block[raw_idx - 1]
        elif raw_idx in by_global:
            seg = by_global[raw_idx]
        else:
            continue

        status = str(entry.get("status", "speech")).strip().lower()
        if status not in {"speech", "mic_bleed", "no_speech"}:
            status = "speech" if str(entry.get("text", "")).strip() else "no_speech"
        text = str(entry.get("text", "")).strip()
        if status != "speech":
            text = ""
        elif not text:
            status = "no_speech"
        source = str(entry.get("source", "audio_corrected")).strip().lower()
        if source not in {"primary", "alt", "combined", "audio_corrected", "none"}:
            source = "audio_corrected" if status == "speech" else "none"

        verdicts[seg["idx"]] = {
            "status": status,
            "text": text,
            "source": source,
            "track": seg["track"],
            "speaker": seg["speaker"],
            "s": round(float(seg["s"]), 3),
            "e": round(float(seg["e"]), 3),
            "origin": seg.get("origin", "reference"),
            "reasons": seg.get("reasons", []),
        }
    return verdicts


# Legacy fallback realign helpers (used only if structured JSON fails after escalation).
def gemini_words(reply: str) -> list[tuple[str, int]]:
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
    best: tuple[dict[int, str], float] = ({}, 0.0)
    for key in ("text", "alt_text"):
        if not any(seg.get(key) for seg in block):
            continue
        result = realign_against(block, reply, key)
        if result[1] > best[1]:
            best = result
    return best


def realign_against(block: list[dict], reply: str, key: str) -> tuple[dict[int, str], float]:
    ref, ref_seg = [], []
    for position, seg in enumerate(block):
        for tok in tokens(seg.get(key) or seg.get("text") or ""):
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
        assert position is not None
        texts.setdefault(position, []).append(word)
    coverage = matched / max(1, len(ref))
    return {block[p]["idx"]: " ".join(words) for p, words in texts.items()}, coverage


def spread_words(seg: dict, text: str) -> list[dict]:
    toks = text.split()
    if not toks:
        return []
    step = max(0.01, (seg["e"] - seg["s"]) / len(toks))
    return [
        {"s": seg["s"] + i * step, "e": seg["s"] + (i + 1) * step, "w": tok, "p": None}
        for i, tok in enumerate(toks)
    ]


def _block_cache_key(block: list[dict], model: str) -> str:
    sig = {
        "model": model,
        "segments": [
            (s["track"], round(s["s"], 2), round(s["e"], 2), s.get("text", ""), s.get("alt_text", ""))
            for s in block
        ],
    }
    return hashlib.sha256(json.dumps(sig, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def arbitrate_blocks(
    blocks: list[list[dict]],
    pool: list[dict],
    names: list[str],
    hints: str,
    *,
    model: str | None = None,
    escalation_model: str | None = None,
    context_lines: int = 3,
    workers: int = 4,
    cache_dir: Path | None = None,
    use_cache: bool = True,
    timeout: int = 600,
) -> tuple[dict[int, dict], dict]:
    """Run audio-grounded arbitration over prepared blocks; reusable by fuse_transcript.py."""
    sys.path.insert(0, str(SCRIPT_DIR))
    import agent_cli

    primary_model = agent_cli.resolve_model("agy", model)
    strong_model = agent_cli.resolve_model("agy", escalation_model or agent_cli.AGY_TIERS["strong"])
    if cache_dir and use_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)

    verdicts: dict[int, dict] = {}
    stats: dict = {"ok": 0, "cached": 0, "escalated": 0, "fallback": 0, "errors": 0, "seconds": []}

    def process_block(block: list[dict]) -> None:
        cache_key = _block_cache_key(block, primary_model)
        cache_file = (cache_dir / f"block_{cache_key}.json") if (cache_dir and use_cache) else None
        if cache_file and cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                parsed = {int(k): v for k, v in cached.get("verdicts", {}).items()}
                if parsed:
                    verdicts.update(parsed)
                    stats["cached"] += 1
                    stats["ok"] += 1
                    print(f"  block @{asr_common.format_ts(block[0]['s'])}: loaded from cache ({len(parsed)} segments)", flush=True)
                    return
            except (OSError, json.JSONDecodeError, ValueError):
                pass

        with tempfile.TemporaryDirectory(prefix="gemini-block-") as tmp:
            clip = write_block_audio(block, Path(tmp) / f"block_{int(block[0]['s']):06d}")
            prompt = block_prompt(clip.name, block, pool, names, hints, context_lines=context_lines)
            t0 = time.monotonic()
            reply = ""
            parsed: dict[int, dict] = {}
            used_model = primary_model

            try:
                reply = agent_cli.run_agent(
                    prompt,
                    provider="agy",
                    model=primary_model,
                    workspace=Path(tmp),
                    write=False,
                    attachments=[clip],
                    json_schema=ARBITRATION_SCHEMA,
                    timeout=timeout,
                    retries=1,
                )
                parsed = parse_structured_reply(block, reply)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"  block @{asr_common.format_ts(block[0]['s'])}: {primary_model} error ({str(exc)[:180]})",
                    flush=True,
                )

            # Escalate if structured parsing failed or returned fewer than half the block.
            if len(parsed) < max(1, len(block) // 2) and strong_model != primary_model:
                stats["escalated"] += 1
                used_model = strong_model
                try:
                    reply2 = agent_cli.run_agent(
                        prompt,
                        provider="agy",
                        model=strong_model,
                        workspace=Path(tmp),
                        write=False,
                        attachments=[clip],
                        json_schema=ARBITRATION_SCHEMA,
                        timeout=timeout,
                        retries=1,
                    )
                    parsed2 = parse_structured_reply(block, reply2)
                    if len(parsed2) > len(parsed):
                        parsed = parsed2
                        reply = reply2
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"  block @{asr_common.format_ts(block[0]['s'])}: escalation {strong_model} error ({str(exc)[:180]})",
                        flush=True,
                    )

        elapsed = time.monotonic() - t0
        stats["seconds"].append(elapsed)

        # Last-resort fallback to content realignment if JSON still failed.
        if not parsed and reply.strip():
            aligned, coverage = realign(block, reply)
            if coverage >= 0.3:
                stats["fallback"] += 1
                for seg in block:
                    if seg["idx"] in aligned:
                        parsed[seg["idx"]] = {
                            "status": "speech",
                            "text": aligned[seg["idx"]],
                            "source": "audio_corrected",
                            "track": seg["track"],
                            "speaker": seg["speaker"],
                            "s": round(float(seg["s"]), 3),
                            "e": round(float(seg["e"]), 3),
                            "origin": seg.get("origin", "reference"),
                            "reasons": seg.get("reasons", []),
                        }

        if not parsed:
            stats["errors"] += 1
            print(f"  block @{asr_common.format_ts(block[0]['s'])}: failed to arbitrate ({elapsed:.0f}s)", flush=True)
            return

        verdicts.update(parsed)
        stats["ok"] += 1
        if cache_file:
            cache_file.write_text(
                json.dumps({"model": used_model, "verdicts": {str(k): v for k, v in parsed.items()}}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        speech_cnt = sum(1 for v in parsed.values() if v["status"] == "speech")
        bleed_cnt = sum(1 for v in parsed.values() if v["status"] == "mic_bleed")
        print(
            f"  block @{asr_common.format_ts(block[0]['s'])}: {len(parsed)}/{len(block)} verdicts "
            f"(speech={speech_cnt}, bleed={bleed_cnt}, model={used_model}) {elapsed:.0f}s",
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=workers) as pool_exec:
        list(pool_exec.map(process_block, blocks))

    return verdicts, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference-dir", required=True, help="Primary engine dir, e.g. <session>/asr/gladia")
    parser.add_argument("--out-dir", required=True, help="Output engine dir, e.g. <session>/asr/gemini")
    parser.add_argument("--alt-dir", help="Second engine dir; unioned for one-sided speech and disagreement triggers")
    parser.add_argument("--hotspots-json", help="Optional hotspot_segments.json from asr_diagnostics.py")
    parser.add_argument("--select", choices=["all", "disputed"], default="disputed")
    parser.add_argument("--dispute-threshold", type=float, default=0.25, help="Normalized token mismatch threshold")
    parser.add_argument("--low-conf-threshold", type=float, default=0.50, help="Trigger arbitration when word p < threshold")
    parser.add_argument("--session")
    parser.add_argument("--model", help="agy model (default: gemini-4-neon-medium / AGY_MODEL)")
    parser.add_argument("--escalation-model", help="Fallback stronger agy model (default: gemini-4-neon-high)")
    parser.add_argument("--block-segments", type=int, default=15)
    parser.add_argument("--block-speech-seconds", type=float, default=90.0)
    parser.add_argument("--block-span-seconds", type=float, default=600.0, help="Max table time one block may span")
    parser.add_argument("--context-lines", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--cache-dir", help="Disk cache directory for resuming blocks (default: <out-dir>/.cache)")
    parser.add_argument("--no-cache", action="store_true", help="Disable reading/writing block cache")
    parser.add_argument("--force", action="store_true", help="Ignore existing cached blocks")
    parser.add_argument("--limit-blocks", type=int, help="Only process the first N blocks (testing)")
    parser.add_argument("--start-at", type=float, default=0.0, help="Skip segments before this many seconds (testing)")
    args = parser.parse_args()

    sys.path.insert(0, str(SCRIPT_DIR))
    import agent_cli
    import assemble_transcript
    import transcribe_gladia
    from name_normalizer import NameNormalizer

    ref_tracks = asr_common.load_engine_dir(Path(args.reference_dir))
    alt_tracks = asr_common.load_engine_dir(Path(args.alt_dir)) if args.alt_dir else {}
    speaker_map = assemble_transcript.load_speaker_map()
    speaker_of = lambda t: assemble_transcript.identify_speaker(t, speaker_map)  # noqa: E731

    pool = collect_union_segments(ref_tracks, alt_tracks, speaker_of)
    candidates = [s for s in pool if s["s"] >= args.start_at]

    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    names = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, args.session, module)[:100]
    common = (
        {l.strip() for l in ENGLISH_WORDLIST.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip().islower()}
        if ENGLISH_WORDLIST.exists()
        else set()
    )
    external_hotspots = []
    if args.hotspots_json and Path(args.hotspots_json).exists():
        raw_hs = json.loads(Path(args.hotspots_json).read_text(encoding="utf-8"))
        external_hotspots = raw_hs.get("segments", raw_hs) if isinstance(raw_hs, dict) else raw_hs

    if args.select == "disputed" and not args.alt_dir and not external_hotspots:
        print("Note: --select disputed without --alt-dir; selecting via confidence, dice, loop, and entity triggers only.", flush=True)

    selected = select_segments(
        candidates,
        alt_tracks,
        threshold=args.dispute_threshold,
        low_conf_threshold=args.low_conf_threshold,
        entity_names=names,
        common_words=common,
        external_hotspots=external_hotspots,
        select_all=(args.select == "all"),
    )
    blocks = build_blocks(selected, args.block_segments, args.block_speech_seconds, args.block_span_seconds)
    if args.limit_blocks:
        blocks = blocks[: args.limit_blocks]

    hints = NameNormalizer().llm_hint_block()
    speech = sum(max(0.1, s["e"] - s["s"]) for b in blocks for s in b)
    alt_only_count = sum(1 for s in selected if s.get("origin") == "alt_only")
    print(
        f"{len(pool)} union segments ({alt_only_count} alt-only), {len(selected)} selected ({args.select}) -> "
        f"{len(blocks)} blocks, {speech / 60:.1f} min of speech",
        flush=True,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else out_dir / ".cache"

    started = time.monotonic()
    verdicts, stats = arbitrate_blocks(
        blocks,
        pool,
        names,
        hints,
        model=args.model,
        escalation_model=args.escalation_model,
        context_lines=args.context_lines,
        workers=args.workers,
        cache_dir=cache_dir,
        use_cache=not (args.no_cache or args.force),
    )

    all_tracks = dict(ref_tracks)
    for track, data in alt_tracks.items():
        all_tracks.setdefault(track, data)

    resolved_model = agent_cli.resolve_model("agy", args.model)
    covered = {s["idx"] for b in blocks for s in b}

    for track, data in all_tracks.items():
        out_segments, words, track_verdicts = [], [], []
        for seg in pool:
            if seg["track"] != track or seg["idx"] not in covered or seg["idx"] not in verdicts:
                continue
            verdict = verdicts[seg["idx"]]
            track_verdicts.append(verdict)
            if verdict["status"] == "speech" and verdict["text"]:
                out_segments.append({"s": seg["s"], "e": seg["e"], "text": verdict["text"]})
                words.extend(spread_words(seg, verdict["text"]))
        asr_common.write_engine_json(
            out_dir / f"{track}.json",
            engine="gemini",
            model=resolved_model,
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
                "word_times": "spread evenly within arbitrated segments",
                "verdicts": track_verdicts,
                "elapsed_seconds": round(time.monotonic() - started, 1),
            },
        )
        asr_common.write_segment_txt(out_dir / f"{track}.txt", out_segments)

    verdicts_payload = {
        "model": resolved_model,
        "escalation_model": agent_cli.resolve_model("agy", args.escalation_model or agent_cli.AGY_TIERS["strong"]),
        "verdicts": [verdicts[k] for k in sorted(verdicts)],
    }
    (out_dir / "verdicts.json").write_text(
        json.dumps(verdicts_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    per_call = sorted(stats["seconds"])
    median = per_call[len(per_call) // 2] if per_call else 0
    bleeds = sum(1 for v in verdicts.values() if v["status"] == "mic_bleed")
    no_speech = sum(1 for v in verdicts.values() if v["status"] == "no_speech")
    recovered = sum(1 for v in verdicts.values() if v["status"] == "speech" and v.get("origin") == "alt_only")
    print(
        f"done in {time.monotonic() - started:.0f}s: {stats['ok']} blocks ok ({stats['cached']} cached, "
        f"{stats['escalated']} escalated, {stats['errors']} errors); {len(verdicts)} verdicts "
        f"(recovered_alt={recovered}, mic_bleed={bleeds}, no_speech={no_speech}); median call {median:.0f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
