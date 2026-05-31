#!/usr/bin/env python3
"""
Create speech-only audio with a timeline map, then restore transcript timestamps.

This is intended for cloud/serverless transcription paths where uploading silence
has a real cost. The local faster-whisper path already applies VAD internally and
restores timestamps before writing transcript lines.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import re
import wave
from pathlib import Path

import numpy as np
from faster_whisper.audio import decode_audio
from faster_whisper.vad import VadOptions, get_speech_timestamps


SAMPLE_RATE = 16000
TIMESTAMP_RE = re.compile(
    r"^\[(?P<start>\d+:\d{2}:\d{2}(?:\.\d+)?)"
    r"(?:\s*->\s*(?P<end>\d+:\d{2}:\d{2}(?:\.\d+)?))?"
    r"\](?P<rest>.*)$"
)


def parse_timestamp(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def format_timestamp(seconds: float) -> str:
    seconds = max(0, seconds)
    whole_seconds = int(seconds)
    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    secs = whole_seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"


def write_wav(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def build_compact_audio(audio: np.ndarray, chunks: list[dict], gap_samples: int) -> np.ndarray:
    if not chunks:
        return np.array([], dtype=np.float32)

    parts = []
    for index, chunk in enumerate(chunks):
        if index and gap_samples > 0:
            parts.append(np.zeros(gap_samples, dtype=np.float32))
        parts.append(audio[chunk["start"]:chunk["end"]])

    return np.concatenate(parts)


def build_timeline(chunks: list[dict], gap_samples: int = 0) -> list[dict]:
    timeline = []
    compact_cursor = 0

    for index, chunk in enumerate(chunks):
        if index:
            compact_cursor += gap_samples

        original_start = chunk["start"] / SAMPLE_RATE
        original_end = chunk["end"] / SAMPLE_RATE
        duration = original_end - original_start
        compact_start = compact_cursor / SAMPLE_RATE
        compact_end = compact_start + duration

        timeline.append({
            "compact_start": compact_start,
            "compact_end": compact_end,
            "original_start": original_start,
            "original_end": original_end,
        })
        compact_cursor += chunk["end"] - chunk["start"]

    return timeline


def json_safe_number(value: float | int) -> float | int | None:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def compact(args: argparse.Namespace) -> None:
    input_path = Path(args.input_audio)
    output_audio = Path(args.output_audio)
    manifest_path = Path(args.manifest)

    audio = decode_audio(str(input_path), sampling_rate=SAMPLE_RATE)
    original_duration = len(audio) / SAMPLE_RATE
    vad_options = VadOptions(
        threshold=args.threshold,
        min_speech_duration_ms=args.min_speech_duration_ms,
        max_speech_duration_s=args.max_speech_duration_s,
        min_silence_duration_ms=args.min_silence_duration_ms,
        speech_pad_ms=args.speech_pad_ms,
    )
    chunks = get_speech_timestamps(audio, vad_options, sampling_rate=SAMPLE_RATE)
    segment_gap_samples = round(args.segment_gap_ms * SAMPLE_RATE / 1000)

    compact_audio = build_compact_audio(audio, chunks, segment_gap_samples)
    timeline = build_timeline(chunks, segment_gap_samples)
    compact_duration = len(compact_audio) / SAMPLE_RATE
    removed_duration = original_duration - compact_duration
    removed_ratio = removed_duration / original_duration if original_duration else 0

    write_wav(output_audio, compact_audio)
    manifest = {
        "source_audio": str(input_path),
        "compact_audio": str(output_audio),
        "sample_rate": SAMPLE_RATE,
        "original_duration": original_duration,
        "compact_duration": compact_duration,
        "removed_duration": removed_duration,
        "removed_ratio": removed_ratio,
        "vad_options": {
            "threshold": args.threshold,
            "min_speech_duration_ms": args.min_speech_duration_ms,
            "max_speech_duration_s": json_safe_number(args.max_speech_duration_s),
            "min_silence_duration_ms": args.min_silence_duration_ms,
            "speech_pad_ms": args.speech_pad_ms,
            "segment_gap_ms": args.segment_gap_ms,
        },
        "segments": timeline,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Compact audio: {output_audio}")
    print(f"Timeline manifest: {manifest_path}")
    print(f"Original duration: {original_duration:.1f}s")
    print(f"Compact duration: {compact_duration:.1f}s")
    print(f"Removed silence: {removed_duration:.1f}s ({removed_ratio:.1%})")
    print(f"Speech segments: {len(timeline)}")


class TimelineMapper:
    def __init__(self, segments: list[dict]):
        if not segments:
            raise ValueError("manifest has no VAD timeline segments")

        self.segments = segments
        self.starts = [segment["compact_start"] for segment in segments]

    def map_time(self, compact_time: float, is_end: bool = False) -> float:
        index = bisect.bisect_right(self.starts, compact_time) - 1
        index = max(0, min(index, len(self.segments) - 1))

        segment = self.segments[index]
        if compact_time > segment["compact_end"] and index + 1 < len(self.segments):
            segment = self.segments[index + 1]

        offset = compact_time - segment["compact_start"]
        if is_end:
            offset = min(max(offset, 0), segment["original_end"] - segment["original_start"])
        else:
            offset = max(offset, 0)

        return segment["original_start"] + offset


def remap(args: argparse.Namespace) -> None:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    mapper = TimelineMapper(manifest["segments"])
    input_path = Path(args.input_transcript)
    output_path = Path(args.output_transcript)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    remapped_lines = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        match = TIMESTAMP_RE.match(line)
        if not match:
            remapped_lines.append(line)
            continue

        start = mapper.map_time(parse_timestamp(match.group("start")))
        end_value = match.group("end")
        if end_value:
            end = mapper.map_time(parse_timestamp(end_value), is_end=True)
            remapped_lines.append(
                f"[{format_timestamp(start)} -> {format_timestamp(end)}]{match.group('rest')}"
            )
        else:
            remapped_lines.append(f"[{format_timestamp(start)}]{match.group('rest')}")

    output_path.write_text("\n".join(remapped_lines) + "\n", encoding="utf-8")
    print(f"Remapped transcript: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    compact_parser = sub.add_parser("compact", help="Create compact speech-only WAV and timeline JSON")
    compact_parser.add_argument("input_audio")
    compact_parser.add_argument("output_audio")
    compact_parser.add_argument("manifest")
    compact_parser.add_argument("--threshold", type=float, default=0.5)
    compact_parser.add_argument("--min-speech-duration-ms", type=int, default=0)
    compact_parser.add_argument("--max-speech-duration-s", type=float, default=float("inf"))
    compact_parser.add_argument("--min-silence-duration-ms", type=int, default=2000)
    compact_parser.add_argument("--speech-pad-ms", type=int, default=400)
    compact_parser.add_argument(
        "--segment-gap-ms",
        type=int,
        default=250,
        help="Insert this much silence between retained VAD islands in compact audio",
    )
    compact_parser.set_defaults(func=compact)

    remap_parser = sub.add_parser("remap", help="Restore compact transcript timestamps to original time")
    remap_parser.add_argument("manifest")
    remap_parser.add_argument("input_transcript")
    remap_parser.add_argument("output_transcript")
    remap_parser.set_defaults(func=remap)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
