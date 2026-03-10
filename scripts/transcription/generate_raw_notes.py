"""
Generate raw session notes from a transcript that is mostly in-game content.

This is an LLM-assisted process:
1. Prepare chunk files with a primary range and surrounding context.
2. Process each chunk with a strong model/subagent.
3. Concatenate the chunk outputs into `Raw Session XX.md`.

Usage:
    # Step 1: Create chunk files for subagents/LLM passes
    python generate_raw_notes.py prepare session-XX-ingame.txt ./notes_chunks

    # Step 2: Process each chunk through an LLM
    #   Input:  notes_chunks/chunk_000.txt
    #   Output: notes_chunks/chunk_000_notes.txt

    # Step 3: Concatenate chunk outputs
    python generate_raw_notes.py concat ./notes_chunks "Raw Session XX.md"

Options:
    --chunk-size N     Primary entries per chunk (default: 20)
    --overlap N        Context entries before/after each chunk (default: 5)
"""
import argparse
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

from note_generation_guidance import CANONICAL_CAST_REFERENCE


RECOMMENDED_MODEL = "gpt-5.2-codex"
ENTRY_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\] [^:]+: .+$")

PROMPT_TEMPLATE = f"""\
Convert this D&D transcript chunk into raw session notes.

The chunk file contains three possible sections:
- `CONTEXT BEFORE`: prior material for continuity only
- `PRIMARY RANGE`: the lines you should actually convert into notes
- `CONTEXT AFTER`: later material for continuity only

Rules:
- Output notes ONLY for the `PRIMARY RANGE`
- Use the context sections only to resolve pronouns, scene continuity, or references
- Strip remaining out-of-character chatter, table talk, scheduling, tech talk, and player-side commentary
- Keep the output in rough raw-note format, not polished campaign recap prose
- Stay close to transcript order and wording
- Keep in-character dialogue as dialogue using `name: "quote"` when a direct quote matters
- Summarize actions and narration in short informal prose or sentence fragments
- It is fine for the notes to feel draft-like and a little messy; do not smooth everything into elegant narration
- Do not add headings, titles, bullet lists, or recap framing
- Use `---` for scene/beat breaks where helpful
- Use lowercase names for dialogue attribution: `nyx: "quote"`
- Clean up filler words but preserve meaning
- Keep important rolls/checks when they matter
- Do not mention timestamps
- Do not add commentary about what you removed
- Do not restate the whole scene if the chunk starts in the middle of it

{CANONICAL_CAST_REFERENCE}

Example target style:
```
nyx: "we have nothing else to go on, so let's go back to the city like ysidor suggested"
the party camps here for the night.
---
nyx picks up three light crystals, each roughly fist-sized.
nyx: investigation 5. the crystals glow dimly.
---
ellara: "it's time for bed. perhaps tomorrow we should ask proctor eduard about those constructs"
nyx: "sure. be careful"
ysidor: "are you not worried for your safety? there's dark magic going on"
ellara: "exactly. who better to ask?"
```

=== CHUNK ===
{{chunk_text}}
=== END CHUNK ===

Output only the raw session notes for the PRIMARY RANGE:"""


NAME_CORRECTIONS = {
    "here's embrace": "hýrda's embrace",
    "heroterra": "hieroterra",
    "Heroterra": "Hieroterra",
}


def parse_entries(text):
    blocks = [e.strip() for e in re.split(r"\n\s*\n+", text.strip()) if e.strip()]
    if len(blocks) > 1:
        return blocks

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and all(ENTRY_RE.match(line) for line in lines):
        return lines

    return lines


def build_chunks(entries, chunk_size, overlap):
    if chunk_size <= 0:
        raise ValueError("--chunk-size must be greater than 0")
    if overlap < 0:
        raise ValueError("--overlap cannot be negative")

    chunks = []
    total = len(entries)
    for chunk_id, start in enumerate(range(0, total, chunk_size)):
        end = min(start + chunk_size, total)
        context_start = max(0, start - overlap)
        context_end = min(total, end + overlap)

        chunks.append({
            "chunk_id": chunk_id,
            "primary_start": start,
            "primary_end": end,
            "context_start": context_start,
            "context_end": context_end,
            "context_before": entries[context_start:start],
            "primary_entries": entries[start:end],
            "context_after": entries[end:context_end],
        })
    return chunks


