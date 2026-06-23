#!/usr/bin/env python3
"""
Run an end-to-end DnD transcript pipeline from speaker-isolated audio files.

Pipeline:
1. Regenerate ENTITY_LIST.md (used for ASR prompting/custom vocabulary).
2. Transcribe per-speaker audio with retries and model fallback.
3. Combine per-speaker transcripts into one chronological transcript.
4. Apply name/speaker corrections and optional speaker display normalization.
5. Copy final files into DnD assets and Ellara transcript folders.
6. Produce legacy linewise OOC outputs and optionally annotation-first OOC cleanup.
7. Prepare overlapping raw-session-note chunks for subagents/LLM passes.
8. Optionally reconcile, promote, and validate Raw Session N markdown.
9. Optionally generate polished Session N markdown and sync website state.
10. Optionally clean scratch artifacts and validate durable outputs.
11. Write a manifest JSON listing all generated artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path


AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".ogg", ".aac"}
DEFAULT_TRANSCRIPTION_PROVIDER = "gladia"
LINE_RE = re.compile(r"^(\[\d{2}:\d{2}:\d{2}\]\s+)([^:]+)(:\s*)(.*)$")


def log(msg: str) -> None:
    print(msg, flush=True)


def run_cmd(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    location = f" (cwd={cwd})" if cwd else ""
    log(f"$ {' '.join(cmd)}{location}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


def load_env_file(path: Path, env: dict[str, str]) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in env:
            env[key] = value


def list_audio_files(audio_dir: Path) -> list[Path]:
    files = [
        p for p in sorted(audio_dir.iterdir())
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return files


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def is_good_transcript(path: Path, min_lines: int) -> bool:
    return path.exists() and path.stat().st_size > 0 and count_lines(path) >= min_lines


def build_whisper_attempt_plan(raw_models: str) -> list[str]:
    models = [m.strip() for m in raw_models.split(",") if m.strip()]
    if not models:
        raise ValueError("at least one model must be provided in --attempt-models")
    return models


def make_smart_replacement(wrong: str, right: str):
    right_has_possessive = right.endswith("'s") or right.endswith("s'")

    def replacer(match: re.Match[str]) -> str:
        matched_base = match.group(1)
        possessive = match.group(2)

        # Preserve capitalization style
        if matched_base.isupper():
            res = right.upper()
        elif matched_base[0].isupper() if matched_base else False:
            if right:
                res = right[0].upper() + right[1:]
            else:
                res = right
        else:
            res = right

        if possessive:
            if not right_has_possessive:
                res = f"{res}{possessive}"
        return res
    return replacer


def load_name_corrections(path: Path) -> tuple[list[tuple[re.Pattern[str], any]], dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    text_fixes = data.get("text_fixes", {})
    speaker_fixes = data.get("speaker_label_fixes", {})

    patterns = []
    for wrong in sorted(text_fixes.keys(), key=len, reverse=True):
        right = text_fixes[wrong]
        pattern = re.compile(
            rf"(?<!\w)({re.escape(wrong)})((?:'s|s)?)(?!\w)",
            re.IGNORECASE
        )
        replacer = make_smart_replacement(wrong, right)
        patterns.append((pattern, replacer))
    return patterns, speaker_fixes


def apply_line_corrections(
    line: str,
    text_patterns: list[tuple[re.Pattern[str], any]],
    speaker_fixes: dict[str, str],
    keep_full_whitaker_name: bool,
) -> str:
    m = LINE_RE.match(line)
    if not m:
        return line

    prefix, speaker, colon, text = m.groups()
    speaker = speaker_fixes.get(speaker, speaker)
    if not keep_full_whitaker_name and speaker == 'Whitaker "Witty" Whitman VI':
        speaker = "Witty"

    for pat, replacement in text_patterns:
        text = pat.sub(replacement, text)

    return f"{prefix}{speaker}{colon}{text}"



def normalize_transcript(
    source: Path,
    dest: Path,
    text_patterns: list[tuple[re.Pattern[str], str]],
    speaker_fixes: dict[str, str],
    keep_full_whitaker_name: bool,
) -> None:
    out_lines = []
    with source.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            out_lines.append(
                apply_line_corrections(
                    line=line,
                    text_patterns=text_patterns,
                    speaker_fixes=speaker_fixes,
                    keep_full_whitaker_name=keep_full_whitaker_name,
                )
            )

    dest.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def transcribe_one(
    audio_file: Path,
    py_bin: Path,
    dnd_dir: Path,
    env_base: dict[str, str],
    models: list[str],
    beam_size: int,
    min_lines: int,
    provider: str,
    gladia_artifact_dir: Path | None,
) -> Path:
    output_file = Path(f"{audio_file}.txt")
    tmp_output = Path(f"{audio_file}.txt.tmp")
    file_log = Path(f"{audio_file}.transcribe.log")

    if provider == "gladia":
        artifact_dir = gladia_artifact_dir or audio_file.parent / ".gladia"
        log(f"{audio_file.name}: transcribing with Gladia after local VAD compaction")
        with file_log.open("w", encoding="utf-8") as lf:
            result = subprocess.run(
                [
                    str(py_bin),
                    "-u",
                    "scripts/transcription/transcribe_gladia.py",
                    str(audio_file),
                    str(tmp_output),
                    "--dnd-dir",
                    str(dnd_dir),
                    "--artifact-dir",
                    str(artifact_dir / audio_file.name),
                ],
                cwd=str(dnd_dir),
                env=env_base,
                stdout=lf,
                stderr=subprocess.STDOUT,
                check=False,
            )

        if result.returncode == 0 and is_good_transcript(tmp_output, min_lines):
            tmp_output.replace(output_file)
            log(f"{audio_file.name}: success ({count_lines(output_file)} lines)")
            return output_file

        if tmp_output.exists():
            tmp_output.unlink()
        raise RuntimeError(f"Gladia transcription failed for {audio_file}; see {file_log}")

    for attempt, model in enumerate(models, start=1):
        log(f"{audio_file.name}: attempt {attempt}/{len(models)} model={model}")

        env = dict(env_base)
        env["WHISPER_MODEL_SIZE"] = model
        env["WHISPER_DEVICE"] = env.get("WHISPER_DEVICE", "cuda")
        env["WHISPER_COMPUTE_TYPE"] = env.get("WHISPER_COMPUTE_TYPE", "float16")
        env["WHISPER_BEAM_SIZE"] = str(beam_size)

        with file_log.open("w", encoding="utf-8") as lf:
            result = subprocess.run(
                [str(py_bin), "-u", "scripts/transcription/transcribe.py", str(audio_file), str(tmp_output)],
                cwd=str(dnd_dir),
                env=env,
                stdout=lf,
                stderr=subprocess.STDOUT,
                check=False,
            )

        if result.returncode == 0 and is_good_transcript(tmp_output, min_lines):
            tmp_output.replace(output_file)
            log(f"{audio_file.name}: success ({count_lines(output_file)} lines)")
            return output_file

        if tmp_output.exists():
            tmp_output.unlink()
        log(f"{audio_file.name}: retrying after failed/short transcript")
        time.sleep(2)

    raise RuntimeError(f"transcription failed after {len(models)} attempts: {audio_file}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--session", required=True, help="Session number or label (e.g. 15)")
    parser.add_argument("--audio-dir", required=True, help="Directory with per-speaker audio files")
    parser.add_argument("--dnd-dir", default="/home/babu/source/dnd", help="Path to dnd repo root")
    parser.add_argument(
        "--ellara-dir",
        default="/home/babu/source/ellara/Session Notes/Transcripts",
        help="Path to Ellara transcript output directory",
    )
    parser.add_argument("--venv-path", default="~/.gemini/tmp/transcribe_env", help="Whisper venv root")
    parser.add_argument(
        "--attempt-models",
        default="large-v3,large-v3,medium,medium,small,small",
        help="Comma-separated retry model sequence",
    )
    parser.add_argument("--beam-size", type=int, default=1, help="Whisper beam size")
    parser.add_argument("--min-lines", type=int, default=20, help="Minimum lines for a valid per-speaker transcript")
    parser.add_argument(
        "--transcription-provider",
        choices=["gladia", "whisper"],
        default=DEFAULT_TRANSCRIPTION_PROVIDER,
        help="Speech-to-text provider; use whisper only for an explicit local fallback",
    )
    parser.add_argument("--gladia-artifact-dir", help="Directory for Gladia compact audio, manifests, and API JSON")
    parser.add_argument("--skip-transcribe", action="store_true", help="Skip transcription and reuse existing *.ext.txt files")
    parser.add_argument("--stop-after-transcript", action="store_true", help="Stop after writing normalized transcript artifacts for manual review")
    parser.add_argument("--resume-after-transcript", action="store_true", help="Resume from an existing Ellara transcript without rebuilding per-speaker/combined transcripts")
    parser.add_argument("--clean", action="store_true", help="Delete existing per-speaker transcript files before transcribing")
    parser.add_argument("--skip-ooc", action="store_true", help="Skip OOC and ambiguous output generation")
    parser.add_argument("--run-ooc-annotation-provider", choices=["codex", "gemini"], help="Dispatch annotation-first OOC cleanup through the selected agent CLI")
    parser.add_argument("--ooc-annotation-model", help="Optional model override for annotation-first OOC cleanup")
    parser.add_argument("--ooc-annotation-chunk-size", type=int, default=80, help="Editable transcript lines per OOC annotation chunk")
    parser.add_argument("--ooc-annotation-overlap", type=int, default=8, help="Context lines before/after each OOC annotation chunk")
    parser.add_argument("--ooc-annotation-force", action="store_true", help="Overwrite existing OOC annotation JSONL outputs")
    parser.add_argument("--ooc-annotation-dry-run", action="store_true", help="Show planned OOC annotation dispatches without invoking the provider")
    parser.add_argument("--ooc-annotation-allow-missing", action="store_true", help="Allow missing annotation records during apply")
    parser.add_argument("--skip-raw-notes-prep", action="store_true", help="Skip preparing raw-session-note chunks for subagents")
    parser.add_argument("--raw-notes-chunk-size", type=int, default=100, help="Primary transcript entries per raw-notes chunk")
    parser.add_argument("--raw-notes-overlap", type=int, default=12, help="Context entries before/after each raw-notes chunk")
    parser.add_argument(
        "--raw-notes-source-mode",
        choices=["canonical", "annotation", "legacy-ooc", "custom"],
        default="canonical",
        help="Default source for raw-note prep when --raw-notes-source is omitted",
    )
    parser.add_argument(
        "--raw-notes-source",
        help="Override transcript source for raw-note prep, usually the annotation-cleaned transcript candidate",
    )
    parser.add_argument(
        "--raw-notes-output",
        help="Output path for finalized raw-note candidate; defaults to 'Raw Session N Candidate.md'",
    )
    parser.add_argument("--run-raw-notes-provider", choices=["codex", "gemini"], help="Optionally dispatch raw-note chunks through the selected agent CLI")
    parser.add_argument("--raw-notes-model", help="Optional model override for raw-note agent runs")
    parser.add_argument("--raw-notes-limit", type=int, help="Limit how many raw-note chunks to dispatch")
    parser.add_argument("--raw-notes-force", action="store_true", help="Overwrite existing raw-note chunk outputs when dispatching agents")
    parser.add_argument("--raw-notes-dry-run", action="store_true", help="Show planned raw-note agent dispatches without invoking the provider")
    parser.add_argument("--raw-notes-finalize", action="store_true", help="Finalize Raw Session N Candidate.md after raw-note agent dispatch")
    parser.add_argument("--run-raw-notes-reconcile-provider", choices=["codex", "gemini"], help="Reconcile chunk-extracted raw-note candidate through the selected agent CLI")
    parser.add_argument("--raw-notes-reconcile-model", help="Optional model override for raw-note reconciliation")
    parser.add_argument("--raw-notes-reconciled-output", help="Output path for reconciled raw-note candidate; defaults to 'Raw Session N Reconciled Candidate.md'")
    parser.add_argument("--raw-notes-reconcile-force", action="store_true", help="Overwrite existing reconciled raw-note candidate")
    parser.add_argument("--raw-notes-reconcile-dry-run", action="store_true", help="Show planned raw-note reconciliation without invoking the provider")
    parser.add_argument("--promote-raw-notes", action="store_true", help="After reconciliation, copy the reconciled candidate to canonical Raw Session N.md")
    parser.add_argument("--run-session-notes-provider", choices=["codex", "gemini"], help="Optionally generate polished Session N.md through the selected agent CLI")
    parser.add_argument("--session-notes-model", help="Optional model override for polished session-note generation")
    parser.add_argument("--session-notes-force", action="store_true", help="Overwrite existing Session N.md when dispatching the agent")
    parser.add_argument("--session-notes-dry-run", action="store_true", help="Show the planned polished session-note run without invoking the provider")
    parser.add_argument("--skip-raw-notes-validation", action="store_true", help="Skip raw-note validation before polished session-note generation")
    parser.add_argument("--sync-website", action="store_true", help="Copy polished Session N.md into website assets")
    parser.add_argument("--website-sync-provider", choices=["codex", "gemini"], help="Optionally run a website-sync agent after copying the session asset")
    parser.add_argument("--website-sync-model", help="Optional model override for website-sync agent")
    parser.add_argument("--website-sync-dry-run", action="store_true", help="Show website sync actions without writing or invoking an agent")
    parser.add_argument("--cleanup-scratch", action="store_true", help="Remove intermediate artifacts after durable outputs are produced")
    parser.add_argument("--cleanup-include-dnd-transcript-assets", action="store_true", help="Cleanup also removes website raw transcript assets for this session")
    parser.add_argument("--cleanup-include-repo-scratch", action="store_true", help="Cleanup also removes dist, pycache, and local logs")
    parser.add_argument("--validate", action="store_true", help="Run durable session output validation before finishing")
    parser.add_argument("--validate-check-clean", action="store_true", help="Validator warns if intermediate artifacts remain")
    parser.add_argument("--validate-strict-clean", action="store_true", help="Validator errors if intermediate artifacts remain")
    parser.add_argument(
        "--keep-full-whitaker-name",
        action="store_true",
        help='Keep speaker name as \'Whitaker "Witty" Whitman VI\' instead of normalizing to "Witty"',
    )
    args = parser.parse_args()

    if (
        (args.raw_notes_finalize or args.run_raw_notes_reconcile_provider)
        and args.run_session_notes_provider
        and not args.promote_raw_notes
    ):
        raise ValueError(
            "raw-note candidate generation/reconciliation must be reviewed first; "
            "run polished session-note generation after promoting it to Raw Session N.md, "
            "or pass --promote-raw-notes for an approved one-pass run"
        )
    if args.raw_notes_source and args.raw_notes_source_mode != "custom":
        log("Explicit --raw-notes-source provided; treating source mode as custom.")
        args.raw_notes_source_mode = "custom"

    session = str(args.session).strip()
    if not session:
        raise ValueError("--session cannot be empty")

    audio_dir = Path(args.audio_dir).expanduser().resolve()
    dnd_dir = Path(args.dnd_dir).expanduser().resolve()
    ellara_dir = Path(args.ellara_dir).expanduser().resolve()
    venv_path = Path(args.venv_path).expanduser().resolve()
    py_bin = venv_path / "bin" / "python3"
    gladia_artifact_dir = Path(args.gladia_artifact_dir).expanduser().resolve() if args.gladia_artifact_dir else None

    if not audio_dir.is_dir():
        raise FileNotFoundError(f"audio directory not found: {audio_dir}")
    if not dnd_dir.is_dir():
        raise FileNotFoundError(f"dnd directory not found: {dnd_dir}")
    if not py_bin.exists():
        raise FileNotFoundError(f"python executable not found in venv: {py_bin}")

    ellara_dir.mkdir(parents=True, exist_ok=True)
    session_notes_dir = ellara_dir.parent
    session_assets_dir = dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"Session {session}"
    dnd_session_raw = dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"session_{session}_raw.txt"
    ellara_transcript = ellara_dir / f"Transcript Session {session}.txt"
    combined_tmp = audio_dir / f"session-{session}-combined.txt"
    combined_final = audio_dir / f"session-{session}-combined-normalized.txt"
    ooc_removed = ellara_dir / f"Transcript Session {session} - OOC Removed.txt"
    ambiguous = ellara_dir / f"Transcript Session {session} - Ambiguous.txt"
    ooc_report = ellara_dir / f"Transcript Session {session} - OOC Filter Report.txt"
    ooc_annotation_dir = ellara_dir / f"Session {session} OOC Annotation Chunks"
    ooc_annotation_manifest = ooc_annotation_dir / "annotation_manifest.json"
    ooc_annotation_cleaned = ellara_dir / f"Transcript Session {session} - Annotation Cleaned Candidate.txt"
    ooc_annotation_report = ellara_dir / f"Transcript Session {session} - Annotation Cleanup Report.md"
    ooc_annotation_ambiguous = ellara_dir / f"Transcript Session {session} - Annotation Ambiguous Review.md"
    ooc_annotation_diff = ellara_dir / f"Transcript Session {session} - Annotation Cleaned Candidate.diff"
    raw_notes_candidate_output = (
        Path(args.raw_notes_output).expanduser()
        if args.raw_notes_output
        else session_notes_dir / f"Raw Session {session} Candidate.md"
    )
    raw_notes_reconciled_output = (
        Path(args.raw_notes_reconciled_output).expanduser()
        if args.raw_notes_reconciled_output
        else session_notes_dir / f"Raw Session {session} Reconciled Candidate.md"
    )
    raw_session_output = session_notes_dir / f"Raw Session {session}.md"
    session_notes_output = session_notes_dir / f"Session {session}.md"
    website_session_output = dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md"
    raw_notes_chunk_dir = session_notes_dir / f"Raw Session {session} Chunks"
    raw_notes_chunk_manifest = raw_notes_chunk_dir / "chunks_manifest.json"
    manifest_path = ellara_dir / f"Transcript Session {session} - Pipeline Manifest.json"

    audio_files = list_audio_files(audio_dir)
    if not audio_files:
        raise RuntimeError(f"no supported audio files found in {audio_dir}")
    log(f"Found {len(audio_files)} speaker audio files")

    models = build_whisper_attempt_plan(args.attempt_models)

    site_packages = venv_path / "lib" / "python3.12" / "site-packages"
    cuda_libs = [
        site_packages / "nvidia" / "cudnn" / "lib",
        site_packages / "nvidia" / "cublas" / "lib",
        site_packages / "nvidia" / "cudart" / "lib",
    ]
    ld_library_path = ":".join(str(p) for p in cuda_libs if p.exists())
    if os.environ.get("LD_LIBRARY_PATH"):
        ld_library_path = f"{ld_library_path}:{os.environ['LD_LIBRARY_PATH']}" if ld_library_path else os.environ["LD_LIBRARY_PATH"]

    env_base = dict(os.environ)
    env_base["WHISPER_SESSION_NUMBER"] = str(session)
    if ld_library_path:
        env_base["LD_LIBRARY_PATH"] = ld_library_path

    if args.transcription_provider == "gladia" and not args.resume_after_transcript and not args.skip_transcribe:
        gladia_env_file = dnd_dir / ".env.local"
        load_env_file(gladia_env_file, env_base)
        if not env_base.get("GLADIA_API_KEY"):
            raise RuntimeError(
                "GLADIA_API_KEY is required because Gladia is the default transcription provider. "
                f"Set it in the environment or in {gladia_env_file}. "
                "Use --transcription-provider whisper only when intentionally running local transcription."
            )

    if args.resume_after_transcript:
        if not ellara_transcript.exists():
            raise FileNotFoundError(f"cannot resume; transcript not found: {ellara_transcript}")
        log(f"Resuming from existing transcript: {ellara_transcript}")
        dnd_session_raw.parent.mkdir(parents=True, exist_ok=True)
        combined_final.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ellara_transcript, combined_final)
        shutil.copy2(ellara_transcript, dnd_session_raw)
    else:
        # 1) Refresh entity list for ASR prompts.
        run_cmd(["node", "scripts/generate_entity_list.js"], cwd=dnd_dir, env=env_base)

        # 2) Transcribe with retries.
        if args.clean:
            for audio in audio_files:
                transcript = Path(f"{audio}.txt")
                if transcript.exists():
                    transcript.unlink()

        if not args.skip_transcribe:
            if args.transcription_provider == "gladia":
                log("Gladia transcription provider selected. Running concurrent speaker transcription...")
                from concurrent.futures import ThreadPoolExecutor

                def run_parallel_transcribe(audio):
                    try:
                        return transcribe_one(
                            audio_file=audio,
                            py_bin=py_bin,
                            dnd_dir=dnd_dir,
                            env_base=env_base,
                            models=models,
                            beam_size=args.beam_size,
                            min_lines=args.min_lines,
                            provider=args.transcription_provider,
                            gladia_artifact_dir=gladia_artifact_dir,
                        )
                    except Exception as e:
                        log(f"ERROR transcribing {audio.name}: {e}")
                        raise

                max_workers = min(len(audio_files), int(os.getenv("GLADIA_MAX_WORKERS", "3")))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    list(executor.map(run_parallel_transcribe, audio_files))
            else:
                log("Whisper/local transcription provider selected. Running sequential speaker transcription...")
                for audio in audio_files:
                    transcribe_one(
                        audio_file=audio,
                        py_bin=py_bin,
                        dnd_dir=dnd_dir,
                        env_base=env_base,
                        models=models,
                        beam_size=args.beam_size,
                        min_lines=args.min_lines,
                        provider=args.transcription_provider,
                        gladia_artifact_dir=gladia_artifact_dir,
                    )
        else:
            log("Skipping transcription step (--skip-transcribe)")

        # 3) Combine transcripts.
        run_cmd(
            [str(py_bin), "scripts/transcription/combine_transcripts.py", str(audio_dir), str(combined_tmp)],
            cwd=dnd_dir,
            env=env_base,
        )

        # 4) Apply canonical corrections.
        correction_file = dnd_dir / "scripts" / "transcription" / "name_corrections.json"
        text_patterns, speaker_fixes = load_name_corrections(correction_file)
        normalize_transcript(
            source=combined_tmp,
            dest=combined_final,
            text_patterns=text_patterns,
            speaker_fixes=speaker_fixes,
            keep_full_whitaker_name=args.keep_full_whitaker_name,
        )

        # 5) Copy final files to expected destinations.
        session_assets_dir.mkdir(parents=True, exist_ok=True)
        for audio in audio_files:
            transcript = Path(f"{audio}.txt")
            if transcript.exists():
                shutil.copy2(transcript, session_assets_dir / transcript.name)

        shutil.copy2(combined_final, dnd_session_raw)
        shutil.copy2(combined_final, ellara_transcript)

        if args.stop_after_transcript:
            manifest = {
                "session": session,
                "stage": "transcript_checkpoint",
                "transcription_provider": args.transcription_provider,
                "audio_dir": str(audio_dir),
                "speaker_audio_files": [str(p) for p in audio_files],
                "speaker_transcripts_dir": str(session_assets_dir),
                "combined_transcript_raw": str(combined_tmp),
                "combined_transcript_normalized": str(combined_final),
                "dnd_session_raw": str(dnd_session_raw),
                "ellara_transcript": str(ellara_transcript),
                "line_counts": {
                    "combined_normalized": count_lines(combined_final),
                    "ellara_transcript": count_lines(ellara_transcript),
                },
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            log("Stopping after normalized transcript generation (--stop-after-transcript).")
            log(f"Review transcript: {ellara_transcript}")
            log(f"Manifest: {manifest_path}")
            log("Resume downstream steps with --resume-after-transcript.")
            return 0

    # 6) Generate OOC-removed and ambiguous variants.
    if not args.skip_ooc:
        run_cmd(
            [
                str(py_bin),
                "scripts/transcription/filter_transcript_linewise.py",
                str(ellara_transcript),
                str(ooc_removed),
                str(ambiguous),
                str(ooc_report),
            ],
            cwd=dnd_dir,
            env=env_base,
        )
    else:
        log("Skipping OOC filtering step (--skip-ooc)")

    if args.run_ooc_annotation_provider:
        run_cmd(
            [
                str(py_bin),
                "scripts/transcription/filter_ooc.py",
                "prepare",
                str(ellara_transcript),
                str(ooc_annotation_dir),
                "--chunk-size",
                str(args.ooc_annotation_chunk_size),
                "--overlap-lines",
                str(args.ooc_annotation_overlap),
            ],
            cwd=dnd_dir,
            env=env_base,
        )
        annotation_cmd = [
            str(py_bin),
            "scripts/transcription/run_ooc_annotation_agents.py",
            str(ooc_annotation_manifest),
            "--provider",
            args.run_ooc_annotation_provider,
            "--workspace-root",
            str(dnd_dir.parent),
            "--cleaned-output",
            str(ooc_annotation_cleaned),
            "--report-output",
            str(ooc_annotation_report),
            "--ambiguous-output",
            str(ooc_annotation_ambiguous),
            "--diff-output",
            str(ooc_annotation_diff),
            "--apply",
        ]
        if args.ooc_annotation_model:
            annotation_cmd.extend(["--model", args.ooc_annotation_model])
        if args.ooc_annotation_force:
            annotation_cmd.append("--force")
        if args.ooc_annotation_dry_run:
            annotation_cmd.append("--dry-run")
        if args.ooc_annotation_allow_missing:
            annotation_cmd.append("--allow-missing")
        run_cmd(annotation_cmd, cwd=dnd_dir, env=env_base)

    if args.raw_notes_source:
        raw_notes_source = Path(args.raw_notes_source).expanduser()
        if not raw_notes_source.exists():
            raise FileNotFoundError(f"--raw-notes-source does not exist: {raw_notes_source}")
    else:
        if args.raw_notes_source_mode == "custom":
            raise ValueError("--raw-notes-source-mode custom requires --raw-notes-source")
        if args.raw_notes_source_mode == "annotation":
            raw_notes_source = ooc_annotation_cleaned
            if not raw_notes_source.exists():
                raise FileNotFoundError(
                    f"annotation-cleaned raw-note source not found: {raw_notes_source}"
                )
        elif args.run_ooc_annotation_provider and ooc_annotation_cleaned.exists():
            raw_notes_source = ooc_annotation_cleaned
        elif args.raw_notes_source_mode == "legacy-ooc":
            raw_notes_source = ooc_removed if ooc_removed.exists() else ellara_transcript
        else:
            raw_notes_source = ellara_transcript

    # 7) Prepare raw-note chunks for subagents/LLM passes.
    if not args.skip_raw_notes_prep:
        run_cmd(
            [
                str(py_bin),
                "scripts/transcription/generate_raw_notes.py",
                "prepare",
                str(raw_notes_source),
                str(raw_notes_chunk_dir),
                "--chunk-size",
                str(args.raw_notes_chunk_size),
                "--overlap",
                str(args.raw_notes_overlap),
            ],
            cwd=dnd_dir,
            env=env_base,
        )
    else:
        log("Skipping raw notes prep (--skip-raw-notes-prep)")

    # 8) Optionally run raw-note subagents.
    if args.run_raw_notes_provider:
        raw_runner_cmd = [
            str(py_bin),
            "scripts/transcription/run_raw_notes_subagents.py",
            str(raw_notes_chunk_manifest),
            "--provider",
            args.run_raw_notes_provider,
            "--workspace-root",
            str(dnd_dir.parent),
        ]
        if args.raw_notes_model:
            raw_runner_cmd.extend(["--model", args.raw_notes_model])
        if args.raw_notes_limit is not None:
            raw_runner_cmd.extend(["--limit", str(args.raw_notes_limit)])
        if args.raw_notes_force:
            raw_runner_cmd.append("--force")
        if args.raw_notes_dry_run:
            raw_runner_cmd.append("--dry-run")
        if args.raw_notes_finalize:
            raw_runner_cmd.append("--finalize")
            raw_runner_cmd.extend(["--output-file", str(raw_notes_candidate_output)])

        run_cmd(raw_runner_cmd, cwd=dnd_dir, env=env_base)

    # 8b) Optionally reconcile the chunk-extracted raw-note candidate.
    if args.run_raw_notes_reconcile_provider:
        if not raw_notes_candidate_output.exists():
            raise FileNotFoundError(
                f"raw-note candidate not found for reconciliation: {raw_notes_candidate_output}"
            )
        reconcile_cmd = [
            str(py_bin),
            "scripts/transcription/reconcile_raw_notes.py",
            str(raw_notes_candidate_output),
            str(raw_notes_reconciled_output),
            "--provider",
            args.run_raw_notes_reconcile_provider,
            "--workspace-root",
            str(dnd_dir.parent),
            "--transcript",
            str(raw_notes_source),
        ]
        if args.raw_notes_reconcile_model:
            reconcile_cmd.extend(["--model", args.raw_notes_reconcile_model])
        if args.raw_notes_reconcile_force:
            reconcile_cmd.append("--force")
        if args.raw_notes_reconcile_dry_run:
            reconcile_cmd.append("--dry-run")

        run_cmd(reconcile_cmd, cwd=dnd_dir, env=env_base)

        if args.promote_raw_notes and not args.raw_notes_reconcile_dry_run:
            if not raw_notes_reconciled_output.exists():
                raise FileNotFoundError(
                    f"reconciled raw-note candidate not found for promotion: {raw_notes_reconciled_output}"
                )
            shutil.copy2(raw_notes_reconciled_output, raw_session_output)
            log(f"Promoted raw notes: {raw_notes_reconciled_output} -> {raw_session_output}")

    elif args.promote_raw_notes:
        if not raw_notes_reconciled_output.exists():
            raise FileNotFoundError(
                f"reconciled raw-note candidate not found for promotion: {raw_notes_reconciled_output}"
            )
        shutil.copy2(raw_notes_reconciled_output, raw_session_output)
        log(f"Promoted raw notes: {raw_notes_reconciled_output} -> {raw_session_output}")

    # 9) Optionally generate polished session notes.
    if args.run_session_notes_provider:
        if not raw_session_output.exists():
            raise FileNotFoundError(
                f"raw session notes not found for polished note generation: {raw_session_output}"
            )

        session_runner_cmd = [
            str(py_bin),
            "scripts/transcription/run_session_notes_agent.py",
            session,
            str(raw_session_output),
            str(session_notes_output),
            "--provider",
            args.run_session_notes_provider,
            "--workspace-root",
            str(dnd_dir.parent),
        ]
        if args.session_notes_model:
            session_runner_cmd.extend(["--model", args.session_notes_model])
        if args.session_notes_force:
            session_runner_cmd.append("--force")
        if args.session_notes_dry_run:
            session_runner_cmd.append("--dry-run")
        if args.skip_raw_notes_validation:
            session_runner_cmd.append("--skip-raw-validation")

        run_cmd(session_runner_cmd, cwd=dnd_dir, env=env_base)

    # 10) Optionally sync polished notes into website assets and run website update agent.
    if args.sync_website or args.website_sync_provider:
        website_cmd = [
            str(py_bin),
            "scripts/transcription/run_website_sync_agent.py",
            "--session",
            str(session),
            "--dnd-dir",
            str(dnd_dir),
            "--ellara-root",
            str(session_notes_dir.parent),
        ]
        if args.website_sync_provider:
            website_cmd.extend(["--provider", args.website_sync_provider])
        if args.website_sync_model:
            website_cmd.extend(["--model", args.website_sync_model])
        if args.website_sync_dry_run:
            website_cmd.append("--dry-run")
        run_cmd(website_cmd, cwd=dnd_dir, env=env_base)

    if args.cleanup_scratch:
        cleanup_cmd = [
            str(py_bin),
            "scripts/transcription/cleanup_session_artifacts.py",
            "--session",
            str(session),
            "--dnd-dir",
            str(dnd_dir),
            "--ellara-root",
            str(session_notes_dir.parent),
            "--audio-dir",
            str(audio_dir),
            "--apply",
        ]
        if args.cleanup_include_dnd_transcript_assets:
            cleanup_cmd.append("--include-dnd-transcript-assets")
        if args.cleanup_include_repo_scratch:
            cleanup_cmd.append("--include-repo-scratch")
        run_cmd(cleanup_cmd, cwd=dnd_dir, env=env_base)

    if args.validate:
        validate_cmd = [
            str(py_bin),
            "scripts/transcription/validate_session_pipeline.py",
            "--session",
            str(session),
            "--dnd-dir",
            str(dnd_dir),
            "--ellara-root",
            str(session_notes_dir.parent),
        ]
        if args.validate_check_clean:
            validate_cmd.append("--check-clean")
        if args.validate_strict_clean:
            validate_cmd.append("--strict-clean")
        run_cmd(validate_cmd, cwd=dnd_dir, env=env_base)
        if website_session_output.exists():
            run_cmd(["npm", "run", "generate-list"], cwd=dnd_dir, env=env_base)
            run_cmd(["npm", "run", "verify-session-sync", "--", "--session", str(session)], cwd=dnd_dir, env=env_base)
            run_cmd(["npm", "run", "build"], cwd=dnd_dir, env=env_base)

    # 11) Write manifest for downstream agents/scripts.
    manifest = {
        "session": session,
        "transcription_provider": args.transcription_provider,
        "audio_dir": str(audio_dir),
        "speaker_audio_files": [str(p) for p in audio_files],
        "speaker_transcripts_dir": str(session_assets_dir),
        "combined_transcript_raw": str(combined_tmp),
        "combined_transcript_normalized": str(combined_final),
        "dnd_session_raw": str(dnd_session_raw),
        "ellara_transcript": str(ellara_transcript),
        "ooc_removed": str(ooc_removed),
        "ambiguous": str(ambiguous),
        "ooc_report": str(ooc_report),
        "ooc_annotation_chunk_dir": str(ooc_annotation_dir),
        "ooc_annotation_manifest": str(ooc_annotation_manifest),
        "ooc_annotation_cleaned": str(ooc_annotation_cleaned),
        "ooc_annotation_report": str(ooc_annotation_report),
        "ooc_annotation_ambiguous": str(ooc_annotation_ambiguous),
        "ooc_annotation_diff": str(ooc_annotation_diff),
        "ooc_annotation_provider": args.run_ooc_annotation_provider or "",
        "raw_notes_source_mode": args.raw_notes_source_mode,
        "raw_notes_source": str(raw_notes_source),
        "raw_notes_candidate_output": str(raw_notes_candidate_output),
        "raw_notes_reconciled_output": str(raw_notes_reconciled_output),
        "raw_notes_chunk_dir": str(raw_notes_chunk_dir),
        "raw_notes_chunk_manifest": str(raw_notes_chunk_manifest),
        "raw_session_output": str(raw_session_output),
        "raw_notes_promoted": bool(args.promote_raw_notes and raw_session_output.exists()),
        "raw_notes_provider": args.run_raw_notes_provider or "",
        "raw_notes_reconcile_provider": args.run_raw_notes_reconcile_provider or "",
        "session_notes_output": str(session_notes_output),
        "session_notes_provider": args.run_session_notes_provider or "",
        "website_session_output": str(website_session_output),
        "website_synced": bool((args.sync_website or args.website_sync_provider) and website_session_output.exists()),
        "website_sync_provider": args.website_sync_provider or "",
        "cleanup_scratch": bool(args.cleanup_scratch),
        "validated": bool(args.validate),
        "line_counts": {
            "combined_normalized": count_lines(combined_final),
            "ellara_transcript": count_lines(ellara_transcript),
            "ooc_removed": count_lines(ooc_removed) if ooc_removed.exists() else 0,
            "ambiguous": count_lines(ambiguous) if ambiguous.exists() else 0,
            "ooc_annotation_cleaned": count_lines(ooc_annotation_cleaned) if ooc_annotation_cleaned.exists() else 0,
            "raw_notes_candidate_output": count_lines(raw_notes_candidate_output) if raw_notes_candidate_output.exists() else 0,
            "raw_notes_reconciled_output": count_lines(raw_notes_reconciled_output) if raw_notes_reconciled_output.exists() else 0,
            "raw_session_output": count_lines(raw_session_output) if raw_session_output.exists() else 0,
            "session_notes_output": count_lines(session_notes_output) if session_notes_output.exists() else 0,
            "website_session_output": count_lines(website_session_output) if website_session_output.exists() else 0,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    log("Pipeline complete.")
    log(f"Per-speaker transcripts: {session_assets_dir}")
    log(f"Combined transcript: {ellara_transcript}")
    if not args.skip_ooc:
        log(f"OOC removed transcript: {ooc_removed}")
        log(f"Ambiguous lines: {ambiguous}")
        log(f"OOC report: {ooc_report}")
    if args.run_ooc_annotation_provider or ooc_annotation_cleaned.exists():
        log(f"Annotation-cleaned transcript: {ooc_annotation_cleaned}")
        log(f"Annotation cleanup report: {ooc_annotation_report}")
        log(f"Annotation cleanup diff: {ooc_annotation_diff}")
    if not args.skip_raw_notes_prep:
        log(f"Raw note chunks: {raw_notes_chunk_dir}")
        log(f"Raw note chunk manifest: {raw_notes_chunk_manifest}")
        log(f"Raw session candidate output target: {raw_notes_candidate_output}")
        log(f"Reconciled raw session candidate target: {raw_notes_reconciled_output}")
        log(f"Approved raw session output target: {raw_session_output}")
    if args.run_session_notes_provider or session_notes_output.exists():
        log(f"Session notes output: {session_notes_output}")
    if args.sync_website or args.website_sync_provider or website_session_output.exists():
        log(f"Website session output: {website_session_output}")
    log(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"ERROR: {exc}")
        raise
