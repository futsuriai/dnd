#!/usr/bin/env python3
"""Fully automatic session pipeline: speaker audio -> transcript -> notes -> website -> ellara-state.

No human checkpoints. Each stage records its status and outputs in
`<audio-dir>/pipeline/manifest.json`; reruns skip finished stages unless
--from-stage/--only/--force say otherwise.

Stages (in order):
    entities      regenerate ENTITY_LIST.md + entity_metadata.json (ASR vocabulary)
    asr           run ASR engines per speaker track (raw provider JSON is kept)
    gemini        Gemini 4 Neon (agy) listens to disputed / one-sided lines (audio arbitration)
    transcript    assemble the chronological transcript from the primary engine
    dice          optional: fetch D&D Beyond rolls, align to audio, re-assemble with DICE lines
    fuse          LLM judge picks/combines the engines' readings per line, in context
    diagnostics   compare engines (coverage, agreement, names, loops; optional audio judge)
    raw-notes     scene-based Raw Session N.md
    audit         LLM audit of each scene's notes vs transcript (OOC leaks, missing beats,
                  misattributions, game content in skipped scenes); patches scene files in place
    notes         polished Session N.md (with post-generation structure/canon validation)
    website       copy into the site, update stores (including sessions.js homeRecap/nextSteps/storyBeat)
    ellara-state  update ~/source/ellara/Ellara/Campaign State/ + IC/OOC audit + Prep Brief
    verify        raw-note validation, npm run sync-check, pipeline validation, ellara-state validation
    publish       only with --publish: preflight + explicit staging + commit both repos (no push unless --push)

Typical runs:
    # full run using Gemini 4 Neon via agy (default)
    python3 -B scripts/transcription/run_session_auto.py --session 22 --audio-dir ~/source/session-22

    # dry-run stage plan and resolved paths
    python3 -B scripts/transcription/run_session_auto.py --session 22 --audio-dir ~/source/session-22 --dry-run

    # cheap/free ASR: local Whisper only
    python3 -B scripts/transcription/run_session_auto.py --session 22 --audio-dir ~/source/session-22 \
        --engines whisper-large-v3 --primary whisper-large-v3
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import agent_cli  # noqa: E402
import pipeline_paths  # noqa: E402

STAGES = [
    "entities",
    "asr",
    "gemini",
    "transcript",
    "dice",
    "fuse",
    "diagnostics",
    "raw-notes",
    "audit",
    "notes",
    "website",
    "ellara-state",
    "verify",
    "publish",
]


def log(msg: str) -> None:
    print(f"[auto {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def resolve_stage_provider_and_model(
    stage_provider: str | None,
    stage_model: str | None,
    default_provider: str,
    default_model: str | None,
) -> tuple[str, str | None]:
    """Resolve a stage's provider and model without leaking --model across different providers."""
    provider = stage_provider or default_provider
    if stage_model:
        return provider, stage_model
    if stage_provider is None or stage_provider == default_provider:
        return provider, default_model
    return provider, None


def ddb_configured(dnd_dir: Path) -> bool:
    env_file = dnd_dir / ".env.local"
    keys = set(os.environ)
    if env_file.exists():
        keys |= {
            line.split("=", 1)[0].strip()
            for line in env_file.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        }
    return {"DDB_COBALT_SESSION", "DDB_CAMPAIGN_ID"} <= keys


def script_accepts_flag(script_path: Path, flag: str) -> bool:
    try:
        return flag in script_path.read_text(encoding="utf-8")
    except OSError:
        return False


def snapshot_pre_fuse(
    transcript: Path,
    lines_jsonl: Path,
    pre_fuse_txt: Path,
    pre_fuse_jsonl: Path,
) -> None:
    """Save unfused transcript snapshots so `--only fuse` reruns are idempotent."""
    pre_fuse_jsonl.parent.mkdir(parents=True, exist_ok=True)
    if lines_jsonl.is_file():
        shutil.copy2(lines_jsonl, pre_fuse_jsonl)
    if transcript.is_file():
        shutil.copy2(transcript, pre_fuse_txt)


