#!/usr/bin/env python3
"""Single-pass chronological mixed-audio transcript review with isolated-track guard.

Replaces multi-engine Whisper + 120-block audio arbitration + transcript fusion for
default zero-Whisper runs:
1. Pass 1: mixes isolated speaker tracks into one compressed VoIP mono stream,
   splits non-OOC stretches into ~10-minute overlapping-context windows, and lets
   Gemini listen once per window to fix mishearings, wrong proper nouns,
   homophones, mic bleed, and genuinely missed gameplay lines.
2. Pass 2 (Isolated-Track Guard): inspects every Pass-1 `delete` (except tiny
   merged split fragments and confirmed word-overlap bleeds) and every heavy
   truncation against the speaker's isolated microphone track—rejecting false
   deletes caused by loud crosstalk masking quieter players on the mono mix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import asr_common  # noqa: E402
import asr_gemini_windows  # noqa: E402
import assemble_transcript  # noqa: E402
import pipeline_paths  # noqa: E402
import transcribe_gladia  # noqa: E402
from name_normalizer import NameNormalizer  # noqa: E402
from note_generation_guidance import CANONICAL_CAST_REFERENCE  # noqa: E402

AUDIO_EXTENSIONS = {".flac", ".wav", ".ogg", ".mp3", ".m4a", ".aac"}
PROMPT_VERSION = "v2-anti-overdelete"
DND_DIR = pipeline_paths.DND_DIR
WORD_RE = re.compile(r"[A-Za-z0-9']+")

SPEAKER_ALIASES = {
    "din": "Berridin",
    "whitaker": "Witty",
    'whitaker "witty" whitman vi': "Witty",
    "dm": "GM",
    "game master": "GM",
}

CHUNK_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "edits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "action": {"type": "string", "enum": ["replace", "delete"]},
                    "text": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "action", "text", "reason"],
            },
        },
        "missed_lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "time_offset_sec": {"type": "number"},
                    "speaker": {"type": "string"},
                    "text": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["time_offset_sec", "speaker", "text", "reason"],
            },
        },
    },
    "required": ["edits", "missed_lines"],
}

ISOLATED_VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "action": {"type": "string", "enum": ["keep_original", "replace", "delete"]},
                    "text": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "action", "text", "reason"],
            },
        },
    },
    "required": ["verdicts"],
}

CHUNK_PROMPT_TEMPLATE = """You are reviewing a Dungeons & Dragons session transcript against the actual session audio.

Attached is `{clip_name}` ({duration_str} long), covering table time {window_start} to {window_end}.
Below is the Gladia ASR draft (`ID [TableTime | +ClipSec] Speaker: text` plus confidence/bleed badges).

CRITICAL AUDIO RULE (read carefully before deleting or shortening anything):
- The draft lines were transcribed from **isolated per-speaker microphones**, whereas the attached `{clip_name}` is a **single mono mix** of all players combined.
- When one player talks loudly, another player speaking quietly at the same moment may sound faint or buried in `{clip_name}` even though their isolated microphone clearly picked up REAL speech.
- Therefore, NEVER delete or heavily truncate a line merely because you cannot hear it clearly underneath someone else's voice on the mix.

Instructions:
- Listen carefully to `{clip_name}` alongside the draft lines below `=== REVIEW LINES START ===`.
- Lines above `=== REVIEW LINES START ===` are earlier context ONLY — do NOT emit edits for them.
- Never edit or delete lines marked `[DICE - DO NOT EDIT]`.
- Return JSON matching the schema with:
  1. `edits`: ONLY lines that genuinely need correction:
     - `replace`: when you hear wrong words, mangled campaign names/titles ("the Roja" -> "the Eulogia", "Dr. Edward" -> "Proctor Eduard", "into our skies Easter" -> "in our disguises, Ysidor"), homophones, wrong character pronouns, garbled idioms, or misheard dice/numbers. Write the exact verbatim spoken words. Do NOT truncate the second half of an overlapped line unless you are certain the trailing words were hallucinated or mic bleed.
     - `delete`: use SPARINGLY — ONLY for `[possible_bleed]` duplicates of another speaker's exact words in the same moment, obvious 1–2 word breath/laughter noise bursts, or premature split fragments already merged into an adjacent line. Never delete a multi-word spoken line just because crosstalk makes it hard to hear.
  2. `missed_lines`: important spoken gameplay dialogue, skill checks, roll totals, or direct answers completely missing from the draft (`time_offset_sec` = seconds into `{clip_name}` `0..{clip_max_sec}`, `speaker` from cast reference, verbatim `text`). Leave empty if nothing important was missed.
- Do NOT polish grammar/slang, drop jokes/profanity, summarize, or touch accurate lines.

{cast}

Campaign canonical spellings:
{names}

{hints}

Lines:
{lines_text}
"""

ISOLATED_VERIFY_PROMPT_TEMPLATE = """You are checking suspect transcript edits against **ISOLATED PER-SPEAKER MICROPHONE CLIPS**.

