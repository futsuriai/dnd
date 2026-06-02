#!/usr/bin/env python3
"""Run annotation-first OOC cleanup chunks through an external agent CLI."""

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


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            stripped = "\n".join(lines[1:-1]).strip()
    return stripped.strip()


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

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"gemini failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def select_chunks(chunks: list[dict], start_chunk: int | None, end_chunk: int | None, limit: int | None) -> list[dict]:
    selected = []
    for index, chunk in enumerate(chunks):
        chunk_number = int(str(chunk["chunk_id"]).split("_")[-1])
        if start_chunk is not None and chunk_number < start_chunk:
            continue
        if end_chunk is not None and chunk_number > end_chunk:
            continue
        selected.append((index, chunk))
    if limit is not None:
        selected = selected[:limit]
    return [chunk for _, chunk in selected]


def prompt_for_chunk(chunk_file: Path) -> str:
    filter_script = Path(__file__).with_name("filter_ooc.py")
    result = subprocess.run(
        [sys.executable, str(filter_script), "prompt", "--chunk-file", str(chunk_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def default_apply_outputs(source: Path) -> tuple[Path, Path, Path, Path]:
    stem = source.stem
    return (
        source.with_name(f"{stem} - Annotation Cleaned Candidate.txt"),
        source.with_name(f"{stem} - Annotation Cleanup Report.md"),
        source.with_name(f"{stem} - Annotation Ambiguous Review.md"),
        source.with_name(f"{stem} - Annotation Cleaned Candidate.diff"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="annotation_manifest.json from filter_ooc.py prepare")
    parser.add_argument("--provider", choices=["codex", "gemini"], required=True, help="Agent CLI to use")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--workspace-root", default="/home/babu/source", help="Workspace root visible to the agent CLI")
    parser.add_argument("--start-chunk", type=int, help="First numeric chunk id to process")
    parser.add_argument("--end-chunk", type=int, help="Last numeric chunk id to process")
    parser.add_argument("--limit", type=int, help="Maximum number of chunks to process")
    parser.add_argument("--force", action="store_true", help="Overwrite existing annotation JSONL")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without invoking an agent")
    parser.add_argument("--apply", action="store_true", help="Run filter_ooc.py apply after all selected chunks are annotated")
    parser.add_argument("--cleaned-output", help="Output cleaned transcript path for --apply")
    parser.add_argument("--report-output", help="Output markdown cleanup report path for --apply")
    parser.add_argument("--ambiguous-output", help="Output markdown ambiguous review path for --apply")
    parser.add_argument("--diff-output", help="Output unified diff path for --apply")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing annotations during --apply")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser().resolve()
    manifest = load_manifest(manifest_path)
    annotation_dir = manifest_path.parent
    selected = select_chunks(manifest.get("chunks", []), args.start_chunk, args.end_chunk, args.limit)
    if not selected:
        raise RuntimeError("No annotation chunks selected")

    log(f"Provider: {args.provider}")
    log(f"Selected chunks: {len(selected)}")
    log(f"Annotation dir: {annotation_dir}")

    for chunk in selected:
        chunk_file = annotation_dir / chunk["chunk_file"]
        output_file = annotation_dir / chunk["annotation_file"]
        if output_file.exists() and not args.force:
            log(f"{chunk['chunk_id']}: skip existing annotation")
            continue

        if args.dry_run:
            log(f"{chunk['chunk_id']}: would run {args.provider} -> {output_file.name}")
            continue

        prompt = prompt_for_chunk(chunk_file)
        log(f"{chunk['chunk_id']}: running {args.provider}")
        if args.provider == "codex":
            text = run_codex(prompt, workspace_root, args.model)
        else:
            text = run_gemini(prompt, workspace_root, args.model)

        output_file.write_text(strip_code_fences(text).rstrip() + "\n", encoding="utf-8")
        log(f"{chunk['chunk_id']}: wrote {output_file}")

    if args.apply and not args.dry_run:
        source = Path(manifest["source"]).expanduser().resolve()
        default_cleaned, default_report, default_ambiguous, default_diff = default_apply_outputs(source)
        cleaned = Path(args.cleaned_output).expanduser().resolve() if args.cleaned_output else default_cleaned
        report = Path(args.report_output).expanduser().resolve() if args.report_output else default_report
        ambiguous = Path(args.ambiguous_output).expanduser().resolve() if args.ambiguous_output else default_ambiguous
        diff = Path(args.diff_output).expanduser().resolve() if args.diff_output else default_diff
        filter_script = Path(__file__).with_name("filter_ooc.py")
        apply_cmd = [
            sys.executable,
            str(filter_script),
            "apply",
            str(manifest_path),
            str(annotation_dir),
            str(cleaned),
            str(report),
            str(ambiguous),
            str(diff),
        ]
        if args.allow_missing:
            apply_cmd.append("--allow-missing")
        log("Applying annotations")
        subprocess.run(apply_cmd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
