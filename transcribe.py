import sys
import torch
from faster_whisper import WhisperModel

def transcribe(audio_path, output_path, model_size="large-v3", device="cuda", compute_type="float16"):
    print(f"Loading model: {model_size} on {device} ({compute_type})...")
    
    # Run on GPU with FP16
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"Transcribing {audio_path}...")
    segments, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)

    print(f"Detected language '{info.language}' with probability {info.language_probability}")

    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            # Format: [00:00:00 -> 00:00:05] Text
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            line = f"[{start} -> {end}] {segment.text}"
            print(line) # Print to console to show progress
            f.write(line + "\n")

    print(f"Transcription saved to {output_path}")

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transcribe.py <audio_file> <output_txt_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # specific optimization for 1660 Ti (Turing) - float16 is supported
    transcribe(audio_file, output_file)
