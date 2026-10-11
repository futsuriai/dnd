#!/usr/bin/env python3
"""Sync polished session notes into the website and optionally run an agent update pass."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import agent_cli


def build_prompt(session: int, session_date: str | None = None, next_session_date: str | None = None) -> str:
    played = f"Session {session} was played on {session_date}: set its `date` to exactly '{session_date}'." if session_date else (
        f"Keep session {session}'s existing `date` unless it is clearly a placeholder."
    )
    upcoming = (
        f"The table scheduled the next session for {next_session_date}: give session {session + 1} the `date` '{next_session_date}'."
        if next_session_date
        else f"No next-session date was scheduled: give session {session + 1} the `date` 'TBD'."
    )
    return f"""Task:
Update the DnD website repo for completed Session {session}.

Use `.copilot/prompts/process-latest-session.md` as the governing instructions.
Use `src/assets/sessions/session-{session}.md` as the primary source summary.

Required work:
- Update `src/store/sessions.js`: mark session {session} complete, set `summaryFile`, update subtitle/description/highlights, and create or verify session {session + 1} as the upcoming stub.
- Review `src/store/locations.js`, `src/store/npcs.js`, and `src/store/lore.js`; add only significant history, connection, description, or entity changes grounded in the polished summary.
- Update `src/views/HomeView.vue` with a deterministic recap/next-step override when generic extraction would be weak.
- Update `src/views/StorySoFarView.vue` when Session {session} materially changes the campaign-state recap.
- Run `npm run generate-list` if entity/store data changes.
- Preserve canonical spellings from `ENTITY_LIST.md`, `src/store/lore.js`, and `scripts/transcription/name_corrections.json`.
- Use `Nites` exactly, pronounced knee-tes. Do not write `Nytes` or `Nýtes`.
- Preserve capitalization for Ellara, Nyx, Ysidor, Berridin, and Witty in public copy.
- Preserve dice/check attribution from `src/assets/sessions/session-{session}.md`; do not reassign a natural 20, skill check, or lore clue to another character while summarizing into stores/views.
- If the polished summary is ambiguous about who rolled, omit the roller from store/view copy instead of guessing.
- Do not touch unrelated files or generated intermediate artifacts.

Dates (authoritative, overriding "today's date" in the governing instructions):
- {played}
- {upcoming}

Keep the update proportionate and in the existing voice:
- Touch only entities whose state or understanding genuinely changed this session; for a normal session that
  is usually 3-8 entities. Look at how sessions 19 and 20 were recorded and match that scale.
- Entity `description` fields describe what the entity is. Do not put the party's current plans, pending tasks,
  or undecided choices into descriptions; record session events as one-sentence `history` notes instead.
- History notes and highlights state what happened plainly, one or two sentences each (highlights: 5-8, under
  ~220 characters). Do not stack caveats such as "without laboratory testing", "remains unconfirmed", or
  "has not yet occurred"; mention an open question once, where it matters.
- Do not rewrite existing descriptions or connection reasons. If the session adds or contradicts a detail, add
  it (e.g. a new history note) rather than replacing earlier canon.

After editing, run `npm run verify-session-sync -- --session latest` and `npm run build`.
Report the files changed and validation commands you ran."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to sync")
    parser.add_argument("--dnd-dir", default="/home/babu/source/dnd", help="DnD repo root")
    parser.add_argument("--ellara-root", default="/home/babu/source/ellara", help="Ellara repo root")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, help="Optional agent provider for store/view updates")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--skip-copy", action="store_true", help="Do not copy Ellara Session N.md into website assets")
    parser.add_argument("--session-date", help="Date the session was played, e.g. 'October 11, 2026'")
    parser.add_argument("--next-session-date", help="Scheduled date of the next session, if the table set one")
    parser.add_argument("--dry-run", action="store_true", help="Print planned prompt/actions without writing or invoking an agent")
    args = parser.parse_args()

    session = args.session
    dnd_dir = Path(args.dnd_dir).expanduser().resolve()
    ellara_root = Path(args.ellara_root).expanduser().resolve()
    source = ellara_root / "Session Notes" / f"Session {session}.md"
    target = dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md"

    if not source.exists():
        raise FileNotFoundError(f"missing polished Ellara session notes: {source}")

    if not args.skip_copy:
        if args.dry_run:
            print(f"would copy: {source} -> {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            print(f"copied: {source} -> {target}")

    prompt = build_prompt(session, args.session_date, args.next_session_date)
    if not args.provider or args.dry_run:
        print()
        print("Website-sync agent prompt:")
        print(prompt)
        return 0

    output = agent_cli.run_agent(args.provider, prompt, dnd_dir, args.model, write=True)

    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
