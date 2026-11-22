#!/usr/bin/env python3
"""Transcribe one speaker track with local Whisper (mlx-whisper on Apple Silicon
if installed, otherwise faster-whisper on CUDA or CPU int8) and word timestamps.

Writes the common dnd-asr-v1 JSON (see asr_common.py) plus the legacy
`[HH:MM:SS.mmm -> HH:MM:SS.mmm] text` per-track transcript.

Example:
    python asr_whisper.py session-21/1-aurusoriale.flac \
        --out-json session-21/asr/whisper-turbo/1-aurusoriale.json \
        --model mobiuslabsgmbh/faster-whisper-large-v3-turbo --session 21
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

import asr_common

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent

DEFAULT_PARTY = ["Berridin", "Ellara", "Nyx", "Ysidor", "Witty"]
MLX_MODEL_REPOS = {
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "mobiuslabsgmbh/faster-whisper-large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "whisper-turbo": "mlx-community/whisper-large-v3-turbo",
    "distil-large-v3": "mlx-community/distil-whisper-large-v3",
}


def is_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}


def mlx_whisper_available() -> bool:
    return importlib.util.find_spec("mlx_whisper") is not None


def select_backend(requested_backend: str, requested_device: str) -> str:
    if requested_backend == "mlx":
        if not mlx_whisper_available():
            raise RuntimeError("mlx-whisper backend requested but `mlx_whisper` is not installed")
        return "mlx"
    if requested_backend == "faster-whisper":
        return "faster-whisper"
    # Auto: prefer mlx-whisper on Apple Silicon when installed, unless CUDA explicitly forced.
    if is_apple_silicon() and requested_device != "cuda" and mlx_whisper_available():
        return "mlx"
    return "faster-whisper"


def resolve_device_and_compute(device: str, compute_type: str) -> tuple[str, str]:
    resolved_device = device
    if resolved_device == "auto":
        if platform.system() == "Darwin":
            resolved_device = "cpu"
        else:
            try:
                import torch

                resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                resolved_device = "cpu"
    elif resolved_device == "cuda" and platform.system() == "Darwin":
        resolved_device = "cpu"

    resolved_compute = compute_type
    if resolved_compute == "auto":
        resolved_compute = "float16" if resolved_device == "cuda" else "int8"
    elif resolved_device == "cpu" and resolved_compute == "float16":
        resolved_compute = "int8"

    return resolved_device, resolved_compute


def _load_party_names(dnd_dir: Path) -> list[str]:
    metadata_path = dnd_dir / "scripts" / "transcription" / "entity_metadata.json"
    if not metadata_path.exists():
        return list(DEFAULT_PARTY)
    try:
        entities = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return list(DEFAULT_PARTY)
    names: list[str] = []
    for entity in entities:
        if entity.get("type") != "Characters":
            continue
        raw = str(entity.get("name", "")).strip()
        quoted = re.findall(r'"([^"]+)"', raw)
        short = quoted[0] if quoted else raw.split()[0]
        if short and short not in names:
            names.append(short)
    return names or list(DEFAULT_PARTY)


def build_prompt(transcribe_module, term_count: int) -> str:
    """Natural-sentence prompt with campaign names only.

    Generic tabletop phrases ("investigation check") and comma lists get echoed
    back by Whisper as hallucinations, so the prompt reads like a real line of
    table talk that happens to contain the canonical spellings.
    """
    import transcribe_gladia

    terms = transcribe_gladia.vocabulary_terms_from_metadata(
        DND_DIR, os.environ.get("WHISPER_SESSION_NUMBER"), transcribe_module
    )
    party = _load_party_names(DND_DIR)
    others = [t for t in terms if t not in party and '"' not in t and "(" not in t][:term_count]
    party_clause = ", ".join(party[:-1]) + (f" and {party[-1]}" if len(party) > 1 else party[0])
    if len(others) >= 2:
        other_clause = f"Last time we heard about {', '.join(others[:-1])} and {others[-1]}. "
    elif len(others) == 1:
        other_clause = f"Last time we heard about {others[0]}. "
    else:
        other_clause = ""
    return f"Okay, so {party_clause} are back. {other_clause}Nites be praised."


def _probe_duration(audio_file: Path) -> float | None:
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(audio_file)],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(proc.stdout.strip())
    except Exception:  # noqa: BLE001
        return None


def _run_mlx_whisper(
    audio_file: Path,
    model_name: str,
    initial_prompt: str | None,
) -> tuple[list[dict], list[dict], float | None, float | None, str]:
    import mlx_whisper

    mlx_repo = MLX_MODEL_REPOS.get(model_name, model_name)
    print(f"Running mlx-whisper ({mlx_repo}) on Apple Silicon Metal GPU...", flush=True)
    result = mlx_whisper.transcribe(
        str(audio_file),
        path_or_hf_repo=mlx_repo,
        language="en",
        word_timestamps=True,
        condition_on_previous_text=False,
        initial_prompt=initial_prompt,
    )
    words: list[dict] = []
    segments: list[dict] = []
    for seg in result.get("segments", []) or []:
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        segments.append({"s": start, "e": end, "text": text})
        for w in seg.get("words", []) or []:
            w_text = str(w.get("word", "")).strip()
            if not w_text:
                continue
            words.append({
                "s": float(w.get("start", start)),
                "e": float(w.get("end", end)),
                "w": w_text,
                "p": w.get("probability"),
            })
    duration = _probe_duration(audio_file)
    speech_seconds = sum(max(0.0, s["e"] - s["s"]) for s in segments)
    return words, segments, duration, speech_seconds, mlx_repo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audio_file")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-txt", help="Legacy per-track transcript path (default: <out-json>.txt)")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--backend", choices=["auto", "mlx", "faster-whisper"], default="auto")
    parser.add_argument("--device", default="auto", help="auto, cuda, or cpu")
    parser.add_argument("--compute-type", default="auto", help="auto, float16, or int8")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--session", help="Session number used to weight entity prompt terms")
    parser.add_argument("--vad-min-silence-ms", type=int, default=2000)
    parser.add_argument("--vad-speech-pad-ms", type=int, default=400)
    parser.add_argument("--vad-threshold", type=float, default=0.5)
    parser.add_argument("--no-prompt", action="store_true", help="Disable the entity initial prompt")
    parser.add_argument("--prompt-terms", type=int, default=30, help="Campaign names to mention in the prompt")
    parser.add_argument("--hotwords", action="store_true", help="Also pass legacy hotwords (can suppress punctuation)")
    parser.add_argument(
        "--hallucination-silence-threshold",
        type=float,
        default=2.0,
        help="Skip silent stretches longer than this inside a segment when a hallucination is suspected",
    )
    args = parser.parse_args()

    if args.session:
        os.environ["WHISPER_SESSION_NUMBER"] = str(args.session)
    sys.path.insert(0, str(SCRIPT_DIR))
    import transcribe_gladia  # noqa: E402

    audio_file = Path(args.audio_file).expanduser().resolve()
    out_json = Path(args.out_json).expanduser().resolve()
    out_txt = Path(args.out_txt).expanduser().resolve() if args.out_txt else out_json.with_suffix(".txt")

    backend = select_backend(args.backend, args.device)
    transcribe_helpers = transcribe_gladia.load_transcribe_module(SCRIPT_DIR)

    initial_prompt = hotwords = None
    if not args.no_prompt:
        initial_prompt = build_prompt(transcribe_helpers, args.prompt_terms)

    started = time.monotonic()
    if backend == "mlx":
        words, segments, duration, speech_seconds, used_model = _run_mlx_whisper(
            audio_file, args.model, initial_prompt
        )
        elapsed = time.monotonic() - started
        params = {
            "backend": "mlx-whisper",
            "initial_prompt": initial_prompt,
            "elapsed_seconds": round(elapsed, 1),
        }
    else:
        if is_apple_silicon() and args.backend == "auto":
            print("mlx-whisper not installed; falling back to faster-whisper on CPU int8.", flush=True)
        import transcribe  # noqa: E402  (imports torch/faster-whisper)

        if args.hotwords:
            entity_terms = transcribe.load_entity_terms(str(DND_DIR / "ENTITY_LIST.md"))
            hotwords = transcribe.build_hotwords(entity_terms)

        device, compute_type = resolve_device_and_compute(args.device, args.compute_type)
        model = transcribe.load_model(model_size=args.model, device=device, compute_type=compute_type)
        if model is None:
            return 1

        segments_iter, info = model.transcribe(
            str(audio_file),
            beam_size=args.beam_size,
            language="en",
            vad_filter=True,
            vad_parameters={
                "threshold": args.vad_threshold,
                "min_silence_duration_ms": args.vad_min_silence_ms,
                "speech_pad_ms": args.vad_speech_pad_ms,
            },
            condition_on_previous_text=False,
            word_timestamps=True,
            hallucination_silence_threshold=args.hallucination_silence_threshold,
            initial_prompt=initial_prompt,
            hotwords=hotwords,
        )

        words, segments = [], []
        for segment in segments_iter:
            segments.append({"s": segment.start, "e": segment.end, "text": segment.text})
            for word in segment.words or []:
                words.append({"s": word.start, "e": word.end, "w": word.word, "p": word.probability})
        elapsed = time.monotonic() - started
        duration = info.duration
        speech_seconds = getattr(info, "duration_after_vad", None)
        used_model = args.model
        params = {
            "backend": "faster-whisper",
            "device": device,
            "beam_size": args.beam_size,
            "compute_type": compute_type,
            "initial_prompt": initial_prompt,
            "hotwords": hotwords,
            "hallucination_silence_threshold": args.hallucination_silence_threshold,
            "elapsed_seconds": round(elapsed, 1),
        }

    asr_common.write_engine_json(
        out_json,
        engine="whisper",
        model=used_model,
        audio_file=audio_file,
        words=words,
        segments=segments,
        duration=duration,
        speech_seconds=speech_seconds,
        params=params,
    )
    asr_common.write_segment_txt(out_txt, segments)
    speech = speech_seconds or duration or 0.0
    print(
        f"{audio_file.name}: {len(words)} words, {len(segments)} segments, "
        f"{speech / 60:.1f} min speech in {elapsed / 60:.1f} min ({speech / max(elapsed, 1):.1f}x realtime)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
