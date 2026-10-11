#!/usr/bin/env python3
"""Fully automatic session pipeline: speaker audio -> transcript -> notes -> website.

No human checkpoints. Each stage records its outputs in
`<audio-dir>/pipeline/manifest.json`; reruns skip finished stages unless
--from-stage/--only/--force say otherwise.

Stages (in order):
    entities     regenerate ENTITY_LIST.md + entity_metadata.json (ASR vocabulary)
    asr          run ASR engines per speaker track (raw provider JSON is kept)
    gemini       Gemini (agy) listens to the lines the engines disagree on (extra reading)
    transcript   assemble the chronological transcript from the primary engine
    dice         optional: fetch D&D Beyond rolls, align to audio, re-assemble with DICE lines
    fuse         LLM judge picks/combines the engines' readings per line, in context
    diagnostics  compare engines (coverage, agreement, names, loops; optional audio judge)
    raw-notes    scene-based Raw Session N.md
    notes        polished Session N.md
    website      copy into the site, update stores/views via agent, regenerate entity list
    verify       raw-note validation, npm run sync-check, pipeline validation
    publish      only with --publish: commit Ellara notes + dnd site changes (no push unless --push)

Typical runs:
    # everything, Gladia primary, Whisper as a free second opinion for diagnostics
    python3 scripts/transcription/run_session_auto.py --session 21 --audio-dir ~/source/session-21

    # cheap/free: local Whisper only
    python3 scripts/transcription/run_session_auto.py --session 21 --audio-dir ... \
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
DND_DIR = SCRIPT_DIR.parent.parent
ELLARA_DIR = Path("/home/babu/source/ellara")
NOTES_DIR = ELLARA_DIR / "Session Notes"
TRANSCRIPTS_DIR = NOTES_DIR / "Transcripts"
VENV_PYTHON = Path("~/.gemini/tmp/transcribe_env/bin/python3").expanduser()

STAGES = ["entities", "asr", "gemini", "transcript", "dice", "fuse", "diagnostics", "raw-notes", "notes", "website", "verify", "publish"]


def log(msg: str) -> None:
    print(f"[auto {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], cwd: Path = DND_DIR, check: bool = True, python: bool = False) -> int:
    if python or str(cmd[0]).endswith(".py"):
        cmd = [str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable)] + cmd
    log("$ " + " ".join(str(c) for c in cmd))
    code = subprocess.run([str(c) for c in cmd], cwd=str(cwd), check=False).returncode
    if check and code != 0:
        raise RuntimeError(f"command failed ({code}): {' '.join(str(c) for c in cmd)}")
    return code


def ddb_configured() -> bool:
    env_file = DND_DIR / ".env.local"
    keys = set(os.environ)
    if env_file.exists():
        keys |= {l.split("=", 1)[0].strip() for l in env_file.read_text().splitlines() if "=" in l}
    return {"DDB_COBALT_SESSION", "DDB_CAMPAIGN_ID"} <= keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", required=True)
    parser.add_argument("--audio-dir", required=True)
    parser.add_argument("--engines", default="gladia,whisper-large-v3", help="ASR engines to run")
    parser.add_argument("--primary", default="gladia", help="Engine whose output becomes the transcript (gladia, whisper-*, gemini)")
    parser.add_argument("--gemini", choices=["off", "disputed", "all"], default="disputed",
                        help="Gemini (agy) as an extra reading: only lines the engines disagree on (default), every line, or off")
    parser.add_argument("--gemini-model", default="gemini-3.8-flash-low")
    parser.add_argument("--fuse-provider", help="Judge for the fusion stage (default: --provider); e.g. claude")
    parser.add_argument("--judge", action="store_true", help="Diagnostics: let Gemini listen to disagreement clips")
    parser.add_argument("--no-fuse", action="store_true", help="Skip the LLM transcript proofreading stage")
    parser.add_argument("--provider", default="codex", help="Agent CLI for notes/website (codex or claude)")
    parser.add_argument("--model")
    parser.add_argument("--notes-provider", help="Override provider for raw + polished notes")
    parser.add_argument("--website-provider", help="Override provider for the website agent")
    parser.add_argument("--from-stage", choices=STAGES)
    parser.add_argument("--only", choices=STAGES, action="append")
    parser.add_argument("--stop-after", choices=STAGES)
    parser.add_argument("--force", action="store_true", help="Redo stages even if outputs exist")
    parser.add_argument("--publish", action="store_true", help="Commit Ellara notes and dnd site changes")
    parser.add_argument("--push", action="store_true", help="With --publish, also push both repos")
    parser.add_argument("--sandbox", help="Write transcripts/notes here instead of Ellara; never touches the dnd site (website/publish skipped)")
    args = parser.parse_args()

    session = str(args.session)
    audio_dir = Path(args.audio_dir).expanduser().resolve()
    work = audio_dir / "pipeline"
    asr_dir = audio_dir / "asr"
    work.mkdir(parents=True, exist_ok=True)
    manifest_path = work / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"session": session, "stages": {}}

    notes_dir, transcripts_dir = NOTES_DIR, TRANSCRIPTS_DIR
    if args.sandbox:
        notes_dir = Path(args.sandbox).expanduser().resolve()
        transcripts_dir = notes_dir / "Transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        work = notes_dir / "pipeline"
        work.mkdir(parents=True, exist_ok=True)
        manifest_path = work / "manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"session": session, "stages": {}}
    transcript = transcripts_dir / f"Transcript Session {session}.txt"
    lines_jsonl = transcripts_dir / f"Transcript Session {session}.lines.jsonl"
    raw_notes = notes_dir / f"Raw Session {session}.md"
    session_notes = notes_dir / f"Session {session}.md"
    website_md = DND_DIR / "src" / "assets" / "sessions" / f"session-{session}.md"
    dnd_raw_copy = DND_DIR / "src" / "assets" / "sessions" / "transcripts" / f"session_{session}_raw.txt"
    notes_provider = args.notes_provider or args.provider
    website_provider = args.website_provider or args.provider
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

    def done(stage: str) -> bool:
        return manifest["stages"].get(stage, {}).get("status") == "done" and not args.force and not args.only and not args.from_stage

    def mark(stage: str, **info) -> None:
        manifest["stages"][stage] = {"status": "done", "finished": datetime.now().isoformat(timespec="seconds"), **info}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def assemble(dice: Path | None = None) -> None:
        engine_dir = asr_dir / args.primary
        cmd = [SCRIPT_DIR / "assemble_transcript.py", engine_dir, transcript, "--lines-jsonl", lines_jsonl]
        if dice and dice.exists() and dice.stat().st_size:
            cmd += ["--dice", dice]
        run(cmd, python=True)
        if not args.sandbox:
            dnd_raw_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(transcript, dnd_raw_copy)

    if args.sandbox:
        selected = [s for s in selected if s not in {"entities", "website", "verify", "publish"}]
    log(f"session {session}: stages {selected}")
    for stage in selected:
        if done(stage):
            log(f"{stage}: already done, skipping")
            continue
        log(f"== {stage}")

        if stage == "entities":
            run(["npm", "run", "generate-list"])
            mark(stage)

        elif stage == "asr":
            cmd = [SCRIPT_DIR / "run_asr_engines.py", "--audio-dir", audio_dir, "--session", session, "--engines", ",".join(engines)]
            if args.force:
                cmd.append("--force")
            run(cmd)
            mark(stage, engines=engines, dir=str(asr_dir))

        elif stage == "gemini":
            if args.gemini == "off":
                log("gemini: disabled (--gemini off)")
                continue
            if not shutil.which("agy"):
                log("gemini: agy CLI not found; skipping")
                continue
            cmd = [SCRIPT_DIR / "asr_gemini_windows.py", "--reference-dir", asr_dir / reference_engine,
                   "--out-dir", asr_dir / "gemini", "--session", session, "--model", args.gemini_model]
            if args.gemini == "disputed" and second_engine:
                cmd += ["--select", "disputed", "--alt-dir", asr_dir / second_engine]
            else:
                cmd += ["--select", "all"]
            if run(cmd, python=True, check=False) != 0:
                log("gemini: failed; fusion will use the other engines only")
                continue
            mark(stage, select=args.gemini)

        elif stage == "transcript":
            assemble()
            mark(stage, transcript=str(transcript), primary=args.primary)

        elif stage == "dice":
            if not ddb_configured():
                log("dice: DDB_COBALT_SESSION / DDB_CAMPAIGN_ID not in .env.local; skipping")
                continue
            ddb_dir = audio_dir / "ddb"
            fetched = run([SCRIPT_DIR / "ddb_rolls.py", "fetch", "--out-dir", ddb_dir], check=False)
            if fetched != 0:
                log("dice: fetch failed; continuing without dice")
                continue
            aligned = ddb_dir / "rolls_aligned.jsonl"
            code = run([SCRIPT_DIR / "ddb_rolls.py", "align", ddb_dir / "rolls.jsonl", lines_jsonl,
                        "--out", aligned, "--report", ddb_dir / "alignment.json"], check=False)
            if code == 0:
                assemble(aligned)
                mark(stage, aligned=str(aligned))
            else:
                log("dice: alignment not confident; transcript left without DICE lines")
                mark(stage, aligned=None)

        elif stage == "fuse":
            if args.no_fuse:
                log("fuse: disabled (--no-fuse)")
                continue
            alts = [e for e in engines if e != args.primary and (asr_dir / e).exists()]
            if args.gemini != "off" and (asr_dir / "gemini").exists():
                alts.append("gemini")
            cmd = [SCRIPT_DIR / "fuse_transcript.py", lines_jsonl, "--session", session,
                   "--provider", args.fuse_provider or notes_provider,
                   "--primary-label", "Gladia" if args.primary == "gladia" else args.primary,
                   "--report", transcripts_dir / f"Transcript Session {session} - Fusion Report.md"]
            for alt in alts:
                cmd += ["--alt-dir", asr_dir / alt]
            if args.model and not args.fuse_provider:
                cmd += ["--model", args.model]
            run(cmd, python=True)
            if not args.sandbox:
                shutil.copy2(transcript, dnd_raw_copy)
            mark(stage, alt_engines=alts)

        elif stage == "diagnostics":
            available = [p.name for p in asr_dir.iterdir() if p.is_dir() and any(p.glob("*.json"))] if asr_dir.exists() else []
            if len(available) < 2:
                log("diagnostics: need at least two engines; skipping")
                continue
            cmd = [SCRIPT_DIR / "asr_diagnostics.py", "--work-dir", asr_dir, "--session", session, "--primary", args.primary,
                   "--out-md", transcripts_dir / f"Transcript Session {session} - ASR Diagnostics.md"]
            if args.judge:
                cmd += ["--judge", "agy"]
            run(cmd, python=True, check=False)
            mark(stage)

        elif stage == "raw-notes":
            cmd = [SCRIPT_DIR / "raw_notes_auto.py", "--session", session, "--transcript", transcript,
                   "--out", raw_notes, "--work-dir", work / "raw_notes", "--provider", notes_provider]
            if args.model:
                cmd += ["--model", args.model]
            if args.force:
                cmd.append("--force")
            run(cmd, python=True)
            run([SCRIPT_DIR / "validate_raw_notes.py", raw_notes, "--session", session], check=False)
            mark(stage, raw_notes=str(raw_notes))

        elif stage == "notes":
            cmd = [SCRIPT_DIR / "run_session_notes_agent.py", session, raw_notes, session_notes,
                   "--provider", notes_provider, "--force", "--skip-raw-validation"]
            if args.model:
                cmd += ["--model", args.model]
            run(cmd, python=True)
            mark(stage, session_notes=str(session_notes))

        elif stage == "website":
            cmd = [SCRIPT_DIR / "run_website_sync_agent.py", "--session", session, "--provider", website_provider]
            if args.model:
                cmd += ["--model", args.model]
            run(cmd, python=True)
            run(["npm", "run", "generate-list"])
            mark(stage, website=str(website_md))

        elif stage == "verify":
            results = {
                "raw_notes": run([SCRIPT_DIR / "validate_raw_notes.py", raw_notes, "--session", session], check=False),
                "sync_check": run(["npm", "run", "sync-check"], check=False),
                "pipeline": run([SCRIPT_DIR / "validate_session_pipeline.py", "--session", session], check=False),
            }
            log(f"verify results (0 = ok): {results}")
            mark(stage, results=results)
            if results["sync_check"] != 0:
                raise SystemExit("website build/sync check failed; see output above")

        elif stage == "publish":
            if not args.publish:
                log("publish: not requested (--publish); leaving changes uncommitted")
                continue
            run(["git", "-C", ELLARA_DIR, "add", raw_notes, session_notes], cwd=ELLARA_DIR)
            run(["git", "-C", ELLARA_DIR, "commit", "-m", f"Publish Session {session} notes"], cwd=ELLARA_DIR, check=False)
            run(["git", "add", "src", "ENTITY_LIST.md", "scripts/transcription/entity_metadata.json"])
            run(["git", "commit", "-m", f"Publish Session {session}"], check=False)
            if args.push:
                run(["git", "-C", ELLARA_DIR, "push", "origin", "HEAD"], cwd=ELLARA_DIR)
                run(["git", "push", "origin", "HEAD"])
            mark(stage, pushed=args.push)

        if args.stop_after == stage:
            break

    log("finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
