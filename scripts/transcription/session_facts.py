#!/usr/bin/env python3
"""Work out when a session was played and when the next one is scheduled.

- played date: --session-date if given, else the first D&D Beyond roll's local
  date (`ddb/rolls.jsonl`), else audio container metadata (`ffprobe` tags such
  as `creation_time` / `date` / `TDRC`) or Craig filename timestamp, and only
  last the oldest audio file's modification date (`st_mtime`)
- next session: an LLM reads the opening, closing, AND any mid-session
  scheduling/break excerpts from the transcript and resolves phrases like
  "next time will be November 1st" against the played date

Writes JSON: {"session_date": "October 11, 2026", "next_session_date": "November 1, 2026" | null, ...}
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

DND_DIR = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent
AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".ogg", ".aac"}
FILENAME_DATE_RE = re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})")
SCHEDULE_RE = re.compile(
    r"\b("
    r"next\s+(?:session|week|time|sunday|saturday|friday|monday|tuesday|wednesday|thursday)|"
    r"two\s+weeks|in\s+a\s+couple\s+weeks|same\s+time|schedule|scheduling|calendar|"
    r"are\s+we\s+playing|can\s+everyone\s+make|free\s+on|available\s+on|play\s+next|"
    r"january|february|march|april|may|june|july|august|september|october|november|december"
    r")\b",
    re.IGNORECASE,
)

SESSION_FACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "next_session_date": {"type": ["string", "null"]},
        "evidence": {"type": "string"},
    },
    "required": ["next_session_date", "evidence"],
}

PROMPT = """Below are excerpts from a Dungeons & Dragons session transcript (opening, mid-session scheduling
mentions if any, and closing talk). The session was played on {played} ({weekday}). Did the table schedule
the next session? Resolve relative dates ("next Sunday", "November 1st", "in two weeks") against the played date.

Return JSON matching the schema: {{"next_session_date": "YYYY-MM-DD" or null, "evidence": "<the line that sets it, or empty>"}}
Use null if no date was agreed or it is unclear.

Transcript:
{lines}
"""


def human(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _parse_date_string(raw: str) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    iso_match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if iso_match:
        try:
            return date.fromisoformat(iso_match.group(1))
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%B %d, %Y"):
        try:
            return datetime.strptime(text[:20].strip(), fmt).date()
        except ValueError:
            continue
    return None


def probe_audio_container_date(audio_path: Path) -> date | None:
    """Inspect audio container tags (`creation_time`, `date`, `TDRC`, etc.) via ffprobe."""
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format_tags:stream_tags",
                "-of",
                "json",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        data = json.loads(proc.stdout)
    except Exception:  # noqa: BLE001
        return None

    tags: dict[str, str] = {}
    fmt_tags = (data.get("format") or {}).get("tags") or {}
    tags.update({k.lower(): str(v) for k, v in fmt_tags.items()})
    for stream in data.get("streams") or []:
        for k, v in (stream.get("tags") or {}).items():
            tags.setdefault(k.lower(), str(v))

    for key in ("creation_time", "date", "tdrc", "origination_date", "icrd", "encoded_date", "comment"):
        if key in tags:
            parsed = _parse_date_string(tags[key])
            if parsed is not None:
                return parsed
    return None


def _filename_date(audio_dir: Path, audio_files: list[Path]) -> date | None:
    for candidate in [audio_dir.name, *(p.name for p in audio_files)]:
        match = FILENAME_DATE_RE.search(candidate)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                continue
    return None


def played_date(audio_dir: Path, override: str | None) -> tuple[date, str]:
    if override:
        for fmt in ("%Y-%m-%d", "%B %d, %Y"):
            try:
                return datetime.strptime(override, fmt).date(), "given"
            except ValueError:
                continue
        raise SystemExit(f"unrecognized --session-date: {override}")

    rolls = audio_dir / "ddb" / "rolls.jsonl"
    if rolls.exists() and rolls.stat().st_size:
        first = json.loads(rolls.read_text(encoding="utf-8").splitlines()[0])
        return datetime.fromisoformat(first["wall_time"]).astimezone().date(), "D&D Beyond rolls"

    audio_files = sorted(p for p in audio_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS)
    container_dates = [d for p in audio_files[:4] if (d := probe_audio_container_date(p)) is not None]
    if container_dates:
        return min(container_dates), "audio container metadata"

    fn_date = _filename_date(audio_dir, audio_files)
    if fn_date is not None:
        return fn_date, "audio filename date"

    mtimes = [p.stat().st_mtime for p in audio_files]
    if not mtimes:
        raise SystemExit(f"no audio files in {audio_dir} to infer played date")
    return datetime.fromtimestamp(min(mtimes)).date(), "audio file mtime"


def build_scheduling_excerpt(
    lines: list[str],
    head_lines: int = 40,
    tail_lines: int = 120,
    mid_context: int = 4,
    max_mid_windows: int = 8,
) -> list[str]:
    """Combine head, mid-session scheduling mentions/breaks, and tail lines."""
    total = len(lines)
    if total <= head_lines + tail_lines:
        return list(lines)

    head_end = head_lines
    tail_start = max(head_end, total - tail_lines)

    # Find mid-session scheduling / break mentions.
    mid_ranges: list[tuple[int, int]] = []
    for idx in range(head_end, tail_start):
        if SCHEDULE_RE.search(lines[idx]):
            lo = max(head_end, idx - mid_context)
            hi = min(tail_start, idx + mid_context + 1)
            if mid_ranges and lo <= mid_ranges[-1][1] + 2:
                mid_ranges[-1] = (mid_ranges[-1][0], max(mid_ranges[-1][1], hi))
            else:
                mid_ranges.append((lo, hi))
                if len(mid_ranges) >= max_mid_windows:
                    break

    excerpt: list[str] = list(lines[:head_end])
    for lo, hi in mid_ranges:
        excerpt.append("[...]")
        excerpt.extend(lines[lo:hi])
    excerpt.append("[...]")
    excerpt.extend(lines[tail_start:])
    return excerpt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audio-dir", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--session-date", help="Override the played date (YYYY-MM-DD or 'October 11, 2026')")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="codex")
    parser.add_argument("--model")
    parser.add_argument("--head-lines", type=int, default=40)
    parser.add_argument("--tail-lines", type=int, default=120)
    args = parser.parse_args()

    played, source = played_date(Path(args.audio_dir), args.session_date)
    lines = [l for l in Path(args.transcript).read_text(encoding="utf-8").splitlines() if l.strip()]
    excerpt = build_scheduling_excerpt(lines, head_lines=args.head_lines, tail_lines=args.tail_lines)
    facts = {"session_date": human(played), "session_date_source": source, "next_session_date": None, "evidence": ""}

    model = args.model
    if args.provider == "agy" and not model:
        model = agent_cli.AGY_TIERS["fast"]

    try:
        reply = agent_cli.run_agent(
            PROMPT.format(played=played.isoformat(), weekday=played.strftime("%A"), lines="\n".join(excerpt)),
            provider=args.provider,
            model=model,
            workspace=DND_DIR,
            write=False,
            json_schema=SESSION_FACTS_SCHEMA,
            timeout=180,
            retries=1,
        )
        data = agent_cli.extract_json(reply)
        if isinstance(data, dict) and data.get("next_session_date"):
            nxt = date.fromisoformat(data["next_session_date"])
            if nxt > played:
                facts["next_session_date"] = human(nxt)
                facts["evidence"] = str(data.get("evidence", ""))
    except Exception as exc:  # noqa: BLE001 - dates are a nicety; never block the pipeline
        facts["error"] = str(exc)[:200]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
