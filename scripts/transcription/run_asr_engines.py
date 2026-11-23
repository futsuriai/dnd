#!/usr/bin/env python3
"""Run one or more ASR engines over every speaker track of a session.

Outputs (per engine) in <work-dir>/<engine>/:
    <track>.json                 common dnd-asr-v1 JSON (word timings, confidence)
    <track>.txt                  legacy per-track transcript
    raw/<track>.result.json.gz   raw provider response (Gladia), kept for reprocessing
    logs/<track>.log

Engines:
    gladia             cloud, VAD-compacted upload (needs GLADIA_API_KEY)
    whisper-large-v3   local Whisper large-v3 (CUDA / Apple MLX / CPU int8)
    whisper-turbo      local Whisper large-v3-turbo (faster on M1/GPU/CPU)
    whisper-distil     local distil-large-v3

Cloud and local engines run concurrently; local tracks run one at a time.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import pipeline_paths as _pipeline_paths
except ImportError:
    _pipeline_paths = None

SCRIPT_DIR = Path(__file__).resolve().parent
DND_DIR = _pipeline_paths.DND_DIR if _pipeline_paths is not None else SCRIPT_DIR.parent.parent
AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".ogg", ".aac"}


def _default_python() -> Path:
    if _pipeline_paths is not None:
        return _pipeline_paths.resolve_python()
    venv_py = DND_DIR / ".venv-transcription" / "bin" / "python3"
    if venv_py.exists():
        return venv_py
    return Path(sys.executable)


DEFAULT_PYTHON = _default_python()

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


def is_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}


def runtime_env(python_bin: Path) -> dict[str, str]:
    """Build subprocess env without injecting Linux CUDA paths on macOS."""
    if _pipeline_paths is not None:
        env = _pipeline_paths.no_bytecode_env()
    else:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

    # NVIDIA pip wheel libraries live under site-packages/nvidia on Linux only.
    if platform.system() == "Linux":
        lib_root = python_bin.parent.parent / "lib"
        if lib_root.exists():
            for site in sorted(lib_root.glob("python*/site-packages/nvidia")):
                libs = [str(site / lib / "lib") for lib in ("cudnn", "cublas", "cudart") if (site / lib / "lib").exists()]
                if libs:
                    existing = env.get("LD_LIBRARY_PATH")
                    env["LD_LIBRARY_PATH"] = ":".join(libs + ([existing] if existing else []))
                    break
    return env


# Preserve legacy helper name if imported externally.
cuda_env = runtime_env

MYNE_BUNDLE_FILES = (
    "asr_whisper.py",
    "asr_common.py",
    "pipeline_paths.py",
    "transcribe.py",
    "transcribe_gladia.py",
    "vad_compact.py",
    "entity_metadata.json",
)


def myne_available(timeout: int = 15) -> bool:
    """Return True when the `myne` offload CLI is on PATH and reaches the desktop."""
    if not shutil.which("myne"):
        return False
    try:
        res = subprocess.run(
            ["myne", "check"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return res.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def resolve_whisper_offload(requested: str) -> str:
    """Resolve whisper offload target (`local` or `myne`) with graceful fallback."""
    if requested == "local":
        return "local"
    if requested == "myne":
        if myne_available():
            return "myne"
        log("myne offload requested, but `myne check` failed; falling back to local Whisper")
        return "local"
    # Auto: offload local Whisper from macOS to MYNE GPU when reachable.
    if platform.system() == "Darwin" and myne_available():
        return "myne"
    return "local"


def stage_myne_bundle(stage_dir: Path, dnd_dir: Path, pending_names: list[str], model: str, session: str) -> Path:
    """Stage non-secret scripts, metadata, and remote runner script for MYNE CUDA Whisper."""
    dnd_stage = stage_dir / "dnd"
    scripts_stage = dnd_stage / "scripts" / "transcription"
    scripts_stage.mkdir(parents=True, exist_ok=True)

    entity_list = dnd_dir / "ENTITY_LIST.md"
    if entity_list.is_file():
        shutil.copy2(entity_list, dnd_stage / "ENTITY_LIST.md")

    src_dir = dnd_dir / "scripts" / "transcription"
    for name in MYNE_BUNDLE_FILES:
        src = src_dir / name
        if src.is_file():
            shutil.copy2(src, scripts_stage / name)

    quoted_files = " ".join(f'"{name}"' for name in pending_names)
    remote_script = stage_dir / "run_remote_whisper.sh"
    remote_script.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export WHISPER_SESSION_NUMBER="{session}"

PY="$HOME/.gemini/tmp/transcribe_env/bin/python3"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3)"
fi

LIB_ROOT="$(dirname "$(dirname "$PY")")/lib"
for site in "$LIB_ROOT"/python*/site-packages/nvidia; do
  if [ -d "$site" ]; then
    for sub in cudnn cublas cudart; do
      if [ -d "$site/$sub/lib" ]; then
        export LD_LIBRARY_PATH="$site/$sub/lib${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"
      fi
    done
  fi
done

mkdir -p out/logs
for audio in {quoted_files}; do
  track="${{audio%%.*}}"
  echo "[myne-whisper] starting $audio (model={model})"
  "$PY" -B -u dnd/scripts/transcription/asr_whisper.py "./$audio" \\
    --out-json "out/$track.json" \\
    --out-txt "out/$track.txt" \\
    --model "{model}" \\
    --backend faster-whisper \\
    --device cuda \\
    --compute-type float16 \\
    --session "{session}" 2>&1 | tee "out/logs/$track.log"
done
""",
        encoding="utf-8",
    )
    remote_script.chmod(0o755)
    return remote_script


