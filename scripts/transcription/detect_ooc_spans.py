#!/usr/bin/env python3
"""Conservatively detect clear non-game OOC stretches before Gemini audio arbitration.

Runs a single fast structured pass over the primary ASR timeline (e.g. Gladia) to
identify unmistakable non-game spans >= 60s (pre-game mic/work setup, mid-session
breaks, post-game wrap-up) with an 8s inward safety margin on each boundary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import asr_common  # noqa: E402
import assemble_transcript  # noqa: E402

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

WORKSPACE = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent

OOC_SPANS_SCHEMA = {
    "type": "object",
    "properties": {
        "spans": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["start", "end", "reason"],
            },
        }
    },
    "required": ["spans"],
}

PROMPT = """You are identifying ONLY unmistakable, continuous out-of-character (OOC) stretches in a Dungeons & Dragons
session transcript so the audio-arbitration step does not waste calls transcribing pre-game banter, breaks, or
post-game sign-off.

Timeline lines (`[seconds | HH:MM:SS] Speaker: text`):
{lines}

Return JSON matching the schema:
{{"spans": [{{"start": <start_seconds>, "end": <end_seconds>, "reason": "<short reason>"}}]}}

STRICT CONSERVATIVE RULES (false negatives are harmless; false positives lose real gameplay):
- ONLY mark a span if it lasts at least 60 seconds AND is 100% pure OOC with ZERO in-character dialogue, ZERO GM
  narration/world-building, ZERO dice rolls/skill checks, ZERO character planning, and ZERO session recaps.
- Typical valid OOC spans:
  1. Pre-game mic check, recording start, and real-world work/life chatter BEFORE the GM says "last time" / recaps / begins play.
  2. Long mid-session intermissions (bathroom/pet/dinner breaks with no gameplay).
  3. Post-game goodbyes, scheduling next session, and wrap-up chatter AFTER the GM ends the session.
- If a span mixes OOC jokes with even one in-game question, action, or GM response, DO NOT mark it.
- Use numeric seconds from the `[seconds | ...]` prefix. If there are no clear >=60s OOC spans, return {{"spans": []}}.
"""


def load_coarse_lines(reference_dir: Path, max_line_chars: int = 140) -> list[dict]:
    """Load sorted per-speaker segments from a primary ASR directory."""
    tracks = asr_common.load_engine_dir(reference_dir)
    speaker_map = assemble_transcript.load_speaker_map()
    coarse: list[dict] = []
    for track, data in tracks.items():
        speaker = assemble_transcript.identify_speaker(track, speaker_map)
        for seg in data.get("segments", []):
            text = " ".join(str(seg.get("text", "")).split())
            if not text:
                continue
            if len(text) > max_line_chars:
                text = text[: max_line_chars - 3].rstrip() + "..."
            coarse.append(
                {
                    "s": float(seg["s"]),
                    "e": float(seg["e"]),
                    "track": track,
                    "speaker": speaker,
                    "text": text,
                }
            )
    coarse.sort(key=lambda item: (item["s"], item["e"], item["track"]))
    return coarse


def render_coarse_timeline(lines: list[dict]) -> str:
    return "\n".join(
        f"[{line['s']:.1f}s->{line['e']:.1f}s | {asr_common.format_ts(line['s'])}] {line['speaker']}: {line['text']}"
        for line in lines
    )


def normalize_ooc_spans(
    raw_spans: list[dict],
    *,
    min_duration: float = 60.0,
    safety_margin: float = 8.0,
) -> list[dict]:
    """Keep only >= min_duration spans, merge overlaps, and inset outer boundaries by safety_margin."""
    min_trimmed = min(45.0, max(1.0, min_duration - 2.0 * safety_margin))
    raw_valid: list[dict] = []
    for item in raw_spans:
        if not isinstance(item, dict):
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end - start < min_duration:
            continue
        reason = " ".join(str(item.get("reason", "")).split()) or "ooc"
        raw_valid.append({"start": start, "end": end, "reason": reason})

    if not raw_valid:
        return []

    raw_valid.sort(key=lambda s: (s["start"], s["end"]))
    merged_raw: list[dict] = [raw_valid[0]]
    for cur in raw_valid[1:]:
        prev = merged_raw[-1]
        if cur["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], cur["end"])
            if cur["reason"] and cur["reason"] not in prev["reason"]:
                prev["reason"] = f"{prev['reason']}; {cur['reason']}"
        else:
            merged_raw.append(cur)

    inset: list[dict] = []
    for span in merged_raw:
        trimmed_start = 0.0 if span["start"] <= 0.0 else span["start"] + safety_margin
        trimmed_end = span["end"] - safety_margin
        if trimmed_end <= trimmed_start or (trimmed_end - trimmed_start) < min_trimmed:
            continue
        inset.append(
            {
                "start": round(trimmed_start, 2),
                "end": round(trimmed_end, 2),
                "reason": span["reason"],
            }
        )
    return inset


def detect_ooc_spans(
    reference_dir: Path,
    *,
    provider: str = "agy",
    model: str | None = None,
    min_duration: float = 60.0,
    safety_margin: float = 8.0,
) -> list[dict]:
    """Detect conservative OOC spans from a primary ASR engine directory."""
    coarse = load_coarse_lines(reference_dir)
    if not coarse:
        return []

    resolved_model = model or (agent_cli.AGY_TIERS["fast"] if provider == "agy" else None)
    prompt = PROMPT.format(lines=render_coarse_timeline(coarse))
    reply = agent_cli.run_agent(
        prompt,
        provider=provider,
        model=resolved_model,
        workspace=WORKSPACE,
        write=False,
        json_schema=OOC_SPANS_SCHEMA,
        timeout=240,
        retries=1,
    )
    payload = agent_cli.extract_json(reply)
    raw_spans = payload.get("spans", []) if isinstance(payload, dict) else []
    if not isinstance(raw_spans, list):
        return []
    return normalize_ooc_spans(raw_spans, min_duration=min_duration, safety_margin=safety_margin)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", required=True, help="Primary engine dir, e.g. <session>/asr/gladia")
    parser.add_argument("--out", required=True, help="Output JSON path for normalized OOC spans")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="agy")
    parser.add_argument("--model", help="Optional model override (default on agy: gemini-4-neon-low)")
    parser.add_argument("--min-duration", type=float, default=60.0)
    parser.add_argument("--safety-margin", type=float, default=8.0)
    args = parser.parse_args(argv)

    ref_dir = Path(args.reference_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    spans = detect_ooc_spans(
        ref_dir,
        provider=args.provider,
        model=args.model,
        min_duration=args.min_duration,
        safety_margin=args.safety_margin,
    )
    payload = {
        "reference_dir": str(ref_dir),
        "min_duration": args.min_duration,
        "safety_margin": args.safety_margin,
        "spans": spans,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total_sec = sum(s["end"] - s["start"] for s in spans)
    print(f"Detected {len(spans)} OOC span(s) ({total_sec / 60:.1f} min) -> {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
