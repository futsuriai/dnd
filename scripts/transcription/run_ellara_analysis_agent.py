#!/usr/bin/env python3
"""Run Ellara post-session campaign-state analysis (`ellara-session-analysis`) against ~/source/ellara."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import pipeline_paths  # noqa: E402


def delta_script_path(ellara_dir: Path) -> Path:
    return ellara_dir / ".agents" / "skills" / "ellara-session-analysis" / "scripts" / "check_session_delta.py"


def check_session_note_parity(
    session: int,
    dnd_dir: Path,
    ellara_dir: Path,
    *,
    sync_from_dnd: bool = False,
    prefer: str | None = None,
    allow_provisional: bool = False,
    dry_run: bool = False,
) -> Path | None:
    """Ensure `ellara/Session Notes/Session N.md` and `dnd/src/assets/sessions/session-N.md` agree."""
    ellara_note = ellara_dir / "Session Notes" / f"Session {session}.md"
    dnd_note = dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md"

    ellara_exists = ellara_note.is_file()
    dnd_exists = dnd_note.is_file()

    if not ellara_exists and not dnd_exists:
        if allow_provisional:
            print(f"No polished Session {session} notes found in either repo; continuing in provisional mode.")
            return None
        raise FileNotFoundError(
            f"Missing polished Session {session} notes in both repos:\n"
            f"  ellara: {ellara_note}\n"
            f"  dnd:    {dnd_note}"
        )

    if not ellara_exists and dnd_exists:
        if sync_from_dnd or prefer == "dnd":
            if dry_run:
                print(f"[dry-run] would copy {dnd_note} -> {ellara_note}")
            else:
                ellara_note.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dnd_note, ellara_note)
                print(f"Synced missing Ellara session notes from dnd: {dnd_note} -> {ellara_note}")
            return ellara_note
        print(f"Note: {ellara_note} not present yet; reading authoritative summary from {dnd_note}.")
        return dnd_note

    if ellara_exists and not dnd_exists:
        print(f"Note: {dnd_note} not present yet; reading authoritative summary from {ellara_note}.")
        return ellara_note

    ellara_text = ellara_note.read_text(encoding="utf-8")
    dnd_text = dnd_note.read_text(encoding="utf-8")
    if ellara_text == dnd_text:
        return ellara_note

    if prefer == "dnd":
        if sync_from_dnd:
            if dry_run:
                print(f"[dry-run] would overwrite {ellara_note} from {dnd_note} (--prefer dnd --sync-from-dnd)")
            else:
                shutil.copy2(dnd_note, ellara_note)
                print(f"Updated Ellara session notes from dnd (--prefer dnd): {dnd_note} -> {ellara_note}")
        else:
            print(f"Parity override (--prefer dnd): using {dnd_note} without overwriting {ellara_note}.")
        return dnd_note

    if prefer == "ellara":
        print(f"Parity override (--prefer ellara): using {ellara_note} (leaving {dnd_note} untouched).")
        return ellara_note

    raise RuntimeError(
        f"Session {session} polished notes differ between repos:\n"
        f"  ellara: {ellara_note}\n"
        f"  dnd:    {dnd_note}\n"
        f"Re-run with --prefer ellara or --prefer dnd (optionally with --sync-from-dnd)."
    )


def run_delta_check(ellara_dir: Path, dnd_dir: Path) -> dict:
    script = delta_script_path(ellara_dir)
    if not script.is_file():
        raise FileNotFoundError(f"Missing Ellara delta script: {script}")
    res = subprocess.run(
        [
            sys.executable,
            "-B",
            str(script),
            "--ellara-root",
            str(ellara_dir),
            "--dnd-root",
            str(dnd_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        env=pipeline_paths.no_bytecode_env(),
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"check_session_delta.py --json failed ({res.returncode}):\n{res.stderr or res.stdout}")
    return json.loads(res.stdout)


def run_validation(
    ellara_dir: Path,
    dnd_dir: Path,
    session: int,
    *,
    allow_provisional: bool = False,
) -> int:
    script = delta_script_path(ellara_dir)
    cmd = [
        sys.executable,
        "-B",
        str(script),
        "--ellara-root",
        str(ellara_dir),
        "--dnd-root",
        str(dnd_dir),
        "--validate",
        "--session",
        str(session),
    ]
    if allow_provisional:
        cmd.append("--allow-provisional")
    res = subprocess.run(cmd, env=pipeline_paths.no_bytecode_env(), check=False)
    return res.returncode


def collect_dnd_store_diff(dnd_dir: Path, max_chars: int = 12000) -> str:
    """Collect the uncommitted git diff of `src/store/` in `dnd_dir`."""
    res = subprocess.run(
        ["git", "-C", str(dnd_dir), "diff", "--", "src/store/"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0 or not res.stdout.strip():
        return ""
    diff = res.stdout.strip()
    if len(diff) > max_chars:
        return diff[:max_chars].rstrip() + "\n... (truncated)"
    return diff


def collect_vault_stems(ellara_dir: Path) -> list[str]:
    """Return sorted unique markdown filename stems across the Ellara vault."""
    excluded = {".git", ".agents", ".github", "node_modules"}
    stems: set[str] = set()
    for path in ellara_dir.rglob("*.md"):
        try:
            rel_parts = path.relative_to(ellara_dir).parts
        except ValueError:
            continue
        if set(rel_parts[:-1]) & excluded:
            continue
        stems.add(path.stem)
    return sorted(stems)


def build_analysis_prompt(
    session: int,
    delta_report: dict,
    dnd_dir: Path,
    *,
    allow_provisional: bool = False,
    allow_shell: bool = True,
    dnd_store_diff: str = "",
    vault_stems: list[str] | None = None,
) -> str:
    provisional_note = (
        "Provisional mode is enabled: if only raw notes/transcripts exist, mark the brief `[PROVISIONAL]`."
        if allow_provisional
        else "Polished session notes exist: do NOT leave a `[PROVISIONAL]` marker in the final brief."
    )
    tool_rule = (
        ""
        if allow_shell
        else (
            "Tool constraint (IMPORTANT):\n"
            "- Use file reading and editing tools ONLY (`read_file`, `edit_file`, `write_file`).\n"
            "- NEVER invoke shell or terminal commands (`run_command`, bash, python, git, find). "
            "`check_session_delta.py --json`, the `dnd/src/store/` diff, and valid vault page stems are precomputed below, "
            "and `check_session_delta.py --validate` runs automatically right after your edits.\n\n"
        )
    )
    store_diff_section = (
        f"\nPrecomputed `git diff` of `dnd/src/store/`:\n```diff\n{dnd_store_diff}\n```\n"
        if dnd_store_diff
        else ""
    )
    stems_section = (
        f"\nPrecomputed valid vault WikiLink target stems ({len(vault_stems)} total): "
        + ", ".join(vault_stems)
        + "\n"
        if vault_stems
        else ""
    )
    validation_step = (
        f"After updating the four files, run:\n"
        f"`python3 -B .agents/skills/ellara-session-analysis/scripts/check_session_delta.py --ellara-root . --dnd-root \"{dnd_dir}\" --validate --session {session}`"
        if allow_shell
        else (
            "After updating the four files, do NOT run any shell validation command — "
            "the Python harness automatically runs `check_session_delta.py --validate` right after your turn completes."
        )
    )
    python_rule = (
        "7. Always invoke Python with `python3 -B` (zero `__pycache__/` or `*.pyc` files)."
        if allow_shell
        else "7. Never create `__pycache__/` or `*.pyc` files (and do not invoke Python/shell commands)."
    )
    return f"""You are running the `ellara-session-analysis` workflow for Session {session} in the `ellara` repository.