def format_chunk(chunk, total_entries):
    lines = [
        "# RAW NOTES CHUNK",
        f"# Chunk: {chunk['chunk_id']:03d}",
        f"# Primary entries: {chunk['primary_start'] + 1}-{chunk['primary_end']} of {total_entries}",
        f"# Context coverage: {chunk['context_start'] + 1}-{chunk['context_end']} of {total_entries}",
        "",
    ]

    if chunk["context_before"]:
        lines.append("=== CONTEXT BEFORE ===")
        lines.extend(chunk["context_before"])
        lines.append("")

    lines.append("=== PRIMARY RANGE ===")
    lines.extend(chunk["primary_entries"])
    lines.append("")

    if chunk["context_after"]:
        lines.append("=== CONTEXT AFTER ===")
        lines.extend(chunk["context_after"])
        lines.append("")

    lines.append("=== END CHUNK ===")
    lines.append("")
    return "\n".join(lines)


def prepare(args):
    input_path = Path(args.input_file)
    output_dir = Path(args.output_dir)

    with input_path.open(encoding="utf-8") as f:
        text = f.read()

    entries = parse_entries(text)
    output_dir.mkdir(parents=True, exist_ok=True)

    for old in output_dir.glob("chunk_*.txt"):
        old.unlink()
    manifest_path = output_dir / "chunks_manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()

    chunks = build_chunks(entries, args.chunk_size, args.overlap)
    manifest_chunks = []

    for chunk in chunks:
        chunk_name = f"chunk_{chunk['chunk_id']:03d}.txt"
        notes_name = f"chunk_{chunk['chunk_id']:03d}_notes.txt"
        chunk_path = output_dir / chunk_name
        chunk_path.write_text(format_chunk(chunk, len(entries)), encoding="utf-8")

        manifest_chunks.append({
            "chunk_id": chunk["chunk_id"],
            "input_file": str(chunk_path),
            "output_file": str(output_dir / notes_name),
            "primary_start_entry": chunk["primary_start"] + 1,
            "primary_end_entry": chunk["primary_end"],
            "context_start_entry": chunk["context_start"] + 1,
            "context_end_entry": chunk["context_end"],
            "primary_entry_count": len(chunk["primary_entries"]),
            "context_before_count": len(chunk["context_before"]),
            "context_after_count": len(chunk["context_after"]),
        })

    manifest = {
        "input_file": str(input_path.resolve()),
        "chunk_dir": str(output_dir.resolve()),
        "recommended_model": RECOMMENDED_MODEL,
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
        "entry_count": len(entries),
        "chunk_count": len(chunks),
        "chunks": manifest_chunks,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Prepared {len(chunks)} chunks from {len(entries)} entries in {output_dir}/")
    print(f"Manifest: {manifest_path}")
    print(f"Recommended model: {RECOMMENDED_MODEL}")
    print(f"Run subagents/LLM passes on chunk_XXX.txt -> chunk_XXX_notes.txt")
    print(f"Prompt template: python {sys.argv[0]} prompt")


def apply_corrections(text):
    for wrong, right in NAME_CORRECTIONS.items():
        text = text.replace(wrong, right)

    text = re.sub(r"(?<!\w)nites(?!\w)", "nýtes", text)
    text = re.sub(r"(?<!\w)Nites(?!\w)", "Nýtes", text)
    return text


def normalize_for_compare(text):
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return normalized.strip()


def blocks_are_similar(left, right):
    left_n = normalize_for_compare(left)
    right_n = normalize_for_compare(right)

    if not left_n or not right_n:
        return False
    if left_n == right_n:
        return True

    shorter, longer = sorted((left_n, right_n), key=len)
    if len(shorter) >= 24 and longer.startswith(shorter):
        return True

    return difflib.SequenceMatcher(None, left_n, right_n).ratio() >= 0.92


def choose_better_block(left, right):
    return right if len(normalize_for_compare(right)) > len(normalize_for_compare(left)) else left


def parse_blocks(text):
    blocks = []
    current = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.strip() == "---":
            if current:
                block = "\n".join(current).strip()
                if block:
                    blocks.append(block)
                current = []
            blocks.append("---")
            continue

        if not line.strip():
            if current and current[-1] != "":
                current.append("")
            continue

        current.append(line)

    if current:
        block = "\n".join(current).strip()
        if block:
            blocks.append(block)

    return blocks


def normalize_blocks(blocks):
    cleaned = []
    for block in blocks:
        if block == "---":
            if not cleaned or cleaned[-1] == "---":
                continue
            cleaned.append(block)
            continue

        if cleaned and cleaned[-1] != "---" and blocks_are_similar(cleaned[-1], block):
            cleaned[-1] = choose_better_block(cleaned[-1], block)
            continue

        cleaned.append(block)

    while cleaned and cleaned[0] == "---":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "---":
        cleaned.pop()
    return cleaned


def smooth_adjacent_seams(blocks):
    smoothed = []
    i = 0
    while i < len(blocks):
        current = blocks[i]
        if (
            i + 2 < len(blocks)
            and current != "---"
            and blocks[i + 1] == "---"
            and blocks[i + 2] != "---"
            and blocks_are_similar(current, blocks[i + 2])
        ):
            smoothed.append(choose_better_block(current, blocks[i + 2]))
            i += 3
            continue

        smoothed.append(current)
        i += 1

    return normalize_blocks(smoothed)


def cleanup_raw_notes_text(text):
    blocks = parse_blocks(text)
    blocks = normalize_blocks(blocks)
    blocks = smooth_adjacent_seams(blocks)
    if not blocks:
        return ""

    lines = []
    for block in blocks:
        if block == "---":
            if lines and lines[-1] != "":
                lines.append("")
            lines.append("---")
            lines.append("")
            continue
        lines.append(block)
        lines.append("")

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned + "\n"


def concat(args):
    chunk_dir = Path(args.chunk_dir)
    manifest_path = chunk_dir / "chunks_manifest.json"

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        note_paths = [Path(chunk["output_file"]) for chunk in manifest.get("chunks", [])]
        missing = [str(path) for path in note_paths if not path.exists()]
        if missing:
            print("Missing notes chunk outputs:")
            for path in missing:
                print(path)
            sys.exit(1)
        notes = note_paths
    else:
        notes = sorted(chunk_dir.glob("chunk_*_notes.txt"))

    if not notes:
        print(f"No notes chunks found in {chunk_dir}/")
        print("Expected files: chunk_000_notes.txt, chunk_001_notes.txt, ...")
        sys.exit(1)

    parts = []
    for path in notes:
        with path.open(encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                parts.append(content)

    result = "\n---\n".join(parts) + "\n"
    result = apply_corrections(result)
    result = cleanup_raw_notes_text(result)

    output_path = Path(args.output_file)
    output_path.write_text(result, encoding="utf-8")

    print(f"Concatenated {len(notes)} chunks -> {output_path}")
    print(f"  {result.count(chr(10))} lines, {len(result):,} chars")


def print_prompt(args):
    print(PROMPT_TEMPLATE.replace("{chunk_text}", "<contents of chunk_XXX.txt>"))
    print(f"\n# Recommended model: {RECOMMENDED_MODEL}")
    print("# Chunk contract:")
    print("# - Read chunk_XXX.txt")
    print("# - Use CONTEXT BEFORE/AFTER only for continuity")
    print("# - Write notes only for PRIMARY RANGE")
    print("# - Save output as chunk_XXX_notes.txt")


def clean_file(args):
    input_path = Path(args.input_file)
    output_path = Path(args.output_file or args.input_file)
    text = input_path.read_text(encoding="utf-8")
    cleaned = cleanup_raw_notes_text(apply_corrections(text))
    output_path.write_text(cleaned, encoding="utf-8")
    print(f"Cleaned raw notes: {output_path}")
    print(f"  {cleaned.count(chr(10))} lines, {len(cleaned):,} chars")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare", help="Create chunk files for raw-note generation")
    p_prepare.add_argument("input_file", help="Transcript file, usually OOC-filtered")
    p_prepare.add_argument("output_dir", help="Directory for chunk files")
    p_prepare.add_argument("--chunk-size", type=int, default=20, help="Primary entries per chunk (default: 20)")
    p_prepare.add_argument("--overlap", type=int, default=5, help="Context entries before/after each chunk (default: 5)")

    p_concat = sub.add_parser("concat", help="Concatenate raw note chunks into one session note file")
    p_concat.add_argument("chunk_dir", help="Directory containing chunk_XXX_notes.txt files")
    p_concat.add_argument("output_file", help="Output raw session notes path")

    p_clean = sub.add_parser("clean", help="Clean seam artifacts in an existing raw session note file")
    p_clean.add_argument("input_file", help="Existing raw session notes path")
    p_clean.add_argument("output_file", nargs="?", help="Optional output path; defaults to in-place")

    sub.add_parser("prompt", help="Print the LLM/subagent prompt template")

    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.command == "concat":
        concat(args)
    elif args.command == "clean":
        clean_file(args)
    elif args.command == "prompt":
        print_prompt(args)


if __name__ == "__main__":
    main()
