import sys
import os
import inspect
import re
import unicodedata
import torch
import json
from pathlib import Path
from faster_whisper import WhisperModel

# Supported audio extensions
AUDIO_EXTENSIONS = {'.flac', '.mp3', '.wav', '.m4a', '.ogg', '.aac'}

SECTION_PRIORITY = {
    "Characters": 0,
    "Locations": 1,
    "NPCs": 2,
    "Lore": 3,
}

CAMPAIGN_TRANSCRIPTION_TERMS = [
    "GM",
    "DM",
    "D&D",
    "Dungeons & Dragons",
    "d20",
    "initiative",
    "armor class",
    "hit points",
    "saving throw",
    "perception check",
    "investigation check",
    "insight check",
    "persuasion check",
    "deception check",
    "stealth check",
    "spell slot",
    "cantrip",
    "wild shape",
    "Lay on Hands",
    "Divine Smite",
    "Hunter's Mark",
    "Dimension Door",
    "sending stone",
]

ENTITY_RE = re.compile(r"^- `(?P<id>[^`]+)`: (?P<name>.+)$")


def clean_term(value):
    return re.sub(r"\s+", " ", value.strip().rstrip("\\").strip())


def dedupe_terms(terms):
    seen = set()
    result = []
    for term in terms:
        term = clean_term(term)
        if not term:
            continue

        key = term.casefold()
        if key in seen:
            continue

        seen.add(key)
        result.append(term)
    return result


def ascii_fallback(term):
    normalized = unicodedata.normalize("NFKD", term)
    fallback = "".join(char for char in normalized if not unicodedata.combining(char))
    return fallback if fallback != term else None


