#!/usr/bin/env python3
"""Remove intermediate artifacts for one session after durable outputs are kept."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".ogg", ".aac"}


def collect_paths(
    session: int,
    dnd_dir: Path,
    ellara_root: Path,
    audio_dir: Path | None,
    include_dnd_transcript_assets: bool,
    include_repo_scratch: bool,
) -> list[Path]:
    notes_dir = ellara_root / "Session Notes"
    transcript_dir = notes_dir / "Transcripts"
    paths: list[Path] = [
        notes_dir / f"Raw Session {session} Candidate.md",
        notes_dir / f"Raw Session {session} Reconciled Candidate.md",
        notes_dir / f"Raw Session {session} Chunks",
        transcript_dir / f"Session {session} OOC Annotation Chunks",
        transcript_dir / f"Session {session} OOC Review Chunks",
        transcript_dir / f"Session {session} OOC Review Chunks From Provider Merge",
    ]
    paths.extend(sorted(transcript_dir.glob(f"Transcript Session {session} - *")))

    if include_dnd_transcript_assets:
        paths.extend(
            [
                dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"Session {session}",
                dnd_dir / "src" / "assets" / "sessions" / "transcripts" / f"session_{session}_raw.txt",
            ]
        )

    if audio_dir:
        paths.extend(
            [
                audio_dir / f"session-{session}-combined.txt",
                audio_dir / f"session-{session}-combined-normalized.txt",
                audio_dir / ".gladia",
            ]
        )
        for audio in sorted(audio_dir.iterdir()) if audio_dir.exists() else []:
            if not audio.is_file() or audio.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            paths.extend(
                [
                    Path(f"{audio}.txt"),
                    Path(f"{audio}.txt.tmp"),
                    Path(f"{audio}.transcribe.log"),
                ]
            )

    if include_repo_scratch:
        paths.extend(
            [
                dnd_dir / "dist",
                dnd_dir / "scripts" / "transcription" / "__pycache__",
                dnd_dir / "scripts" / "transcription" / "transcribe.log",
                dnd_dir / "transcribe.log",
                dnd_dir / "transcription_job.log",
            ]
        )

    durable = {
        notes_dir / f"Raw Session {session}.md",
        notes_dir / f"Session {session}.md",
        transcript_dir / f"Transcript Session {session}.txt",
        transcript_dir / f"Transcript Session {session} - Pipeline Manifest.json",
        dnd_dir / "src" / "assets" / "sessions" / f"session-{session}.md",
    }
    return [path for path in dict.fromkeys(paths) if path not in durable]


def remove_path(path: Path, dry_run: bool) -> bool:
    if not path.exists():
        return False
    action = "would remove" if dry_run else "remove"
    print(f"{action}: {path}")
    if dry_run:
        return True
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int, help="Session number to clean")
    parser.add_argument("--dnd-dir", default="/home/babu/source/dnd", help="DnD repo root")
    parser.add_argument("--ellara-root", default="/home/babu/source/ellara", help="Ellara repo root")
    parser.add_argument("--audio-dir", help="Optional original audio directory to clean sidecars from")
    parser.add_argument(
        "--include-dnd-transcript-assets",
        action="store_true",
        help="Also remove website raw transcript assets for this session",
    )
    parser.add_argument(
        "--include-repo-scratch",
        action="store_true",
        help="Also remove repo scratch outputs such as dist, logs, and pycache",
    )
    parser.add_argument("--apply", action="store_true", help="Actually remove files. Default is dry-run.")
    args = parser.parse_args()

    dnd_dir = Path(args.dnd_dir).expanduser().resolve()
    ellara_root = Path(args.ellara_root).expanduser().resolve()
    audio_dir = Path(args.audio_dir).expanduser().resolve() if args.audio_dir else None
    dry_run = not args.apply

    paths = collect_paths(
        session=args.session,
        dnd_dir=dnd_dir,
        ellara_root=ellara_root,
        audio_dir=audio_dir,
        include_dnd_transcript_assets=args.include_dnd_transcript_assets,
        include_repo_scratch=args.include_repo_scratch,
    )
    removed = sum(1 for path in paths if remove_path(path, dry_run=dry_run))
    if dry_run:
        print(f"Dry run complete: {removed} existing artifact(s) would be removed. Re-run with --apply to delete.")
    else:
        print(f"Cleanup complete: removed {removed} artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
