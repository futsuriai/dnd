import os
import sys
import re
import json

# Path to speaker map
SPEAKER_MAP_FILE = os.path.join(os.path.dirname(__file__), 'speaker_map.json')

def load_speaker_map():
    if os.path.exists(SPEAKER_MAP_FILE):
        with open(SPEAKER_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def parse_timestamp(timestamp_str):
    """Converts HH:MM:SS or H:MM:SS to seconds."""
    parts = timestamp_str.split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def identify_speaker(filename, speaker_map):
    """Identifies speaker from filename using the map."""
    base_name = os.path.basename(filename).lower()
    for key, name in speaker_map.items():
        clean_key = os.path.basename(key).lower()
        if clean_key.replace('.png', '').replace('.webp', '').replace('.jpeg', '') in base_name:
             return name
        if key.lower() in base_name:
            return name
    name_part = os.path.splitext(base_name)[0]
    name_part = name_part.replace('.flac', '').replace('.mp3', '').replace('.wav', '')
    return name_part.title()

def process_file(filepath, speaker_name):
    entries = []
    # VERY loose regex to debug
    # Just look for something that looks like a timestamp in brackets
    pattern = re.compile(r'\[(\d+:\d+:\d+).*?\]\s*(.*)')
    
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        count = 0
        for line in f:
            line = line.strip()
            if not line: continue
            match = pattern.search(line)
            if match:
                start_str, text = match.groups()
                start_sec = parse_timestamp(start_str)
                entries.append({
                    'start': start_sec,
                    'start_str': start_str,
                    'speaker': speaker_name,
                    'text': text.strip()
                })
                count += 1
        print(f"  Matched {count} lines in {filepath}")
    return entries

def main():
    if len(sys.argv) < 2:
        print("Usage: python combine_transcripts.py <directory_with_transcripts> [output_file]")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "combined_transcript.txt"

    speaker_map = load_speaker_map()
    all_entries = []

    print(f"Scanning {input_dir} for transcript files...")
    
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a directory.")
        sys.exit(1)

    output_path = os.path.abspath(output_file)

    for file in os.listdir(input_dir):
        if file.endswith('.txt') and file != os.path.basename(output_path) and file != "transcribe.log" and file != "info.txt":
            filepath = os.path.join(input_dir, file)
            speaker = identify_speaker(file, speaker_map)
            print(f"Processing {file} (Speaker: {speaker})")
            entries = process_file(filepath, speaker)
            all_entries.extend(entries)

    if not all_entries:
        print("No entries found to combine!")
        return

    all_entries.sort(key=lambda x: x['start'])

    print(f"Writing combined transcript to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in all_entries:
            ts = entry['start_str']
            if ts.count(':') == 2 and len(ts.split(':')[0]) == 1:
                ts = '0' + ts
            line = f"[{ts}] {entry['speaker']}: {entry['text']}\n"
            f.write(line)
    print("Done.")

if __name__ == "__main__":
    main()