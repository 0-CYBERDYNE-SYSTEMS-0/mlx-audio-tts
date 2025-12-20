#!/bin/bash
# Start TTS Service

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"

# Activate environment if using UV
if command -v uv &> /dev/null; then
    export PATH="$HOME/.cargo/bin:$PATH"
    export TTS_CLONE_MODEL="senstella/csm-1b-mlx"
    uv run python -m backend.main --production
else
    export TTS_CLONE_MODEL="senstella/csm-1b-mlx"
    /Users/scrimwiggins/miniconda3/bin/python3 -m backend.main --production
fi
