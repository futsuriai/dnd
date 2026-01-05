import sys
import os
import torch
from faster_whisper import WhisperModel

# Supported audio extensions
AUDIO_EXTENSIONS = {'.flac', '.mp3', '.wav', '.m4a', '.ogg'}

def transcribe_file(model, audio_path, output_path):
    print(f"Transcribing {audio_path}...")
    try:
        segments, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")

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
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def load_model(model_size="large-v3", device="cuda", compute_type="float16"):
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

    # Load model once
    model = load_model()
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
        
        transcribe_file(model, audio_file, output_file)

if __name__ == "__main__":
    main()