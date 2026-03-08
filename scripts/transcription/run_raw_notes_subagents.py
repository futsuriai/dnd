#!/usr/bin/env python3
"""
Run per-chunk raw-session-note generation through external agent CLIs.

Supported providers:
- codex
- gemini

The script reads `chunks_manifest.json`, dispatches one agent run per chunk,
writes `chunk_XXX_notes.txt`, and can optionally finalize `Raw Session XX.md`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def log(msg: str) -> None:
    print(msg, flush=True)


def build_prompt(chunk_text: str) -> str:
    return f"""Task:
- Convert the chunk into raw D&D session notes.
- Use only the PRIMARY RANGE for the output.
- Use CONTEXT BEFORE and CONTEXT AFTER only for continuity, pronouns, and scene boundaries.
- Remove out-of-character chatter, player discussion, scheduling, tech talk, and table banter.
- Keep the result in rough raw-note format, not polished campaign recap prose.
- Stay close to transcript order and wording.
- Preserve in-character dialogue as dialogue using `name: "quote"` when a direct quote matters.
- Summarize actions and narration in short informal prose or sentence fragments.
- It is fine if the notes feel draft-like and a little messy.
- Use --- for scene or beat breaks when helpful.
- Use lowercase names for dialogue attribution when you quote someone directly.
- Do not mention timestamps.
- Do not include commentary, headings, code fences, or explanations.
- Do not restate the whole scene if the chunk starts in the middle of it.

Chunk:
{chunk_text}

Return only the final note text."""


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


def finalize(chunk_dir: Path, output_file: Path) -> None:
    script_path = Path(__file__).with_name("generate_raw_notes.py")
    subprocess.run(
        [sys.executable, str(script_path), "concat", str(chunk_dir), str(output_file)],
        check=True,
    )


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def select_chunks(chunks: list[dict], start_chunk: int | None, end_chunk: int | None, limit: int | None) -> list[dict]:
    selected = []
    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        if start_chunk is not None and chunk_id < start_chunk:
            continue
        if end_chunk is not None and chunk_id > end_chunk:
            continue
        selected.append(chunk)
    if limit is not None:
        selected = selected[:limit]
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Path to chunks_manifest.json")
    parser.add_argument("--provider", choices=["codex", "gemini"], required=True, help="Agent CLI to use")
    parser.add_argument("--model", help="Optional model override for the provider")
    parser.add_argument("--workspace-root", default="/home/babu/source", help="Workspace root visible to the agent CLI")
    parser.add_argument("--start-chunk", type=int, help="First chunk id to process")
    parser.add_argument("--end-chunk", type=int, help="Last chunk id to process")
    parser.add_argument("--limit", type=int, help="Maximum number of chunks to process")
    parser.add_argument("--force", action="store_true", help="Overwrite existing chunk note outputs")
    parser.add_argument("--finalize", action="store_true", help="Finalize Raw Session output after processing")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without invoking an agent")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser().resolve()

    manifest = load_manifest(manifest_path)
    chunks = select_chunks(manifest.get("chunks", []), args.start_chunk, args.end_chunk, args.limit)
    chunk_dir = Path(manifest["chunk_dir"])
    raw_session_output = chunk_dir.parent / f"{chunk_dir.name.replace(' Chunks', '')}.md"

    if not chunks:
        raise RuntimeError("No chunks selected")

    log(f"Provider: {args.provider}")
    log(f"Selected chunks: {len(chunks)}")
    log(f"Chunk dir: {chunk_dir}")

    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        input_file = Path(chunk["input_file"])
        output_file = Path(chunk["output_file"])

        if output_file.exists() and not args.force:
            log(f"chunk {chunk_id:03d}: skip existing output")
            continue

        chunk_text = input_file.read_text(encoding="utf-8")
        prompt = build_prompt(chunk_text)
        if args.dry_run:
            log(f"chunk {chunk_id:03d}: would run {args.provider} -> {output_file.name}")
            continue

        log(f"chunk {chunk_id:03d}: running {args.provider}")
        if args.provider == "codex":
            text = run_codex(prompt, workspace_root, args.model)
        else:
            text = run_gemini(prompt, workspace_root, args.model)

        text = strip_code_fences(text)
        output_file.write_text(text.rstrip() + "\n", encoding="utf-8")
        log(f"chunk {chunk_id:03d}: wrote {output_file}")

    if args.finalize and not args.dry_run:
        log(f"finalizing: {raw_session_output}")
        finalize(chunk_dir, raw_session_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
