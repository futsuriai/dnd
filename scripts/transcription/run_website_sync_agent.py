#!/usr/bin/env python3
"""Sync polished session notes into the website and optionally run an agent update pass."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import pipeline_paths  # noqa: E402


def sync_session_markdown(
    source: Path,
    target: Path,
    *,
    prefer: str | None = None,
    skip_copy: bool = False,
    dry_run: bool = False,
) -> str:
    """Safely sync Ellara `Session N.md` <-> DnD `session-N.md` with bidirectional parity protection."""
    if skip_copy:
        if not target.is_file():
            raise FileNotFoundError(f"--skip-copy set but target session markdown is missing: {target}")
        return "skipped"

    source_exists = source.is_file()
    target_exists = target.is_file()

    if not source_exists:
        if target_exists and prefer == "dnd":
            print(f"Keeping existing website session markdown (--prefer dnd): {target}")
            return "kept_dnd"
        raise FileNotFoundError(f"missing polished Ellara session notes: {source}")

    if target_exists:
        src_text = source.read_text(encoding="utf-8")
        tgt_text = target.read_text(encoding="utf-8")
        if src_text == tgt_text:
            print(f"in sync: {source} == {target}")
            return "in_sync"
        if prefer == "dnd":
            print(f"Keeping newer/existing website session markdown (--prefer dnd): {target}")
            return "kept_dnd"
        if prefer != "ellara":
            raise RuntimeError(
                f"Parity mismatch between Ellara and DnD session notes:\n"
                f"  ellara: {source}\n"
                f"  dnd:    {target}\n"
                f"Re-run with --prefer ellara to overwrite DnD, --prefer dnd to keep DnD, or --skip-copy."
            )

    if dry_run:
        print(f"would copy: {source} -> {target}")
        return "would_copy"

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"copied: {source} -> {target}")
    return "copied"


def build_prompt(session: int, session_date: str | None = None, next_session_date: str | None = None) -> str:
    played = (
        f"Session {session} was played on {session_date}: set its `date` to exactly '{session_date}'."
        if session_date
        else f"Keep session {session}'s existing `date` unless it is clearly a placeholder."
    )
    upcoming = (
        f"The table scheduled the next session for {next_session_date}: give session {session + 1} the `date` '{next_session_date}'."
        if next_session_date
        else f"No next-session date was scheduled: give session {session + 1} the `date` 'TBD'."
    )
    return f"""MODE: autofix (edit the repository files directly in place; do NOT output a unified diff instead of editing).

Task:
Update the DnD website repo for completed Session {session}.

Use `.copilot/prompts/process-latest-session.md` as the governing instructions.
Use `src/assets/sessions/session-{session}.md` as the primary source summary.

Required work:
- Update `src/store/sessions.js`:
  - Mark session {session} complete (`upcoming: false`), set `summaryFile: 'session-{session}.md'`, update `subtitle`, `location`, `description`, and `highlights` (5-8 concise entries).
  - Populate `homeRecap` (string), `nextSteps` (array of concise next-step strings or string), and `storyBeat` (narrative chronicle paragraph when Session {session} materially advances the campaign arc) directly on the `session-{session}` object in `src/store/sessions.js`.
  - Do NOT manually edit `src/views/HomeView.vue` or `src/views/StorySoFarView.vue` — both views are data-driven from `sessions.js`!
  - Create or verify `session-{session + 1}` at the top of `sessions` as the single `upcoming: true` stub with a non-placeholder description and `highlights: []`.
- Review `src/store/locations.js`, `src/store/npcs.js`, and `src/store/lore.js`:
  - Add only significant `history` entries (`{{ session: {session}, note: '...' }}`), connections (ALWAYS use `reason:`, NEVER `relationship:`), description refinements, or genuinely new entities grounded in the polished summary.
  - Do NOT add `updatedInSessions`; `history` is the single source of truth.
  - Do NOT treat party members (`Nyx`, `Ellara`, `Ysidor`, `Berridin`, `Witty` / `Whitaker "Witty" Whitman VI`, or former PC `Tsi'nyra`) as NPCs.
