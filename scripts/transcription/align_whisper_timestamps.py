"""
Align Whisper transcript timestamps to match a Zoom transcript's clock.

Whisper transcripts start at 00:00:00 relative to the recording start.
Zoom transcripts use wall-clock time (e.g., 13:39:12). This script computes
the offset by matching distinctive dialogue lines between both files, then
rewrites the Whisper timestamps in-place.

Usage:
    python align_whisper_timestamps.py <zoom_file> <whisper_file> [--dry-run]

The script finds matching lines using difflib, computes a median offset from
multiple triangulation points, and shifts all Whisper timestamps by that offset.
"""
import re
import sys
import argparse
from difflib import SequenceMatcher


def time_to_sec(hms: str) -> int:
    parts = hms.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def sec_to_time(s: int) -> str:
    return f'{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}'


def normalize(text: str) -> str:
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', text.lower()).split())


def parse_zoom_turns(path: str) -> list:
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
                current = {
                    'speaker': m.group(1),
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


def parse_whisper_segments(path: str) -> list:
    pattern = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\s*->\s*(\d{2}:\d{2}:\d{2})\]\s*(.*)$')
    segs = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                segs.append({
                    'start_sec': time_to_sec(m.group(1)),
                    'end_sec': time_to_sec(m.group(2)),
                    'text': m.group(3).strip(),
                })
    return segs


def compute_offset(zoom_turns, whisper_segs, sample_count=60, min_text_len=30):
    """Find matching lines between Zoom and Whisper, return median offset."""
    zoom_data = [(normalize(t['text']), t['time_sec']) for t in zoom_turns if len(t['text']) >= 20]
    offsets = []

    for seg in whisper_segs[:sample_count]:
        if len(seg['text']) < min_text_len:
            continue
        w_norm = normalize(seg['text'])
        best_ratio, best_zoom_sec = 0.0, None
        for z_norm, z_sec in zoom_data:
            ratio = SequenceMatcher(None, w_norm, z_norm).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_zoom_sec = z_sec
        if best_ratio >= 0.6 and best_zoom_sec is not None:
            offsets.append(best_zoom_sec - seg['start_sec'])

    if not offsets:
        raise RuntimeError("Could not find enough matching lines to compute offset")

    offsets.sort()
    return offsets[len(offsets) // 2]  # median


def apply_offset(whisper_path: str, offset: int, dry_run: bool = False):
    pattern = re.compile(r'\[(\d{2}:\d{2}:\d{2})\s*->\s*(\d{2}:\d{2}:\d{2})\]')

    with open(whisper_path, encoding='utf-8') as f:
        content = f.read()

    def replace_ts(m):
        start = sec_to_time(time_to_sec(m.group(1)) + offset)
        end = sec_to_time(time_to_sec(m.group(2)) + offset)
        return f'[{start} -> {end}]'

    new_content = pattern.sub(replace_ts, content)

    if dry_run:
        lines = new_content.splitlines()
        print("First line:", lines[0] if lines else "(empty)")
        print("Last line:", lines[-1] if lines else "(empty)")
        print(f"Offset: {offset} sec ({sec_to_time(offset)})")
    else:
        with open(whisper_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Applied offset {offset}s ({sec_to_time(offset)}) to {whisper_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('zoom_file', help='Path to the Zoom transcript (speaker-labeled)')
    parser.add_argument('whisper_file', help='Path to the Whisper transcript (timestamped)')
    parser.add_argument('--dry-run', action='store_true', help='Print offset without modifying files')
    args = parser.parse_args()

    print(f"Parsing Zoom transcript: {args.zoom_file}")
    zoom_turns = parse_zoom_turns(args.zoom_file)
    print(f"  {len(zoom_turns)} turns")

    print(f"Parsing Whisper transcript: {args.whisper_file}")
    whisper_segs = parse_whisper_segments(args.whisper_file)
    print(f"  {len(whisper_segs)} segments")

    offset = compute_offset(zoom_turns, whisper_segs)
    print(f"Computed offset: {offset} sec ({sec_to_time(offset)})")

    apply_offset(args.whisper_file, offset, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