{tool_rule}Governing instructions (read these files in the workspace first; do not ignore any rule):
- `AGENTS.md`
- `.agents/skills/ellara-session-analysis/SKILL.md`
- `.agents/skills/ellara-session-analysis/references/repo-map-and-methodology.md`
- `.agents/skills/ellara-session-analysis/references/analysis-template.md`

Sibling DnD campaign repo (read-only access via extra dir): `{dnd_dir}`

Precomputed `check_session_delta.py --json` report:
```json
{json.dumps(delta_report, indent=2)}
```
{store_diff_section}{stems_section}
Mandatory scope & boundaries:
1. Edit ONLY files inside `Ellara/Campaign State/`:
   - `Ellara/Campaign State/Ellara Current State.md`
   - `Ellara/Campaign State/Ellara Threads and Callbacks.md`
   - `Ellara/Campaign State/Knowledge Boundary and Dramatic Irony.md`
   - `Ellara/Campaign State/Session Briefs/Session {session} Analysis.md`
2. NEVER modify any file in `{dnd_dir}` or outside `Ellara/Campaign State/`.
3. Preserve strict IC vs. OOC separation: items in Section 2 of `Knowledge Boundary and Dramatic Irony.md` must NEVER appear in Ellara's IC headspace, motives, or planned moves unless explicitly revealed to Ellara on-page in Session {session}.
4. Primary-text discipline: verify every verbatim quote and exact skill-check scope (especially Insight / Perception) against the primary session summary; never put quotation marks around narrator paraphrase.
5. Wiki compatibility: keep every `.md` filename stem globally unique, ensure every `[[WikiLink]]` resolves to a real vault page, and never place `[[WikiLinks]]` inside fenced code blocks.
6. Keep frontmatter synchronized (`last_analyzed_session: {session}`, `next_session: {session + 1}`, and `next_session_title` matching `dnd/src/store/sessions.js` upcoming subtitle when present). {provisional_note}
{python_rule}

