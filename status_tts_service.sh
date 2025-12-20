#!/bin/bash
# Check TTS Service Status

cd "$(dirname "$0")"
python3 service/tts_manager.py status