def rewrite_offloaded_json(
    downloaded_json: Path,
    dest_json: Path,
    local_audio: Path,
    offload_host: str = "myne",
) -> None:
    """Rewrite remote `audio_file` path in downloaded engine JSON back to the local Mac path."""
    data = json.loads(downloaded_json.read_text(encoding="utf-8"))
    data["audio_file"] = str(local_audio.resolve())
    params = data.setdefault("params", {})
    if isinstance(params, dict):
        params["offload_host"] = offload_host
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_json.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_path.replace(dest_json)


def whisper_engine_myne(
    audio_files: list[Path],
    out_dir: Path,
    model: str,
    session: str,
    force: bool,
) -> list[bool]:
    """Run local Whisper on MYNE's CUDA GPU in one batch job and pull engine JSONs back."""
    pending = [
        audio
        for audio in audio_files
        if force or not (out_dir / f"{audio.name.split('.', 1)[0]}.json").exists()
    ]
    if not pending:
        for audio in audio_files:
            log(f"{out_dir.name} {audio.name.split('.', 1)[0]}: exists, skipping")
        return [True] * len(audio_files)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "logs").mkdir(parents=True, exist_ok=True)
    job_id = re.sub(r"[^A-Za-z0-9._-]+", "-", f"dnd-whisper-s{session}-{out_dir.name}")
    log(f"{out_dir.name}: offloading {len(pending)} track(s) to MYNE CUDA (job={job_id})")

    env = dict(os.environ)
    env["COPYFILE_DISABLE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    with tempfile.TemporaryDirectory(prefix="myne_whisper_") as td:
        tmp_dir = Path(td)
        stage_dir = tmp_dir / "stage"
        dl_dir = tmp_dir / "download"
        remote_script = stage_myne_bundle(
            stage_dir, DND_DIR, [audio.name for audio in pending], model, session
        )
        cmd = [
            "myne",
            "run",
            "-j",
            job_id,
            "--keep",
            "-i",
            str(stage_dir / "dnd"),
            "-i",
            str(remote_script),
        ]
        for audio in pending:
            cmd.extend(["-i", str(audio.resolve())])
        cmd.extend(["-o", "out", "-d", str(dl_dir), "--", "bash run_remote_whisper.sh"])

        myne_log = out_dir / "logs" / "myne_offload.log"
        proc = subprocess.run(cmd, cwd=str(DND_DIR), env=env, capture_output=True, text=True, check=False)
        myne_log.write_text(
            (proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else ""),
            encoding="utf-8",
        )
        if proc.returncode != 0:
            log(f"{out_dir.name}: MYNE offload failed ({proc.returncode}); see {myne_log}")

        results: list[bool] = []
        dl_out = dl_dir / "out"
        for audio in audio_files:
            track = audio.name.split(".", 1)[0]
            dest_json = out_dir / f"{track}.json"
            if audio not in pending:
                results.append(dest_json.exists())
                continue
            src_json = dl_out / f"{track}.json"
            src_txt = dl_out / f"{track}.txt"
            src_log = dl_out / "logs" / f"{track}.log"
            if src_log.is_file():
                shutil.copy2(src_log, out_dir / "logs" / f"{track}.log")
            if src_txt.is_file():
                shutil.copy2(src_txt, out_dir / f"{track}.txt")
            if src_json.is_file():
                rewrite_offloaded_json(src_json, dest_json, audio)
                log(f"{out_dir.name} {track}: downloaded from MYNE")
                results.append(True)
            else:
                log(f"{out_dir.name} {track}: FAILED on MYNE (missing output JSON)")
                results.append(False)

        if proc.returncode == 0 and all(results):
            subprocess.run(["myne", "clean", job_id], env=env, capture_output=True, check=False)
            log(f"{out_dir.name}: cleaned MYNE job {job_id}")
        return results


def run_logged(cmd: list[str], log_path: Path, env: dict[str, str]) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as lf:
        return subprocess.run(cmd, cwd=str(DND_DIR), env=env, stdout=lf, stderr=subprocess.STDOUT, check=False).returncode


def gladia_track(
    audio: Path,
    out_dir: Path,
    python_bin: Path,
    env: dict[str, str],
    force: bool,
    vocab_intensity: float | None = None,
) -> bool:
    track = audio.name.split(".", 1)[0]
    out_json = out_dir / f"{track}.json"
    if out_json.exists() and not force:
        log(f"gladia {track}: exists, skipping")
        return True
    log(f"gladia {track}: start")
    cmd = [
        str(python_bin), "-B", "-u", str(SCRIPT_DIR / "transcribe_gladia.py"),
        str(audio), str(out_dir / f"{track}.txt"),
        "--dnd-dir", str(DND_DIR),
        "--artifact-dir", str(out_dir / "work" / track),
        "--words-json", str(out_json),
        "--raw-archive", str(out_dir / "raw" / f"{track}.result.json.gz"),
    ]
    if vocab_intensity is not None:
        cmd.extend(["--vocab-intensity", str(vocab_intensity)])
    code = run_logged(cmd, out_dir / "logs" / f"{track}.log", env)
    log(f"gladia {track}: {'done' if code == 0 else f'FAILED ({code})'}")
    return code == 0


def whisper_track(
    audio: Path,
    out_dir: Path,
    model: str,
    python_bin: Path,
    env: dict[str, str],
    session: str,
    force: bool,
    backend: str = "auto",
) -> bool:
    track = audio.name.split(".", 1)[0]
    out_json = out_dir / f"{track}.json"
    if out_json.exists() and not force:
        log(f"{out_dir.name} {track}: exists, skipping")
        return True
    log(f"{out_dir.name} {track}: start")
    cmd = [
        str(python_bin), "-B", "-u", str(SCRIPT_DIR / "asr_whisper.py"), str(audio),
        "--out-json", str(out_json),
        "--model", model,
        "--session", session,
        "--backend", backend,
    ]
    code = run_logged(cmd, out_dir / "logs" / f"{track}.log", env)
    log(f"{out_dir.name} {track}: {'done' if code == 0 else f'FAILED ({code})'}")
    return code == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audio-dir", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--engines", default="gladia,whisper-large-v3", help="Comma-separated engine list")
    parser.add_argument("--work-dir", help="Default: <audio-dir>/asr")
    parser.add_argument("--python", help=f"Python with faster-whisper/mlx-whisper installed (default: {DEFAULT_PYTHON})")
    parser.add_argument("--whisper-backend", choices=["auto", "mlx", "faster-whisper"], default="auto")
    parser.add_argument(
        "--whisper-offload",
        choices=["auto", "local", "myne"],
        default="auto",
        help="Where to run local Whisper engines: auto (MYNE CUDA if reachable from macOS), local, or myne",
    )
    parser.add_argument("--vocab-intensity", type=float, help="Optional Gladia custom vocabulary intensity override")
    parser.add_argument("--gladia-workers", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir).expanduser().resolve()
    work_dir = Path(args.work_dir).expanduser().resolve() if args.work_dir else audio_dir / "asr"
    python_bin = (
        _pipeline_paths.resolve_python(args.python)
        if _pipeline_paths is not None
        else (Path(args.python).expanduser() if args.python else _default_python())
    )
    audio_files = list_audio(audio_dir)
    if not audio_files:
        raise SystemExit(f"no audio files in {audio_dir}")

    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    unknown = [e for e in engines if e != "gladia" and e not in WHISPER_MODELS]
    if unknown:
        raise SystemExit(f"unknown engines: {unknown}")

    whisper_engines = [e for e in engines if e != "gladia"]
    offload_target = resolve_whisper_offload(args.whisper_offload) if whisper_engines else "local"

    env = runtime_env(python_bin)
    env["WHISPER_SESSION_NUMBER"] = str(args.session)
    arch = "Apple Silicon" if is_apple_silicon() else f"{platform.system()} {platform.machine()}"
    log(
        f"{len(audio_files)} tracks, engines={engines}, host={arch}, "
        f"whisper_offload={offload_target}, python={python_bin}, work_dir={work_dir}"
    )

    results: list[bool] = []
    results_lock = threading.Lock()

    def _record_results(items: list[bool]) -> None:
        with results_lock:
            results.extend(items)

    def run_gladia() -> None:
        out_dir = work_dir / "gladia"
        with ThreadPoolExecutor(max_workers=args.gladia_workers) as pool:
            _record_results(
                list(
                    pool.map(
                        lambda a: gladia_track(a, out_dir, python_bin, env, args.force, args.vocab_intensity),
                        audio_files,
                    )
                )
            )

    def run_local() -> None:
        for engine in whisper_engines:
            out_dir = work_dir / engine
            if offload_target == "myne":
                _record_results(
                    whisper_engine_myne(
                        audio_files,
                        out_dir,
                        WHISPER_MODELS[engine],
                        str(args.session),
                        args.force,
                    )
                )
            else:
                for audio in audio_files:
                    _record_results(
                        [
                            whisper_track(
                                audio,
                                out_dir,
                                WHISPER_MODELS[engine],
                                python_bin,
                                env,
                                str(args.session),
                                args.force,
                                backend=args.whisper_backend,
                            )
                        ]
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