Attached is `{clip_name}` containing {count} short clip(s) separated by 880 Hz beep tones (Clip 1, Clip 2, ...).
Unlike the full-session mix, each clip comes ONLY from THAT SPEAKER'S **ISOLATED MICROPHONE** (with ~0.5s padding before/after, and only faint acoustic headphone bleed if any).

For each item below, listen to its numbered clip and decide what happened:
- `keep_original`: the speaker ACTUALLY said something close to the Original draft line (for example, it was real overlapped speech masked on the mix). Return empty `text` or Original text.
- `replace`: the speaker ACTUALLY spoke on their isolated mic, AND you can hear what they said more accurately than both Original and Proposed. Put exact verbatim words in `text`.
- `delete`: the isolated clip is genuinely empty silence, mic breath/laughter/noise, a duplicate word cut off at a split, OR pure bleed of another speaker's line (`Proposed` deletion is confirmed).

{items_block}

Return JSON `verdicts` covering every ID above.
"""


def word_tokens(text: str) -> list[str]:
    return WORD_RE.findall(text)


def discover_speaker_tracks(
    audio_dir: Path,
    speaker_map: dict[str, str],
) -> tuple[list[Path], dict[str, Path], dict[str, Path]]:
    """Return top-level speaker audio files sorted by name plus stem/speaker lookup maps."""
    tracks = sorted(
        p
        for p in audio_dir.iterdir()
        if p.is_file()
        and p.suffix.lower() in AUDIO_EXTENSIONS
        and not p.stem.startswith("mixed_")
    )
    by_stem: dict[str, Path] = {}
    by_speaker: dict[str, Path] = {}
    for track in tracks:
        by_stem[track.stem] = track
        spk = assemble_transcript.identify_speaker(track.stem, speaker_map)
        by_speaker.setdefault(spk, track)
    return tracks, by_stem, by_speaker


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def mix_audio(audio_tracks: list[Path], dest: Path, force: bool = False) -> Path:
    """Mix all isolated speaker tracks into one compressed mono VoIP Opus track."""
    if not force and dest.exists() and dest.stat().st_size > 0:
        return dest
    if not audio_tracks:
        raise ValueError("mix_audio requires at least one audio track")
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for track in audio_tracks:
        cmd.extend(["-i", str(track)])
    inputs = "".join(f"[{i}:a]" for i in range(len(audio_tracks)))
    filter_chain = (
        f"{inputs}amix=inputs={len(audio_tracks)}:duration=longest:dropout_transition=0:normalize=0,"
        "dynaudnorm=f=150:g=15"
    )
    cmd.extend(
        [
            "-filter_complex",
            filter_chain,
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "libopus",
            "-b:a",
            "32k",
            "-application",
            "voip",
            str(dest),
        ]
    )
    subprocess.run(cmd, check=True)
    return dest


def subtract_ooc(total_dur: float, ooc_spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Subtract out-of-character stretches from [0, total_dur], keeping intervals >= 5s."""
    intervals: list[tuple[float, float]] = [(0.0, float(total_dur))]
    for raw_s, raw_e in sorted(ooc_spans):
        os_, oe = float(raw_s), float(raw_e)
        if oe <= os_:
            continue
        next_intervals: list[tuple[float, float]] = []
        for s, e in intervals:
            if oe <= s or os_ >= e:
                next_intervals.append((s, e))
                continue
            if os_ > s:
                next_intervals.append((s, os_))
            if oe < e:
                next_intervals.append((oe, e))
        intervals = next_intervals
    return [(s, e) for s, e in intervals if e - s >= 5.0]


def chunk_intervals(intervals: list[tuple[float, float]], target_sec: float = 600.0) -> list[tuple[float, float]]:
    """Partition active intervals into balanced windows around `target_sec` seconds each."""
    chunks: list[tuple[float, float]] = []
    step_target = max(30.0, float(target_sec))
    for s, e in intervals:
        span = e - s
        if span <= 0:
            continue
        n = max(1, round(span / step_target))
        step = span / n
        for idx in range(n):
            cs = s + idx * step
            ce = e if idx == n - 1 else s + (idx + 1) * step
            chunks.append((round(cs, 2), round(ce, 2)))
    return chunks


def format_line(line: dict, chunk_start: float) -> str:
    rel = float(line["start"]) - chunk_start
    prefix = f"+{rel:.0f}s" if rel >= 0 else f"{rel:.0f}s"
    if line.get("speaker") == "DICE":
        return f"{line['id']} [{asr_common.format_ts(float(line['start']))} | {prefix}] DICE: {line['text']}  [DICE - DO NOT EDIT]"
    badges: list[str] = []
    if line.get("mean_conf") is not None and float(line["mean_conf"]) < 0.72:
        badges.append(f"conf={float(line['mean_conf']):.2f}")
    if line.get("low_conf_words"):
        badges.append("low=[" + ", ".join(line["low_conf_words"][:5]) + "]")
    if line.get("possible_bleed"):
        badges.append("possible_bleed")
    if line.get("overlap_speakers"):
        badges.append("overlap=" + "/".join(line["overlap_speakers"]))
    badge_str = f"  [{' ; '.join(badges)}]" if badges else ""
    return f"{line['id']} [{asr_common.format_ts(float(line['start']))} | {prefix}] {line['speaker']}: {line['text']}{badge_str}"


