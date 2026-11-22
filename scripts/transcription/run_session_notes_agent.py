#!/usr/bin/env python3
"""
Generate polished Session N markdown from Raw Session N markdown through an agent CLI.

Supported providers (from agent_cli.PROVIDERS):
- agy (default, Gemini 4 Neon)
- codex
- claude
- gemini
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import pipeline_paths  # noqa: E402
from note_generation_guidance import CANONICAL_CAST_REFERENCE  # noqa: E402

STYLE_EXAMPLE = pipeline_paths.DND_DIR / "src" / "assets" / "sessions" / "session-8.md"
TIMESTAMP_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\s+", re.MULTILINE)


def _compile_rule(rule: dict) -> tuple[re.Pattern[str], str]:
    flags = 0
    raw_flags = str(rule.get("flags", ""))
    if "i" in raw_flags:
        flags |= re.IGNORECASE
    if "m" in raw_flags:
        flags |= re.MULTILINE
    return re.compile(rule["pattern"], flags), rule["message"]


def load_shared_rules(rules_path: Path | None = None) -> tuple[list[tuple[re.Pattern[str], str]], dict[str, list[tuple[re.Pattern[str], str]]]]:
    path = rules_path or (pipeline_paths.DND_DIR / "scripts" / "shared_sync_rules.json")
    if not path.is_file():
        return [], {}
    data = json.loads(path.read_text(encoding="utf-8"))
    public_patterns = [_compile_rule(r) for r in data.get("badPublicPatterns", [])]
    session_rules = {
        str(k): [_compile_rule(r) for r in v]
        for k, v in data.get("sessionSpecificRules", {}).items()
    }
    return public_patterns, session_rules


def validate_generated_notes(
    session: str,
    text: str,
    rules_path: Path | None = None,
) -> list[str]:
    """Validate structure, timestamps, and canon spelling/fact rules on generated Session N.md."""
    errors: list[str] = []
    if not text.strip():
        return [f"Generated Session {session}.md is empty."]

    for marker in (f"# Session {session}", "**Locales:**", "**Time:**", "## 1)"):
        if marker not in text:
            errors.append(f"Session {session}.md missing required structural marker `{marker}`.")

    ts_matches = TIMESTAMP_RE.findall(text)
    if ts_matches:
        errors.append(f"Session {session}.md leaked {len(ts_matches)} raw transcript timestamp(s).")

    public_patterns, session_rules = load_shared_rules(rules_path)
    for pattern, message in public_patterns:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"line {line}: {message} Found `{match.group(0)}`.")

    for pattern, message in session_rules.get(str(session), []):
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"line {line}: {message} Found `{match.group(0)}`.")

    return errors


def build_prompt(session: str, raw_text: str) -> str:
    return f"""Task:
- Convert these raw D&D session notes into polished markdown session notes.
- Match the structure and story-forward style of existing `session-7.md` and `session-8.md`.
- This is the polished campaign-notes layer, not the raw-notes layer.

Required format:
- Start with `# Session {session} — *<title>*`
- Then a `**Locales:**` line
- Then a `**Time:**` line
- Then `---`
- Use numbered markdown sections like `## 1) ...`
- End with a status section like `## Where We Stand` when useful, preferably as a thread/status table.
- Add `### Next Steps` or a similar short forward-looking section when the session leaves clear immediate objectives.

Rules:
- Keep chronology accurate.
- Turn rough raw notes into readable narrative prose.
- Preserve only the most important direct quotes.
- Treat dialogue and thoughts preserved in the raw notes as intentional evidence; do not paraphrase away important wording unless the final summary clearly benefits from compression.
- Keep key rolls/checks when they matter to the story.
- Preserve roll attribution exactly from the raw notes. If the raw notes mark the roller as uncertain, keep the uncertainty or omit the roller instead of guessing.
- When a roll unlocks a lore clue, do not credit a different character with that clue unless the raw notes explicitly support the transfer.
- Preserve GM revelations, world facts, character motivations, and consequences.
- Fold any prior-context summary into the opening section rather than presenting it as transcript recap.
- Do not invent facts, names, dialogue, or outcomes.
- Do not mention transcript mechanics, chunking, or timestamps.
- If the raw notes are uncertain, be modest and avoid false precision.
- Output markdown only. No code fences. No commentary.
- Preserve canonical character genders/pronouns consistently across the whole document.

{CANONICAL_CAST_REFERENCE}

Example of the target style (an earlier finished session; match its structure and voice, not its content):
<example>
{STYLE_EXAMPLE.read_text(encoding="utf-8") if STYLE_EXAMPLE.exists() else "(missing)"}
</example>

Raw notes:
{raw_text}

Return only the final markdown."""


def main(argv: list[str] | None = None) -> int:
    default_workspace = str(pipeline_paths.resolve_dnd_dir().parent)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Session label/number for the title")
    parser.add_argument("raw_notes_file", help="Path to Raw Session N.md")
    parser.add_argument("output_file", help="Path to Session N.md")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, required=True, help="Agent CLI to use")
    parser.add_argument("--model", help="Optional model override")
    parser.add_argument("--workspace-root", default=default_workspace, help="Workspace root visible to the agent CLI")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned action without invoking the provider")
    parser.add_argument("--skip-raw-validation", action="store_true", help="Skip validate_raw_notes.py before generation")
    parser.add_argument("--skip-output-validation", action="store_true", help="Skip post-generation structure/canon validation")
    args = parser.parse_args(argv)

    raw_notes_file = Path(args.raw_notes_file).expanduser().resolve()
    output_file = Path(args.output_file).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser().resolve()

    if output_file.exists() and not args.force:
        print(f"Session notes output already exists, skipping: {output_file}")
        return 0

    if not args.skip_raw_validation:
        validator = Path(__file__).with_name("validate_raw_notes.py")
        subprocess.run(
            [str(pipeline_paths.resolve_python()), "-B", str(validator), str(raw_notes_file), "--session", str(args.session)],
            env=pipeline_paths.no_bytecode_env(),
            check=True,
        )

    raw_text = raw_notes_file.read_text(encoding="utf-8")
    prompt = build_prompt(args.session, raw_text)

    if args.dry_run:
        print(f"Would run {args.provider} (model={args.model or 'default'}) -> {output_file}")
        return 0

    print(f"Running {args.provider} for polished session notes -> {output_file}")
    text = pipeline_paths.call_agent(
        agent_cli,
        prompt=prompt,
        provider=args.provider,
        model=args.model,
        workspace=workspace_root,
        write=False,
        timeout=600,
    )
    text = agent_cli.strip_code_fences(text).rstrip() + "\n"

    if not args.skip_output_validation:
        errors = validate_generated_notes(str(args.session), text)
        if errors:
            invalid_path = output_file.with_suffix(".invalid.md")
            invalid_path.parent.mkdir(parents=True, exist_ok=True)
            invalid_path.write_text(text, encoding="utf-8")
            print(
                f"ERROR: Generated Session {args.session} notes failed post-generation validation "
                f"(draft saved to {invalid_path}):",
                file=sys.stderr,
            )
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(text, encoding="utf-8")
    print(f"Wrote {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