- Run `npm run sync-check` (which runs `npm run generate-list`, `npm run verify-session-sync -- --session latest`, and `npm run build`).
- Preserve canonical spellings from `ENTITY_LIST.md`, `src/store/lore.js`, and `scripts/transcription/name_corrections.json`.
- Use `Nites` exactly, pronounced knee-tes. Do not write `Nytes` or `Nýtes`.
- Preserve capitalization for Ellara, Nyx, Ysidor, Berridin, and Witty in public copy.
- Preserve dice/check attribution from `src/assets/sessions/session-{session}.md`; do not reassign a natural 20, skill check, or lore clue to another character while summarizing into stores.
- If the polished summary is ambiguous about who rolled, omit the roller from store copy instead of guessing.
- Do not touch unrelated files or generated intermediate artifacts.

Dates (authoritative, overriding "today's date" in the governing instructions):
- {played}
- {upcoming}

Keep the update proportionate and in the existing voice:
- Touch only entities whose state or understanding genuinely changed this session; for a normal session that
  is usually 3-8 entities. Look at how sessions 19, 20, and 21 were recorded and match that scale.
- Entity `description` fields describe what the entity is. Do not put the party's current plans, pending tasks,
  or undecided choices into descriptions; record session events as one-sentence `history` notes instead.
- History notes and highlights state what happened plainly, one or two sentences each (highlights: 5-8, under
  ~220 characters). Do not stack caveats such as "without laboratory testing", "remains unconfirmed", or
  "has not yet occurred"; mention an open question once, where it matters.
- Do not rewrite existing descriptions or connection reasons. If the session adds or contradicts a detail, add
  it (e.g. a new history note) rather than replacing earlier canon.

After editing, run `npm run sync-check`.
Report the files changed and validation commands you ran."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to sync")
    parser.add_argument("--dnd-dir", default=str(pipeline_paths.resolve_dnd_dir()), help="DnD repo root")
    parser.add_argument("--ellara-root", default=str(pipeline_paths.resolve_ellara_dir()), help="Ellara repo root")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, help="Optional agent provider for store updates")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--skip-copy", action="store_true", help="Do not copy Ellara Session N.md into website assets")
    parser.add_argument("--prefer", choices=("ellara", "dnd"), help="Resolve parity mismatch if Session N.md and session-N.md differ")
    parser.add_argument("--skip-sync-check", action="store_true", help="Skip running `npm run sync-check` after agent edits")
    parser.add_argument("--session-date", help="Date the session was played, e.g. 'October 11, 2026'")
    parser.add_argument("--next-session-date", help="Scheduled date of the next session, if the table set one")
    parser.add_argument("--dry-run", action="store_true", help="Print planned prompt/actions without writing or invoking an agent")
    args = parser.parse_args(argv)

    session = args.session
    dnd_dir = pipeline_paths.resolve_dnd_dir(args.dnd_dir)
    ellara_root = pipeline_paths.resolve_ellara_dir(args.ellara_root)
    source = ellara_root / "Session Notes" / f"Session {session}.md"
    target = dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md"

    sync_session_markdown(
        source,
        target,
        prefer=args.prefer,
        skip_copy=args.skip_copy,
        dry_run=args.dry_run,
    )

    prompt = build_prompt(session, args.session_date, args.next_session_date)
    if not args.provider or args.dry_run:
        print()
        print("Website-sync agent prompt:")
        print(prompt)
        return 0

    output = pipeline_paths.call_agent(
        agent_cli,
        prompt=prompt,
        provider=args.provider,
        model=args.model,
        workspace=dnd_dir,
        write=True,
        timeout=600,
    )

    if output:
        print(output)

    if not args.skip_sync_check:
        res = subprocess.run(
            ["npm", "run", "sync-check"],
            cwd=str(dnd_dir),
            env=pipeline_paths.no_bytecode_env(),
            check=False,
        )
        if res.returncode != 0:
            print(f"ERROR: `npm run sync-check` failed with exit code {res.returncode}", file=sys.stderr)
            return res.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
