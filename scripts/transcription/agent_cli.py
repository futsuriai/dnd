"""Shared helpers for running prompts through subscription-backed agent CLIs.

Providers:
- codex: ChatGPT-backed Codex CLI (`codex exec`)
- claude: Claude Code CLI (`claude -p`)
- agy: Antigravity CLI (`agy -p`), Gemini models; also used for audio clips
- gemini: legacy Gemini CLI (its individual tier is no longer supported upstream)

Prompts are passed on stdin (or through a prompt file for agy) so long
transcripts never hit the per-argument ARG_MAX limit.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

PROVIDERS = ("codex", "claude", "agy", "gemini")

DEFAULT_MODELS = {
    "codex": None,
    "claude": "claude-opus-5-5",
    "agy": "gemini-3.8-flash-high",
    "gemini": None,
}

# Tools the Claude CLI may use when an agent is allowed to edit the repo.
CLAUDE_WRITE_TOOLS = [
    "Read",
    "Edit",
    "Write",
    "Glob",
    "Grep",
    "Bash(npm run:*)",
    "Bash(node:*)",
    "Bash(git diff:*)",
    "Bash(git status:*)",
]


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            stripped = "\n".join(lines[1:-1]).strip()
    return stripped


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise FileNotFoundError(f"{binary} CLI not found in PATH")
    return path


def run_codex(prompt: str, workspace: Path, model: str | None, write: bool) -> str:
    codex_bin = _require("codex")
    with tempfile.NamedTemporaryFile("r+", encoding="utf-8", delete=False) as tmp:
        output_file = Path(tmp.name)

    cmd = [
        codex_bin,
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(workspace),
        "-s",
        "workspace-write" if write else "read-only",
        "-o",
        str(output_file),
    ]
    if not write:
        cmd.insert(2, "--ephemeral")
    if model:
        cmd.extend(["-m", model])
    cmd.append("-")

    try:
        # Codex echoes the whole prompt and its progress to stderr; keep it out
        # of pipeline logs unless the run fails.
        result = subprocess.run(cmd, input=prompt, text=True, check=False, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"codex failed with exit code {result.returncode}\n{result.stderr[-3000:]}")
        return output_file.read_text(encoding="utf-8").strip()
    finally:
        output_file.unlink(missing_ok=True)


def run_claude(prompt: str, workspace: Path, model: str | None, write: bool) -> str:
    claude_bin = _require("claude")
    cmd = [
        claude_bin,
        "-p",
        "--output-format",
        "text",
        "--no-session-persistence",
        "--model",
        model or DEFAULT_MODELS["claude"],
    ]
    if write:
        cmd.extend(["--permission-mode", "acceptEdits", "--allowedTools", *CLAUDE_WRITE_TOOLS])
    else:
        cmd.extend(["--tools", ""])

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        cwd=str(workspace),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude failed with exit code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


AGY_INLINE_LIMIT = 60_000  # bytes; longer prompts go through a prompt file


def run_agy(
    prompt: str,
    workspace: Path,
    model: str | None,
    write: bool,
    attachments: list[Path] | None = None,
    timeout: int | None = None,
) -> str:
    """Run Antigravity in print mode.

    Short prompts are passed inline with `@file` references to the attachments,
    so the agent goes straight to the audio instead of first opening a prompt
    file (one fewer tool round trip per call). Long prompts are written to
    prompt.md and referenced, which keeps argv under ARG_MAX.
    """
    agy_bin = _require("agy")
    with tempfile.TemporaryDirectory(prefix="agy-prompt-") as tmp_dir:
        tmp = Path(tmp_dir)
        refs = []
        for attachment in attachments or []:
            target = tmp / attachment.name
            shutil.copy2(attachment, target)
            refs.append(f"@{target.name}")

        rules = "Use your file viewing tool only; do not run shell commands."
        attached = (" Attached files: " + " ".join(refs) + ".") if refs else ""
        if len(prompt.encode("utf-8")) <= AGY_INLINE_LIMIT:
            instruction = f"{rules}{attached}\n\n{prompt}"
        else:
            (tmp / "prompt.md").write_text(prompt, encoding="utf-8")
            instruction = f"Follow the instructions in @prompt.md exactly. {rules}{attached}"

        cmd = [agy_bin, "-p", instruction, "--model", model or DEFAULT_MODELS["agy"], "--add-dir", str(tmp)]
        if write:
            cmd.extend(["--add-dir", str(workspace), "--mode", "accept-edits"])
        result = subprocess.run(
            cmd,
            text=True,
            cwd=str(tmp),
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"agy failed with exit code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def run_gemini(prompt: str, workspace: Path, model: str | None, write: bool) -> str:
    gemini_bin = _require("gemini")
    cmd = [gemini_bin, "--include-directories", str(workspace), "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])
    result = subprocess.run(cmd, input=prompt, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gemini failed with exit code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def run_agent(
    provider: str,
    prompt: str,
    workspace: Path,
    model: str | None = None,
    write: bool = False,
) -> str:
    """Run a prompt and return the final text response."""
    workspace = Path(workspace)
    if provider == "codex":
        return run_codex(prompt, workspace, model, write)
    if provider == "claude":
        return run_claude(prompt, workspace, model, write)
    if provider == "agy":
        return run_agy(prompt, workspace, model, write)
    if provider == "gemini":
        return run_gemini(prompt, workspace, model, write)
    raise ValueError(f"unknown provider: {provider}")