def prepare_fuse_input(
    transcript: Path,
    lines_jsonl: Path,
    pre_fuse_txt: Path,
    pre_fuse_jsonl: Path,
) -> None:
    """Restore unfused baseline before fusion, or capture it if this is the first fuse run."""
    if pre_fuse_jsonl.is_file():
        shutil.copy2(pre_fuse_jsonl, lines_jsonl)
        if pre_fuse_txt.is_file():
            shutil.copy2(pre_fuse_txt, transcript)
    else:
        snapshot_pre_fuse(transcript, lines_jsonl, pre_fuse_txt, pre_fuse_jsonl)


def collect_publish_files(
    session: str,
    dnd_dir: Path,
    ellara_dir: Path,
    *,
    include_ellara_state: bool = True,
) -> tuple[list[Path], list[Path]]:
    """Return explicit allowlists of existing session files to stage in (ellara_dir, dnd_dir)."""
    ellara_candidates = [
        ellara_dir / "Session Notes" / f"Raw Session {session}.md",
        ellara_dir / "Session Notes" / f"Session {session}.md",
        ellara_dir / "Session Notes" / "Transcripts" / f"Transcript Session {session}.txt",
    ]
    if include_ellara_state:
        campaign_state = ellara_dir / "Ellara" / "Campaign State"
        ellara_candidates.extend(
            [
                campaign_state / "Ellara Current State.md",
                campaign_state / "Ellara Threads and Callbacks.md",
                campaign_state / "Knowledge Boundary and Dramatic Irony.md",
                campaign_state / "Session Briefs" / f"Session {session} Analysis.md",
            ]
        )

    dnd_candidates = [
        dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md",
        dnd_dir / "src" / "store" / "sessions.js",
        dnd_dir / "src" / "store" / "lore.js",
        dnd_dir / "src" / "store" / "locations.js",
        dnd_dir / "src" / "store" / "npcs.js",
        dnd_dir / "src" / "store" / "characters.js",
        dnd_dir / "src" / "store" / "worldHistory.js",
        dnd_dir / "src" / "store" / "correspondence.js",
        dnd_dir / "src" / "views" / "HomeView.vue",
        dnd_dir / "src" / "views" / "StorySoFarView.vue",
        dnd_dir / "ENTITY_LIST.md",
        dnd_dir / "scripts" / "transcription" / "entity_metadata.json",
    ]

    ellara_files = [p for p in ellara_candidates if p.is_file()]
    dnd_files = [p for p in dnd_candidates if p.is_file()]
    return ellara_files, dnd_files


