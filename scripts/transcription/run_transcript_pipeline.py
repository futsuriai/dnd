#!/usr/bin/env python3
"""
Run an end-to-end DnD transcript pipeline from speaker-isolated audio files.

Pipeline:
1. Regenerate ENTITY_LIST.md (used as Whisper initial prompt).
2. Transcribe per-speaker audio with retries and model fallback.
3. Combine per-speaker transcripts into one chronological transcript.
4. Apply name/speaker corrections and optional speaker display normalization.
5. Copy final files into DnD assets and Ellara transcript folders.
6. Produce OOC-removed and ambiguous outputs with the linewise filter.
7. Prepare overlapping raw-session-note chunks for subagents/LLM passes.
8. Optionally generate polished Session N markdown from Raw Session N markdown.
9. Write a manifest JSON listing all generated artifacts.
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
LINE_RE = re.compile(r"^(\[\d{2}:\d{2}:\d{2}\]\s+)([^:]+)(:\s*)(.*)$")


def log(msg: str) -> None:
    print(msg, flush=True)


def run_cmd(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    location = f" (cwd={cwd})" if cwd else ""
    log(f"$ {' '.join(cmd)}{location}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


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


def load_name_corrections(path: Path) -> tuple[list[tuple[re.Pattern[str], str]], dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    text_fixes = data.get("text_fixes", {})
    speaker_fixes = data.get("speaker_label_fixes", {})

    patterns: list[tuple[re.Pattern[str], str]] = []
    for wrong in sorted(text_fixes.keys(), key=len, reverse=True):
        right = text_fixes[wrong]
        patterns.append((re.compile(rf"(?<!\w){re.escape(wrong)}(?!\w)"), right))
    return patterns, speaker_fixes


def apply_line_corrections(
    line: str,
    text_patterns: list[tuple[re.Pattern[str], str]],
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
) -> Path:
    output_file = Path(f"{audio_file}.txt")
    tmp_output = Path(f"{audio_file}.txt.tmp")
    file_log = Path(f"{audio_file}.transcribe.log")

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
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--skip-transcribe", action="store_true", help="Skip transcription and reuse existing *.ext.txt files")
    parser.add_argument("--clean", action="store_true", help="Delete existing per-speaker transcript files before transcribing")
    parser.add_argument("--skip-ooc", action="store_true", help="Skip OOC and ambiguous output generation")
    parser.add_argument("--skip-raw-notes-prep", action="store_true", help="Skip preparing raw-session-note chunks for subagents")
    parser.add_argument("--raw-notes-chunk-size", type=int, default=20, help="Primary transcript entries per raw-notes chunk")
    parser.add_argument("--raw-notes-overlap", type=int, default=5, help="Context entries before/after each raw-notes chunk")
    parser.add_argument("--run-raw-notes-provider", choices=["codex", "gemini"], help="Optionally dispatch raw-note chunks through the selected agent CLI")
    parser.add_argument("--raw-notes-model", help="Optional model override for raw-note agent runs")
    parser.add_argument("--raw-notes-limit", type=int, help="Limit how many raw-note chunks to dispatch")
    parser.add_argument("--raw-notes-force", action="store_true", help="Overwrite existing raw-note chunk outputs when dispatching agents")
    parser.add_argument("--raw-notes-dry-run", action="store_true", help="Show planned raw-note agent dispatches without invoking the provider")
    parser.add_argument("--raw-notes-finalize", action="store_true", help="Finalize Raw Session N.md after raw-note agent dispatch")
    parser.add_argument("--run-session-notes-provider", choices=["codex", "gemini"], help="Optionally generate polished Session N.md through the selected agent CLI")
    parser.add_argument("--session-notes-model", help="Optional model override for polished session-note generation")
    parser.add_argument("--session-notes-force", action="store_true", help="Overwrite existing Session N.md when dispatching the agent")
    parser.add_argument("--session-notes-dry-run", action="store_true", help="Show the planned polished session-note run without invoking the provider")
    parser.add_argument(
        "--keep-full-whitaker-name",
        action="store_true",
        help='Keep speaker name as \'Whitaker "Witty" Whitman VI\' instead of normalizing to "Witty"',
    )
    args = parser.parse_args()

    session = str(args.session).strip()
    if not session:
        raise ValueError("--session cannot be empty")

    audio_dir = Path(args.audio_dir).expanduser().resolve()
    dnd_dir = Path(args.dnd_dir).expanduser().resolve()
    ellara_dir = Path(args.ellara_dir).expanduser().resolve()
    venv_path = Path(args.venv_path).expanduser().resolve()
    py_bin = venv_path / "bin" / "python3"

    if not audio_dir.is_dir():
        raise FileNotFoundError(f"audio directory not found: {audio_dir}")
    if not dnd_dir.is_dir():
        raise FileNotFoundError(f"dnd directory not found: {dnd_dir}")
    if not py_bin.exists():
        raise FileNotFoundError(f"python executable not found in venv: {py_bin}")

    ellara_dir.mkdir(parents=True, exist_ok=True)
    session_notes_dir = ellara_dir.parent

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
    if ld_library_path:
        env_base["LD_LIBRARY_PATH"] = ld_library_path

    # 1) Refresh entity list for Whisper initial prompt spellings.
    run_cmd(["node", "scripts/generate_entity_list.js"], cwd=dnd_dir, env=env_base)

    # 2) Transcribe with retries.
    if args.clean:
        for audio in audio_files:
            transcript = Path(f"{audio}.txt")
            if transcript.exists():
                transcript.unlink()

    if not args.skip_transcribe:
        for audio in audio_files:
            transcribe_one(
                audio_file=audio,
                py_bin=py_bin,
                dnd_dir=dnd_dir,
                env_base=env_base,
                models=models,
                beam_size=args.beam_size,
                min_lines=args.min_lines,
            )
    else:
        log("Skipping transcription step (--skip-transcribe)")

    # 3) Combine transcripts.
    combined_tmp = audio_dir / f"session-{session}-combined.txt"
    combined_final = audio_dir / f"session-{session}-combined-normalized.txt"
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
    session_assets_dir = dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"Session {session}"
    session_assets_dir.mkdir(parents=True, exist_ok=True)
    for audio in audio_files:
        transcript = Path(f"{audio}.txt")
        if transcript.exists():
            shutil.copy2(transcript, session_assets_dir / transcript.name)

    dnd_session_raw = dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"session_{session}_raw.txt"
    ellara_transcript = ellara_dir / f"Transcript Session {session}.txt"
    shutil.copy2(combined_final, dnd_session_raw)
    shutil.copy2(combined_final, ellara_transcript)

    ooc_removed = ellara_dir / f"Transcript Session {session} - OOC Removed.txt"
    ambiguous = ellara_dir / f"Transcript Session {session} - Ambiguous.txt"
    ooc_report = ellara_dir / f"Transcript Session {session} - OOC Filter Report.txt"

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

    raw_session_output = session_notes_dir / f"Raw Session {session}.md"
    session_notes_output = session_notes_dir / f"Session {session}.md"
    raw_notes_chunk_dir = session_notes_dir / f"Raw Session {session} Chunks"
    raw_notes_chunk_manifest = raw_notes_chunk_dir / "chunks_manifest.json"
    raw_notes_source = ooc_removed if ooc_removed.exists() else ellara_transcript

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

        run_cmd(raw_runner_cmd, cwd=dnd_dir, env=env_base)

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

        run_cmd(session_runner_cmd, cwd=dnd_dir, env=env_base)

    # 10) Write manifest for downstream agents/scripts.
    manifest = {
        "session": session,
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
        "raw_notes_source": str(raw_notes_source),
        "raw_notes_chunk_dir": str(raw_notes_chunk_dir),
        "raw_notes_chunk_manifest": str(raw_notes_chunk_manifest),
        "raw_session_output": str(raw_session_output),
        "raw_notes_provider": args.run_raw_notes_provider or "",
        "session_notes_output": str(session_notes_output),
        "session_notes_provider": args.run_session_notes_provider or "",
        "line_counts": {
            "combined_normalized": count_lines(combined_final),
            "ellara_transcript": count_lines(ellara_transcript),
            "ooc_removed": count_lines(ooc_removed) if ooc_removed.exists() else 0,
            "ambiguous": count_lines(ambiguous) if ambiguous.exists() else 0,
            "raw_session_output": count_lines(raw_session_output) if raw_session_output.exists() else 0,
            "session_notes_output": count_lines(session_notes_output) if session_notes_output.exists() else 0,
        },
    }
    manifest_path = ellara_dir / f"Transcript Session {session} - Pipeline Manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    log("Pipeline complete.")
    log(f"Per-speaker transcripts: {session_assets_dir}")
    log(f"Combined transcript: {ellara_transcript}")
    if not args.skip_ooc:
        log(f"OOC removed transcript: {ooc_removed}")
        log(f"Ambiguous lines: {ambiguous}")
        log(f"OOC report: {ooc_report}")
    if not args.skip_raw_notes_prep:
        log(f"Raw note chunks: {raw_notes_chunk_dir}")
        log(f"Raw note chunk manifest: {raw_notes_chunk_manifest}")
        log(f"Raw session output target: {raw_session_output}")
    if args.run_session_notes_provider or session_notes_output.exists():
        log(f"Session notes output: {session_notes_output}")
    log(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"ERROR: {exc}")
        raise
