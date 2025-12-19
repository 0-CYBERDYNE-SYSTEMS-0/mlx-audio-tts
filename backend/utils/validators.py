"""
Input validation utilities for the TTS API.
"""
import os
from pathlib import Path
from typing import Optional

from backend.config import (
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    MIN_SPEED,
    MAX_SPEED,
    MIN_TEMPERATURE,
    MAX_TEMPERATURE,
)


def validate_text(text: str) -> str:
    """Validate text input for TTS generation."""
    if not text or not text.strip():
        raise ValueError("Text input is required")

    if len(text) > 5000:
        raise ValueError("Text input exceeds maximum length of 5000 characters")

    return text.strip()


def validate_speed(speed: float) -> float:
    """Validate speed parameter."""
    if not isinstance(speed, (int, float)):
        raise ValueError("Speed must be a number")

    if speed < MIN_SPEED or speed > MAX_SPEED:
        raise ValueError(f"Speed must be between {MIN_SPEED} and {MAX_SPEED}")

    return float(speed)


def validate_temperature(temperature: float) -> float:
    """Validate temperature parameter."""
    if not isinstance(temperature, (int, float)):
        raise ValueError("Temperature must be a number")

    if temperature < MIN_TEMPERATURE or temperature > MAX_TEMPERATURE:
        raise ValueError(f"Temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}")

    return float(temperature)


def validate_audio_file(file_path: str, file_size: int) -> bool:
    """Validate uploaded audio file."""
    if not os.path.exists(file_path):
        raise ValueError("Uploaded file not found")

    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum of {MAX_FILE_SIZE // (1024*1024)}MB")

    # Check file extension
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")

    # Note: Magic bytes check skipped - relying on extension validation
    # This is acceptable for internal use where file sources are trusted

    return True


def validate_voice_mode(mode: str, voice: Optional[str], ref_audio_id: Optional[str]) -> dict:
    """Validate voice selection mode and parameters."""
    if mode not in ['preset', 'clone']:
        raise ValueError("Mode must be 'preset' or 'clone'")

    if mode == 'preset':
        if not voice:
            raise ValueError("Voice selection is required for preset mode")
        return {'mode': 'preset', 'voice': voice}

    elif mode == 'clone':
        if not ref_audio_id:
            raise ValueError("Reference audio ID is required for clone mode")
        return {'mode': 'clone', 'ref_audio_id': ref_audio_id}

    return {}
