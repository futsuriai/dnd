"""
Merge a Zoom (speaker-labeled) and Whisper (text-accurate) transcript into
a single diarized output, with canonical name corrections.

This script performs the MECHANICAL portion of the merge:
1. Parses both transcripts
2. Aligns Whisper segments to Zoom speaker turns by timestamp
3. Applies regex-based name corrections from an entity list
4. Outputs a side-by-side JSONL file for LLM refinement

The LLM step (not automated here) processes each chunk to:
- Synthesize the best wording from both sources
- Fix contextual name errors regex can't catch
- Handle speaker attribution when Whisper segments span multiple turns

Usage:
    python merge_transcripts.py <zoom_file> <whisper_file> <entity_list> <output_dir>

Outputs:
    <output_dir>/chunks/        - Individual chunk files (zoom + whisper pairs)
    <output_dir>/merged_mechanical.txt - Regex-only mechanical merge (fallback)
"""
import re
import os
import sys
import json
import argparse
from bisect import bisect_right


def time_to_sec(hms: str) -> int:
    parts = hms.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def sec_to_time(s: int) -> str:
    return f'{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}'


# Canonical name correction map
# Keys: common mis-transcriptions. Values: canonical spelling.
NAME_FIXES = {
    'Mary': 'Meri',
    'Merry': 'Meri',
    'Isidore': 'Ysidor',
    'Isidor': 'Ysidor',
    'Yesodor': 'Ysidor',
    'Yasura': 'Ysidor',
    'Ysidore': 'Ysidor',
    'Yisidor': 'Ysidor',
    'Alara': 'Ellara',
    'Eleah': 'Ellara',
    'Elara': 'Ellara',
    'Beridin': 'Berridin',
    'Beriden': 'Berridin',
    'Nix': 'Nyx',
    'Nixon': 'Nyx',
    'Nicks': 'Nyx',
    'Hyuba': 'Hýrda',
}

# Speaker label normalization (Zoom display names → canonical)
SPEAKER_FIXES = {
    'Witty': 'Whitaker',
    'Beridin': 'Berridin',
}


def build_name_patterns(fixes: dict) -> list:
    patterns = []
    for key in sorted(fixes.keys(), key=len, reverse=True):
        pat = re.compile(r'(?<!\w)' + re.escape(key) + r'(?!\w)')
        patterns.append((pat, fixes[key]))
    return patterns


def apply_name_fixes(text: str, patterns: list) -> str:
    for pat, repl in patterns:
        text = pat.sub(repl, text)
    return text


def parse_zoom(path: str) -> list:
    speaker_re = re.compile(r'^\[(.+?)\]\s+(\d{2}:\d{2}:\d{2})\s*$')
    turns = []
    current = None
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = speaker_re.match(line)
            if m:
                if current:
                    current['text'] = ' '.join(current['_lines']).strip()
                    del current['_lines']
                    turns.append(current)
                speaker = m.group(1).strip()
                speaker = SPEAKER_FIXES.get(speaker, speaker)
                current = {
                    'speaker': speaker,
                    'time': m.group(2),
                    'time_sec': time_to_sec(m.group(2)),
                    '_lines': [],
                }
            elif current:
                s = line.strip()
                if s:
                    current['_lines'].append(s)
    if current:
        current['text'] = ' '.join(current['_lines']).strip()
        del current['_lines']
        turns.append(current)
    return turns


def parse_whisper(path: str) -> list:
    pattern = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\s*->\s*(\d{2}:\d{2}:\d{2})\]\s*(.*)$')
    segs = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                segs.append({
                    'start_sec': time_to_sec(m.group(1)),
                    'text': m.group(3).strip(),
                    'raw': line.strip(),
                })
    return segs


def build_chunks(zoom_turns, whisper_segs, chunk_size=50):
    """Build chunks pairing Zoom turns with overlapping Whisper segments."""
    chunks = []
    for i in range(0, len(zoom_turns), chunk_size):
        batch = zoom_turns[i:i + chunk_size]
        t_start = batch[0]['time_sec']
        t_end = zoom_turns[i + chunk_size]['time_sec'] if i + chunk_size < len(zoom_turns) else 999999

        zoom_block = []
        for t in batch:
            zoom_block.append(f"[{t['speaker']}] {t['time']}")
            if t['text']:
                zoom_block.append(t['text'])
            zoom_block.append('')

        whisper_block = [s['raw'] for s in whisper_segs
                         if s['start_sec'] >= t_start and s['start_sec'] < t_end]

        chunks.append({
            'chunk_id': i // chunk_size,
            'time_range': f"{sec_to_time(t_start)} - {sec_to_time(min(t_end, 999999))}",
            'zoom_text': '\n'.join(zoom_block),
            'whisper_text': '\n'.join(whisper_block),
        })
    return chunks


def mechanical_merge(zoom_turns, whisper_segs, name_patterns):
    """Simple timestamp-based merge with regex name fixes (no LLM)."""
    zoom_times = [t['time_sec'] for t in zoom_turns]

    # Assign whisper segments to zoom turns by timestamp
    whisper_for_turn = {i: [] for i in range(len(zoom_turns))}
    for seg in whisper_segs:
        idx = bisect_right(zoom_times, seg['start_sec']) - 1
        if idx >= 0:
            whisper_for_turn[idx].append(seg['text'])

    lines = []
    for i, turn in enumerate(zoom_turns):
        if whisper_for_turn[i]:
            text = ' '.join(whisper_for_turn[i]).strip()
        else:
            text = turn['text']
        text = apply_name_fixes(text, name_patterns)
        if text:
            lines.append(f"[{turn['time']}] {turn['speaker']}: {text}")
    return '\n\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('zoom_file')
    parser.add_argument('whisper_file')
    parser.add_argument('entity_list', help='Path to ENTITY_LIST.md (for reference)')
    parser.add_argument('output_dir', help='Directory for output files')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    chunks_dir = os.path.join(args.output_dir, 'chunks')
    os.makedirs(chunks_dir, exist_ok=True)

    name_patterns = build_name_patterns(NAME_FIXES)

    print(f"Parsing Zoom: {args.zoom_file}")
    zoom_turns = parse_zoom(args.zoom_file)
    print(f"  {len(zoom_turns)} turns")

    print(f"Parsing Whisper: {args.whisper_file}")
    whisper_segs = parse_whisper(args.whisper_file)
    print(f"  {len(whisper_segs)} segments")

    # Build chunks for LLM processing
    chunks = build_chunks(zoom_turns, whisper_segs)
    for c in chunks:
        zoom_path = os.path.join(chunks_dir, f"c{c['chunk_id']}_zoom.txt")
        whisper_path = os.path.join(chunks_dir, f"c{c['chunk_id']}_whisper.txt")
        with open(zoom_path, 'w', encoding='utf-8') as f:
            f.write(c['zoom_text'])
        with open(whisper_path, 'w', encoding='utf-8') as f:
            f.write(c['whisper_text'])
    print(f"Wrote {len(chunks)} chunk pairs to {chunks_dir}/")

    # Also produce a mechanical merge as baseline
    mech_path = os.path.join(args.output_dir, 'merged_mechanical.txt')
    mech = mechanical_merge(zoom_turns, whisper_segs, name_patterns)
    with open(mech_path, 'w', encoding='utf-8') as f:
        f.write(mech)
    print(f"Wrote mechanical merge to {mech_path}")


if __name__ == '__main__':
    main()
