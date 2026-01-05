# Session Transcription Guide

This guide documents the process for transcribing and diarizing D&D sessions using local AI tools on Linux (WSL).

## 🚀 Quick Start (If Already Setup)

If you have performed this setup before (e.g., on Dec 29, 2025), you can likely skip the installation steps.

**1. Check if the environment exists:**
```bash
ls -d ~/.gemini/tmp/transcribe_env && echo "Environment Found ✅" || echo "Environment Missing ❌"
```

**2. Check if the script exists:**
```bash
ls transcribe.py && echo "Script Found ✅" || echo "Script Missing ❌"
```

**3. If both are ✅, run the transcription immediately:**
```bash
# Set up library paths (REQUIRED every time you open a new terminal)
export VENV_SITE="$HOME/.gemini/tmp/transcribe_env/lib/python3.12/site-packages"
export LD_LIBRARY_PATH="$VENV_SITE/nvidia/cudnn/lib:$VENV_SITE/nvidia/cublas/lib:$VENV_SITE/nvidia/cudart/lib:$LD_LIBRARY_PATH"

# Run the script
nohup ~/.gemini/tmp/transcribe_env/bin/python3 transcribe.py "/path/to/audio.mp3" "output.txt" > transcribe.log 2>&1 &
```

---

## 1. First-Time Setup (Only if Quick Start failed)

Follow these steps only if the "Environment Found" check above failed.

### Install System Dependencies
(Ubuntu/Debian based systems)
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv build-essential git python3-dev
```

### Create Python Virtual Environment
We use a dedicated virtual environment to avoid conflicts.
```bash
# Create the environment (if not exists)
python3 -m venv ~/.gemini/tmp/transcribe_env

# Activate it
source ~/.gemini/tmp/transcribe_env/bin/activate
```

### Install AI Libraries
We use `faster-whisper` for optimized transcription and `torch` with CUDA support.
```bash
# Install PyTorch with CUDA 12.1 support
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install transcription engine
pip install faster-whisper
```

## 2. The Transcription Script

Save the following code as `transcribe.py` in your project root.

```python
import sys
import torch
from faster_whisper import WhisperModel

def transcribe(audio_path, output_path, model_size="large-v3", device="cuda", compute_type="float16"):
    print(f"Loading model: {model_size} on {device} ({compute_type})...")
    
    try:
        # Load model (downloads automatically on first run)
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"Transcribing {audio_path}...")
    # vad_filter=True removes silence/non-speech
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
    
    transcribe(audio_file, output_file)
```

## 3. How to Run Transcription

**Crucial Step for WSL/Linux:**
You must export the library paths so the AI engine can find the NVIDIA libraries (cuDNN).

```bash
# 1. Define the path to the venv site-packages
export VENV_SITE="$HOME/.gemini/tmp/transcribe_env/lib/python3.12/site-packages"

# 2. Add NVIDIA libs to LD_LIBRARY_PATH
export LD_LIBRARY_PATH="$VENV_SITE/nvidia/cudnn/lib:$VENV_SITE/nvidia/cublas/lib:$VENV_SITE/nvidia/cudart/lib:$LD_LIBRARY_PATH"

# 3. Run the script (in background with nohup is recommended for long files)
nohup ~/.gemini/tmp/transcribe_env/bin/python3 transcribe.py "/path/to/audio.mp3" "output.txt" > transcribe.log 2>&1 &
```

**Monitoring Progress:**
```bash
# Check the text output as it happens
tail -f output.txt

# Check process status (CPU/Memory)
top -p $(pgrep -f transcribe.py)

# Check GPU usage
nvidia-smi
```

## 4. Improvements & Optimization

### Speed vs. Accuracy
The script defaults to `model_size="large-v3"`. This is the most accurate but slowest.
*   **Large-v3:** Best for accents, overlapping speech, and D&D terminology. Speed: ~0.6x real-time (on GTX 1660 Ti).
*   **Medium:** Good balance. Speed: ~2-3x real-time. Much faster restart if `large` fails.
*   **Small/Base:** Very fast, but higher error rate.

To change this, edit the `transcribe` function call in the script:
```python
transcribe(audio_file, output_file, model_size="medium")
```

### True Diarization (Speaker Labels)
The current script gives timestamps but doesn't label "Speaker 1" vs "Speaker 2".
To add this in the future:
1.  **Get a HuggingFace Token:** Create an account and get a read-access token.
2.  **Accept Terms:** Go to the `pyannote/speaker-diarization` page on HuggingFace and accept the user agreement.
3.  **Install Library:** `pip install pyannote.audio`
4.  **Update Script:** Use the pyannote pipeline to process the audio *after* transcription to assign speakers to segments.

### Troubleshooting
*   **OOM (Out Of Memory):** If the script crashes immediately, your GPU VRAM is full. Switch to `medium` model or close other apps (browser, games).
*   **Stuck/Slow:** If output stops for >5 mins, the model might be hallucinating on silence/music. Restarting with `medium` often fixes this.
