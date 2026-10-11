#!/usr/bin/env python3
"""
Transcribe one speaker-isolated audio file with Gladia after local VAD compaction.

The output transcript uses the same timestamp format as transcribe.py:
    [HH:MM:SS -> HH:MM:SS] text

Gladia receives only the compact speech-only WAV. Timestamps from Gladia's
compact-audio result are mapped back to the original audio timeline before
writing the final transcript.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import mimetypes
import re
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib import error, request

import asr_common
import vad_compact


UPLOAD_URL = "https://api.gladia.io/v2/upload"
PRE_RECORDED_URL = "https://api.gladia.io/v2/pre-recorded"
DEFAULT_POLL_INTERVAL = 5
DEFAULT_TIMEOUT = 1800


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_transcribe_module(script_dir: Path):
    path = script_dir / "transcribe.py"
    spec = importlib.util.spec_from_file_location("dnd_transcribe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def http_json(method: str, url: str, api_key: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"x-gladia-key": api_key}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gladia {method} {url} failed: HTTP {exc.code}: {body}") from exc


def upload_audio(path: Path, api_key: str, attempts: int = 4) -> dict:
    """Upload with retries; transient 408/429/5xx and network errors back off."""
    for attempt in range(1, attempts + 1):
        try:
            return _upload_audio_once(path, api_key)
        except (RuntimeError, error.URLError, TimeoutError, ConnectionError) as exc:
            transient = not isinstance(exc, RuntimeError) or any(
                f"HTTP {code}" in str(exc) for code in (408, 429, 500, 502, 503, 504)
            )
            if not transient or attempt == attempts:
                raise
            delay = 15 * attempt
            print(f"Upload attempt {attempt} failed ({exc}); retrying in {delay}s", flush=True)
            time.sleep(delay)
    raise RuntimeError("unreachable")


def _upload_audio_once(path: Path, api_key: str) -> dict:
    upload_path = path
    # Always send lossless FLAC: roughly half the bytes of 16-bit WAV, which
    # avoids upload timeouts on long GM tracks.
    if path.suffix.lower() == ".wav" and path.stat().st_size >= 8 * 1024 * 1024:
        flac_path = path.with_suffix(".flac")
        if not flac_path.exists() or flac_path.stat().st_mtime < path.stat().st_mtime:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(path),
                    "-compression_level",
                    "8",
                    str(flac_path),
                ],
                check=True,
            )
        upload_path = flac_path
        print(f"Compressed upload audio: {upload_path} ({upload_path.stat().st_size} bytes)")

    boundary = f"----dnd-gladia-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(upload_path.name)[0] or "application/octet-stream"
    file_bytes = upload_path.read_bytes()
    body = b"".join([
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="audio"; filename="{upload_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ])

    headers = {
        "x-gladia-key": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    }
    req = request.Request(UPLOAD_URL, data=body, headers=headers, method="POST")
    try:
        upload_timeout = int(os.environ.get("GLADIA_UPLOAD_TIMEOUT_SECONDS", "1200"))
        with request.urlopen(req, timeout=upload_timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gladia upload failed: HTTP {exc.code}: {body}") from exc


def load_name_correction_pronunciations(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    pronunciations: dict[str, list[str]] = {}
    for wrong, right in data.get("text_fixes", {}).items():
        pronunciations.setdefault(right, []).append(wrong)
    return pronunciations


def load_custom_spelling_config(path: Path) -> dict:
    if not path.exists():
        return {"spelling_dictionary": {}}

    data = json.loads(path.read_text(encoding="utf-8"))
    spelling_dictionary: dict[str, list[str]] = {}
    for wrong, right in data.get("text_fixes", {}).items():
        # Gladia custom spelling is literal matching. Very short variants are
        # better left to the deterministic local correction pass to avoid
        # aggressive cloud-side substitutions.
        if len(wrong) < 4 and " " not in wrong:
            continue
        spelling_dictionary.setdefault(right, []).append(wrong)

    return {"spelling_dictionary": spelling_dictionary}


def ascii_fallback(value: str, transcribe_module) -> str | None:
    return transcribe_module.ascii_fallback(value)


def naive_pronunciations(term: str, transcribe_module, corrections: dict[str, list[str]]) -> list[str]:
    candidates = []
    candidates.extend(corrections.get(term, []))

    fallback = ascii_fallback(term, transcribe_module)
    if fallback:
        candidates.append(fallback)

    if "&" in term:
        candidates.append(term.replace("&", "and"))

    simplified = (
        term.replace('"', "")
        .replace("'", "")
        .replace("’", "")
        .replace("-", " ")
    )
    if simplified != term:
        candidates.append(simplified)

    return transcribe_module.dedupe_terms(candidates)[:6]


VOCAB_SKIP_TERMS = {
    # Common English words or fragments that phoneme matching would over-apply.
    "static", "vi", "the", "light", "estate", "mines", "gate", "road", "barkeep", "lex",
}
VOCAB_TITLE_WORDS = {
    "The", "Duke", "Duchess", "Lady", "Lord", "Proctor", "Empress", "Emperor",
    "Consort", "Captain", "Director", "Grand", "Saint", "Sir", "Master", "Mistress",
}
VOCAB_MAX_CHARS = 9500  # Gladia caps custom vocabulary at ~10k characters overall.
ENGLISH_WORDLIST = Path("/usr/share/dict/words")


def load_common_words() -> set[str]:
    if not ENGLISH_WORDLIST.exists():
        return set()
    return {
        line.strip()
        for line in ENGLISH_WORDLIST.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and line.strip().islower()
    }


def is_plain_english(term: str, common_words: set[str]) -> bool:
    """True when every word is ordinary lowercase English (ASR needs no help)."""
    if not common_words:
        return False
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+|\d+", term)
    for word in words:
        if word.isdigit():
            continue
        base = word.lower()
        for suffix in ("'s", "’s"):
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        if base not in common_words and base.rstrip("s") not in common_words:
            return False
    return bool(words)


def vocabulary_terms_from_metadata(dnd_dir: Path, current_session: str | None, transcribe_module) -> list[str]:
    """All campaign entity names plus useful sub-terms, most relevant first."""
    metadata_path = dnd_dir / "scripts" / "transcription" / "entity_metadata.json"
    entities = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else []

    def weight(entity: dict) -> float:
        if entity.get("type") == "Characters":
            return 1000.0
        return transcribe_module.get_session_weight(entity.get("updatedInSessions", []), current_session)

    entities.sort(key=lambda e: (-weight(e), transcribe_module.SECTION_PRIORITY.get(e.get("type"), 99), e["name"]))

    terms: list[str] = list(transcribe_module.PRIORITY_TRANSCRIPTION_TERMS)
    for entity in entities:
        name = transcribe_module.clean_term(entity["name"])
        terms.append(name)
        if name.startswith("The "):
            terms.append(name[4:])
        for quoted in re.findall(r'"([^"]+)"', name):
            terms.append(quoted)
        for parenthetical in re.findall(r"\(([^)]+)\)", name):
            terms.append(parenthetical)
            terms.append(re.sub(r"\s*\([^)]*\)", "", name))
        if entity.get("type") in {"Characters", "NPCs"}:
            person = re.sub(r'"[^"]+"', "", name)
            for word in re.findall(r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'-]+", person):
                if word not in VOCAB_TITLE_WORDS and len(word) >= 4:
                    terms.append(word)

    corrections_path = dnd_dir / "scripts" / "transcription" / "name_corrections.json"
    if corrections_path.exists():
        aliases = json.loads(corrections_path.read_text(encoding="utf-8")).get("aliases", {})
        terms.extend(aliases.keys())

    common_words = load_common_words()
    keep_anyway = set(transcribe_module.PRIORITY_TRANSCRIPTION_TERMS) | {"Witty", "Din", "Little Hill"}
    return [
        term for term in transcribe_module.dedupe_terms(terms)
        if term in keep_anyway
        or (term.casefold() not in VOCAB_SKIP_TERMS and len(term) >= 3 and not is_plain_english(term, common_words))
    ]


def build_custom_vocabulary(
    dnd_dir: Path,
    limit: int,
    default_intensity: float,
    transcribe_module,
) -> dict:
    corrections = load_name_correction_pronunciations(
        dnd_dir / "scripts" / "transcription" / "name_corrections.json"
    )
    terms = vocabulary_terms_from_metadata(
        dnd_dir, os.getenv("WHISPER_SESSION_NUMBER"), transcribe_module
    )[:limit]

    vocabulary = []
    used_chars = 0
    for term in terms:
        entry = {"value": term}
        # Only unambiguous misspellings become pronunciations; ASCII folding of
        # accented names is left out because it re-introduces rejected spellings.
        pronunciations = transcribe_module.dedupe_terms(corrections.get(term, []))[:6]
        if pronunciations:
            entry["pronunciations"] = pronunciations
        cost = len(term) + sum(len(p) for p in pronunciations)
        if used_chars + cost > VOCAB_MAX_CHARS:
            break
        used_chars += cost
        vocabulary.append(entry)

    return {
        "vocabulary": vocabulary,
        "default_intensity": default_intensity,
    }


def initiate_transcription(
    audio_url: str,
    api_key: str,
    custom_vocabulary_config: dict,
    custom_spelling_config: dict,
    audio_file: Path,
) -> dict:
    payload = {
        "audio_url": audio_url,
        "diarization": False,
        "sentences": False,
        "punctuation_enhanced": True,
        "language_config": {
            "languages": ["en"],
            "code_switching": False,
        },
        "custom_metadata": {
            "source": "dnd/scripts/transcription/transcribe_gladia.py",
            "audio_file": str(audio_file),
        },
    }

    if custom_vocabulary_config.get("vocabulary"):
        payload["custom_vocabulary"] = True
        payload["custom_vocabulary_config"] = custom_vocabulary_config

    if custom_spelling_config.get("spelling_dictionary"):
        payload["custom_spelling"] = True
        payload["custom_spelling_config"] = custom_spelling_config

    return http_json("POST", PRE_RECORDED_URL, api_key, payload)


def poll_result(result_url: str, api_key: str, timeout: int, poll_interval: int) -> dict:
    started = time.monotonic()
    while True:
        result = http_json("GET", result_url, api_key)
        status = result.get("status")
        print(f"Gladia status: {status}", flush=True)

        if status in {"done", "completed", "success"}:
            return result
        if result.get("completed_at") and result.get("result"):
            return result
        if status == "error":
            raise RuntimeError(json.dumps(result, indent=2))
        if time.monotonic() - started > timeout:
            raise TimeoutError(f"Timed out waiting for Gladia result after {timeout}s")

        time.sleep(poll_interval)


def extract_utterances(result: dict) -> list[dict]:
    transcription = result.get("result", {}).get("transcription", {})
    utterances = transcription.get("utterances") or []
    if utterances:
        return utterances

    full_transcript = transcription.get("full_transcript", "").strip()
    if full_transcript:
        return [{"start": 0, "end": 0, "text": full_transcript}]

    return []


def clean_text(value: str) -> str:
    return " ".join(value.split())


def join_text(left: str, right: str) -> str:
    left = left.rstrip()
    right = right.lstrip()
    if not left:
        return right
    if not right:
        return left
    return f"{left} {right}"


def coalesce_entries(
    entries: list[dict],
    max_gap: float,
    max_duration: float,
    max_chars: int,
) -> list[dict]:
    merged: list[dict] = []

    for entry in entries:
        text = clean_text(entry.get("text", ""))
        if not text:
            continue

        current = {
            "start": float(entry.get("start", 0)),
            "end": float(entry.get("end", entry.get("start", 0))),
            "text": text,
        }
        if not merged:
            merged.append(current)
            continue

        previous = merged[-1]
        candidate_text = join_text(previous["text"], current["text"])
        gap = current["start"] - previous["end"]
        duration = current["end"] - previous["start"]

        if gap <= max_gap and duration <= max_duration and len(candidate_text) <= max_chars:
            previous["end"] = max(previous["end"], current["end"])
            previous["text"] = candidate_text
        else:
            merged.append(current)

    return merged


def text_from_words(words: list[dict]) -> str:
    return clean_text("".join(word.get("word", "") for word in words))


def utterance_to_original_entries(
    utterance: dict,
    mapper: vad_compact.TimelineMapper,
    max_original_word_gap: float,
) -> list[dict]:
    words = [word for word in utterance.get("words", []) if clean_text(word.get("word", ""))]
    if not words:
        text = clean_text(utterance.get("text", ""))
        if not text:
            return []

        return [{
            "start": mapper.map_time(float(utterance.get("start", 0))),
            "end": mapper.map_time(
                float(utterance.get("end", utterance.get("start", 0))),
                is_end=True,
            ),
            "text": text,
        }]

    entries = []
    current_words = []
    current_start = None
    current_end = None

    for word in words:
        original_start = mapper.map_time(float(word.get("start", 0)))
        original_end = mapper.map_time(
            float(word.get("end", word.get("start", 0))),
            is_end=True,
        )

        if (
            current_words
            and current_end is not None
            and original_start - current_end > max_original_word_gap
        ):
            entries.append({
                "start": current_start,
                "end": current_end,
                "text": text_from_words(current_words),
            })
            current_words = []
            current_start = None
            current_end = None

        if not current_words:
            current_start = original_start

        current_words.append(word)
        current_end = original_end

    if current_words:
        entries.append({
            "start": current_start,
            "end": current_end,
            "text": text_from_words(current_words),
        })

    return [entry for entry in entries if entry["text"]]


def remapped_words(result: dict, mapper: vad_compact.TimelineMapper) -> list[dict]:
    words = []
    for utterance in extract_utterances(result):
        for word in utterance.get("words", []) or []:
            text = clean_text(word.get("word", ""))
            if not text:
                continue
            words.append({
                "s": mapper.map_time(float(word.get("start", 0))),
                "e": mapper.map_time(float(word.get("end", word.get("start", 0))), is_end=True),
                "w": text,
                "p": word.get("confidence"),
            })
    words.sort(key=lambda w: w["s"])
    return words


def write_remapped_transcript(
    result: dict,
    manifest_path: Path,
    output_path: Path,
    words_json_path: Path | None = None,
    audio_file: Path | None = None,
    params: dict | None = None,
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mapper = vad_compact.TimelineMapper(manifest["segments"])
    utterances = extract_utterances(result)

    original_entries = []
    max_original_word_gap = float(os.getenv("GLADIA_WORD_SPLIT_GAP", "2.5"))
    for utterance in utterances:
        original_entries.extend(
            utterance_to_original_entries(utterance, mapper, max_original_word_gap)
        )

    merged_entries = coalesce_entries(
        original_entries,
        max_gap=float(os.getenv("GLADIA_UTTERANCE_MERGE_GAP", "1.25")),
        max_duration=float(os.getenv("GLADIA_UTTERANCE_MERGE_MAX_DURATION", "18")),
        max_chars=int(os.getenv("GLADIA_UTTERANCE_MERGE_MAX_CHARS", "260")),
    )

    segments = [{"s": e["start"], "e": e["end"], "text": e["text"]} for e in merged_entries]
    asr_common.write_segment_txt(output_path, segments)

    if words_json_path:
        asr_common.write_engine_json(
            words_json_path,
            engine="gladia",
            model=str(result.get("request_params", {}).get("model") or "gladia-default"),
            audio_file=audio_file or Path(manifest.get("source_audio", "")),
            words=remapped_words(result, mapper),
            segments=segments,
            duration=manifest.get("original_duration"),
            speech_seconds=sum(
                seg["original_end"] - seg["original_start"] for seg in manifest.get("segments", [])
            ),
            params=params,
        )


def compact_audio(input_audio: Path, compact_audio_path: Path, manifest_path: Path, args) -> None:
    compact_args = argparse.Namespace(
        input_audio=str(input_audio),
        output_audio=str(compact_audio_path),
        manifest=str(manifest_path),
        threshold=args.vad_threshold,
        min_speech_duration_ms=args.vad_min_speech_ms,
        max_speech_duration_s=args.vad_max_speech_s,
        min_silence_duration_ms=args.vad_min_silence_ms,
        speech_pad_ms=args.vad_speech_pad_ms,
        segment_gap_ms=args.vad_segment_gap_ms,
    )
    vad_compact.compact(compact_args)


def count_result_utterances(result: dict) -> int:
    return len(extract_utterances(result))


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_gladia_job(
    audio_file: Path,
    compact_audio_path: Path,
    manifest_path: Path,
    artifact_dir: Path,
    api_key: str,
    custom_vocabulary_config: dict,
    custom_spelling_config: dict,
    args,
) -> dict:
    upload_response_path = artifact_dir / "upload_response.json"
    init_response_path = artifact_dir / "init_response.json"
    result_path = artifact_dir / "result.json"

    upload_response = upload_audio(compact_audio_path, api_key)
    upload_response_path.write_text(json.dumps(upload_response, indent=2) + "\n", encoding="utf-8")
    audio_url = upload_response["audio_url"]

    init_response = initiate_transcription(
        audio_url,
        api_key,
        custom_vocabulary_config,
        custom_spelling_config,
        audio_file,
    )
    init_response_path.write_text(json.dumps(init_response, indent=2) + "\n", encoding="utf-8")

    result_url = init_response.get("result_url") or f"{PRE_RECORDED_URL}/{init_response['id']}"
    result = poll_result(result_url, api_key, timeout=args.timeout, poll_interval=args.poll_interval)
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def retry_compaction_args(args: argparse.Namespace, input_audio: Path, output_audio: Path, manifest: Path) -> argparse.Namespace:
    return argparse.Namespace(
        input_audio=str(input_audio),
        output_audio=str(output_audio),
        manifest=str(manifest),
        threshold=min(args.vad_threshold, 0.35),
        min_speech_duration_ms=args.vad_min_speech_ms,
        max_speech_duration_s=args.vad_max_speech_s,
        min_silence_duration_ms=min(args.vad_min_silence_ms, 700),
        speech_pad_ms=max(args.vad_speech_pad_ms, 1000),
        segment_gap_ms=max(args.vad_segment_gap_ms, 500),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_file")
    parser.add_argument("output_file")
    parser.add_argument("--dnd-dir", default="/home/babu/source/dnd")
    parser.add_argument("--artifact-dir", help="Directory for compact audio, manifests, and Gladia JSON")
    parser.add_argument("--env-file", help="Local env file with GLADIA_API_KEY; defaults to <dnd-dir>/.env.local")
    parser.add_argument("--api-key-env", default="GLADIA_API_KEY")
    parser.add_argument("--custom-vocabulary-limit", type=int, default=400)
    parser.add_argument("--custom-vocabulary-intensity", type=float, default=0.45)
    parser.add_argument("--disable-custom-vocabulary", action="store_true")
    parser.add_argument("--disable-custom-spelling", action="store_true")
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--vad-threshold", type=float, default=0.5)
    parser.add_argument("--vad-min-speech-ms", type=int, default=0)
    parser.add_argument("--vad-max-speech-s", type=float, default=float("inf"))
    parser.add_argument("--vad-min-silence-ms", type=int, default=2000)
    parser.add_argument("--vad-speech-pad-ms", type=int, default=400)
    parser.add_argument(
        "--vad-segment-gap-ms",
        type=int,
        default=250,
        help="Insert this much silence between retained VAD islands before upload",
    )
    parser.add_argument(
        "--words-json",
        help="Also write the common dnd-asr-v1 JSON (word timings + confidence) here",
    )
    parser.add_argument(
        "--raw-archive",
        help="Copy the raw Gladia result JSON (gzipped) to this path for later reprocessing",
    )
    parser.add_argument(
        "--no-empty-result-retry",
        action="store_true",
        help="Do not retry with a less aggressive compact file if Gladia returns no utterances",
    )
    args = parser.parse_args()

    audio_file = Path(args.audio_file).expanduser().resolve()
    output_file = Path(args.output_file).expanduser().resolve()
    dnd_dir = Path(args.dnd_dir).expanduser().resolve()
    env_file = Path(args.env_file).expanduser().resolve() if args.env_file else dnd_dir / ".env.local"
    load_env_file(env_file)

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"{args.api_key_env} is required for Gladia transcription; checked {env_file}")

    script_dir = Path(__file__).resolve().parent
    artifact_dir = (
        Path(args.artifact_dir).expanduser().resolve()
        if args.artifact_dir
        else output_file.parent / ".gladia" / audio_file.name
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    compact_audio_path = artifact_dir / f"{audio_file.stem}.vad.wav"
    manifest_path = artifact_dir / f"{audio_file.stem}.vad.json"
    transcribe_module = load_transcribe_module(script_dir)
    compact_audio(audio_file, compact_audio_path, manifest_path, args)

    custom_vocabulary_config = (
        {"vocabulary": [], "default_intensity": args.custom_vocabulary_intensity}
        if args.disable_custom_vocabulary
        else build_custom_vocabulary(
            dnd_dir=dnd_dir,
            limit=args.custom_vocabulary_limit,
            default_intensity=args.custom_vocabulary_intensity,
            transcribe_module=transcribe_module,
        )
    )
    custom_spelling_config = (
        {"spelling_dictionary": {}}
        if args.disable_custom_spelling
        else load_custom_spelling_config(
            dnd_dir / "scripts" / "transcription" / "name_corrections.json"
        )
    )
    print(f"Using {len(custom_vocabulary_config['vocabulary'])} Gladia custom vocabulary entries.")
    print(f"Using {len(custom_spelling_config['spelling_dictionary'])} Gladia custom spelling entries.")

    result = run_gladia_job(
        audio_file,
        compact_audio_path,
        manifest_path,
        artifact_dir,
        api_key,
        custom_vocabulary_config,
        custom_spelling_config,
        args,
    )
    final_manifest_path = manifest_path

    manifest = load_manifest(manifest_path)
    if (
        count_result_utterances(result) == 0
        and not args.no_empty_result_retry
        and manifest.get("compact_duration", 0) >= 1
        and manifest.get("segments")
    ):
        print("Gladia returned no utterances for non-empty compact audio; retrying with relaxed VAD.")
        retry_dir = artifact_dir / "empty-result-retry"
        retry_dir.mkdir(parents=True, exist_ok=True)
        retry_compact_audio_path = retry_dir / f"{audio_file.stem}.vad.wav"
        retry_manifest_path = retry_dir / f"{audio_file.stem}.vad.json"
        vad_compact.compact(
            retry_compaction_args(args, audio_file, retry_compact_audio_path, retry_manifest_path)
        )
        retry_result = run_gladia_job(
            audio_file,
            retry_compact_audio_path,
            retry_manifest_path,
            retry_dir,
            api_key,
            custom_vocabulary_config,
            custom_spelling_config,
            args,
        )
        if count_result_utterances(retry_result) > 0:
            result = retry_result
            final_manifest_path = retry_manifest_path
        else:
            print("Relaxed VAD retry also returned no utterances; keeping the original empty result.")

    params = {
        "custom_vocabulary_entries": len(custom_vocabulary_config["vocabulary"]),
        "custom_vocabulary_intensity": custom_vocabulary_config.get("default_intensity"),
        "custom_spelling_entries": len(custom_spelling_config["spelling_dictionary"]),
        "vad_manifest": str(final_manifest_path),
    }
    write_remapped_transcript(
        result,
        final_manifest_path,
        output_file,
        words_json_path=Path(args.words_json).expanduser().resolve() if args.words_json else None,
        audio_file=audio_file,
        params=params,
    )
    if args.raw_archive:
        raw_result = final_manifest_path.parent / "result.json"
        archive = Path(args.raw_archive).expanduser().resolve()
        asr_common.archive_json(raw_result, archive)
        asr_common.archive_json(final_manifest_path, archive.with_name(archive.name.replace(".result.json.gz", "") + ".vad.json.gz"))
        print(f"Archived raw Gladia result: {archive}")
    print(f"Transcript saved to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