{validation_step}

In your final response, deliver ONLY the concise, table-ready **Prep Brief** for Session {session + 1}:
- What Ellara is thinking right now (strictly IC)
- Immediate next moves / conversations she would initiate
- Prioritized next-session hooks
- Useful RP callbacks & exact quotes
- A clearly separated **OOC Watchlist** (what Ellara still does NOT know)"""


def collect_campaign_state_diff(ellara_dir: Path, session: int) -> str:
    diff_res = subprocess.run(
        ["git", "-C", str(ellara_dir), "diff", "--", "Ellara/Campaign State"],
        capture_output=True,
        text=True,
        check=False,
    )
    parts: list[str] = []
    if diff_res.stdout.strip():
        parts.append("### git diff Ellara/Campaign State\n" + diff_res.stdout.strip())
    brief_path = ellara_dir / "Ellara" / "Campaign State" / "Session Briefs" / f"Session {session} Analysis.md"
    if brief_path.is_file():
        parts.append(f"### Full {brief_path.name}\n" + brief_path.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts)


def build_audit_prompt(
    session: int,
    primary_summary: Path | None,
    dnd_dir: Path,
    state_diff: str,
    *,
    allow_shell: bool = True,
    vault_stems: list[str] | None = None,
) -> str:
    summary_hint = str(primary_summary) if primary_summary else f"{dnd_dir}/src/assets/sessions/session-{session}.md"
    tool_rule = (
        ""
        if allow_shell
        else (
            "Tool constraint (IMPORTANT): Use file reading and editing tools ONLY (`read_file`, `edit_file`, `write_file`). "
            "NEVER invoke shell or terminal commands (`run_command`, bash, python, git, find); validation runs automatically afterward.\n\n"
        )
    )
    stems_section = (
        f"\nValid vault WikiLink target stems ({len(vault_stems)} total): "
        + ", ".join(vault_stems)
        + "\n"
        if vault_stems
        else ""
    )
    return f"""Perform a clean-context primary-text & IC/OOC audit of the Session {session} updates in `Ellara/Campaign State/`.

{tool_rule}Read:
- Primary session summary: `{summary_hint}`
- `Ellara/Campaign State/Knowledge Boundary and Dramatic Irony.md`
- `Ellara/Campaign State/Ellara Current State.md`
- `Ellara/Campaign State/Ellara Threads and Callbacks.md`
- `Ellara/Campaign State/Session Briefs/Session {session} Analysis.md`
{stems_section}
Check strictly for these four defect classes:
1. **OOC / Dramatic Irony Leakage:** Any item from Section 2 of `Knowledge Boundary and Dramatic Irony.md` (or offscreen scene Ellara did not witness) appearing inside Ellara's IC thoughts, headspace, motives, or planned moves.
2. **Paraphrase-as-Quote:** Any narrator summary or paraphrase wrapped in quotation marks as if it were verbatim dialogue from `{summary_hint}`.
3. **Over-broad Skill Check Scope:** Any `Insight`, `Perception`, or other check credited with revealing more than the specific moment/beat it applied to in `{summary_hint}`.
4. **Wiki / Frontmatter Safety:** Any broken `[[WikiLink]]`, `[[WikiLink]]` inside a fenced code block, or frontmatter mismatch.

