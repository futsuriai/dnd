#!/usr/bin/env python3
"""Transcribe one speaker track with local faster-whisper and word timestamps.

Writes the common dnd-asr-v1 JSON (see asr_common.py) plus the legacy
`[HH:MM:SS.mmm -> HH:MM:SS.mmm] text` per-track transcript.

Example:
    python asr_whisper.py session-21/1-aurusoriale.flac \
        --out-json session-21/asr/whisper-large-v3/1-aurusoriale.json \
        --model large-v3 --session 21
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import asr_common

SCRIPT_DIR = Path(__file__).resolve().parent


def build_prompt(transcribe, term_count: int) -> str:
    """Natural-sentence prompt with campaign names only.

    Generic tabletop phrases ("investigation check") and comma lists get echoed
    back by Whisper as hallucinations, so the prompt reads like a real line of
    table talk that happens to contain the canonical spellings.
    """
    import transcribe_gladia

    terms = transcribe_gladia.vocabulary_terms_from_metadata(
        SCRIPT_DIR.parent.parent, os.environ.get("WHISPER_SESSION_NUMBER"), transcribe
    )
    party = ["Berridin", "Ellara", "Nyx", "Ysidor", "Witty"]
    others = [t for t in terms if t not in party and '"' not in t and "(" not in t][:term_count]
    return (
        "Okay, so Berridin, Ellara, Nyx, Ysidor and Witty are back. "
        f"Last time we heard about {', '.join(others[:-1])} and {others[-1]}. "
        "Nites be praised."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audio_file")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-txt", help="Legacy per-track transcript path (default: <out-json>.txt)")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--compute-type", default="float16")
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
    import transcribe  # noqa: E402  (imports torch/faster-whisper)

    audio_file = Path(args.audio_file).expanduser().resolve()
    out_json = Path(args.out_json).expanduser().resolve()
    out_txt = Path(args.out_txt).expanduser().resolve() if args.out_txt else out_json.with_suffix(".txt")

    initial_prompt = hotwords = None
    if not args.no_prompt:
        initial_prompt = build_prompt(transcribe, args.prompt_terms)
    if args.hotwords:
        entity_terms = transcribe.load_entity_terms(str(SCRIPT_DIR.parent.parent / "ENTITY_LIST.md"))
        hotwords = transcribe.build_hotwords(entity_terms)

    model = transcribe.load_model(model_size=args.model, device=args.device, compute_type=args.compute_type)
    if model is None:
        return 1

    started = time.monotonic()
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

    asr_common.write_engine_json(
        out_json,
        engine="whisper",
        model=args.model,
        audio_file=audio_file,
        words=words,
        segments=segments,
        duration=info.duration,
        speech_seconds=getattr(info, "duration_after_vad", None),
        params={
            "beam_size": args.beam_size,
            "compute_type": args.compute_type,
            "initial_prompt": initial_prompt,
            "hotwords": hotwords,
            "hallucination_silence_threshold": args.hallucination_silence_threshold,
            "elapsed_seconds": round(elapsed, 1),
        },
    )
    asr_common.write_segment_txt(out_txt, segments)
    speech = getattr(info, "duration_after_vad", None) or info.duration
    print(
        f"{audio_file.name}: {len(words)} words, {len(segments)} segments, "
        f"{speech / 60:.1f} min speech in {elapsed / 60:.1f} min ({speech / max(elapsed, 1):.1f}x realtime)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
