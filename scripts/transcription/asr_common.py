"""Common per-track ASR output format shared by every transcription engine.

Each engine writes one JSON file per speaker track:

{
  "format": "dnd-asr-v1",
  "engine": "gladia" | "whisper" | ...,
  "model": "...",
  "audio_file": "/path/to/1-aurusoriale.flac",
  "track": "1-aurusoriale",
  "duration": 3901.2,            # seconds of original audio
  "speech_seconds": 812.4,       # VAD speech time when known
  "params": {...},               # engine settings worth reproducing
  "words": [{"s": 12.31, "e": 12.62, "w": "Hello", "p": 0.94}, ...],
  "segments": [{"s": 12.31, "e": 15.02, "text": "Hello there."}, ...]
}

Times are seconds on the original (uncompacted) audio timeline. `p` is the
engine's word confidence/probability when available, else null.
"""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

FORMAT = "dnd-asr-v1"


def track_name(audio_file: Path | str) -> str:
    name = Path(audio_file).name
    return name.split(".", 1)[0]


def format_ts(seconds: float, millis: bool = False) -> str:
    seconds = max(0.0, float(seconds))
    whole = int(seconds)
    text = f"{whole // 3600:02}:{whole % 3600 // 60:02}:{whole % 60:02}"
    if millis:
        text += f".{int(round((seconds - whole) * 1000)) % 1000:03}"
    return text


def parse_ts(value: str) -> float:
    parts = value.split(":")
    hours, minutes = int(parts[0]), int(parts[1])
    return hours * 3600 + minutes * 60 + float(parts[2])


def clean_word(word: str) -> str:
    return re.sub(r"\s+", " ", word or "").strip()


def write_engine_json(
    path: Path,
    engine: str,
    model: str,
    audio_file: Path,
    words: list[dict],
    segments: list[dict],
    duration: float | None = None,
    speech_seconds: float | None = None,
    params: dict | None = None,
) -> None:
    payload = {
        "format": FORMAT,
        "engine": engine,
        "model": model,
        "audio_file": str(audio_file),
        "track": track_name(audio_file),
        "duration": duration,
        "speech_seconds": speech_seconds,
        "params": params or {},
        "words": [
            {
                "s": round(float(w["s"]), 3),
                "e": round(float(w["e"]), 3),
                "w": clean_word(w["w"]),
                "p": None if w.get("p") is None else round(float(w["p"]), 4),
            }
            for w in words
            if clean_word(w.get("w", ""))
        ],
        "segments": [
            {"s": round(float(s["s"]), 3), "e": round(float(s["e"]), 3), "text": s["text"].strip()}
            for s in segments
            if s.get("text", "").strip()
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def load_engine_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") != FORMAT:
        raise ValueError(f"{path} is not a {FORMAT} file")
    return data


def load_engine_dir(directory: Path) -> dict[str, dict]:
    """Map track name -> engine JSON for every track file in a directory."""
    tracks = {}
    for path in sorted(Path(directory).glob("*.json")):
        try:
            data = load_engine_json(path)
        except (ValueError, json.JSONDecodeError):
            continue
        tracks[data["track"]] = data
    return tracks


def archive_json(source: Path, dest: Path) -> Path:
    """Store a raw provider response compactly (gzip) for later reprocessing."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Path(source).open("rb") as src, gzip.open(dest, "wb") as out:
        out.write(src.read())
    return dest


def write_segment_txt(path: Path, segments: list[dict]) -> None:
    """Legacy per-track text format, now with millisecond timestamps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8") as f:
        for seg in segments:
            text = seg["text"].strip()
            if text:
                f.write(f"[{format_ts(seg['s'], True)} -> {format_ts(seg['e'], True)}] {text}\n")