If you find any genuine violation, fix it directly in place inside `Ellara/Campaign State/` (NEVER touch `{dnd_dir}` or files outside `Ellara/Campaign State/`). If everything is clean, make no edits.

Changes to audit:
{state_diff[:40000]}

Return a concise bullet list of findings and fixes applied (or `No IC/OOC or quote defects found.`)."""


def resolve_audit_model(provider: str, model: str | None, audit_model: str | None) -> str | None:
    if audit_model:
        return audit_model
    if model:
        return model
    if provider == "agy":
        tiers = getattr(agent_cli, "AGY_TIERS", None)
        if isinstance(tiers, dict) and tiers.get("strong"):
            return tiers["strong"]
        return "gemini-4-neon-high"
    return None


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(tok in msg for tok in ("quota", "429", "resource_exhausted", "rate limit"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to analyze")
    parser.add_argument("--dnd-dir", default=str(pipeline_paths.resolve_dnd_dir()), help="DnD repo root")
    parser.add_argument("--ellara-root", default=str(pipeline_paths.resolve_ellara_dir()), help="Ellara repo root")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="agy", help="Agent CLI provider")
    parser.add_argument("--model", help="Optional model override for the analysis pass")
    parser.add_argument("--audit-model", help="Optional model override for the IC/OOC audit pass")
    parser.add_argument("--no-audit", action="store_true", help="Skip the clean-context IC/OOC & quote audit pass")
    parser.add_argument("--audit-only", action="store_true", help="Skip Pass 1 analysis and run only Pass 2 IC/OOC audit + validation")
    parser.add_argument("--sync-from-dnd", action="store_true", help="Copy dnd session-N.md into Ellara if missing (or with --prefer dnd)")
    parser.add_argument("--prefer", choices=("ellara", "dnd"), help="Resolve parity mismatch if Session N.md and session-N.md differ")
    parser.add_argument("--allow-provisional", action="store_true", help="Allow provisional mode when only raw notes exist")
    parser.add_argument("--force", action="store_true", help="Re-run analysis even if last_analyzed_session >= session")
    parser.add_argument("--brief-out", help="Optional path to save the table-ready Prep Brief markdown")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions and prompt without writing or invoking agents")
    args = parser.parse_args(argv)

    dnd_dir = pipeline_paths.resolve_dnd_dir(args.dnd_dir)
    ellara_dir = pipeline_paths.resolve_ellara_dir(args.ellara_root)

    primary_summary = check_session_note_parity(
        args.session,
        dnd_dir,
        ellara_dir,
        sync_from_dnd=args.sync_from_dnd,
        prefer=args.prefer,
        allow_provisional=args.allow_provisional,
        dry_run=args.dry_run,
    )

    delta_report = run_delta_check(ellara_dir, dnd_dir)
    last_analyzed = delta_report.get("last_analyzed_session")
    if not args.audit_only and isinstance(last_analyzed, int) and last_analyzed >= args.session and not args.force:
        print(
            f"Ellara Campaign State already analyzed through Session {last_analyzed} (>= {args.session}); skipping agent run."
        )
        if args.dry_run:
            return 0
        return run_validation(
            ellara_dir,
            dnd_dir,
            args.session,
            allow_provisional=args.allow_provisional,
        )

    allow_shell = args.provider != "agy"
    vault_stems = collect_vault_stems(ellara_dir)

    if args.audit_only:
        state_diff = collect_campaign_state_diff(ellara_dir, args.session)
        audit_model = resolve_audit_model(args.provider, args.model, args.audit_model)
        audit_prompt = build_audit_prompt(
            args.session,
            primary_summary,
            dnd_dir,
            state_diff,
            allow_shell=allow_shell,
            vault_stems=vault_stems,
        )
        if args.dry_run:
            print(f"[dry-run] --audit-only: would run Pass 2 IC/OOC audit with {args.provider} (model={audit_model or 'default'}, allow_shell={allow_shell})")
            print()
            print(audit_prompt)
            return 0
    else:
        dnd_store_diff = collect_dnd_store_diff(dnd_dir)
        prompt = build_analysis_prompt(
            args.session,
            delta_report,
            dnd_dir,
            allow_provisional=args.allow_provisional,
            allow_shell=allow_shell,
            dnd_store_diff=dnd_store_diff,
            vault_stems=vault_stems,
        )

        if args.dry_run:
            print(f"[dry-run] Would run {args.provider} (model={args.model or 'default'}, allow_shell={allow_shell}) in {ellara_dir} with extra_dirs=[{dnd_dir}]")
            if not args.no_audit:
                audit_model = resolve_audit_model(args.provider, args.model, args.audit_model)
                print(f"[dry-run] Would run clean-context IC/OOC audit pass with {args.provider} (model={audit_model or 'default'})")
            if args.brief_out:
                print(f"[dry-run] Would write Prep Brief to {args.brief_out}")
            print()
            print(prompt)
            return 0

        print(f"Running Ellara campaign-state analysis for Session {args.session} via {args.provider}...")
        brief = pipeline_paths.call_agent(
            agent_cli,
            prompt=prompt,
            provider=args.provider,
            model=args.model,
            workspace=ellara_dir,
            write=True,
            extra_dirs=[dnd_dir],
            extra_allowed_tools=["Bash(python3 -B:*)"],
            timeout=600,
        ).strip()

        state_diff = collect_campaign_state_diff(ellara_dir, args.session)
        if not brief and not state_diff:
            print(
                "ERROR: Ellara analysis pass returned no Prep Brief and made no changes in Ellara/Campaign State/; aborting before audit.",
                file=sys.stderr,
            )
            return 1

        if args.brief_out:
            brief_path = Path(args.brief_out).expanduser().resolve()
            brief_path.parent.mkdir(parents=True, exist_ok=True)
            brief_path.write_text((brief + "\n") if brief else "", encoding="utf-8")
            print(f"Saved Ellara Prep Brief -> {brief_path}")
        if brief:
            print()
            print(brief)

    if args.audit_only or not args.no_audit:
        audit_model = resolve_audit_model(args.provider, args.model, args.audit_model)
        audit_prompt = build_audit_prompt(
            args.session,
            primary_summary,
            dnd_dir,
            state_diff,
            allow_shell=allow_shell,
            vault_stems=vault_stems,
        )
        default_tier = agent_cli.AGY_TIERS["default"]
        fallback_model = (
            default_tier
            if args.provider == "agy" and not args.audit_model and audit_model != default_tier
            else None
        )

        def _invoke_audit(target_model: str | None) -> str:
            return pipeline_paths.call_agent(
                agent_cli,
                prompt=audit_prompt,
                provider=args.provider,
                model=target_model,
                workspace=ellara_dir,
                write=True,
                extra_dirs=[dnd_dir],
                extra_allowed_tools=["Bash(python3 -B:*)"],
                timeout=600,
            ).strip()

        print(f"Running clean-context IC/OOC & quote audit via {args.provider} (model={audit_model or 'default'})...")
        try:
            audit_reply = _invoke_audit(audit_model)
        except Exception as exc:  # noqa: BLE001
            if fallback_model and _is_quota_error(exc):
                print(
                    f"WARNING: Audit pass hit quota/429 on {audit_model}; retrying once with {fallback_model}...",
                    file=sys.stderr,
                )
                try:
                    audit_reply = _invoke_audit(fallback_model)
                except Exception as exc2:  # noqa: BLE001
                    print(
                        f"ERROR: Ellara audit pass failed on fallback model {fallback_model}: {exc2}\n"
                        f"HINT: Pass 1 changes in Ellara/Campaign State/ are preserved. Resume audit only with:\n"
                        f"  python3 -B {Path(__file__).name} --session {args.session} --dnd-dir {dnd_dir} --ellara-root {ellara_dir} --provider {args.provider} --audit-only",
                        file=sys.stderr,
                    )
                    return 1
            else:
                print(
                    f"ERROR: Ellara audit pass failed: {exc}\n"
                    f"HINT: Pass 1 changes in Ellara/Campaign State/ are preserved. Resume audit only with:\n"
                    f"  python3 -B {Path(__file__).name} --session {args.session} --dnd-dir {dnd_dir} --ellara-root {ellara_dir} --provider {args.provider} --audit-only",
                    file=sys.stderr,
                )
                return 1
        if audit_reply:
            print(audit_reply)

    val_code = run_validation(
        ellara_dir,
        dnd_dir,
        args.session,
        allow_provisional=args.allow_provisional,
    )
    if val_code != 0:
        print(f"ERROR: Ellara Campaign State validation failed for Session {args.session}", file=sys.stderr)
    return val_code


if __name__ == "__main__":
    raise SystemExit(main())