def canonicalize_speaker(raw_speaker: str, valid_speakers: set[str]) -> str:
    """Normalize LLM-returned speaker names to canonical transcript speaker labels."""
    cleaned = " ".join(str(raw_speaker or "").split()).strip()
    if not cleaned:
        return "Unknown"
    folded = cleaned.casefold()
    alias = SPEAKER_ALIASES.get(folded)
    if alias:
        return alias
    for candidate in valid_speakers:
        if candidate.casefold() == folded:
            return candidate
    if folded.startswith("gm"):
        return "GM"
    return cleaned


def is_heavy_truncation(old_text: str, new_text: str) -> bool:
    """True when a replacement drops >= 3 words and at least half of a >= 5-word line."""
    old_w = word_tokens(old_text)
    new_w = word_tokens(new_text)
    return len(old_w) >= 5 and len(new_w) <= len(old_w) * 0.5 and (len(old_w) - len(new_w)) >= 3


def is_merged_adjacent_split(line_idx: int, lines: list[dict], edits_by_id: dict[str, dict]) -> bool:
    """True if a <= 2-word deleted line's content was merged into a nearby same-speaker edit."""
    line = lines[line_idx]
    if len(word_tokens(line.get("text", ""))) > 2:
        return False
    deleted_tokens = set(assemble_transcript.content_tokens(line.get("text", "")))
    if not deleted_tokens:
        return False
    spk = line.get("speaker")
    for j in range(max(0, line_idx - 2), min(len(lines), line_idx + 3)):
        if j == line_idx or lines[j].get("speaker") != spk:
            continue
        adj_edit = edits_by_id.get(lines[j]["id"])
        if not adj_edit or adj_edit.get("action") != "replace":
            continue
        new_tokens = set(assemble_transcript.content_tokens(adj_edit.get("text", "")))
        if deleted_tokens <= new_tokens:
            return True
    return False


def is_confirmed_short_bleed(line_idx: int, lines: list[dict]) -> bool:
    """True when a <= 3-token line flagged possible_bleed overlaps an active line sharing >= 60% tokens."""
    line = lines[line_idx]
    if not line.get("possible_bleed"):
        return False
    my_tokens = set(assemble_transcript.content_tokens(line.get("text", "")))
    if not my_tokens or len(my_tokens) > 3:
        return False
    s, e = float(line["start"]), float(line["end"])
    spk = line.get("speaker")
    for j in range(max(0, line_idx - 12), min(len(lines), line_idx + 13)):
        if j == line_idx:
            continue
        other = lines[j]
        if other.get("speaker") in {spk, "DICE"}:
            continue
        if float(other["start"]) < e + 0.5 and float(other["end"]) > s - 0.5:
            other_tokens = set(assemble_transcript.content_tokens(other.get("text", "")))
            if other_tokens and (len(my_tokens & other_tokens) / len(my_tokens)) >= 0.6:
                return True
    return False