def expand_entity_terms(records):
    terms = []

    for record in records:
        section = record["section"]
        name = record["name"]
        terms.append(name)

        fallback = ascii_fallback(name)
        if fallback:
            terms.append(fallback)

        if name.startswith("The "):
            terms.append(name[4:])

        for quoted in re.findall(r'"([^"]+)"|“([^”]+)”', name):
            terms.extend(part for part in quoted if part)

        for parenthetical in re.findall(r"\(([^)]+)\)", name):
            terms.append(parenthetical)
            terms.append(re.sub(r"\s*\([^)]*\)", "", name))

        for suffix in ("'s", "’s"):
            if name.endswith(suffix):
                terms.append(name[: -len(suffix)])

        if section in {"Characters", "NPCs"}:
            person_name = re.sub(r'"[^"]+"|“[^”]+”', "", name)
            for word in re.findall(r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'-]+", person_name):
                if word not in {"The", "Duke", "Lady", "Lord", "Proctor", "Empress", "Consort"}:
                    terms.append(word)

    return dedupe_terms(terms)


def get_session_weight(sessions, current_session):
    if not sessions:
        return 1.0
    if not current_session:
        return 10.0
    try:
        current_session = int(current_session)
    except ValueError:
        return 10.0
    max_weight = 1.0
    for s in sessions:
        try:
            s_val = int(s)
            distance = current_session - s_val
            if distance == 0:
                weight = 100.0
            elif distance == 1:
                weight = 70.0
            elif distance == 2:
                weight = 40.0
            elif distance > 0:
                weight = 10.0 + max(0.0, 10.0 - distance)
            else:
                weight = 5.0
            max_weight = max(max_weight, weight)
        except ValueError:
            continue
    return max_weight


def load_weighted_entities(dnd_dir, current_session, term_limit=24):
    metadata_path = dnd_dir / "scripts" / "transcription" / "entity_metadata.json"
    if not metadata_path.exists():
        return None
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            entities = json.load(f)
    except Exception as e:
        print(f"Error loading entity metadata: {e}")
        return None

    # Compute weights and sort globally by:
    # 1. Weight desc
    # 2. Section priority asc (Characters = 0, Locations = 1, NPCs = 2, Lore = 3)
    # 3. Name asc
    weighted_entities = []
    for entity in entities:
        weight = get_session_weight(entity.get("updatedInSessions", []), current_session)
        # Give Characters a strong base weight boost so party names are always included
        if entity.get("type") == "Characters":
            weight = max(weight, 100.0)
        weighted_entities.append((weight, entity))

    weighted_entities.sort(key=lambda x: (
        -x[0],
        SECTION_PRIORITY.get(x[1]["type"], 99),
        x[1]["name"].casefold()
    ))

    # Take the top term_limit entities
    selected = weighted_entities[:term_limit]

    print(f"Priority-Weighted selection complete. Selected {len(selected)} terms:")
    for w, ent in selected:
        print(f"  [{ent['type']}] {ent['name']} (weight={w:.1f}, sessions={ent['updatedInSessions']})")

    return [x[1] for x in selected]


def load_entity_terms(entity_list_path):
    dnd_dir = Path(entity_list_path).parent
    current_session = os.getenv("WHISPER_SESSION_NUMBER")
    term_limit = optional_int_env("WHISPER_PROMPT_TERM_LIMIT") or 24

    # Try weighted proportional loading first
    weighted_entities = load_weighted_entities(dnd_dir, current_session, term_limit)
    if weighted_entities is not None:
        records = []
        for ent in weighted_entities:
            records.append({
                "section": ent["type"],
                "id": ent["id"],
                "name": clean_term(ent["name"]),
            })
        terms = dedupe_terms(expand_entity_terms(records) + CAMPAIGN_TRANSCRIPTION_TERMS)
        return terms

    # Fallback to standard parsing of ENTITY_LIST.md if metadata file is not available
    if not os.path.isfile(entity_list_path):
        print(f"Entity list not found: {entity_list_path}")
        return []

    records = []
    section = ""
    try:
        with open(entity_list_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("## "):
                    section = line[3:].strip()
                    continue

                match = ENTITY_RE.match(line)
                if not match:
                    continue

                records.append({
                    "section": section,
                    "id": match.group("id"),
                    "name": clean_term(match.group("name")),
                })
    except Exception as e:
        print(f"Error reading entity list {entity_list_path}: {e}")
        return []

    if not records:
        print(f"No entity terms found in {entity_list_path}")
        return []

    records.sort(key=lambda record: (
        SECTION_PRIORITY.get(record["section"], 99),
        record["name"].casefold(),
    ))
    terms = dedupe_terms(expand_entity_terms(records) + CAMPAIGN_TRANSCRIPTION_TERMS)

    if terms:
        print(f"Loaded {len(records)} entities and expanded to {len(terms)} prompt terms from {entity_list_path}")
    else:
        print(f"No usable entity terms found in {entity_list_path}")
    return terms


def build_initial_prompt(entity_terms):
    configured = os.getenv("WHISPER_INITIAL_PROMPT")
    if configured:
        return configured.strip()

    if not entity_terms:
        return "English D&D campaign transcript. Preserve speaker names, fantasy proper nouns, and tabletop terms."

    term_limit = optional_int_env("WHISPER_PROMPT_TERM_LIMIT") or 24
    max_chars = optional_int_env("WHISPER_INITIAL_PROMPT_MAX_CHARS") or 600
    sample_terms = join_terms_with_budget(entity_terms[:term_limit], max_chars=max_chars - 120, separator=", ")
    return (
        "English D&D campaign transcript. Preserve exact spellings for speaker names, "
        f"fantasy proper nouns, and tabletop terms such as: {sample_terms}."
    )


def build_hotwords(entity_terms):
    configured = os.getenv("WHISPER_HOTWORDS")
    if configured:
        return configured.strip()

    if not entity_terms:
        return None

    limit = get_hotword_limit()
    if limit <= 0:
        return None

    max_chars = optional_int_env("WHISPER_HOTWORD_MAX_CHARS") or 900
    return join_terms_with_budget(entity_terms[:limit], max_chars=max_chars, separator="; ")


def get_hotword_limit():
    raw_limit = os.getenv("WHISPER_HOTWORD_LIMIT", "80")
    try:
        return int(raw_limit)
    except ValueError:
        print(f"Invalid WHISPER_HOTWORD_LIMIT={raw_limit!r}; using 80.")
        return 80


def join_terms_with_budget(terms, max_chars, separator):
    result = []
    current_length = 0
    for term in terms:
        addition = len(term) if not result else len(separator) + len(term)
        if current_length + addition > max_chars:
            break
        result.append(term)
        current_length += addition
    return separator.join(result)


def optional_int_env(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        print(f"Invalid {name}={value!r}; ignoring.")
        return None


def optional_float_env(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        print(f"Invalid {name}={value!r}; ignoring.")
        return None


def build_vad_parameters():
    options = {
        "threshold": optional_float_env("WHISPER_VAD_THRESHOLD"),
        "min_speech_duration_ms": optional_int_env("WHISPER_VAD_MIN_SPEECH_MS"),
        "max_speech_duration_s": optional_float_env("WHISPER_VAD_MAX_SPEECH_S"),
        "min_silence_duration_ms": optional_int_env("WHISPER_VAD_MIN_SILENCE_MS"),
        "speech_pad_ms": optional_int_env("WHISPER_VAD_SPEECH_PAD_MS"),
    }
    return {key: value for key, value in options.items() if value is not None}


def bool_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def transcribe_file(model, audio_path, output_path, initial_prompt=None, hotwords=None):
    print(f"Transcribing {audio_path}...")
    try:
        beam_size = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
        transcribe_kwargs = {
            "beam_size": beam_size,
            "vad_filter": True,
            "condition_on_previous_text": bool_env("WHISPER_CONDITION_ON_PREVIOUS_TEXT", True),
        }
        vad_parameters = build_vad_parameters()
        if vad_parameters:
            transcribe_kwargs["vad_parameters"] = vad_parameters
        language = os.getenv("WHISPER_LANGUAGE")
        if language:
            transcribe_kwargs["language"] = language
        if initial_prompt:
            transcribe_kwargs["initial_prompt"] = initial_prompt
        if hotwords and "hotwords" in inspect.signature(model.transcribe).parameters:
            transcribe_kwargs["hotwords"] = hotwords

        segments, info = model.transcribe(audio_path, **transcribe_kwargs)
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        if getattr(info, "duration_after_vad", None) is not None:
            removed = info.duration - info.duration_after_vad
            ratio = removed / info.duration if info.duration else 0
            print(
                "VAD kept "
                f"{info.duration_after_vad:.1f}s / {info.duration:.1f}s "
                f"and removed {removed:.1f}s ({ratio:.1%})."
            )

        with open(output_path, "w", encoding="utf-8") as f:
            for segment in segments:
                # Format timestamp: 00:00:00
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                
                # Output format: [Start -> End] Text
                line = f"[{start} -> {end}] {segment.text}"
                
                # Print to console (for logs) and write to file
                print(line) 
                f.write(line + "\n")
                f.flush() # Ensure it writes immediately

        print(f"Transcription saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        return False

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def load_model(model_size="large-v3", device="cuda", compute_type="float16"):
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available; falling back to CPU with int8 compute.")
        device = "cpu"
        if compute_type == "float16":
            compute_type = "int8"

    print(f"Loading model: {model_size} on {device} ({compute_type})...")
    try:
        return WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file_or_directory> [output_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Check if input is a directory or file
    files_to_process = []
    if os.path.isdir(input_path):
        print(f"Scanning directory: {input_path}")
        for root, _, files in os.walk(input_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in AUDIO_EXTENSIONS:
                    files_to_process.append(os.path.join(root, file))
    elif os.path.isfile(input_path):
        files_to_process.append(input_path)
    else:
        print(f"Error: {input_path} is not a valid file or directory.")
        sys.exit(1)

    if not files_to_process:
        print("No audio files found to process.")
        sys.exit(0)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    entity_list_path = os.getenv(
        "WHISPER_ENTITY_LIST",
        os.path.normpath(os.path.join(script_dir, "..", "..", "ENTITY_LIST.md")),
    )
    entity_terms = load_entity_terms(entity_list_path)
    initial_prompt = build_initial_prompt(entity_terms)
    hotwords = build_hotwords(entity_terms)
    if initial_prompt:
        print(f"Using initial prompt ({len(initial_prompt)} chars).")
    else:
        print("No entity prompt loaded; continuing without it.")
    if hotwords:
        hotword_count = min(len(entity_terms), get_hotword_limit())
        print(f"Using hotwords with {hotword_count} terms ({len(hotwords)} chars).")
    else:
        print("No hotwords loaded; continuing without hotword hints.")

    model_size = os.getenv("WHISPER_MODEL_SIZE", "large-v3")
    device = os.getenv("WHISPER_DEVICE", "cuda")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

    # Load model once
    model = load_model(model_size=model_size, device=device, compute_type=compute_type)
    if not model:
        sys.exit(1)

    # Process files
    for audio_file in files_to_process:
        # Determine output path
        # If output path was provided and input was a single file, use it
        if len(sys.argv) >= 3 and os.path.isfile(input_path):
             output_file = sys.argv[2]
        else:
            # Default to <filename>.txt in the same directory
            output_file = f"{audio_file}.txt"
        
        if not transcribe_file(model, audio_file, output_file, initial_prompt=initial_prompt, hotwords=hotwords):
            sys.exit(1)

if __name__ == "__main__":
    main()
