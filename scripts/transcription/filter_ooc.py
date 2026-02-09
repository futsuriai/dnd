"""
Filter out-of-character (OOC) dialogue from a diarized D&D session transcript.

This script prepares chunks for LLM-based OOC filtering and can concatenate
the results. The LLM classifies each entry as in-game or OOC, keeping only
in-game content.

Usage:
    # Step 1: Split into chunks and generate prompts
    python filter_ooc.py prepare session-XX-diarized.txt ./ooc_chunks

    # Step 2: Process each chunk through an LLM (e.g., Copilot CLI)
    #   See --print-prompt for the prompt template
    #   Input:  ooc_chunks/chunk_NN.txt
    #   Output: ooc_chunks/chunk_NN_filtered.txt

    # Step 3: Concatenate filtered chunks
    python filter_ooc.py concat ./ooc_chunks session-XX-ingame.txt

Options:
    --chunk-size N     Entries per chunk (default: 60)
    --print-prompt     Print the LLM prompt template and exit
"""
import re
import os
import sys
import argparse
from pathlib import Path

# Recommended model: gpt-5.2-codex (or similar reasoning-capable model)
RECOMMENDED_MODEL = "gpt-5.2-codex"

PROMPT_TEMPLATE = """\
You are filtering a D&D session transcript to extract only IN-GAME content.

Read the following transcript chunk. For each entry, decide:
- **KEEP**: GM narration, world-building, in-character dialogue, NPC speech,
  session recaps, in-game strategic discussion, dice rolls/checks
- **REMOVE**: Pre/post-game chatter, real-world tangents, meta-commentary about
  recording/tech, player banter not in-character, scheduling, jokes about
  real-world topics unrelated to the game

Output ONLY the kept entries, preserving their exact format ([HH:MM:SS] Speaker: text).
Do not add commentary. Do not renumber. Preserve blank lines between entries.

When in doubt, KEEP the entry — it's better to include borderline content than
lose in-game material.

=== TRANSCRIPT CHUNK ===
{chunk_text}
=== END CHUNK ===

Output the filtered entries below:"""


def parse_entries(text):
    """Split diarized transcript into individual entries."""
    return [e.strip() for e in re.split(r'\n\n+', text.strip()) if e.strip()]


def prepare(args):
    with open(args.input_file, encoding='utf-8') as f:
        text = f.read()

    entries = parse_entries(text)
    os.makedirs(args.output_dir, exist_ok=True)

    chunk_id = 0
    for i in range(0, len(entries), args.chunk_size):
        batch = entries[i:i + args.chunk_size]
        chunk_path = os.path.join(args.output_dir, f'chunk_{chunk_id:02d}.txt')
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(batch) + '\n')
        chunk_id += 1

    print(f"Split {len(entries)} entries into {chunk_id} chunks in {args.output_dir}/")
    print(f"\nRecommended model: {RECOMMENDED_MODEL}")
    print(f"Process each chunk with the prompt from --print-prompt")
    print(f"Save results as chunk_NN_filtered.txt in the same directory")


def concat(args):
    chunk_dir = Path(args.chunk_dir)
    filtered = sorted(chunk_dir.glob('chunk_*_filtered.txt'))

    if not filtered:
        print(f"No filtered chunks found in {chunk_dir}/")
        print("Expected files: chunk_00_filtered.txt, chunk_01_filtered.txt, ...")
        sys.exit(1)

    parts = []
    for p in filtered:
        with open(p, encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                parts.append(content)

    result = '\n\n'.join(parts) + '\n'
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    entries = parse_entries(result)
    print(f"Concatenated {len(filtered)} chunks → {args.output_file}")
    print(f"  {len(entries)} entries, {len(result):,} chars")


def print_prompt(args):
    print(PROMPT_TEMPLATE.replace('{chunk_text}', '<contents of chunk_NN.txt>'))
    print(f"\n# Recommended model: {RECOMMENDED_MODEL}")
    print(f"# Example Copilot CLI invocation:")
    print(f'# Use task agent (general-purpose, model: {RECOMMENDED_MODEL}) with prompt:')
    print(f'#   "Read /path/to/chunk_NN.txt and apply the OOC filter. Write result to chunk_NN_filtered.txt"')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)

    p_prepare = sub.add_parser('prepare', help='Split transcript into chunks')
    p_prepare.add_argument('input_file', help='Diarized transcript file')
    p_prepare.add_argument('output_dir', help='Directory for chunk files')
    p_prepare.add_argument('--chunk-size', type=int, default=60,
                          help='Entries per chunk (default: 60)')

    p_concat = sub.add_parser('concat', help='Concatenate filtered chunks')
    p_concat.add_argument('chunk_dir', help='Directory containing filtered chunks')
    p_concat.add_argument('output_file', help='Output ingame transcript path')

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
