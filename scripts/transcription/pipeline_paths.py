#!/usr/bin/env python3
"""Centralized path, Python venv, and subprocess environment helpers for the session pipeline."""

from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path
from typing import Any

TRANSCRIPTION_DIR: Path = Path(__file__).resolve().parent
DND_DIR: Path = TRANSCRIPTION_DIR.parent.parent


def resolve_dnd_dir(override: str | Path | None = None) -> Path:
    """Resolve the DnD repository root: override -> $DND_REPO_ROOT -> DND_DIR."""
    if override is not None and str(override).strip():
        return Path(override).expanduser().resolve()
    env_val = os.environ.get("DND_REPO_ROOT", "").strip()
    if env_val:
        return Path(env_val).expanduser().resolve()
    return DND_DIR


def resolve_ellara_dir(override: str | Path | None = None) -> Path:
    """Resolve the Ellara vault root: override -> $ELLARA_ROOT -> DND_DIR.parent / 'ellara'."""
    if override is not None and str(override).strip():
        return Path(override).expanduser().resolve()
    env_val = os.environ.get("ELLARA_ROOT", "").strip()
    if env_val:
        return Path(env_val).expanduser().resolve()
    return (DND_DIR.parent / "ellara").resolve()


def resolve_python(override: str | Path | None = None) -> Path:
    """Resolve the Python interpreter for transcription/pipeline child scripts."""
    if override is not None and str(override).strip():
        return Path(override).expanduser().resolve()
    candidates = [
        DND_DIR / ".venv-transcription" / "bin" / "python3",
        Path("~/.gemini/tmp/transcribe_env/bin/python3").expanduser(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


ELLARA_DIR: Path = resolve_ellara_dir()
VENV_PYTHON: Path = resolve_python()


def no_bytecode_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return a copy of os.environ with PYTHONDONTWRITEBYTECODE=1."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        env.update(extra)
    return env


def call_agent(
    agent_module: Any,
    *,
    prompt: str,
    provider: str = "agy",
    model: str | None = None,
    workspace: Path | None = None,
    write: bool = False,
    attachments: list[Path] | None = None,
    json_schema: dict | Path | None = None,
    effort: str | None = None,
    timeout: int = 300,
    retries: int = 1,
    extra_dirs: list[Path] | None = None,
    extra_allowed_tools: list[str] | None = None,
    disable_slash_commands: bool = True,
) -> str:
    """Invoke agent_cli.run_agent safely across both legacy and upgraded signatures."""
    fn = agent_module.run_agent
    all_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "provider": provider,
        "model": model,
        "workspace": workspace,
        "write": write,
        "attachments": attachments,
        "json_schema": json_schema,
        "effort": effort,
        "timeout": timeout,
        "retries": retries,
        "extra_dirs": extra_dirs,
        "extra_allowed_tools": extra_allowed_tools,
        "disable_slash_commands": disable_slash_commands,
    }
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return fn(**all_kwargs)

    has_var_kw = any(
        param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values()
    )
    if has_var_kw:
        return fn(**all_kwargs)

    accepted = {k: v for k, v in all_kwargs.items() if k in sig.parameters}
    return fn(**accepted)
