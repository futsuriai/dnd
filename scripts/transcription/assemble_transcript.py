#!/usr/bin/env python3
"""Assemble a chronological multi-speaker transcript from per-track ASR JSON.

Input: a directory of dnd-asr-v1 track files (one engine), e.g. session/asr/gladia.
Output:
    Transcript Session N.txt          `[HH:MM:SS] Speaker: text` (downstream format)
    Transcript Session N.lines.jsonl  one record per line: precise times, track,
                                      confidence, low-confidence words, name edits

Compared with combine_transcripts.py this:
- orders lines by sub-second start time (whole-second sorting scrambled overlaps)
- builds utterances from word timings, then merges a speaker's consecutive
  utterances into one turn when nobody else spoke in between
- drops filler tokens (um/uh) and filler-only backchannels that overlap another
  speaker's turn ("yeah", "mm-hmm") so LLM passes see conversation, not noise
- applies context-aware canonical-name normalization (name_normalizer.py)
- optionally interleaves D&D Beyond dice events (from align_ddb_rolls.py)
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

FILLER_TOKENS = {"um", "uh", "erm", "hmm", "mm", "mhm", "uh-huh", "um-hum", "ah"}
BACKCHANNEL_WORDS = FILLER_TOKENS | {
    "yeah", "yes", "yep", "yup", "okay", "ok", "right", "mm-hmm", "uh-huh", "sure",
    "true", "nice", "oh", "wow", "cool", "gotcha", "alright",
}
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


def words_to_utterances(words: list[dict], split_gap: float, max_duration: float) -> list[dict]:
    utterances: list[dict] = []
    current: list[dict] = []
    for word in words:
        if current:
            gap = word["s"] - current[-1]["e"]
            duration = word["e"] - current[0]["s"]
            sentence_end = current[-1]["w"].endswith((".", "?", "!"))
            if gap > split_gap or (duration > max_duration and sentence_end):
                utterances.append({"s": current[0]["s"], "e": current[-1]["e"], "words": current})
                current = []
        current.append(word)
    if current:
        utterances.append({"s": current[0]["s"], "e": current[-1]["e"], "words": current})
    return utterances


def segments_to_utterances(segments: list[dict]) -> list[dict]:
    return [
        {"s": seg["s"], "e": seg["e"], "words": [{"s": seg["s"], "e": seg["e"], "w": w, "p": None} for w in seg["text"].split()]}
        for seg in segments
    ]


def utterance_text(words: list[dict]) -> str:
    kept = [w["w"] for w in words if bare(w["w"]) not in FILLER_TOKENS]
    text = " ".join(kept)
    text = re.sub(r"\s+([,.?!;:])", r"\1", text)
    text = re.sub(r"([,.?!])\1+", r"\1", text)
    text = re.sub(r"^[,.;:]\s*", "", text)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text.strip()


def is_backchannel(words: list[dict]) -> bool:
    tokens = [bare(w["w"]) for w in words if bare(w["w"])]
    return bool(tokens) and len(tokens) <= 3 and all(t in BACKCHANNEL_WORDS for t in tokens)


def build_lines(
    tracks: dict[str, dict],
    speaker_map: dict[str, str],
    split_gap: float,
    merge_gap: float,
    max_turn_chars: int,
    max_duration: float,
    low_conf: float,
    keep_backchannels: bool,
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

    if not keep_backchannels:
        filtered = []
        for i, utt in enumerate(utterances):
            if is_backchannel(utt["words"]):
                overlapping = any(
                    other["speaker"] != utt["speaker"] and other["s"] - 1.0 <= utt["s"] <= other["e"] + 1.0
                    for other in utterances[max(0, i - 6): i + 6]
                    if other is not utt and not is_backchannel(other["words"])
                )
                if overlapping:
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
            continue
        turns.append({"s": utt["s"], "e": utt["e"], "speaker": utt["speaker"], "track": utt["track"], "words": list(utt["words"])})

    lines = []
    for turn in turns:
        text = utterance_text(turn["words"])
        if not text:
            continue
        confidences = [w["p"] for w in turn["words"] if w.get("p") is not None]
        lines.append({
            "start": round(turn["s"], 3),
            "end": round(turn["e"], 3),
            "speaker": turn["speaker"],
            "track": turn["track"],
            "text": text,
            "mean_conf": round(sum(confidences) / len(confidences), 3) if confidences else None,
            "low_conf_words": [w["w"] for w in turn["words"] if w.get("p") is not None and w["p"] < low_conf],
        })
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


def dice_line(event: dict) -> dict:
    detail = f" ({event['detail']})" if event.get("detail") else ""
    label = " ".join(part for part in (event.get("action"), event.get("roll_type")) if part)
    text = f"{event.get('character', 'Someone')} rolled {label or 'a roll'}: {event.get('total')}{detail}"
    return {
        "start": round(float(event["audio_time"]), 3),
        "end": round(float(event["audio_time"]), 3),
        "speaker": "DICE",
        "track": "ddb",
        "text": text,
        "mean_conf": None,
        "low_conf_words": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engine_dir", help="Directory with one engine's dnd-asr-v1 track JSON files")
    parser.add_argument("output_txt")
    parser.add_argument("--lines-jsonl", help="Default: <output_txt minus .txt>.lines.jsonl")
    parser.add_argument("--dice", help="Aligned dice events JSONL from align_ddb_rolls.py")
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

    lines = build_lines(
        tracks,
        load_speaker_map(),
        split_gap=args.split_gap,
        merge_gap=args.merge_gap,
        max_turn_chars=args.max_turn_chars,
        max_duration=args.max_utterance_seconds,
        low_conf=args.low_conf,
        keep_backchannels=args.keep_backchannels,
    )

    normalizer = NameNormalizer(Path(args.corrections))
    for line in lines:
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
    print(f"Assembled {len(lines)} lines ({len(dice)} dice) from {len(tracks)} tracks / {words} words -> {output_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
