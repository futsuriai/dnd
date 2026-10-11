#!/usr/bin/env python3
"""Run one or more ASR engines over every speaker track of a session.

Outputs (per engine) in <work-dir>/<engine>/:
    <track>.json                 common dnd-asr-v1 JSON (word timings, confidence)
    <track>.txt                  legacy per-track transcript
    raw/<track>.result.json.gz   raw provider response (Gladia), kept for reprocessing
    logs/<track>.log

Engines:
    gladia             cloud, VAD-compacted upload (needs GLADIA_API_KEY)
    whisper-large-v3   local faster-whisper large-v3 (GPU)
    whisper-turbo      local faster-whisper large-v3-turbo (GPU, faster)

Cloud and GPU engines run concurrently; GPU tracks run one at a time.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = SCRIPT_DIR.parent.parent
AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".ogg", ".aac"}
DEFAULT_PYTHON = Path("~/.gemini/tmp/transcribe_env/bin/python3").expanduser()

WHISPER_MODELS = {
    "whisper-large-v3": "large-v3",
    "whisper-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "whisper-distil": "distil-large-v3",
}

_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(f"[asr {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def list_audio(audio_dir: Path) -> list[Path]:
    return sorted(p for p in audio_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS)


def cuda_env(python_bin: Path) -> dict[str, str]:
    env = dict(os.environ)
    site = python_bin.parent.parent / "lib" / "python3.12" / "site-packages" / "nvidia"
    libs = [str(site / lib / "lib") for lib in ("cudnn", "cublas", "cudart") if (site / lib / "lib").exists()]
    if libs:
        env["LD_LIBRARY_PATH"] = ":".join(libs + ([env["LD_LIBRARY_PATH"]] if env.get("LD_LIBRARY_PATH") else []))
    return env


def run_logged(cmd: list[str], log_path: Path, env: dict[str, str]) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as lf:
        return subprocess.run(cmd, cwd=str(DND_DIR), env=env, stdout=lf, stderr=subprocess.STDOUT, check=False).returncode


def gladia_track(audio: Path, out_dir: Path, python_bin: Path, env: dict[str, str], force: bool) -> bool:
    track = audio.name.split(".", 1)[0]
    out_json = out_dir / f"{track}.json"
    if out_json.exists() and not force:
        log(f"gladia {track}: exists, skipping")
        return True
    log(f"gladia {track}: start")
    code = run_logged(
        [
            str(python_bin), "-u", str(SCRIPT_DIR / "transcribe_gladia.py"),
            str(audio), str(out_dir / f"{track}.txt"),
            "--dnd-dir", str(DND_DIR),
            "--artifact-dir", str(out_dir / "work" / track),
            "--words-json", str(out_json),
            "--raw-archive", str(out_dir / "raw" / f"{track}.result.json.gz"),
        ],
        out_dir / "logs" / f"{track}.log",
        env,
    )
    log(f"gladia {track}: {'done' if code == 0 else f'FAILED ({code})'}")
    return code == 0


def whisper_track(
    audio: Path, out_dir: Path, model: str, python_bin: Path, env: dict[str, str], session: str, force: bool
) -> bool:
    track = audio.name.split(".", 1)[0]
    out_json = out_dir / f"{track}.json"
    if out_json.exists() and not force:
        log(f"{out_dir.name} {track}: exists, skipping")
        return True
    log(f"{out_dir.name} {track}: start")
    code = run_logged(
        [
            str(python_bin), "-u", str(SCRIPT_DIR / "asr_whisper.py"), str(audio),
            "--out-json", str(out_json),
            "--model", model,
            "--session", session,
        ],
        out_dir / "logs" / f"{track}.log",
        env,
    )
    log(f"{out_dir.name} {track}: {'done' if code == 0 else f'FAILED ({code})'}")
    return code == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audio-dir", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--engines", default="gladia,whisper-large-v3", help="Comma-separated engine list")
    parser.add_argument("--work-dir", help="Default: <audio-dir>/asr")
    parser.add_argument("--python", default=str(DEFAULT_PYTHON), help="Python with faster-whisper installed")
    parser.add_argument("--gladia-workers", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir).expanduser().resolve()
    work_dir = Path(args.work_dir).expanduser().resolve() if args.work_dir else audio_dir / "asr"
    python_bin = Path(args.python).expanduser()
    audio_files = list_audio(audio_dir)
    if not audio_files:
        raise SystemExit(f"no audio files in {audio_dir}")

    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    unknown = [e for e in engines if e != "gladia" and e not in WHISPER_MODELS]
    if unknown:
        raise SystemExit(f"unknown engines: {unknown}")

    env = cuda_env(python_bin)
    env["WHISPER_SESSION_NUMBER"] = str(args.session)
    log(f"{len(audio_files)} tracks, engines={engines}, work_dir={work_dir}")

    results: list[bool] = []

    def run_gladia() -> None:
        out_dir = work_dir / "gladia"
        with ThreadPoolExecutor(max_workers=args.gladia_workers) as pool:
            results.extend(pool.map(lambda a: gladia_track(a, out_dir, python_bin, env, args.force), audio_files))

    def run_local() -> None:
        for engine in engines:
            if engine == "gladia":
                continue
            out_dir = work_dir / engine
            for audio in audio_files:
                results.append(
                    whisper_track(audio, out_dir, WHISPER_MODELS[engine], python_bin, env, str(args.session), args.force)
                )

    threads = []
    if "gladia" in engines:
        threads.append(threading.Thread(target=run_gladia))
    if any(e != "gladia" for e in engines):
        threads.append(threading.Thread(target=run_local))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    failed = results.count(False)
    log(f"finished: {len(results) - failed} ok, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
