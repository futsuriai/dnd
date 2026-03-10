#!/usr/bin/env python3
"""
Generate polished Session N markdown from Raw Session N markdown through an agent CLI.

Supported providers:
- codex
- gemini
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from note_generation_guidance import CANONICAL_CAST_REFERENCE


def build_prompt(session: str, raw_text: str) -> str:
    return f"""Task:
- Convert these raw D&D session notes into polished markdown session notes.
- Match the style of the existing `Session 11.md` through `Session 14.md` files.
- This is the polished campaign-notes layer, not the raw-notes layer.

Required format:
- Start with `# Session {session} — *<title>*`
- Then a `**Locales:**` line
- Then a `**Time:**` line
- Then `---`
- Use numbered markdown sections like `## 1) ...`

Rules:
- Keep chronology accurate.
- Turn rough raw notes into readable narrative prose.
- Preserve only the most important direct quotes.
- Keep key rolls/checks when they matter to the story.
- Do not invent facts, names, dialogue, or outcomes.
- Do not mention transcript mechanics, chunking, or timestamps.
- If the raw notes are uncertain, be modest and avoid false precision.
- Output markdown only. No code fences. No commentary.
- Preserve canonical character genders/pronouns consistently across the whole document.

{CANONICAL_CAST_REFERENCE}

Raw notes:
{raw_text}

Return only the final markdown."""


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            stripped = "\n".join(lines[1:-1]).strip()
    return stripped


def run_codex(prompt: str, workspace_root: Path, model: str | None) -> str:
    codex_bin = shutil.which("codex")
    if not codex_bin:
        raise FileNotFoundError("codex CLI not found in PATH")

    with tempfile.NamedTemporaryFile("r+", encoding="utf-8", delete=False) as tmp:
        output_file = Path(tmp.name)

    cmd = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        str(workspace_root),
        "-s",
        "read-only",
        "-o",
        str(output_file),
    ]
    if model:
        cmd.extend(["-m", model])
    cmd.append(prompt)

    try:
        subprocess.run(cmd, check=True)
        return output_file.read_text(encoding="utf-8").strip()
    finally:
        output_file.unlink(missing_ok=True)


def run_gemini(prompt: str, workspace_root: Path, model: str | None) -> str:
    gemini_bin = shutil.which("gemini")
    if not gemini_bin:
        raise FileNotFoundError("gemini CLI not found in PATH")

    cmd = [
        gemini_bin,
        "--include-directories",
        str(workspace_root),
        "--output-format",
        "text",
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gemini failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Session label/number for the title")
    parser.add_argument("raw_notes_file", help="Path to Raw Session N.md")
    parser.add_argument("output_file", help="Path to Session N.md")
    parser.add_argument("--provider", choices=["codex", "gemini"], required=True, help="Agent CLI to use")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--workspace-root", default="/home/babu/source", help="Workspace root visible to the agent CLI")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned action without invoking the provider")
    args = parser.parse_args()

    raw_notes_file = Path(args.raw_notes_file).expanduser().resolve()
    output_file = Path(args.output_file).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser().resolve()

    if output_file.exists() and not args.force:
        print(f"Session notes output already exists, skipping: {output_file}")
        return 0

    raw_text = raw_notes_file.read_text(encoding="utf-8")
    prompt = build_prompt(args.session, raw_text)

    if args.dry_run:
        print(f"Would run {args.provider} -> {output_file}")
        return 0

    print(f"Running {args.provider} for polished session notes -> {output_file}")
    if args.provider == "codex":
        text = run_codex(prompt, workspace_root, args.model)
    else:
        text = run_gemini(prompt, workspace_root, args.model)

    text = strip_code_fences(text).rstrip() + "\n"
    output_file.write_text(text, encoding="utf-8")
    print(f"Wrote {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
