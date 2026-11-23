#!/usr/bin/env python3
"""Assemble a chronological multi-speaker transcript from per-track ASR JSON.

Input: a directory of dnd-asr-v1 track files (one engine), e.g. session/asr/gladia.
Output:
    Transcript Session N.txt          `[HH:MM:SS] Speaker: text` (downstream format)
    Transcript Session N.lines.jsonl  one record per line: precise times, track,
                                      confidence, low-confidence words, raw_asr_text,
                                      overlap_speakers, possible_bleed, name edits

Features:
- orders lines by sub-second start time
- builds utterances from word timings, then merges a speaker's consecutive
  utterances into one turn when nobody else spoke in between
- drops filler tokens (um/uh) and short backchannels ONLY when strictly nested
  inside another speaker's active utterance (preserving "yes"/"yeah"/"okay"/
  "sure"/"right" when answering a turn that just ended!)
- optionally merges verified Whisper/Gemini one-sided speech and mic-bleed
  verdicts from --gemini-dir
- preserves raw_asr_text before NameNormalizer runs
- attaches overlap_speakers and possible_bleed metadata
- cleanly formats single and multi-roll D&D Beyond DICE events
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import asr_common
from name_normalizer import NameNormalizer

SCRIPT_DIR = Path(__file__).resolve().parent
SPEAKER_MAP_FILE = SCRIPT_DIR / "speaker_map.json"

FILLER_TOKENS = {"um", "uh", "erm", "hmm", "mm", "mhm", "uh-huh", "um-hum", "ah", "mm-hmm"}
RESPONSE_BACKCHANNELS = {
    "yeah", "yes", "yep", "yup", "okay", "ok", "right", "sure",
    "true", "nice", "oh", "wow", "cool", "gotcha", "alright",
}
BACKCHANNEL_WORDS = FILLER_TOKENS | RESPONSE_BACKCHANNELS
DISPLAY_SPEAKER = {'Whitaker "Witty" Whitman VI': "Witty"}


def load_speaker_map() -> dict[str, str]:
    return json.loads(SPEAKER_MAP_FILE.read_text(encoding="utf-8")) if SPEAKER_MAP_FILE.exists() else {}


def identify_speaker(track: str, speaker_map: dict[str, str]) -> str:
    base = track.lower()
    for key, name in speaker_map.items():
        clean = Path(key).name.lower()
        for ext in (".png", ".webp", ".jpeg", ".jpg"):
            clean = clean.replace(ext, "")
        if clean and clean in base:
            return DISPLAY_SPEAKER.get(name, name)
    return re.sub(r"^\d+-", "", track).title()


def bare(word: str) -> str:
    return re.sub(r"[^\w'-]", "", word.lower())


def content_tokens(text: str) -> list[str]:
    return [t for t in (bare(w) for w in text.split()) if t and t not in FILLER_TOKENS]


def words_to_utterances(words: list[dict], split_gap: float, max_duration: float) -> list[dict]:
    utterances: list[dict] = []
    current: list[dict] = []
    for word in words:
        w_start = float(word["s"])
        w_end = min(float(word["e"]), w_start + 2.0)  # guard against legacy cross-island spans
        clean_w = {**word, "s": w_start, "e": max(w_start, w_end)}
        if current:
            gap = clean_w["s"] - current[-1]["e"]
            duration = clean_w["e"] - current[0]["s"]
            sentence_end = current[-1]["w"].endswith((".", "?", "!"))
            if gap > split_gap or (duration > max_duration and sentence_end):
                utterances.append({"s": current[0]["s"], "e": current[-1]["e"], "words": current})
                current = []
        current.append(clean_w)
    if current:
        utterances.append({"s": current[0]["s"], "e": current[-1]["e"], "words": current})
    return utterances


def segments_to_utterances(segments: list[dict]) -> list[dict]:
    out = []
    for seg in segments:
        toks = seg["text"].split()
        if not toks:
            continue
        step = max(0.01, (float(seg["e"]) - float(seg["s"])) / len(toks))
        out.append({
            "s": float(seg["s"]),
            "e": float(seg["e"]),
            "words": [
                {"s": float(seg["s"]) + i * step, "e": float(seg["s"]) + (i + 1) * step, "w": w, "p": None}
                for i, w in enumerate(toks)
            ],
        })
    return out


def utterance_text(words: list[dict]) -> str:
    kept = [w["w"] for w in words if bare(w["w"]) not in FILLER_TOKENS]
    text = " ".join(kept)
    text = re.sub(r"\s+([,.?!;:])", r"\1", text)
    text = re.sub(r"([,.?!])\1+", r"\1", text)
    text = re.sub(r"^[,.;:]\s*", "", text)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text.strip()


def is_pure_filler(words: list[dict]) -> bool:
    tokens = [bare(w["w"]) for w in words if bare(w["w"])]
    return bool(tokens) and all(t in FILLER_TOKENS for t in tokens)


def is_backchannel(words: list[dict]) -> bool:
    tokens = [bare(w["w"]) for w in words if bare(w["w"])]
    return bool(tokens) and len(tokens) <= 3 and all(t in BACKCHANNEL_WORDS for t in tokens)


def should_drop_backchannel(utt: dict, neighbors: list[dict]) -> bool:
    """Drop short backchannels ONLY when strictly nested inside another active turn.

    Affirmative answers ("yes", "yeah", "okay", "sure", "right") spoken after or
    at the end of another speaker's turn are preserved.
    """
    if is_pure_filler(utt["words"]):
        return True

    if not is_backchannel(utt["words"]):
        return False

    for other in neighbors:
        if other is utt or other["speaker"] == utt["speaker"]:
            continue
        if is_backchannel(other["words"]):
            continue
        # Strictly nested inside an ongoing utterance: the other speaker started
        # before this backchannel AND kept speaking after it ended.
        if other["s"] + 0.15 <= utt["s"] and utt["e"] <= other["e"] - 0.15:
            return True
    return False


def load_gemini_verdicts(gemini_dir: Path | None) -> list[dict]:
    if not gemini_dir or not gemini_dir.exists():
        return []
    verdicts_file = gemini_dir / "verdicts.json"
    if verdicts_file.exists():
        try:
            data = json.loads(verdicts_file.read_text(encoding="utf-8"))
            items = data.get("verdicts", data) if isinstance(data, dict) else data
            if isinstance(items, list):
                return items
        except (OSError, json.JSONDecodeError):
            pass

    # Fallback: read verdicts embedded in track JSON params or raw segments.
    verdicts: list[dict] = []
    for track, data in asr_common.load_engine_dir(gemini_dir).items():
        embedded = (data.get("params") or {}).get("verdicts")
        if isinstance(embedded, list) and embedded:
            verdicts.extend(embedded)
        else:
            for seg in data.get("segments", []):
                verdicts.append({
                    "track": track,
                    "s": seg["s"],
                    "e": seg["e"],
                    "status": "speech",
                    "text": seg["text"],
                    "origin": "gemini",
                    "source": "audio_corrected",
                })
    return verdicts


def _merge_supplemental_utterances(
    utterances: list[dict],
    verdicts: list[dict],
    speaker_map: dict[str, str],
) -> list[dict]:
    """Merge verified Whisper/Gemini one-sided speech that primary missed."""
    if not verdicts:
        return utterances

    added: list[dict] = []
    for v in verdicts:
        if v.get("status") != "speech" or not str(v.get("text", "")).strip():
            continue
        track = v.get("track")
        if not track:
            continue
        s, e = float(v["s"]), float(v["e"])
        # Only add when primary has no utterance on the same track overlapping this span.
        overlaps_primary = any(
            u["track"] == track and u["s"] <= e + 0.45 and u["e"] >= s - 0.45
            for u in utterances
        )
        if overlaps_primary:
            continue
        toks = str(v["text"]).split()
        step = max(0.01, (e - s) / max(1, len(toks)))
        added.append({
            "s": s,
            "e": e,
            "speaker": v.get("speaker") or identify_speaker(track, speaker_map),
            "track": track,
            "words": [
                {"s": s + i * step, "e": s + (i + 1) * step, "w": tok, "p": None}
                for i, tok in enumerate(toks)
            ],
            "recovered_from": v.get("origin") or "gemini",
        })

    if added:
        utterances = sorted(utterances + added, key=lambda u: (u["s"], u["e"]))
    return utterances


def _annotate_overlaps_and_bleed(lines: list[dict], verdicts: list[dict] | None = None) -> None:
    """Attach `overlap_speakers`, `possible_bleed`, and optional `gemini_verdict`."""
    negative_by_track: dict[str, list[dict]] = {}
    for v in verdicts or []:
        if v.get("status") in {"mic_bleed", "no_speech"} and v.get("track"):
            negative_by_track.setdefault(v["track"], []).append(v)

    token_sets = [set(content_tokens(line["text"])) for line in lines]

    for i, line in enumerate(lines):
        s, e = line["start"], line["end"]
        overlaps: list[str] = []
        possible_bleed = False
        my_tokens = token_sets[i]

        # Check negative Gemini audio verdicts first.
        for v in negative_by_track.get(line["track"], []):
            if float(v["s"]) <= e + 0.25 and float(v["e"]) >= s - 0.25:
                line["gemini_verdict"] = v["status"]
                possible_bleed = True
                break

        # Scan nearby lines (list is sorted by start time).
        for j in range(max(0, i - 12), min(len(lines), i + 12)):
            if j == i:
                continue
            other = lines[j]
            if other["speaker"] == line["speaker"]:
                continue
            if other["start"] < e and other["end"] > s:
                if other["speaker"] not in overlaps:
                    overlaps.append(other["speaker"])
                other_tokens = token_sets[j]
                if my_tokens and other_tokens:
                    shared = len(my_tokens & other_tokens) / len(my_tokens)
                    if shared >= 0.6 and len(my_tokens) <= len(other_tokens):
                        possible_bleed = True
                if (
                    line.get("mean_conf") is not None
                    and line["mean_conf"] < 0.45
                    and other["start"] <= s
                    and other["end"] >= e
                    and (other.get("mean_conf") is None or other["mean_conf"] > line["mean_conf"] + 0.15)
                ):
                    possible_bleed = True

        line["overlap_speakers"] = sorted(overlaps)
        line["possible_bleed"] = possible_bleed


def build_lines(
    tracks: dict[str, dict],
    speaker_map: dict[str, str],
    split_gap: float,
    merge_gap: float,
    max_turn_chars: int,
    max_duration: float,
    low_conf: float,
    keep_backchannels: bool,
    gemini_verdicts: list[dict] | None = None,
) -> list[dict]:
    utterances = []
    for track, data in tracks.items():
        speaker = identify_speaker(track, speaker_map)
        units = (
            words_to_utterances(data["words"], split_gap, max_duration)
            if data.get("words")
            else segments_to_utterances(data.get("segments", []))
        )
        for unit in units:
            unit["speaker"] = speaker
            unit["track"] = track
            utterances.append(unit)
    utterances.sort(key=lambda u: (u["s"], u["e"]))

    if gemini_verdicts:
        utterances = _merge_supplemental_utterances(utterances, gemini_verdicts, speaker_map)

    if not keep_backchannels:
        filtered = []
        for i, utt in enumerate(utterances):
            neighbors = utterances[max(0, i - 8) : min(len(utterances), i + 9)]
            if should_drop_backchannel(utt, neighbors):
                continue
            filtered.append(utt)
        utterances = filtered

    turns: list[dict] = []
    for utt in utterances:
        if (
            turns
            and turns[-1]["speaker"] == utt["speaker"]
            and utt["s"] - turns[-1]["e"] <= merge_gap
            and sum(len(w["w"]) + 1 for w in turns[-1]["words"] + utt["words"]) <= max_turn_chars
        ):
            turns[-1]["words"].extend(utt["words"])
            turns[-1]["e"] = max(turns[-1]["e"], utt["e"])
            if utt.get("recovered_from") and not turns[-1].get("recovered_from"):
                turns[-1]["recovered_from"] = utt["recovered_from"]
            continue
        turns.append({
            "s": utt["s"],
            "e": utt["e"],
            "speaker": utt["speaker"],
            "track": utt["track"],
            "words": list(utt["words"]),
            "recovered_from": utt.get("recovered_from"),
        })

    lines = []
    for turn in turns:
        text = utterance_text(turn["words"])
        if not text:
            continue
        confidences = [w["p"] for w in turn["words"] if w.get("p") is not None]
        rec = {
            "start": round(turn["s"], 3),
            "end": round(turn["e"], 3),
            "speaker": turn["speaker"],
            "track": turn["track"],
            "text": text,
            "raw_asr_text": text,
            "mean_conf": round(sum(confidences) / len(confidences), 3) if confidences else None,
            "low_conf_words": [w["w"] for w in turn["words"] if w.get("p") is not None and w["p"] < low_conf],
        }
        if turn.get("recovered_from"):
            rec["recovered_from"] = turn["recovered_from"]
        lines.append(rec)

    _annotate_overlaps_and_bleed(lines, verdicts=gemini_verdicts)
    return lines


def load_dice(path: Path | None) -> list[dict]:
    if not path or not path.exists():
        return []
    events = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            event = json.loads(raw)
            if event.get("audio_time") is not None:
                events.append(event)
    return events


def format_dice_total(total) -> str:
    """Format single or multi-roll D&D Beyond totals cleanly (never `[12, 8]`)."""
    if isinstance(total, (list, tuple)):
        parts = [str(item) for item in total if item is not None]
        return ", ".join(parts) if parts else "?"
    if total is None:
        return "?"
    return str(total)


def dice_line(event: dict) -> dict:
    detail = f" ({event['detail']})" if event.get("detail") else ""
    label = " ".join(part for part in (event.get("action"), event.get("roll_type")) if part)
    total_str = event.get("total_display") or format_dice_total(event.get("total"))
    text = f"{event.get('character', 'Someone')} rolled {label or 'a roll'}: {total_str}{detail}"
    return {
        "start": round(float(event["audio_time"]), 3),
        "end": round(float(event["audio_time"]), 3),
        "speaker": "DICE",
        "track": "ddb",
        "text": text,
        "raw_asr_text": text,
        "mean_conf": None,
        "low_conf_words": [],
        "overlap_speakers": [],
        "possible_bleed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engine_dir", help="Directory with one engine's dnd-asr-v1 track JSON files")
    parser.add_argument("output_txt")
    parser.add_argument("--lines-jsonl", help="Default: <output_txt minus .txt>.lines.jsonl")
    parser.add_argument("--dice", help="Aligned dice events JSONL from ddb_rolls.py")
    parser.add_argument("--gemini-dir", help="Optional Gemini arbitration dir (merges verified one-sided speech & bleed verdicts)")
    parser.add_argument("--no-gemini", action="store_true", help="Do not auto-load sibling asr/gemini/verdicts.json")
    parser.add_argument("--split-gap", type=float, default=0.9, help="Seconds of silence that end an utterance")
    parser.add_argument("--merge-gap", type=float, default=2.0, help="Merge a speaker's consecutive utterances within this gap")
    parser.add_argument("--max-turn-chars", type=int, default=600)
    parser.add_argument("--max-utterance-seconds", type=float, default=25.0)
    parser.add_argument("--low-conf", type=float, default=0.45)
    parser.add_argument("--keep-backchannels", action="store_true")
    parser.add_argument("--corrections", default=str(SCRIPT_DIR / "name_corrections.json"))
    args = parser.parse_args()

    tracks = asr_common.load_engine_dir(Path(args.engine_dir))
    if not tracks:
        raise SystemExit(f"no dnd-asr-v1 track files in {args.engine_dir}")

    gemini_dir = None if args.no_gemini else (Path(args.gemini_dir) if args.gemini_dir else None)
    if not args.no_gemini and gemini_dir is None:
        sibling_gemini = Path(args.engine_dir).resolve().parent / "gemini"
        if (sibling_gemini / "verdicts.json").exists():
            gemini_dir = sibling_gemini
    verdicts = load_gemini_verdicts(gemini_dir)

    lines = build_lines(
        tracks,
        load_speaker_map(),
        split_gap=args.split_gap,
        merge_gap=args.merge_gap,
        max_turn_chars=args.max_turn_chars,
        max_duration=args.max_utterance_seconds,
        low_conf=args.low_conf,
        keep_backchannels=args.keep_backchannels,
        gemini_verdicts=verdicts,
    )

    normalizer = NameNormalizer(Path(args.corrections))
    for line in lines:
        line["raw_asr_text"] = line["text"]
        line["text"], edits = normalizer.apply(line["text"])
        if edits:
            line["name_edits"] = edits

    dice = [dice_line(e) for e in load_dice(Path(args.dice) if args.dice else None)]
    lines = sorted(lines + dice, key=lambda l: (l["start"], l["speaker"] != "DICE"))

    output_txt = Path(args.output_txt)
    lines_jsonl = Path(args.lines_jsonl) if args.lines_jsonl else output_txt.with_name(output_txt.stem + ".lines.jsonl")
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    with output_txt.open("w", encoding="utf-8") as txt, lines_jsonl.open("w", encoding="utf-8") as jl:
        for index, line in enumerate(lines, start=1):
            line["id"] = f"L{index:05d}"
            txt.write(f"[{asr_common.format_ts(line['start'])}] {line['speaker']}: {line['text']}\n")
            jl.write(json.dumps(line, ensure_ascii=False) + "\n")

    words = sum(len(t.get("words", [])) for t in tracks.values())
    recovered = sum(1 for l in lines if l.get("recovered_from"))
    bleeds = sum(1 for l in lines if l.get("possible_bleed"))
    print(
        f"Assembled {len(lines)} lines ({len(dice)} dice, {recovered} recovered, {bleeds} possible_bleed) "
        f"from {len(tracks)} tracks / {words} words -> {output_txt}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