def measure_peak_db(track_path: Path, start_s: float, end_s: float) -> float:
    """Return max_volume (dBFS) on an isolated track over [start_s, end_s]."""
    clip_start = max(0.0, float(start_s))
    dur = max(0.25, float(end_s) - clip_start)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-ss",
        f"{clip_start:.3f}",
        "-t",
        f"{dur:.3f}",
        "-i",
        str(track_path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    match = re.search(r"max_volume:\s*([-\d.]+)\s*dB", proc.stderr or "")
    return float(match.group(1)) if match else -99.0


def is_duplicate_missed_line(abs_s: float, speaker: str, text: str, lines: list[dict]) -> bool:
    """True when a candidate missed line duplicates an active same-speaker line within +-2.5s."""
    cand_norm = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    cand_tokens = set(assemble_transcript.content_tokens(text))
    for line in lines:
        if line.get("speaker") != speaker:
            continue
        if abs(float(line["start"]) - abs_s) > 2.5:
            continue
        exist_txt = str(line.get("text", ""))
        exist_norm = re.sub(r"[^a-z0-9]+", " ", exist_txt.lower()).strip()
        if cand_norm and exist_norm and (cand_norm == exist_norm or cand_norm in exist_norm or exist_norm in cand_norm):
            return True
        if cand_tokens:
            exist_tokens = set(assemble_transcript.content_tokens(exist_txt))
            if exist_tokens and (len(cand_tokens & exist_tokens) / len(cand_tokens)) >= 0.75:
                return True
    return False


def _chunk_cache_path(chunks_dir: Path, idx: int, model: str, ws: float, we: float, items: list[dict]) -> Path:
    sig_payload = {
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "ws": round(ws, 2),
        "we": round(we, 2),
        "lines": [[l["id"], l["speaker"], l["text"]] for l in items],
    }
    digest = hashlib.sha1(json.dumps(sig_payload, ensure_ascii=False).encode("utf-8")).hexdigest()[:10]
    return chunks_dir / f"chunk_{idx + 1:02d}_{digest}.json"


def _conservative_fallback_verdict(line: dict, proposed_edit: dict) -> tuple[str, str, str]:
    """Keep >= 3-word lines and heavy truncations; allow <= 2-word deletes when unverified."""
    orig_words = word_tokens(line.get("text", ""))
    if proposed_edit["action"] == "delete" and len(orig_words) <= 2:
        return "delete", "", "unverified_short_delete"
    return "keep_original", line.get("text", ""), "conservative_guard_keep"


def _build_verify_blocks(candidates: list[dict], max_items: int = 16, max_seconds: float = 90.0) -> list[list[dict]]:
    blocks: list[list[dict]] = []
    cur: list[dict] = []
    cur_sec = 0.0
    for item in candidates:
        dur = item["clip_end"] - item["clip_start"] + 0.7
        if cur and (len(cur) >= max_items or cur_sec + dur > max_seconds):
            blocks.append(cur)
            cur = []
            cur_sec = 0.0
        cur.append(item)
        cur_sec += dur
    if cur:
        blocks.append(cur)
    return blocks


def verify_destructive_edits(
    lines: list[dict],
    edits_by_id: dict[str, dict],
    *,
    track_by_stem: dict[str, Path],
    track_by_speaker: dict[str, Path],
    work_dir: Path,
    provider: str,
    model: str,
    normalizer: NameNormalizer,
    timeout: int = 240,
    disable_llm: bool = False,
) -> tuple[dict[str, dict], dict, list[dict]]:
    """Verify Pass-1 deletes and heavy truncations against isolated speaker audio."""
    guard_stats = {
        "guard_checked": 0,
        "guard_auto_merged_split": 0,
        "guard_auto_bleed": 0,
        "guard_silent_delete": 0,
        "guard_kept": 0,
        "guard_replaced": 0,
        "guard_confirmed_delete": 0,
        "guard_blocks": 0,
    }
    guard_events: list[dict] = []
    idx_by_id = {line["id"]: i for i, line in enumerate(lines)}
    need_audio: list[dict] = []
    result_edits = {lid: dict(ed) for lid, ed in edits_by_id.items()}

    for lid, ed in list(result_edits.items()):
        line_idx = idx_by_id.get(lid)
        if line_idx is None:
            continue
        line = lines[line_idx]
        old_txt = line["text"]
        action = ed["action"]

        is_trunc = action == "replace" and is_heavy_truncation(old_txt, ed.get("text", ""))
        if action != "delete" and not is_trunc:
            continue

        guard_stats["guard_checked"] += 1

        if action == "delete" and is_merged_adjacent_split(line_idx, lines, result_edits):
            guard_stats["guard_auto_merged_split"] += 1
            guard_stats["guard_confirmed_delete"] += 1
            guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "CONFIRMED_DELETE", "via": "merged_split", "orig": old_txt, "new": ""})
            continue

        if action == "delete" and is_confirmed_short_bleed(line_idx, lines):
            guard_stats["guard_auto_bleed"] += 1
            guard_stats["guard_confirmed_delete"] += 1
            guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "CONFIRMED_DELETE", "via": "confirmed_short_bleed", "orig": old_txt, "new": ""})
            continue

        track = track_by_stem.get(line.get("track", "")) or track_by_speaker.get(line.get("speaker", ""))
        if action == "delete" and track is not None:
            peak_db = measure_peak_db(track, float(line["start"]) - 0.3, float(line["end"]) + 0.3)
            if peak_db < -45.0:
                guard_stats["guard_silent_delete"] += 1
                guard_stats["guard_confirmed_delete"] += 1
                guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "CONFIRMED_DELETE", "via": f"isolated_silent({peak_db:.1f}dB)", "orig": old_txt, "new": ""})
                continue

        if disable_llm or track is None:
            fb_action, _, fb_via = _conservative_fallback_verdict(line, ed)
            if fb_action == "keep_original":
                result_edits.pop(lid, None)
                guard_stats["guard_kept"] += 1
                guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "GUARD_KEPT", "via": fb_via, "orig": old_txt, "new": old_txt})
            else:
                guard_stats["guard_confirmed_delete"] += 1
                guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "CONFIRMED_DELETE", "via": fb_via, "orig": old_txt, "new": ""})
            continue

        clip_start = max(0.0, float(line["start"]) - 0.35)
        clip_end = max(clip_start + 0.25, float(line["end"]) + 0.35)
        need_audio.append(
            {
                "id": lid,
                "line": line,
                "edit": ed,
                "track": track,
                "clip_start": clip_start,
                "clip_end": clip_end,
            }
        )

    if not need_audio:
        return result_edits, guard_stats, guard_events

    guard_dir = work_dir / "isolated_guard"
    guard_dir.mkdir(parents=True, exist_ok=True)
    blocks = _build_verify_blocks(need_audio)
    guard_stats["guard_blocks"] = len(blocks)

    def run_block(block_idx: int) -> list[tuple[dict, dict | None]]:
        block = blocks[block_idx]
        segs = [{"audio": str(item["track"]), "s": item["clip_start"], "e": item["clip_end"]} for item in block]
        clip_path = asr_gemini_windows.write_block_audio(segs, guard_dir / f"guard_{block_idx + 1:03d}")
        desc_lines = []
        for idx, item in enumerate(block, 1):
            line = item["line"]
            ed = item["edit"]
            kind = "DELETE" if ed["action"] == "delete" else f"HEAVY_TRUNCATE -> {ed['text']!r}"
            desc_lines.append(
                f"{idx}. {item['id']} [{asr_common.format_ts(float(line['start']))}] {line['speaker']} "
                f"(Proposed: {kind}; Reason: {ed.get('reason', '')})\n"
                f"   Original: {line['text']!r}"
            )
        prompt = ISOLATED_VERIFY_PROMPT_TEMPLATE.format(
            clip_name=clip_path.name,
            count=len(block),
            items_block="\n".join(desc_lines),
        )
        verdict_map: dict[str, dict] = {}
        try:
            reply = agent_cli.run_agent(
                prompt,
                provider=provider,
                model=model,
                workspace=guard_dir,
                write=False,
                attachments=[clip_path],
                json_schema=ISOLATED_VERIFY_SCHEMA,
                timeout=timeout,
                retries=1,
            )
            payload = agent_cli.extract_json(reply)
            if isinstance(payload, dict):
                for entry in payload.get("verdicts", []) or []:
                    if isinstance(entry, dict) and entry.get("id"):
                        verdict_map[str(entry["id"]).strip()] = entry
        except Exception as exc:
            print(f"[audio_review guard] block {block_idx + 1} failed ({exc}); falling back conservatively", flush=True)
        return [(item, verdict_map.get(item["id"])) for item in block]

    with ThreadPoolExecutor(max_workers=min(4, len(blocks))) as pool:
        block_outcomes = list(pool.map(run_block, range(len(blocks))))

    for pairs in block_outcomes:
        for item, verdict in pairs:
            lid = item["id"]
            line = item["line"]
            ed = item["edit"]
            old_txt = line["text"]
            action = str((verdict or {}).get("action", "")).strip()
            v_text = str((verdict or {}).get("text", "")).strip()
            v_reason = str((verdict or {}).get("reason", "")).strip()

            if action not in {"keep_original", "replace", "delete"}:
                action, v_text, fb_via = _conservative_fallback_verdict(line, ed)
                v_reason = v_reason or fb_via

            if action == "keep_original":
                result_edits.pop(lid, None)
                guard_stats["guard_kept"] += 1
                guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "GUARD_KEPT", "via": v_reason or "isolated_speech", "orig": old_txt, "new": old_txt})
            elif action == "replace":
                norm_txt = normalizer.normalize(v_text) if v_text else old_txt
                if norm_txt == old_txt:
                    result_edits.pop(lid, None)
                    guard_stats["guard_kept"] += 1
                    guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "GUARD_KEPT", "via": v_reason or "isolated_matched_orig", "orig": old_txt, "new": old_txt})
                else:
                    result_edits[lid] = {
                        "id": lid,
                        "action": "replace",
                        "text": norm_txt,
                        "reason": f"isolated-verified: {v_reason or ed.get('reason', '')}".strip(),
                    }
                    guard_stats["guard_replaced"] += 1
                    guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "GUARD_REPLACED", "via": v_reason or "isolated_retranscribe", "orig": old_txt, "new": norm_txt})
            else:  # delete
                guard_stats["guard_confirmed_delete"] += 1
                guard_events.append({"id": lid, "speaker": line["speaker"], "start": line["start"], "outcome": "CONFIRMED_DELETE", "via": v_reason or "isolated_confirmed", "orig": old_txt, "new": ""})

    return result_edits, guard_stats, guard_events