def git_stage_and_commit(
    repo_dir: Path,
    files: list[Path],
    commit_message: str,
    run_fn,
) -> bool:
    """Stage only explicit files and commit with check=True if staged diff is non-empty."""
    if not files:
        log(f"publish: no matching files to stage in {repo_dir}")
        return False

    rel_paths = [str(p.relative_to(repo_dir)) for p in files]
    run_fn(["git", "-C", str(repo_dir), "add", "--", *rel_paths], cwd=repo_dir, check=True)
    diff_code = run_fn(["git", "-C", str(repo_dir), "diff", "--cached", "--quiet"], cwd=repo_dir, check=False)
    if diff_code == 0:
        log(f"publish: nothing staged to commit in {repo_dir}")
        return False
    run_fn(["git", "-C", str(repo_dir), "commit", "-m", commit_message], cwd=repo_dir, check=True)
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", required=True)
    parser.add_argument("--audio-dir", required=True)
    parser.add_argument("--dnd-dir", default=str(pipeline_paths.resolve_dnd_dir()), help="DnD repo root")
    parser.add_argument("--ellara-root", default=str(pipeline_paths.resolve_ellara_dir()), help="Ellara repo root")
    parser.add_argument("--python", help="Override Python interpreter for transcription/pipeline child scripts")
    parser.add_argument("--engines", default="gladia,whisper-large-v3", help="ASR engines to run")
    parser.add_argument("--primary", default="gladia", help="Engine whose output becomes the transcript (gladia, whisper-*, gemini)")
    parser.add_argument(
        "--gemini",
        choices=["off", "disputed", "all"],
        default="disputed",
        help="Gemini 4 Neon (agy) audio arbitration: disputed/one-sided lines (default), every line, or off",
    )
    parser.add_argument("--gemini-model", default="gemini-4-neon-medium", help="Model for Gemini audio arbitration")
    parser.add_argument("--judge", action="store_true", help="Diagnostics: let Gemini listen to disagreement clips")
    parser.add_argument("--no-fuse", action="store_true", help="Skip the LLM transcript proofreading stage")
    parser.add_argument("--no-audit", action="store_true", help="Skip the raw-notes audit/repair stage")
    parser.add_argument("--no-ellara", action="store_true", help="Skip the Ellara Campaign State analysis stage")
    parser.add_argument("--no-ellara-audit", action="store_true", help="Skip the IC/OOC audit pass inside ellara-state")
    parser.add_argument("--session-date", help="Date the session was played (default: D&D Beyond rolls, else audio file date)")
    parser.add_argument("--provider", choices=agent_cli.PROVIDERS, default="agy", help="Default agent CLI across LLM stages")
    parser.add_argument("--model", help="Default model override (only applied to stages using --provider)")
    parser.add_argument("--fuse-provider", choices=agent_cli.PROVIDERS, help="Override provider for fusion")
    parser.add_argument("--fuse-model", help="Override model for fusion")
    parser.add_argument("--notes-provider", choices=agent_cli.PROVIDERS, help="Override provider for raw + polished notes")
    parser.add_argument("--notes-model", help="Override model for raw + polished notes")
    parser.add_argument("--website-provider", choices=agent_cli.PROVIDERS, help="Override provider for the website agent")
    parser.add_argument("--website-model", help="Override model for the website agent")
    parser.add_argument("--ellara-provider", choices=agent_cli.PROVIDERS, help="Override provider for the Ellara analysis agent")
    parser.add_argument("--ellara-model", help="Override model for the Ellara analysis agent")
    parser.add_argument("--from-stage", choices=STAGES)
    parser.add_argument("--only", choices=STAGES, action="append")
    parser.add_argument("--stop-after", choices=STAGES)
    parser.add_argument("--force", action="store_true", help="Redo stages even if outputs exist")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved paths, providers, and planned stages without running")
    parser.add_argument("--publish", action="store_true", help="Commit Ellara notes/state and dnd site changes")
    parser.add_argument("--push", action="store_true", help="With --publish, also push both repos")
    parser.add_argument("--sandbox", help="Write transcripts/notes here instead of Ellara; skips website/ellara-state/verify/publish")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    session = str(args.session)
    dnd_dir = pipeline_paths.resolve_dnd_dir(args.dnd_dir)
    ellara_dir = pipeline_paths.resolve_ellara_dir(args.ellara_root)
    python_bin = pipeline_paths.resolve_python(args.python)
    audio_dir = Path(args.audio_dir).expanduser().resolve()
    work = audio_dir / "pipeline"
    asr_dir = audio_dir / "asr"

    notes_dir = ellara_dir / "Session Notes"
    transcripts_dir = notes_dir / "Transcripts"
    if args.sandbox:
        notes_dir = Path(args.sandbox).expanduser().resolve()
        transcripts_dir = notes_dir / "Transcripts"
        work = notes_dir / "pipeline"

    manifest_path = work / "manifest.json"
    transcript = transcripts_dir / f"Transcript Session {session}.txt"
    lines_jsonl = transcripts_dir / f"Transcript Session {session}.lines.jsonl"
    pre_fuse_txt = work / f"Transcript Session {session}.pre_fuse.txt"
    pre_fuse_jsonl = work / f"Transcript Session {session}.pre_fuse.lines.jsonl"
    fusion_report = work / f"session_{session}_fusion_report.md"
    diagnostics_report = work / f"session_{session}_asr_diagnostics.md"
    audit_report = work / f"session_{session}_raw_notes_audit.md"
    prep_brief_path = work / f"ellara_prep_brief_session_{session}.md"
    raw_notes = notes_dir / f"Raw Session {session}.md"
    session_notes = notes_dir / f"Session {session}.md"
    website_md = dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md"

    notes_provider, notes_model = resolve_stage_provider_and_model(
        args.notes_provider, args.notes_model, args.provider, args.model
    )
    fuse_provider, fuse_model = resolve_stage_provider_and_model(
        args.fuse_provider,
        args.fuse_model,
        args.notes_provider or args.provider,
        notes_model,
    )
    website_provider, website_model = resolve_stage_provider_and_model(
        args.website_provider, args.website_model, args.provider, args.model
    )
    ellara_provider, ellara_model = resolve_stage_provider_and_model(
        args.ellara_provider, args.ellara_model, args.provider, args.model
    )

    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    if args.primary != "gemini" and args.primary not in engines:
        engines.insert(0, args.primary)
    reference_engine = args.primary
    second_engine = next((e for e in engines if e != args.primary), None)

    selected = list(STAGES)
    if args.from_stage:
        selected = STAGES[STAGES.index(args.from_stage):]
    if args.only:
        selected = [s for s in STAGES if s in args.only]
    if args.stop_after:
        selected = [s for s in selected if STAGES.index(s) <= STAGES.index(args.stop_after)]
    if args.sandbox:
        selected = [s for s in selected if s not in {"entities", "website", "ellara-state", "verify", "publish"}]

    if args.dry_run:
        plan = {
            "session": session,
            "dnd_dir": str(dnd_dir),
            "ellara_dir": str(ellara_dir),
            "audio_dir": str(audio_dir),
            "work_dir": str(work),
            "python": str(python_bin),
            "engines": engines,
            "primary": args.primary,
            "gemini": {"mode": args.gemini, "model": args.gemini_model},
            "providers": {
                "fuse": {"provider": fuse_provider, "model": fuse_model},
                "notes": {"provider": notes_provider, "model": notes_model},
                "website": {"provider": website_provider, "model": website_model},
                "ellara_state": {"provider": ellara_provider, "model": ellara_model, "enabled": not args.no_ellara},
            },
            "stages": selected,
            "publish": args.publish,
            "push": args.push,
        }
        print(json.dumps(plan, indent=2))
        return 0

    work.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"session": session, "stages": {}}
    env = pipeline_paths.no_bytecode_env()

    def run(cmd: list[object], cwd: Path = dnd_dir, check: bool = True, python: bool = False) -> int:
        argv_cmd = [str(c) for c in cmd]
        if python or argv_cmd[0].endswith(".py"):
            argv_cmd = [str(python_bin), "-B"] + argv_cmd
        log("$ " + " ".join(argv_cmd))
        code = subprocess.run(argv_cmd, cwd=str(cwd), env=env, check=False).returncode
        if check and code != 0:
            raise RuntimeError(f"command failed ({code}): {' '.join(argv_cmd)}")
        return code

    def done(stage: str) -> bool:
        return (
            manifest["stages"].get(stage, {}).get("status") == "done"
            and not args.force
            and not args.only
            and not args.from_stage
        )

    def mark(stage: str, status: str = "done", **info) -> None:
        manifest["stages"][stage] = {
            "status": status,
            "finished": datetime.now().isoformat(timespec="seconds"),
            **info,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def assemble(dice: Path | None = None) -> None:
        engine_dir = asr_dir / args.primary
        cmd: list[object] = [SCRIPT_DIR / "assemble_transcript.py", engine_dir, transcript, "--lines-jsonl", lines_jsonl]
        if dice and dice.exists() and dice.stat().st_size:
            cmd += ["--dice", dice]
        run(cmd, python=True)
        snapshot_pre_fuse(transcript, lines_jsonl, pre_fuse_txt, pre_fuse_jsonl)

    notes_ran_this_invocation = False
    log(f"session {session}: stages {selected}")
    for stage in selected:
        if done(stage):
            log(f"{stage}: already done, skipping")
            continue
        log(f"== {stage}")

        try:
            if stage == "entities":
                run(["npm", "run", "generate-list"])
                mark(stage)

            elif stage == "asr":
                cmd = [SCRIPT_DIR / "run_asr_engines.py", "--audio-dir", audio_dir, "--session", session, "--engines", ",".join(engines)]
                if args.force:
                    cmd.append("--force")
                run(cmd, python=True)
                mark(stage, engines=engines, dir=str(asr_dir))

            elif stage == "gemini":
                if args.gemini == "off":
                    log("gemini: disabled (--gemini off)")
                    mark(stage, status="skipped", reason="--gemini off")
                    continue
                if not shutil.which("agy"):
                    log("gemini: agy CLI not found; skipping")
                    mark(stage, status="skipped", reason="agy CLI not found")
                    continue
                cmd = [
                    SCRIPT_DIR / "asr_gemini_windows.py",
                    "--reference-dir", asr_dir / reference_engine,
                    "--out-dir", asr_dir / "gemini",
                    "--session", session,
                    "--model", args.gemini_model,
                ]
                if args.gemini == "disputed" and second_engine:
                    cmd += ["--select", "disputed", "--alt-dir", asr_dir / second_engine]
                else:
                    cmd += ["--select", "all"]
                if run(cmd, python=True, check=False) != 0:
                    log("gemini: failed; fusion will use the other engines only")
                    mark(stage, status="failed", reason="asr_gemini_windows.py exited non-zero")
                    continue
                mark(stage, select=args.gemini, model=args.gemini_model)

            elif stage == "transcript":
                assemble()
                mark(stage, transcript=str(transcript), primary=args.primary)

            elif stage == "dice":
                if not ddb_configured(dnd_dir):
                    log("dice: DDB_COBALT_SESSION / DDB_CAMPAIGN_ID not configured; skipping")
                    mark(stage, status="skipped", reason="DDB credentials not configured")
                    continue
                ddb_dir = audio_dir / "ddb"
                fetched = run([SCRIPT_DIR / "ddb_rolls.py", "fetch", "--out-dir", ddb_dir], python=True, check=False)
                if fetched != 0:
                    log("dice: fetch failed; continuing without dice")
                    mark(stage, status="failed", reason="ddb_rolls fetch failed")
                    continue
                aligned = ddb_dir / "rolls_aligned.jsonl"
                code = run(
                    [
                        SCRIPT_DIR / "ddb_rolls.py", "align",
                        ddb_dir / "rolls.jsonl", lines_jsonl,
                        "--out", aligned, "--report", ddb_dir / "alignment.json",
                    ],
                    python=True,
                    check=False,
                )
                if code == 0:
                    assemble(aligned)
                    mark(stage, aligned=str(aligned))
                else:
                    log("dice: alignment not confident; transcript left without DICE lines")
                    mark(stage, status="failed", aligned=None, reason="alignment not confident")

            elif stage == "fuse":
                if args.no_fuse:
                    log("fuse: disabled (--no-fuse)")
                    mark(stage, status="skipped", reason="--no-fuse")
                    continue
                prepare_fuse_input(transcript, lines_jsonl, pre_fuse_txt, pre_fuse_jsonl)
                alts = [e for e in engines if e != args.primary and (asr_dir / e).exists()]
                if args.gemini != "off" and (asr_dir / "gemini").exists():
                    alts.append("gemini")
                cmd = [
                    SCRIPT_DIR / "fuse_transcript.py",
                    lines_jsonl,
                    "--session", session,
                    "--provider", fuse_provider,
                    "--primary-label", "Gladia" if args.primary == "gladia" else args.primary,
                    "--report", fusion_report,
                ]
                for alt in alts:
                    cmd += ["--alt-dir", asr_dir / alt]
                if fuse_model:
                    cmd += ["--model", fuse_model]
                run(cmd, python=True)
                mark(stage, alt_engines=alts, provider=fuse_provider, model=fuse_model, report=str(fusion_report))

            elif stage == "diagnostics":
                available = (
                    [p.name for p in asr_dir.iterdir() if p.is_dir() and any(p.glob("*.json"))]
                    if asr_dir.exists()
                    else []
                )
                if len(available) < 2:
                    log("diagnostics: need at least two engines; skipping")
                    mark(stage, status="skipped", reason="fewer than 2 engines available")
                    continue
                cmd = [
                    SCRIPT_DIR / "asr_diagnostics.py",
                    "--work-dir", asr_dir,
                    "--session", session,
                    "--primary", args.primary,
                    "--out-md", diagnostics_report,
                ]
                if args.judge:
                    cmd += ["--judge", "agy"]
                diag_code = run(cmd, python=True, check=False)
                mark(stage, status="done" if diag_code == 0 else "failed", report=str(diagnostics_report))

            elif stage == "raw-notes":
                cmd = [
                    SCRIPT_DIR / "raw_notes_auto.py",
                    "--session", session,
                    "--transcript", transcript,
                    "--out", raw_notes,
                    "--work-dir", work / "raw_notes",
                    "--provider", notes_provider,
                ]
                if notes_model:
                    cmd += ["--model", notes_model]
                if args.force:
                    cmd.append("--force")
                run(cmd, python=True)
                val_code = run([SCRIPT_DIR / "validate_raw_notes.py", raw_notes, "--session", session], python=True, check=False)
                mark(stage, raw_notes=str(raw_notes), raw_validation_exit=val_code)

            elif stage == "audit":
                if args.no_audit:
                    log("audit: disabled (--no-audit)")
                    mark(stage, status="skipped", reason="--no-audit")
                    continue
                audit_script = SCRIPT_DIR / "audit_raw_notes.py"
                cmd = [
                    audit_script,
                    "--session", session,
                    "--transcript", transcript,
                    "--notes", raw_notes,
                    "--work-dir", work / "raw_notes",
                    "--provider", notes_provider,
                    "--fix",
                ]
                if script_accepts_flag(audit_script, "--report"):
                    cmd += ["--report", audit_report]
                if notes_model:
                    cmd += ["--model", notes_model]
                run(cmd, python=True)
                # Keep Ellara/Session Notes clean even if an older audit script wrote beside raw_notes.
                legacy_audit = raw_notes.with_name(raw_notes.stem + " - Audit.md")
                if legacy_audit.is_file() and legacy_audit.resolve() != audit_report.resolve():
                    shutil.move(str(legacy_audit), str(audit_report))
                val_code = run([SCRIPT_DIR / "validate_raw_notes.py", raw_notes, "--session", session], python=True, check=False)
                mark(stage, report=str(audit_report), raw_validation_exit=val_code)

            elif stage == "notes":
                cmd = [
                    SCRIPT_DIR / "run_session_notes_agent.py",
                    session,
                    raw_notes,
                    session_notes,
                    "--provider", notes_provider,
                    "--workspace-root", str(dnd_dir.parent),
                    "--force",
                ]
                if notes_model:
                    cmd += ["--model", notes_model]
                run(cmd, python=True)
                notes_ran_this_invocation = True
                mark(stage, session_notes=str(session_notes), provider=notes_provider, model=notes_model)

            elif stage == "website":
                facts_path = work / "session_facts.json"
                facts_cmd: list[object] = [
                    SCRIPT_DIR / "session_facts.py",
                    "--audio-dir", audio_dir,
                    "--transcript", transcript,
                    "--out", facts_path,
                    "--provider", notes_provider,
                ]
                if notes_model:
                    facts_cmd += ["--model", notes_model]
                if args.session_date:
                    facts_cmd += ["--session-date", args.session_date]
                run(facts_cmd, python=True, check=False)
                facts = json.loads(facts_path.read_text(encoding="utf-8")) if facts_path.exists() else {}
                cmd = [
                    SCRIPT_DIR / "run_website_sync_agent.py",
                    "--session", session,
                    "--dnd-dir", dnd_dir,
                    "--ellara-root", ellara_dir,
                    "--provider", website_provider,
                ]
                if notes_ran_this_invocation or args.force:
                    cmd += ["--prefer", "ellara"]
                if facts.get("session_date"):
                    cmd += ["--session-date", facts["session_date"]]
                if facts.get("next_session_date"):
                    cmd += ["--next-session-date", facts["next_session_date"]]
                if website_model:
                    cmd += ["--model", website_model]
                run(cmd, python=True)
                mark(stage, website=str(website_md), provider=website_provider, model=website_model)

            elif stage == "ellara-state":
                if args.no_ellara:
                    log("ellara-state: disabled (--no-ellara)")
                    mark(stage, status="skipped", reason="--no-ellara")
                    continue
                cmd = [
                    SCRIPT_DIR / "run_ellara_analysis_agent.py",
                    "--session", session,
                    "--dnd-dir", dnd_dir,
                    "--ellara-root", ellara_dir,
                    "--provider", ellara_provider,
                    "--brief-out", prep_brief_path,
                ]
                if ellara_model:
                    cmd += ["--model", ellara_model]
                if args.no_ellara_audit:
                    cmd.append("--no-audit")
                if args.force:
                    cmd.append("--force")
                run(cmd, python=True)
                mark(stage, provider=ellara_provider, model=ellara_model, brief=str(prep_brief_path))

            elif stage == "verify":
                pipeline_cmd: list[object] = [
                    SCRIPT_DIR / "validate_session_pipeline.py",
                    "--session", session,
                    "--dnd-dir", dnd_dir,
                    "--ellara-root", ellara_dir,
                ]
                if args.no_ellara:
                    pipeline_cmd.append("--skip-ellara-state")
                results: dict[str, int] = {
                    "raw_notes": run([SCRIPT_DIR / "validate_raw_notes.py", raw_notes, "--session", session], python=True, check=False),
                    "sync_check": run(["npm", "run", "sync-check"], cwd=dnd_dir, check=False),
                    "pipeline": run(pipeline_cmd, python=True, check=False),
                }
                if not args.no_ellara:
                    delta_script = ellara_dir / ".agents" / "skills" / "ellara-session-analysis" / "scripts" / "check_session_delta.py"
                    results["ellara_state"] = run(
                        [
                            delta_script,
                            "--ellara-root", ellara_dir,
                            "--dnd-root", dnd_dir,
                            "--validate",
                            "--session", session,
                        ],
                        python=True,
                        check=False,
                    )
                log(f"verify results (0 = ok): {results}")
                failed = [name for name, code in results.items() if code != 0]
                if failed:
                    mark(stage, status="failed", results=results, failed=failed)
                    raise SystemExit(f"verify stage failed ({', '.join(failed)}); see output above")
                mark(stage, status="done", results=results)

            elif stage == "publish":
                if not args.publish:
                    log("publish: not requested (--publish); leaving changes uncommitted")
                    mark(stage, status="skipped", reason="--publish not set")
                    continue
                verify_status = manifest["stages"].get("verify", {}).get("status")
                if verify_status != "done" and not args.force:
                    mark(stage, status="failed", reason="verify stage has not passed")
                    raise SystemExit("publish aborted: verify stage must pass before publishing (or pass --force)")
                for repo in (ellara_dir, dnd_dir):
                    if run(["git", "-C", repo, "rev-parse", "--git-dir"], cwd=repo, check=False) != 0:
                        mark(stage, status="failed", reason=f"not a git repo: {repo}")
                        raise SystemExit(f"publish aborted: not a git repository: {repo}")

                ellara_files, dnd_files = collect_publish_files(
                    session,
                    dnd_dir,
                    ellara_dir,
                    include_ellara_state=not args.no_ellara,
                )
                ellara_committed = git_stage_and_commit(
                    ellara_dir,
                    ellara_files,
                    f"Publish Session {session} notes and campaign state",
                    run,
                )
                dnd_committed = git_stage_and_commit(
                    dnd_dir,
                    dnd_files,
                    f"Publish Session {session}",
                    run,
                )
                if args.push:
                    run(["git", "-C", ellara_dir, "push", "origin", "HEAD"], cwd=ellara_dir, check=True)
                    run(["git", "-C", dnd_dir, "push", "origin", "HEAD"], cwd=dnd_dir, check=True)
                mark(
                    stage,
                    pushed=args.push,
                    ellara_committed=ellara_committed,
                    dnd_committed=dnd_committed,
                )
        except Exception as exc:
            if manifest["stages"].get(stage, {}).get("status") != "failed":
                mark(stage, status="failed", error=str(exc))
            raise

        if args.stop_after == stage:
            break

    log("finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
