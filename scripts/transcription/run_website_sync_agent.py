#!/usr/bin/env python3
"""Sync polished session notes into the website and optionally run an agent update pass."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def build_prompt(session: int) -> str:
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

After editing, run `npm run verify-session-sync -- --session latest` and `npm run build`.
Report the files changed and validation commands you ran."""


def run_codex(prompt: str, dnd_dir: Path, model: str | None) -> str:
    codex_bin = shutil.which("codex")
    if not codex_bin:
        raise FileNotFoundError("codex CLI not found in PATH")

    with tempfile.NamedTemporaryFile("r+", encoding="utf-8", delete=False) as tmp:
        output_file = Path(tmp.name)

    cmd = [
        codex_bin,
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(dnd_dir),
        "-s",
        "workspace-write",
        "-o",
        str(output_file),
    ]
    if model:
        cmd.extend(["-m", model])
    cmd.append("-")

    try:
        subprocess.run(cmd, input=prompt, text=True, check=True)
        return output_file.read_text(encoding="utf-8").strip()
    finally:
        output_file.unlink(missing_ok=True)


def run_gemini(prompt: str, dnd_dir: Path, model: str | None) -> str:
    gemini_bin = shutil.which("gemini")
    if not gemini_bin:
        raise FileNotFoundError("gemini CLI not found in PATH")

    cmd = [
        gemini_bin,
        "--include-directories",
        str(dnd_dir),
        "--output-format",
        "text",
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    result = subprocess.run(cmd, cwd=str(dnd_dir), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"gemini failed with exit code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to sync")
    parser.add_argument("--dnd-dir", default="/home/babu/source/dnd", help="DnD repo root")
    parser.add_argument("--ellara-root", default="/home/babu/source/ellara", help="Ellara repo root")
    parser.add_argument("--provider", choices=["codex", "gemini"], help="Optional agent provider for store/view updates")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--skip-copy", action="store_true", help="Do not copy Ellara Session N.md into website assets")
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

    prompt = build_prompt(session)
    if not args.provider or args.dry_run:
        print()
        print("Website-sync agent prompt:")
        print(prompt)
        return 0

    if args.provider == "codex":
        output = run_codex(prompt, dnd_dir=dnd_dir, model=args.model)
    else:
        output = run_gemini(prompt, dnd_dir=dnd_dir, model=args.model)

    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
