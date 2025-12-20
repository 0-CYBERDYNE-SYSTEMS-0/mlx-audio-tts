#!/bin/bash
# Stop TTS Service

cd "$(dirname "$0")"
python3 service/tts_manager.py stop
