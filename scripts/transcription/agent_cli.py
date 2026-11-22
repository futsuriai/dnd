"""Shared helpers for running prompts through subscription-backed agent CLIs.

Providers:
- codex: ChatGPT-backed Codex CLI (`codex exec`)
- claude: Claude Code CLI (`claude -p`)
- agy: Antigravity CLI (`agy -p`), Gemini 4 Neon models; also used for audio clips
- gemini: Gemini CLI (`gemini -p`)

Prompts are passed on stdin (or through a prompt file for agy) so long
transcripts never hit the per-argument ARG_MAX limit.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

PROVIDERS = ("codex", "claude", "agy", "gemini")

_BASE_DEFAULT_MODELS = {
    "codex": "gpt-5.4",
    "claude": "claude-opus-5-5",
    "agy": "gemini-4-neon-medium",
    "gemini": "gemini-2.5-pro",
}

_MODEL_ENV_VARS = {
    "codex": "CODEX_MODEL",
    "claude": "CLAUDE_MODEL",
    "agy": "AGY_MODEL",
    "gemini": "GEMINI_MODEL",
}

DEFAULT_MODELS = {
    provider: os.environ.get(_MODEL_ENV_VARS[provider]) or base_model
    for provider, base_model in _BASE_DEFAULT_MODELS.items()
}

AGY_TIERS = {
    "fast": "gemini-4-neon-low",
    "default": "gemini-4-neon-medium",
    "strong": "gemini-4-neon-high",
    "max": "gemini-4-neon-xhigh",
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
    "Bash(python3 -B:*)",
    "Bash(git diff:*)",
    "Bash(git status:*)",
]

AGY_INLINE_LIMIT = 60_000  # bytes; longer prompts go through a prompt file

_FENCE_BLOCK_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_CLI_ENVELOPE_META_KEYS = {
    "type",
    "is_error",
    "session_id",
    "conversation_id",
    "cost_usd",
    "total_cost_usd",
    "duration_ms",
    "duration_api_ms",
    "num_turns",
    "usage",
    "stats",
    "model",
    "status",
    "error",
    "metadata",
    "request_id",
}


def _subprocess_env() -> dict[str, str]:
    if _pipeline_paths is not None:
        return _pipeline_paths.no_bytecode_env()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def resolve_model(provider: str, model: str | None = None) -> str:
    """Resolve explicit model, tier alias (for agy), env override, or default."""
    if provider not in _BASE_DEFAULT_MODELS:
        raise ValueError(f"unknown provider: {provider}")
    if model:
        if provider == "agy" and model in AGY_TIERS:
            return AGY_TIERS[model]
        return model
    env_override = os.environ.get(_MODEL_ENV_VARS[provider])
    if env_override:
        return env_override
    return DEFAULT_MODELS.get(provider) or _BASE_DEFAULT_MODELS[provider]


def strip_code_fences(text: str) -> str:
    """Strip outer markdown code fences, including brief preamble/postscript fluff."""
    stripped = text.strip()
    if not stripped:
        return ""

    # Exact outer fence
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[0].lstrip().startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()

    # Single fenced block wrapped by short conversational preamble/postscript
    matches = list(_FENCE_BLOCK_RE.finditer(stripped))
    if len(matches) == 1:
        match = matches[0]
        preamble = stripped[: match.start()].strip()
        postscript = stripped[match.end() :].strip()
        preamble_lines = [line for line in preamble.splitlines() if line.strip()]
        postscript_lines = [line for line in postscript.splitlines() if line.strip()]
        has_heading = any(
            line.lstrip().startswith("#") for line in preamble_lines + postscript_lines
        )
        if not has_heading and len(preamble_lines) <= 3 and len(postscript_lines) <= 3:
            return match.group(1).strip()

    return stripped


def extract_json(text: str) -> Any:
    """Parse JSON from a model response, tolerating code fences and surrounding prose."""
    cleaned = strip_code_fences(text)
    if not cleaned:
        raise ValueError("empty response")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    obj_start, obj_end = cleaned.find("{"), cleaned.rfind("}")
    arr_start, arr_end = cleaned.find("["), cleaned.rfind("]")
    candidates: list[tuple[int, int]] = []
    if obj_start != -1 and obj_end > obj_start:
        candidates.append((obj_start, obj_end + 1))
    if arr_start != -1 and arr_end > arr_start:
        candidates.append((arr_start, arr_end + 1))
    candidates.sort(key=lambda span: span[0])

    for start, end in candidates:
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError:
            continue

    raise ValueError(f"could not parse JSON from response: {cleaned[:200]}")


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise FileNotFoundError(f"{binary} CLI not found in PATH")
    return path


def _dedupe_paths(paths: list[Path | None]) -> list[Path]:
    seen: set[str] = set()
    ordered: list[Path] = []
    for item in paths:
        if item is None:
            continue
        resolved = Path(item).expanduser().resolve()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            ordered.append(resolved)
    return ordered


def _prepare_json_schema(
    json_schema: dict | Path | str | None, tmp_dir: Path
) -> tuple[str | None, Path | None]:
    if json_schema is None:
        return None, None
    if isinstance(json_schema, Path):
        schema_path = json_schema.expanduser().resolve()
        schema_str = json.dumps(json.loads(schema_path.read_text(encoding="utf-8")), separators=(",", ":"))
        return schema_str, schema_path
    if isinstance(json_schema, str):
        candidate = Path(json_schema).expanduser()
        if candidate.exists() and candidate.is_file():
            schema_path = candidate.resolve()
            schema_str = json.dumps(json.loads(schema_path.read_text(encoding="utf-8")), separators=(",", ":"))
            return schema_str, schema_path
        parsed = json.loads(json_schema)
        schema_str = json.dumps(parsed, separators=(",", ":"))
        schema_path = tmp_dir / "schema.json"
        schema_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        return schema_str, schema_path
    if isinstance(json_schema, dict):
        schema_str = json.dumps(json_schema, separators=(",", ":"))
        schema_path = tmp_dir / "schema.json"
        schema_path.write_text(json.dumps(json_schema, indent=2) + "\n", encoding="utf-8")
        return schema_str, schema_path
    raise TypeError(f"unsupported json_schema type: {type(json_schema).__name__}")


def _is_non_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, (FileNotFoundError, ValueError, TypeError)):
        return True
    msg = str(exc).lower()
    non_retryable_markers = (
        "unknown flag",
        "unrecognized option",
        "invalid option",
        "unknown option",
        "invalid model",
        "flag provided but not defined",
    )
    return any(marker in msg for marker in non_retryable_markers)


def _run_with_retries(fn, retries: int = 1, base_delay: float = 2.0) -> str:
    attempts = 1 + max(0, int(retries))
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt + 1 >= attempts or _is_non_retryable_error(exc):
                raise
            delay = min(base_delay * (2**attempt), 15.0)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def _unpack_agy_json_output(raw: str) -> str:
    """Extract final text or structured JSON payload from `agy --output-format json`."""
    stripped = raw.strip()
    if not stripped:
        return ""

    parsed: Any = None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        # Some CLI versions print log lines before the final JSON object.
        for line in reversed(stripped.splitlines()):
            candidate = line.strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    parsed = json.loads(candidate)
                    break
                except json.JSONDecodeError:
                    continue
    if parsed is None:
        return stripped

    if not isinstance(parsed, dict):
        return json.dumps(parsed, ensure_ascii=False)

    if parsed.get("is_error"):
        detail = parsed.get("error") or parsed.get("result") or parsed.get("message") or stripped[:400]
        raise RuntimeError(f"agy returned error result: {detail}")

    if parsed.get("structured_output") is not None:
        val = parsed["structured_output"]
        return val.strip() if isinstance(val, str) else json.dumps(val, ensure_ascii=False)

    keys = set(parsed.keys())
    has_envelope_meta = bool(keys & _CLI_ENVELOPE_META_KEYS)
    for field in ("result", "response", "text", "output"):
        if field in parsed and parsed[field] is not None and (has_envelope_meta or keys == {field}):
            val = parsed[field]
            return val.strip() if isinstance(val, str) else json.dumps(val, ensure_ascii=False)

    if "message" in parsed and isinstance(parsed["message"], dict) and has_envelope_meta:
        content = parsed["message"].get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and isinstance(item.get("text"), str)
            ]
            if parts:
                return "\n".join(parts).strip()

    # The JSON object itself is the structured schema response.
    return json.dumps(parsed, ensure_ascii=False)


def run_codex(
    prompt: str,
    workspace: Path | None,
    model: str | None = None,
    write: bool = False,
    *,
    json_schema: dict | Path | str | None = None,
    timeout: int | None = 300,
    retries: int = 1,
    extra_dirs: list[Path] | None = None,
) -> str:
    codex_bin = _require("codex")
    resolved_workspace = Path(workspace).expanduser().resolve() if workspace else Path.cwd()
    resolved_model = resolve_model("codex", model)

    def _once() -> str:
        with tempfile.TemporaryDirectory(prefix="codex-exec-") as tmp_dir:
            tmp = Path(tmp_dir)
            output_file = tmp / "last_message.txt"
            _, schema_path = _prepare_json_schema(json_schema, tmp)

            cmd = [
                codex_bin,
                "exec",
                "--skip-git-repo-check",
                "-C",
                str(resolved_workspace),
                "-s",
                "workspace-write" if write else "read-only",
                "-o",
                str(output_file),
            ]
            if not write:
                cmd.insert(2, "--ephemeral")
            if resolved_model:
                cmd.extend(["-m", resolved_model])
            for extra in _dedupe_paths(list(extra_dirs or [])):
                if extra != resolved_workspace:
                    cmd.extend(["--add-dir", str(extra)])
            if schema_path is not None:
                cmd.extend(["--output-schema", str(schema_path)])
            cmd.append("-")

            # Codex echoes the whole prompt and its progress to stderr; keep it out
            # of pipeline logs unless the run fails.
            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                check=False,
                capture_output=True,
                timeout=timeout,
                env=_subprocess_env(),
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"codex failed with exit code {result.returncode}\n{result.stderr[-3000:]}"
                )
            if output_file.exists():
                return output_file.read_text(encoding="utf-8").strip()
            return result.stdout.strip()

    return _run_with_retries(_once, retries=retries)


def run_claude(
    prompt: str,
    workspace: Path | None,
    model: str | None = None,
    write: bool = False,
    *,
    json_schema: dict | Path | str | None = None,
    effort: str | None = None,
    timeout: int | None = 300,
    retries: int = 1,
    extra_dirs: list[Path] | None = None,
    extra_allowed_tools: list[str] | None = None,
    disable_slash_commands: bool = True,
) -> str:
    claude_bin = _require("claude")
    resolved_workspace = Path(workspace).expanduser().resolve() if workspace else Path.cwd()
    resolved_model = resolve_model("claude", model)

    def _once() -> str:
        with tempfile.TemporaryDirectory(prefix="claude-exec-") as tmp_dir:
            tmp = Path(tmp_dir)
            schema_str, _ = _prepare_json_schema(json_schema, tmp)

            cmd = [
                claude_bin,
                "-p",
                "--output-format",
                "text",
                "--no-session-persistence",
                "--model",
                resolved_model,
            ]
            if disable_slash_commands:
                cmd.append("--disable-slash-commands")
            if effort:
                cmd.extend(["--effort", effort])
            if schema_str is not None:
                cmd.extend(["--json-schema", schema_str])
            for extra in _dedupe_paths(list(extra_dirs or [])):
                if extra != resolved_workspace:
                    cmd.extend(["--add-dir", str(extra)])
            if write:
                tools = list(dict.fromkeys([*CLAUDE_WRITE_TOOLS, *(extra_allowed_tools or [])]))
                cmd.extend(["--permission-mode", "acceptEdits", "--allowedTools", *tools])
            else:
                cmd.extend(["--tools", ""])

            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                cwd=str(resolved_workspace),
                capture_output=True,
                check=False,
                timeout=timeout,
                env=_subprocess_env(),
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"claude failed with exit code {result.returncode}\n"
                    f"stdout:\n{result.stdout[-2000:]}\nstderr:\n{result.stderr[-2000:]}"
                )
            return result.stdout.strip()

    return _run_with_retries(_once, retries=retries)


def run_agy(
    prompt: str,
    workspace: Path | None,
    model: str | None = None,
    write: bool = False,
    attachments: list[Path] | None = None,
    timeout: int | None = 300,
    *,
    json_schema: dict | Path | str | None = None,
    effort: str | None = None,
    retries: int = 1,
    extra_dirs: list[Path] | None = None,
    disable_slash_commands: bool = True,
) -> str:
    """Run Antigravity (`agy -p`) in print mode.

    When `write=False`, short prompts run inline with `@file` attachments copied
    into an isolated temp dir. When `write=True`, `cwd` is set to `workspace`
    with `--mode accept-edits` and without read-only shell restrictions.
    """
    agy_bin = _require("agy")
    resolved_workspace = Path(workspace).expanduser().resolve() if workspace else None
    resolved_model = resolve_model("agy", model)
    resolved_attachments = [Path(a).expanduser().resolve() for a in (attachments or [])]

    def _once() -> str:
        with tempfile.TemporaryDirectory(prefix="agy-prompt-") as tmp_dir:
            tmp = Path(tmp_dir).resolve()
            refs: list[str] = []
            used_tmp = False

            for attachment in resolved_attachments:
                if write:
                    if resolved_workspace is not None:
                        try:
                            rel = attachment.relative_to(resolved_workspace)
                            refs.append(f"@{rel}")
                            continue
                        except ValueError:
                            pass
                    refs.append(f"@{attachment}")
                else:
                    target = tmp / attachment.name
                    if target.exists():
                        target = tmp / f"{len(refs)}_{attachment.name}"
                    shutil.copy2(attachment, target)
                    refs.append(f"@{target.name}")
                    used_tmp = True

            attached = (" Attached files: " + " ".join(refs) + ".") if refs else ""
            prefix_parts: list[str] = []
            if not write and refs:
                prefix_parts.append("Use your file viewing tool only; do not run shell commands.")
            if attached:
                prefix_parts.append(attached.strip())
            prefix = " ".join(prefix_parts)

            if len(prompt.encode("utf-8")) <= AGY_INLINE_LIMIT:
                instruction = f"{prefix}\n\n{prompt}" if prefix else prompt
            else:
                prompt_file = tmp / "prompt.md"
                prompt_file.write_text(prompt, encoding="utf-8")
                used_tmp = True
                prompt_ref = f"@{prompt_file}" if write else "@prompt.md"
                instruction = f"Follow the instructions in {prompt_ref} exactly."
                if prefix:
                    instruction = f"{instruction} {prefix}"

            _, schema_path = _prepare_json_schema(json_schema, tmp)
            if schema_path is not None and schema_path.parent == tmp:
                used_tmp = True

            add_dir_candidates: list[Path | None] = []
            if resolved_workspace is not None:
                add_dir_candidates.append(resolved_workspace)
            for extra in extra_dirs or []:
                add_dir_candidates.append(extra)
            for attachment in resolved_attachments:
                add_dir_candidates.append(attachment.parent)
            if not write or used_tmp:
                add_dir_candidates.append(tmp)
            add_dirs = _dedupe_paths(add_dir_candidates)

            cmd = [
                agy_bin,
                "-p",
                instruction,
                "--model",
                resolved_model,
                "--output-format",
                "json",
            ]
            if disable_slash_commands:
                cmd.append("--disable-slash-commands")
            if effort:
                cmd.extend(["--effort", effort])
            if schema_path is not None:
                cmd.extend(["--json-schema", str(schema_path)])
            if timeout and timeout > 0:
                cmd.extend(["--print-timeout", f"{int(timeout)}s"])
            for directory in add_dirs:
                cmd.extend(["--add-dir", str(directory)])
            if write:
                cmd.extend(["--mode", "accept-edits"])

            run_cwd = str(resolved_workspace) if (write and resolved_workspace is not None) else str(tmp)
            proc_timeout = (int(timeout) + 30) if (timeout and timeout > 0) else None
            result = subprocess.run(
                cmd,
                text=True,
                cwd=run_cwd,
                capture_output=True,
                check=False,
                timeout=proc_timeout,
                env=_subprocess_env(),
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"agy failed with exit code {result.returncode}\n"
                    f"stdout:\n{result.stdout[-2000:]}\nstderr:\n{result.stderr[-2000:]}"
                )
            return _unpack_agy_json_output(result.stdout)

    return _run_with_retries(_once, retries=retries)


def run_gemini(
    prompt: str,
    workspace: Path | None,
    model: str | None = None,
    write: bool = False,
    *,
    timeout: int | None = 300,
    retries: int = 1,
    extra_dirs: list[Path] | None = None,
) -> str:
    gemini_bin = _require("gemini")
    resolved_workspace = Path(workspace).expanduser().resolve() if workspace else Path.cwd()
    resolved_model = resolve_model("gemini", model)
    include_dirs = _dedupe_paths([resolved_workspace, *(extra_dirs or [])])

    def _once() -> str:
        cmd = [gemini_bin, "--output-format", "text"]
        for directory in include_dirs:
            cmd.extend(["--include-directories", str(directory)])
        if resolved_model:
            cmd.extend(["--model", resolved_model])
        if write:
            cmd.extend(["--approval-mode", "auto_edit"])
        result = subprocess.run(
            cmd,
            input=prompt,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(resolved_workspace),
            timeout=timeout,
            env=_subprocess_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"gemini failed with exit code {result.returncode}\n"
                f"stdout:\n{result.stdout[-2000:]}\nstderr:\n{result.stderr[-2000:]}"
            )
        return result.stdout.strip()

    return _run_with_retries(_once, retries=retries)


def run_agent(
    prompt: str,
    *legacy_args: Any,
    provider: str = "codex",
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
    """Run a prompt through the chosen CLI provider and return the final text response.

    Canonical signature:
        run_agent(prompt, *, provider="codex", model=None, workspace=None, write=False, ...)

    Also accepts legacy positional invocation `(provider, prompt, workspace[, model[, write]])`
    so older callers continue working without modification.
    """
    if legacy_args:
        if prompt not in PROVIDERS:
            raise TypeError(
                "run_agent() takes prompt as the only positional argument "
                "(or legacy positional (provider, prompt, workspace[, model[, write]]))"
            )
        provider = prompt
        prompt = legacy_args[0]
        if len(legacy_args) >= 2 and workspace is None:
            workspace = legacy_args[1]
        if len(legacy_args) >= 3 and model is None:
            model = legacy_args[2]
        if len(legacy_args) >= 4 and not write:
            write = bool(legacy_args[3])
        if len(legacy_args) > 4:
            raise TypeError(f"run_agent() received too many positional arguments ({len(legacy_args) + 1})")

    resolved_workspace = Path(workspace) if workspace is not None else None

    if provider == "codex":
        return run_codex(
            prompt,
            resolved_workspace,
            model,
            write,
            json_schema=json_schema,
            timeout=timeout,
            retries=retries,
            extra_dirs=extra_dirs,
        )
    if provider == "claude":
        return run_claude(
            prompt,
            resolved_workspace,
            model,
            write,
            json_schema=json_schema,
            effort=effort,
            timeout=timeout,
            retries=retries,
            extra_dirs=extra_dirs,
            extra_allowed_tools=extra_allowed_tools,
            disable_slash_commands=disable_slash_commands,
        )
    if provider == "agy":
        return run_agy(
            prompt,
            resolved_workspace,
            model,
            write,
            attachments=attachments,
            timeout=timeout,
            json_schema=json_schema,
            effort=effort,
            retries=retries,
            extra_dirs=extra_dirs,
            disable_slash_commands=disable_slash_commands,
        )
    if provider == "gemini":
        return run_gemini(
            prompt,
            resolved_workspace,
            model,
            write,
            timeout=timeout,
            retries=retries,
            extra_dirs=extra_dirs,
        )
    raise ValueError(f"unknown provider: {provider}")