def load_lines(path: Path) -> list[dict]:
    return [json.loads(raw) for raw in path.read_text(encoding="utf-8").splitlines() if raw.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lines_jsonl", help="Assembled `.lines.jsonl` transcript (updated in place)")
    parser.add_argument("--audio-dir", required=True, help="Directory with per-speaker audio tracks")
    parser.add_argument("--session", required=True, help="Session number/label")
    parser.add_argument("--out-txt", help="Companion readable transcript output (default: derived from lines_jsonl)")
    parser.add_argument("--work-dir", help="Working dir for mixed audio/chunks (default: <audio-dir>/pipeline/audio_review)")
    parser.add_argument("--report", help="Markdown report path")
    parser.add_argument("--stats-out", help="JSON stats output path")
    parser.add_argument("--ooc-spans", help="Optional OOC spans JSON from detect_ooc_spans.py")
    parser.add_argument("--mixed-audio", help="Optional pre-mixed mono Opus audio path to reuse")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="agy")
    parser.add_argument("--model", default="gemini-4-neon-medium")
    parser.add_argument("--chunk-seconds", type=float, default=600.0)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--no-isolated-verify", action="store_true", help="Skip LLM isolated-track verification pass")
    parser.add_argument("--force", action="store_true", help="Re-mix audio and ignore chunk caches")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    t_total = time.monotonic()
    lines_jsonl = Path(args.lines_jsonl).expanduser().resolve()
    audio_dir = Path(args.audio_dir).expanduser().resolve()
    session = str(args.session)

    if args.out_txt:
        out_txt = Path(args.out_txt).expanduser().resolve()
    elif str(lines_jsonl).endswith(".lines.jsonl"):
        out_txt = Path(str(lines_jsonl)[: -len(".lines.jsonl")] + ".txt")
    else:
        out_txt = lines_jsonl.with_suffix(".txt")

    work_dir = Path(args.work_dir).expanduser().resolve() if args.work_dir else (audio_dir / "pipeline" / "audio_review")
    work_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir = work_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    report_path = Path(args.report).expanduser().resolve() if args.report else (work_dir / f"session_{session}_audio_review_report.md")
    stats_path = Path(args.stats_out).expanduser().resolve() if args.stats_out else (work_dir / "audio_review_stats.json")

    lines = load_lines(lines_jsonl)
    if not lines:
        raise SystemExit(f"no transcript lines in {lines_jsonl}")
    for line in lines:
        if line.get("raw_asr_text"):
            line["text"] = line["raw_asr_text"]
        else:
            line["raw_asr_text"] = line["text"]

    speaker_map = assemble_transcript.load_speaker_map()
    tracks, track_by_stem, track_by_speaker = discover_speaker_tracks(audio_dir, speaker_map)
    if not tracks and not args.mixed_audio:
        raise SystemExit(f"no speaker audio tracks found in {audio_dir}")

    t_mix = time.monotonic()
    mixed_path = Path(args.mixed_audio).expanduser().resolve() if args.mixed_audio else (work_dir / f"mixed_session{session}.ogg")
    if tracks and (not mixed_path.exists() or mixed_path.stat().st_size == 0 or args.force):
        mix_audio(tracks, mixed_path, force=args.force)
    mix_sec = time.monotonic() - t_mix

    total_dur = max(
        [probe_duration(mixed_path)] + [probe_duration(t) for t in tracks]
        if mixed_path.exists()
        else [probe_duration(t) for t in tracks]
    )

    ooc_spans: list[tuple[float, float]] = []
    if args.ooc_spans:
        ooc_file = Path(args.ooc_spans).expanduser().resolve()
        if ooc_file.is_file():
            ooc_spans = asr_gemini_windows.load_ooc_spans(ooc_file)

    active = subtract_ooc(total_dur, ooc_spans)
    windows = chunk_intervals(active, target_sec=args.chunk_seconds)
    if not windows:
        windows = [(0.0, round(total_dur, 2))]

    win_lines: list[list[dict]] = [[] for _ in windows]
    for line in lines:
        s = float(line["start"])
        placed = False
        for idx, (ws, we) in enumerate(windows):
            if ws <= s <= we:
                win_lines[idx].append(line)
                placed = True
                break
        if not placed and not ooc_spans and windows:
            # Guard against rounding edges beyond probe duration.
            nearest_idx = min(range(len(windows)), key=lambda i: abs(s - windows[i][1]))
            win_lines[nearest_idx].append(line)

    module = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)
    vocab_names = transcribe_gladia.vocabulary_terms_from_metadata(DND_DIR, session, module)[:100]
    normalizer = NameNormalizer()
    hints = normalizer.llm_hint_block()
    valid_speakers = {str(l["speaker"]) for l in lines if l.get("speaker") and l.get("speaker") != "DICE"} | {"GM", "Nyx", "Ellara", "Ysidor", "Berridin", "Witty"}

    print(
        f"[audio_review] session={session} mix={mix_sec:.1f}s windows={len(windows)} "
        f"({args.chunk_seconds / 60:.0f}m target, workers={args.workers}) "
        f"lines={sum(len(w) for w in win_lines)}/{len(lines)}",
        flush=True,
    )

    t_llm = time.monotonic()
    by_id_index = {l["id"]: i for i, l in enumerate(lines)}

    def run_chunk(idx: int) -> dict:
        ws, we = windows[idx]
        chunk_items = win_lines[idx]
        if not chunk_items:
            return {"idx": idx, "ws": ws, "we": we, "edits": [], "missed_lines": [], "seconds": 0.0, "cached": False, "skipped": True}

        cache_path = _chunk_cache_path(chunks_dir, idx, args.model, ws, we, chunk_items)
        if not args.force and cache_path.is_file():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["idx"] = idx
            cached["cached"] = True
            return cached

        clip_path = chunks_dir / f"chunk_{idx + 1:02d}.ogg"
        if args.force or not clip_path.exists() or clip_path.stat().st_size == 0:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    f"{ws:.2f}",
                    "-t",
                    f"{max(0.5, we - ws):.2f}",
                    "-i",
                    str(mixed_path),
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "32k",
                    "-application",
                    "voip",
                    str(clip_path),
                ],
                check=True,
            )

        first_global = by_id_index[chunk_items[0]["id"]]
        ctx = lines[max(0, first_global - 5) : first_global]
        ctx_txt = "\n".join(format_line(l, ws) for l in ctx)
        body_txt = "\n".join(format_line(l, ws) for l in chunk_items)
        lines_text = (ctx_txt + "\n" if ctx_txt else "") + "=== REVIEW LINES START ===\n" + body_txt

        prompt = CHUNK_PROMPT_TEMPLATE.format(
            clip_name=clip_path.name,
            duration_str=f"{(we - ws) / 60:.1f} min",
            window_start=asr_common.format_ts(ws),
            window_end=asr_common.format_ts(we),
            clip_max_sec=int(we - ws),
            cast=CANONICAL_CAST_REFERENCE,
            names=", ".join(vocab_names),
            hints=hints,
            lines_text=lines_text,
        )
        t0 = time.monotonic()
        reply = agent_cli.run_agent(
            prompt,
            provider=args.provider,
            model=args.model,
            workspace=chunks_dir,
            write=False,
            attachments=[clip_path],
            json_schema=CHUNK_REVIEW_SCHEMA,
            timeout=args.timeout,
            retries=1,
        )
        payload = agent_cli.extract_json(reply)
        sec = round(time.monotonic() - t0, 1)
        result = {
            "idx": idx,
            "ws": ws,
            "we": we,
            "edits": payload.get("edits", []) if isinstance(payload, dict) else [],
            "missed_lines": payload.get("missed_lines", []) if isinstance(payload, dict) else [],
            "seconds": sec,
            "cached": False,
        }
        cache_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"  chunk {idx + 1}/{len(windows)} [{asr_common.format_ts(ws)}-{asr_common.format_ts(we)}] "
            f"({len(chunk_items)} lines): edits={len(result['edits'])}, missed={len(result['missed_lines'])} ({sec:.0f}s)",
            flush=True,
        )
        return result

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        chunk_results = list(pool.map(run_chunk, range(len(windows))))
    llm_sec = time.monotonic() - t_llm

    # Collect valid Pass-1 edits before applying destructive guard.
    raw_edits_by_id: dict[str, dict] = {}
    raw_missed: list[dict] = []
    valid_ids_by_chunk = [{l["id"] for l in w} for w in win_lines]
    line_by_id = {l["id"]: l for l in lines}

    for res in chunk_results:
        idx = res["idx"]
        allowed = valid_ids_by_chunk[idx]
        for ed in res.get("edits", []) or []:
            if not isinstance(ed, dict):
                continue
            lid = str(ed.get("id", "")).strip()
            action = str(ed.get("action", "")).strip()
            if lid not in allowed or lid not in line_by_id or action not in {"replace", "delete"}:
                continue
            target = line_by_id[lid]
            if target.get("speaker") == "DICE":
                continue
            if action == "replace":
                new_txt = normalizer.normalize(str(ed.get("text", "")).strip())
                if not new_txt or new_txt == target["text"]:
                    continue
                raw_edits_by_id[lid] = {
                    "id": lid,
                    "action": "replace",
                    "text": new_txt,
                    "reason": str(ed.get("reason", "")).strip(),
                }
            else:
                raw_edits_by_id[lid] = {
                    "id": lid,
                    "action": "delete",
                    "text": "",
                    "reason": str(ed.get("reason", "")).strip(),
                }
        for missed in res.get("missed_lines", []) or []:
            if not isinstance(missed, dict):
                continue
            txt = str(missed.get("text", "")).strip()
            if not txt:
                continue
            offset = max(0.0, float(missed.get("time_offset_sec", 0.0)))
            abs_s = min(float(res["we"]), float(res["ws"]) + offset)
            spk = canonicalize_speaker(str(missed.get("speaker", "")), valid_speakers)
            norm_txt = normalizer.normalize(txt)
            if is_duplicate_missed_line(abs_s, spk, norm_txt, lines):
                continue
            raw_missed.append(
                {
                    "start": round(abs_s, 3),
                    "end": round(abs_s + 2.0, 3),
                    "speaker": spk,
                    "track": "",
                    "text": norm_txt,
                    "raw_asr_text": norm_txt,
                    "recovered_from": "audio_review_mixed",
                    "audio_review_action": "missed_added",
                    "audio_review_reason": str(missed.get("reason", "")).strip(),
                }
            )

    t_guard = time.monotonic()
    final_edits_by_id, guard_stats, guard_events = verify_destructive_edits(
        lines,
        raw_edits_by_id,
        track_by_stem=track_by_stem,
        track_by_speaker=track_by_speaker,
        work_dir=work_dir,
        provider=args.provider,
        model=args.model,
        normalizer=normalizer,
        timeout=args.timeout,
        disable_llm=args.no_isolated_verify,
    )
    guard_sec = time.monotonic() - t_guard

    final_lines: list[dict] = []
    report_rows: list[str] = []
    replaced = 0
    deleted = 0

    for line in lines:
        item = dict(line)
        lid = item["id"]
        ed = final_edits_by_id.get(lid)
        if ed is not None:
            old_txt = item["text"]
            if ed["action"] == "delete":
                deleted += 1
                report_rows.append(
                    f"- DELETE {lid} [{asr_common.format_ts(float(item['start']))}] {item['speaker']}: "
                    f"~~{old_txt}~~ ({ed.get('reason', '')})"
                )
                continue
            if ed["action"] == "replace":
                item["text"] = ed["text"]
                item["audio_review_action"] = "replace"
                item["audio_review_reason"] = ed.get("reason", "")
                replaced += 1
                report_rows.append(
                    f"- EDIT {lid} [{asr_common.format_ts(float(item['start']))}] {item['speaker']}: "
                    f"~~{old_txt}~~ -> **{item['text']}** ({ed.get('reason', '')})"
                )
        elif item.get("speaker") != "DICE":
            norm_orig = normalizer.normalize(item["text"])
            if norm_orig != item["text"]:
                item["text"] = norm_orig
                item["audio_review_action"] = "name_normalized"
        final_lines.append(item)

    missed_added: list[dict] = []
    for idx, missed in enumerate(raw_missed, start=1):
        rec = dict(missed)
        rec["id"] = f"M{idx:04d}"
        missed_added.append(rec)
        final_lines.append(rec)
        report_rows.append(
            f"- MISSED [{asr_common.format_ts(float(rec['start']))}] {rec['speaker']}: "
            f"**{rec['text']}** ({rec.get('audio_review_reason', '')})"
        )

    final_lines.sort(key=lambda l: (float(l["start"]), l.get("speaker") != "DICE"))

    lines_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.parent.mkdir(parents=True, exist_ok=True)

    lines_jsonl.write_text(
        "\n".join(json.dumps(l, ensure_ascii=False) for l in final_lines) + "\n",
        encoding="utf-8",
    )
    out_txt.write_text(
        "\n".join(f"[{asr_common.format_ts(float(l['start']))}] {l['speaker']}: {l['text']}" for l in final_lines) + "\n",
        encoding="utf-8",
    )

    guard_lines = [
        f"- {ev['outcome']} {ev['id']} [{asr_common.format_ts(float(ev['start']))}] {ev['speaker']} "
        f"via `{ev['via']}`: `{ev['orig']}` -> `{ev['new']}`"
        for ev in guard_events
    ]
    report_path.write_text(
        f"# Session {session} Mixed-Audio Review Report\n\n"
        f"- Windows: {len(windows)} ({args.chunk_seconds / 60:.0f} min target, model `{args.model}`)\n"
        f"- Mix time: {mix_sec:.1f}s | Pass 1 LLM time: {llm_sec:.1f}s | Pass 2 Guard time: {guard_sec:.1f}s\n"
        f"- Final edits: {replaced} replaced, {deleted} deleted, {len(missed_added)} missed added\n"
        f"- Isolated-track guard: checked={guard_stats['guard_checked']}, kept={guard_stats['guard_kept']}, "
        f"replaced={guard_stats['guard_replaced']}, confirmed_delete={guard_stats['guard_confirmed_delete']} "
        f"(silent={guard_stats['guard_silent_delete']}, bleed={guard_stats['guard_auto_bleed']}, split={guard_stats['guard_auto_merged_split']})\n\n"
        + ("## Isolated-Track Guard Decisions\n\n" + "\n".join(guard_lines) + "\n\n" if guard_lines else "")
        + "## Applied Edits & Missed Lines\n\n"
        + ("\n".join(report_rows) if report_rows else "_No edits applied._")
        + "\n",
        encoding="utf-8",
    )

    stats = {
        "session": session,
        "provider": args.provider,
        "model": args.model,
        "mix_seconds": round(mix_sec, 1),
        "llm_seconds": round(llm_sec, 1),
        "guard_seconds": round(guard_sec, 1),
        "total_seconds": round(time.monotonic() - t_total, 1),
        "chunks": len(windows),
        "replaced": replaced,
        "deleted": deleted,
        "missed_added": len(missed_added),
        "final_line_count": len(final_lines),
        **guard_stats,
    }
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"[audio_review] complete in {stats['total_seconds']}s: {replaced} replaced, {deleted} deleted "
        f"(guard kept {guard_stats['guard_kept']}, replaced {guard_stats['guard_replaced']}), "
        f"{len(missed_added)} missed added -> {out_txt}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
