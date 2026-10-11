#!/usr/bin/env python3
"""Work out when a session was played and when the next one is scheduled.

- played date: --session-date if given, else the first D&D Beyond roll's local
  date (ddb/rolls.jsonl), else the oldest audio file's modification date
- next session: an LLM reads the table's closing talk (the last minutes of the
  transcript, where scheduling usually happens) and resolves phrases like
  "next time will be November 1st" against the played date

Writes JSON: {"session_date": "October 11, 2026", "next_session_date": "November 1, 2026" | null, ...}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402

AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".ogg", ".aac"}

PROMPT = """Below are the first and last minutes of a Dungeons & Dragons session transcript. The session was played on
{played} ({weekday}). Did the table schedule the next session? Resolve relative dates ("next Sunday", "November 1st",
"in two weeks") against the played date.

Return JSON only: {{"next_session_date": "YYYY-MM-DD" or null, "evidence": "<the line that sets it, or empty>"}}
Use null if no date was agreed or it is unclear.

Transcript:
{lines}
"""


def human(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}, {d.year}"


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
    mtimes = [p.stat().st_mtime for p in audio_dir.iterdir() if p.suffix.lower() in AUDIO_EXTENSIONS]
    return datetime.fromtimestamp(min(mtimes)).date(), "audio file date"


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
    excerpt = lines[: args.head_lines] + ["[...]"] + lines[-args.tail_lines:]
    facts = {"session_date": human(played), "session_date_source": source, "next_session_date": None, "evidence": ""}
    try:
        reply = agent_cli.run_agent(
            args.provider,
            PROMPT.format(played=played.isoformat(), weekday=played.strftime("%A"), lines="\n".join(excerpt)),
            SCRIPT_DIR.parent.parent,
            args.model,
        )
        text = agent_cli.strip_code_fences(reply)
        data = json.loads(text[text.find("{"): text.rfind("}") + 1])
        if data.get("next_session_date"):
            nxt = date.fromisoformat(data["next_session_date"])
            if nxt > played:
                facts["next_session_date"] = human(nxt)
                facts["evidence"] = data.get("evidence", "")
    except Exception as exc:  # noqa: BLE001 - dates are a nicety; never block the pipeline
        facts["error"] = str(exc)[:200]
    Path(args.out).write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
