#!/usr/bin/env python3
"""
Reconcile chunk-extracted raw notes into a scene-level raw session candidate.

This pass is required between chunk extraction and promotion to Raw Session N.md.
The chunk pass preserves local transcript fidelity; this pass restores session
shape by merging duplicate overlaps, compressing repeated planning loops, and
keeping the IC dialogue/thoughts that matter.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from note_generation_guidance import CANONICAL_CAST_REFERENCE


def build_prompt(raw_text: str, transcript_text: str | None) -> str:
    transcript_section = ""
    if transcript_text:
        transcript_section = f"""
Cleaned transcript for spot-checking quotes and uncertain facts:
```
{transcript_text}
```
"""

    return f"""Task:
- Reconcile chunk-extracted D&D raw notes into a scene-level raw session-note candidate.
- The input was produced from many independent transcript chunks, so it may repeat beats, over-explain local process, preserve too much table chatter, or miss long-range scene shape.
- Do not write polished website prose. Keep the output as rough, human-editable raw notes in the style of Raw Session 7/8.

Required behavior:
- Preserve clear in-character dialogue as `name: "quote"` with the character's actual wording where possible.
- Preserve stated character thoughts/emotional beats, preferably in the character's own words when clear.
- Preserve GM revelations, scene descriptions, rulings, checks, outcomes, resource changes, discoveries, and open hooks.
- Merge duplicated overlap and repeated chunk summaries.
- Compress repeated planning loops into final options, choices, and outcomes.
- Keep player intent/tactical discussion when it affects character action or consequences.
- Remove low-impact OOC logistics, rules fumbling that has no outcome, and table jokes that do not affect character/story.
- Keep uncertainty when uncertainty affected a choice. If a fact remains risky, include a short `review:` line near that beat.
- Preserve chronology and use `---` for scene/beat breaks.
- Do not include headings, timestamps, chunk IDs, transcript mechanics, code fences, or commentary about this task.
- Do not invent facts or smooth away meaningful wording.

{CANONICAL_CAST_REFERENCE}
{transcript_section}
Chunk-extracted raw notes:
```
{raw_text}
```

Return only the reconciled raw session notes."""


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
    cmd.append("-")

    try:
        subprocess.run(cmd, input=prompt, text=True, check=True)
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
    parser.add_argument("input_file", help="Chunk-extracted Raw Session N Candidate.md")
    parser.add_argument("output_file", help="Reconciled raw-note candidate path")
    parser.add_argument("--provider", choices=["codex", "gemini"], required=True, help="Agent CLI to use")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--workspace-root", default="/home/babu/source", help="Workspace root visible to the agent CLI")
    parser.add_argument("--transcript", help="Optional cleaned transcript for spot-checking quotes/facts")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    parser.add_argument("--dry-run", action="store_true", help="Print planned action without invoking the provider")
    args = parser.parse_args()

    input_file = Path(args.input_file).expanduser().resolve()
    output_file = Path(args.output_file).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser().resolve()
    transcript_file = Path(args.transcript).expanduser().resolve() if args.transcript else None

    if output_file.exists() and not args.force:
        print(f"Reconciled raw-note output already exists, skipping: {output_file}")
        return 0

    raw_text = input_file.read_text(encoding="utf-8")
    transcript_text = transcript_file.read_text(encoding="utf-8") if transcript_file else None
    prompt = build_prompt(raw_text, transcript_text)

    if args.dry_run:
        print(f"Would run {args.provider} -> {output_file}")
        return 0

    print(f"Running {args.provider} for raw-note reconciliation -> {output_file}")
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
