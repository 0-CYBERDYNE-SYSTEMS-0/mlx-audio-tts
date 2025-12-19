"""
Agent Integration Helper - Simplifies TTS integration for any agent.

This module provides a simple interface for agents to use the TTS service
without worrying about service management.
"""
import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from client.tts_client import TTSClient, create_speech
from service.tts_manager import ensure_tts_service, TTSManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSIntegration:
    """
    High-level TTS integration for agents.

    Handles service management automatically and provides simple methods
    for generating speech.
    """

    def __init__(
        self,
        auto_start: bool = True,
        base_url: str = "http://localhost:8000",
        production: bool = True,
        voice: str = "af_heart",
        speed: float = 1.0,
        temperature: float = 0.7,
        format: str = "wav"
    ):
        """
        Initialize TTS integration.

        Args:
            auto_start: Automatically start service if not running
            base_url: TTS service URL
            production: Use production mode
            voice: Default voice
            speed: Default speech speed
            temperature: Default randomness
            format: Default audio format
        """
        self.auto_start = auto_start
        self.base_url = base_url
        self.production = production
        self.default_voice = voice
        self.default_speed = speed
        self.default_temperature = temperature
        self.default_format = format

        # Initialize service manager and client
        self.manager = None
        self.client = None

        self._initialize()

    def _initialize(self):
        """Initialize service and client."""
        # Ensure service is running
        if self.auto_start:
            logger.info("Ensuring TTS service is available...")
            self.manager = ensure_tts_service(
                auto_start=self.auto_start,
                production=self.production
            )
            # Update base_url if service started on different port
            if self.manager:
                status = self.manager.get_status()
                if status.get("status") == "running":
                    self.base_url = f"http://{status['host']}:{status['port']}"

        # Initialize client
        self.client = TTSClient(base_url=self.base_url)
        logger.info(f"TTS integration ready with service at {self.base_url}")

    def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        temperature: Optional[float] = None,
        format: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech.

        Args:
            text: Text to speak
            voice: Voice to use (overrides default)
            speed: Speech speed (overrides default)
            temperature: Randomness (overrides default)
            format: Audio format (overrides default)

        Returns:
            Audio bytes
        """
        if not self.client:
            raise RuntimeError("TTS client not initialized")

        return self.client.audio.speech.create(
            text=text,
            voice=voice or self.default_voice,
            speed=speed or self.default_speed,
            temperature=temperature or self.default_temperature,
            response_format=format or self.default_format
        )

    def clone_voice(
        self,
        text: str,
        ref_audio_path: Union[str, Path],
        ref_text: Optional[str] = None,
        speed: Optional[float] = None,
        temperature: Optional[float] = None,
        format: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using voice cloning.

        Args:
            text: Text to speak
            ref_audio_path: Path to reference audio file
            ref_text: Optional reference text
            speed: Speech speed
            temperature: Randomness
            format: Audio format

        Returns:
            Audio bytes
        """
        if not self.client:
            raise RuntimeError("TTS client not initialized")

        # Upload reference audio
        upload_result = self.client.upload_reference_audio(ref_audio_path)
        ref_audio_id = upload_result.get("ref_audio_id")

        if not ref_audio_id:
            raise RuntimeError("Failed to upload reference audio")

        # Generate speech with cloned voice
        return self.client.audio.speech.create(
            text=text,
            voice="clone",
            mode="clone",
            ref_audio_id=ref_audio_id,
            ref_text=ref_text,
            speed=speed or self.default_speed,
            temperature=temperature or self.default_temperature,
            response_format=format or self.default_format
        )

    def list_voices(self) -> Dict[str, Any]:
        """List available voices."""
        if not self.client:
            raise RuntimeError("TTS client not initialized")
        return self.client.list_voices()

    def get_service_status(self) -> Dict[str, Any]:
        """Get TTS service status."""
        if self.manager:
            return self.manager.get_status()
        else:
            return {"status": "unknown", "message": "Service manager not initialized"}

    def stop_service(self):
        """Stop the TTS service (if auto-started)."""
        if self.manager and self.auto_start:
            self.manager.stop_service()
            logger.info("TTS service stopped")


# Global integration instance
_tts_integration: Optional[TTSIntegration] = None


def initialize_tts(
    auto_start: bool = True,
    base_url: str = "http://localhost:8000",
    production: bool = True,
    **kwargs
) -> TTSIntegration:
    """
    Initialize TTS integration globally.

    Args:
        auto_start: Automatically start service
        base_url: Service URL
        production: Production mode
        **kwargs: Additional arguments

    Returns:
        TTSIntegration instance
    """
    global _tts_integration
    _tts_integration = TTSIntegration(
        auto_start=auto_start,
        base_url=base_url,
        production=production,
        **kwargs
    )
    return _tts_integration


def get_tts() -> TTSIntegration:
    """Get the global TTS integration instance."""
    if _tts_integration is None:
        raise RuntimeError("TTS not initialized. Call initialize_tts() first.")
    return _tts_integration


def speak(text: str, **kwargs) -> bytes:
    """
    Quick function to speak text using the global TTS instance.

    Args:
        text: Text to speak
        **kwargs: Additional speech parameters

    Returns:
        Audio bytes
    """
    return get_tts().speak(text, **kwargs)


# Example usage
def example_usage():
    """Example of how to use the TTS integration."""
    # Method 1: Using the global interface
    initialize_tts(auto_start=True)

    # Simple speech generation
    audio = speak("Hello, world!")
    # Use audio bytes (play, save, etc.)

    # Custom voice
    audio = speak(
        "This is a different voice",
        voice="am_adam",
        speed=1.2
    )

    # Method 2: Using the class directly
    tts = TTSIntegration(
        auto_start=True,
        voice="af_heart",
        speed=0.9
    )

    audio = tts.speak("Hello from the class interface!")

    # Voice cloning
    audio = tts.clone_voice(
        "This is my cloned voice",
        ref_audio_path="path/to/reference.wav"
    )

    # List available voices
    voices = tts.list_voices()
    print(f"Available voices: {voices}")

    # Get service status
    status = tts.get_service_status()
    print(f"Service status: {status}")


# Command-line interface for testing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TTS Agent Integration")
    parser.add_argument("--text", default="Hello, this is a test of the TTS service.", help="Text to speak")
    parser.add_argument("--voice", default="af_heart", help="Voice to use")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--production", action="store_true", default=True, help="Use production mode")
    parser.add_argument("--dev", action="store_true", help="Use development mode")

    args = parser.parse_args()

    if args.dev:
        args.production = False

    if args.list_voices:
        # Initialize and list voices
        tts = TTSIntegration(auto_start=False, production=args.production)
        try:
            voices = tts.list_voices()
            print("Available voices:")
            for voice in voices.get("voices", []):
                print(f"  - {voice['id']}: {voice['name']}")
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure the TTS service is running")

    elif args.status:
        # Show service status
        tts = TTSIntegration(auto_start=False, production=args.production)
        status = tts.get_service_status()
        print("TTS Service Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    else:
        # Generate speech
        print(f"Initializing TTS integration...")
        tts = TTSIntegration(
            auto_start=True,
            production=args.production,
            voice=args.voice
        )

        print(f"Generating speech for: '{args.text}'")
        try:
            audio = tts.speak(args.text)
            print(f"Generated {len(audio)} bytes of audio data")

            if args.output:
                with open(args.output, 'wb') as f:
                    f.write(audio)
                print(f"Saved audio to: {args.output}")
            else:
                print("Audio generated successfully (no output file specified)")

        except Exception as e:
            print(f"Error generating speech: {e}")