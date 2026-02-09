"""
Generate raw session notes from an in-game transcript.

Converts a diarized in-game transcript into condensed prose-style session notes
matching the format used in Raw Session 1-4. This is an LLM-assisted process:
the script handles chunking and concatenation, while the LLM does the actual
summarization.

Usage:
    # Step 1: Split transcript into narrative chunks
    python generate_raw_notes.py prepare session-XX-ingame.txt ./notes_chunks

    # Step 2: Process each chunk through an LLM (e.g., Copilot CLI)
    #   See --print-prompt for the prompt template
    #   Input:  notes_chunks/chunk_N.txt
    #   Output: notes_chunks/chunk_N_notes.txt

    # Step 3: Concatenate and apply name corrections
    python generate_raw_notes.py concat ./notes_chunks "Raw Session XX.md" \
        --entity-list ENTITY_LIST.md

Options:
    --chunk-size N     Entries per chunk (default: 120)
    --print-prompt     Print the LLM prompt template and exit
"""
import re
import os
import sys
import json
import argparse
from pathlib import Path

# Recommended model: gpt-5.2-codex (or similar reasoning-capable model)
RECOMMENDED_MODEL = "gpt-5.2-codex"

PROMPT_TEMPLATE = """\
Convert this D&D session transcript into raw session notes.

**FORMAT RULES:**
- Casual shorthand prose, not verbatim transcript
- Use `---` as scene/beat separators
- Character names lowercase in dialogue attribution: `nyx: "quote here"`
- GM narration summarized into concise descriptions
- **CRITICAL: Preserve ALL in-character dialogue.** Every line where a character
  speaks in-character should appear as a quote. Clean up filler words (um, uh,
  like) but keep the substance and voice intact.
- Dice rolls/checks noted when mentioned (e.g., "perception 15")
- Third-person perspective for action descriptions
- Strip timestamps — they are not needed in the notes
- Group rapid back-and-forth exchanges naturally
- Note important world-building details
- Players sometimes describe their characters' actions in first person — convert
  to third person shorthand

**EXAMPLE of the target style:**
```
nyx: "we have nothing else to go on, so let's go back to the city like ysidor suggested"
we will camp here for the night.
---
nyx picks up the light crystals (3), they are roughly fist sized
nyx: investigation 5. you see the crystals as dimly glowing.
---
ellara: "it's time for bed, perhaps tomorrow we should ask proctor edouard about those constructs"
nyx: "sure, be careful"
ysidor: "are you not worried for your safety, there's some dark magic going on"
ellara: "exactly, who better to ask"
```

=== TRANSCRIPT CHUNK ===
{chunk_text}
=== END CHUNK ===

Output the raw session notes below (no commentary, just the notes):"""

# Canonical name corrections for post-processing
NAME_CORRECTIONS = {
    "here's embrace": "hýrda's embrace",
    "heroterra": "hieroterra",
    "Heroterra": "Hieroterra",
}


def parse_entries(text):
    return [e.strip() for e in re.split(r'\n\n+', text.strip()) if e.strip()]


def prepare(args):
    with open(args.input_file, encoding='utf-8') as f:
        text = f.read()

    entries = parse_entries(text)
    os.makedirs(args.output_dir, exist_ok=True)

    chunk_id = 0
    for i in range(0, len(entries), args.chunk_size):
        batch = entries[i:i + args.chunk_size]
        chunk_path = os.path.join(args.output_dir, f'chunk_{chunk_id}.txt')
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(batch) + '\n')
        chunk_id += 1

    print(f"Split {len(entries)} entries into {chunk_id} chunks in {args.output_dir}/")
    print(f"\nRecommended model: {RECOMMENDED_MODEL}")
    print(f"Process each chunk with the prompt from: python {sys.argv[0]} prompt")
    print(f"Save results as chunk_N_notes.txt in the same directory")


def apply_corrections(text):
    """Apply canonical name corrections to generated notes."""
    for wrong, right in NAME_CORRECTIONS.items():
        text = text.replace(wrong, right)

    # Also fix nýtes with word-boundary awareness
    text = re.sub(r'(?<!\w)nites(?!\w)', 'nýtes', text)
    text = re.sub(r'(?<!\w)Nites(?!\w)', 'Nýtes', text)

    return text


def concat(args):
    chunk_dir = Path(args.chunk_dir)
    notes = sorted(chunk_dir.glob('chunk_*_notes.txt'))

    if not notes:
        print(f"No notes chunks found in {chunk_dir}/")
        print("Expected files: chunk_0_notes.txt, chunk_1_notes.txt, ...")
        sys.exit(1)

    parts = []
    for p in notes:
        with open(p, encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                parts.append(content)

    result = '\n---\n'.join(parts) + '\n'
    result = apply_corrections(result)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Concatenated {len(notes)} chunks → {args.output_file}")
    print(f"  {result.count(chr(10))} lines, {len(result):,} chars")


def print_prompt(args):
    print(PROMPT_TEMPLATE.replace('{chunk_text}', '<contents of chunk_N.txt>'))
    print(f"\n# Recommended model: {RECOMMENDED_MODEL}")
    print(f"# Example Copilot CLI invocation:")
    print(f'# Use task agent (general-purpose, model: {RECOMMENDED_MODEL}) with prompt:')
    print(f'#   "Read /path/chunk_N.txt. Convert to raw session notes per these rules: [paste FORMAT RULES]."')
    print(f'#   "Write result to /path/chunk_N_notes.txt"')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)

    p_prepare = sub.add_parser('prepare', help='Split transcript into chunks')
    p_prepare.add_argument('input_file', help='In-game transcript file')
    p_prepare.add_argument('output_dir', help='Directory for chunk files')
    p_prepare.add_argument('--chunk-size', type=int, default=120,
                          help='Entries per chunk (default: 120)')

    p_concat = sub.add_parser('concat', help='Concatenate notes chunks')
    p_concat.add_argument('chunk_dir', help='Directory containing notes chunks')
    p_concat.add_argument('output_file', help='Output raw session notes path')

    sub.add_parser('prompt', help='Print the LLM prompt template')

    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args)
    elif args.command == 'concat':
        concat(args)
    elif args.command == 'prompt':
        print_prompt(args)


if __name__ == '__main__':
    main()
