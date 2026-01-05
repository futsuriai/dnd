#!/bin/bash
# Path to the virtual environment
VENV_PATH="$HOME/.gemini/tmp/transcribe_env"

# Ensure venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Set up library paths for NVIDIA/CUDA support
export VENV_SITE="$VENV_PATH/lib/python3.12/site-packages"
export LD_LIBRARY_PATH="$VENV_SITE/nvidia/cudnn/lib:$VENV_SITE/nvidia/cublas/lib:$VENV_SITE/nvidia/cudart/lib:$LD_LIBRARY_PATH"

# Run the transcription script
echo "Starting transcription for directory: $1"
"$VENV_PATH/bin/python3" scripts/transcription/transcribe.py "$1"
