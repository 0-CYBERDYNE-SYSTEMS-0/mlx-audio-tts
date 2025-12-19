"""
One-Stop Voice Cloning Interface
Provides a simple interface for agents to record, clone, and generate speech with custom voices.
"""
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Callable

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from client.tts_client import TTSClient
from service.tts_manager import ensure_tts_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceCloner:
    """
    One-stop interface for voice cloning and TTS generation.

    Provides simple methods to:
    1. Record voice samples
    2. Clone the voice
    3. Generate speech with the cloned voice
    """

    def __init__(
        self,
        auto_start_service: bool = True,
        base_url: str = "http://localhost:8000"
    ):
        """
        Initialize voice cloner.

        Args:
            auto_start_service: Automatically start TTS service
            base_url: TTS service URL
        """
        self.base_url = base_url

        # Ensure service is running
        if auto_start_service:
            logger.info("Ensuring TTS service is available...")
            manager = ensure_tts_service(auto_start=True)
            status = manager.get_status()
            if status.get("status") == "running":
                self.base_url = f"http://{status['host']}:{status['port']}"
                logger.info(f"TTS service running at {self.base_url}")

        # Initialize client
        self.client = TTSClient(base_url=self.base_url)
        logger.info("Voice cloner initialized")

    def record_voice_sample(
        self,
        prompt_text: str = "Please say the following: The quick brown fox jumps over the lazy dog.",
        duration_hint: float = 5.0,
        device_id: Optional[str] = None,
        auto_stop: bool = False
    ) -> Dict[str, Any]:
        """
        Record a voice sample for cloning.

        Args:
            prompt_text: Text to display to the user
            duration_hint: Expected duration in seconds
            device_id: Audio device ID (None for default)
            auto_stop: Whether to automatically stop after duration_hint

        Returns:
            Recording session information
        """
        logger.info(f"Voice recording prompt: {prompt_text}")

        # Start recording
        result = self.client.audio.recording.start(
            device_id=device_id,
            sample_rate=22050,
            channels=1
        )

        recording_id = result.get('recording_id')
        if not recording_id:
            raise RuntimeError("Failed to start recording")

        logger.info(f"Recording started (ID: {recording_id})")

        if auto_stop:
            # Auto-stop after duration_hint
            logger.info(f"Recording for {duration_hint} seconds...")
            time.sleep(duration_hint)
            return self.stop_voice_recording(recording_id)
        else:
            # Return session info for manual stop
            return {
                "recording_id": recording_id,
                "message": "Recording started. Call stop_voice_recording() when done.",
                "stop_function": lambda: self.stop_voice_recording(recording_id)
            }

    def stop_voice_recording(self, recording_id: str) -> Dict[str, Any]:
        """
        Stop voice recording and return reference audio ID.

        Args:
            recording_id: Recording session ID

        Returns:
            Recording result with reference audio ID
        """
        logger.info("Stopping recording...")

        result = self.client.audio.recording.stop(
            recording_id=recording_id,
            process_audio=True,
            normalize=True,
            trim_silence=True,
            noise_reduce=True
        )

        if result.get('status') != 'success':
            raise RuntimeError(f"Recording failed: {result}")

        logger.info(f"Recording stopped successfully (Duration: {result.get('duration', 0):.2f}s)")
        return result

    def clone_voice_and_speak(
        self,
        text: str,
        ref_audio_id: Optional[str] = None,
        ref_audio_path: Optional[str] = None,
        ref_text: Optional[str] = None,
        speed: float = 1.0,
        temperature: float = 0.7,
        audio_format: str = "wav"
    ) -> bytes:
        """
        Generate speech using a cloned voice.

        Args:
            text: Text to speak
            ref_audio_id: Reference audio ID from upload
            ref_audio_path: Path to reference audio file
            ref_text: Reference text for the audio
            speed: Speech speed
            temperature: Generation temperature
            audio_format: Output audio format

        Returns:
            Generated audio bytes
        """
        if ref_audio_id:
            # Use uploaded reference audio
            audio = self.client.audio.speech.create(
                text=text,
                voice="clone",
                mode="clone",
                ref_audio_id=ref_audio_id,
                ref_text=ref_text,
                speed=speed,
                temperature=temperature,
                response_format=audio_format
            )
            return audio

        elif ref_audio_path:
            # Upload reference audio file
            upload_result = self.client.upload_reference_audio(ref_audio_path)
            ref_audio_id = upload_result.get('ref_audio_id')

            if not ref_audio_id:
                raise RuntimeError("Failed to upload reference audio")

            # Generate speech
            audio = self.client.audio.speech.create(
                text=text,
                voice="clone",
                mode="clone",
                ref_audio_id=ref_audio_id,
                ref_text=ref_text,
                speed=speed,
                temperature=temperature,
                response_format=audio_format
            )
            return audio

        else:
            raise ValueError("Either ref_audio_id or ref_audio_path must be provided")

    def record_and_clone(
        self,
        text_to_speak: str,
        prompt_text: Optional[str] = None,
        ref_text: Optional[str] = None,
        device_id: Optional[str] = None,
        auto_stop: bool = False,
        duration_hint: float = 5.0,
        speed: float = 1.0,
        temperature: float = 0.7,
        audio_format: str = "wav"
    ) -> bytes:
        """
        One-stop method to record voice and generate speech with it.

        Args:
            text_to_speak: Text to generate speech with cloned voice
            prompt_text: Prompt for the recording (auto-generated if None)
            ref_text: Reference text for the recorded audio
            device_id: Audio device ID
            auto_stop: Automatically stop recording after duration_hint
            duration_hint: Expected recording duration
            speed: Speech speed for output
            temperature: Generation temperature
            audio_format: Output audio format

        Returns:
            Generated speech audio bytes
        """
        # Generate prompt if not provided
        if not prompt_text:
            prompt_text = (
                "Please speak clearly in your natural voice. "
                f"Say something like: {text_to_speak[:100]}... "
                "Try to speak for about 10-30 seconds."
            )

        # Record voice sample
        recording_result = self.record_voice_sample(
            prompt_text=prompt_text,
            device_id=device_id,
            auto_stop=auto_stop,
            duration_hint=duration_hint
        )

        if auto_stop:
            # Recording already stopped
            ref_audio_id = recording_result.get('ref_audio_id')
        else:
            # Need to stop manually
            if 'stop_function' in recording_result:
                # Interactive mode - wait for user
                input("Press Enter when done recording...")
                recording_result = recording_result['stop_function']()
            ref_audio_id = recording_result.get('ref_audio_id')

        if not ref_audio_id:
            raise RuntimeError("Failed to get reference audio ID")

        # Generate speech with cloned voice
        logger.info(f"Generating speech with cloned voice...")
        audio = self.clone_voice_and_speak(
            text=text_to_speak,
            ref_audio_id=ref_audio_id,
            ref_text=ref_text,
            speed=speed,
            temperature=temperature,
            audio_format=audio_format
        )

        logger.info(f"Generated {len(audio)} bytes of speech with cloned voice")
        return audio

    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available preset voices."""
        return self.client.list_voices()

    def get_audio_devices(self) -> Dict[str, Any]:
        """Get list of available audio input devices."""
        return self.client.audio.recording.list_devices()


# Convenience functions for quick usage
def quick_clone_voice(
    text: str,
    prompt: Optional[str] = None,
    base_url: str = "http://localhost:8000"
) -> bytes:
    """
    Quick function to record voice and generate speech with it.

    Args:
        text: Text to speak with cloned voice
        prompt: Recording prompt
        base_url: TTS service URL

    Returns:
        Generated audio bytes
    """
    cloner = VoiceCloner(auto_start_service=True, base_url=base_url)
    return cloner.record_and_clone(text, prompt_text=prompt)


def clone_from_file(
    text: str,
    ref_audio_path: str,
    ref_text: Optional[str] = None,
    base_url: str = "http://localhost:8000"
) -> bytes:
    """
    Clone voice from an existing audio file.

    Args:
        text: Text to speak
        ref_audio_path: Path to reference audio file
        ref_text: Reference text
        base_url: TTS service URL

    Returns:
        Generated audio bytes
    """
    cloner = VoiceCloner(auto_start_service=True, base_url=base_url)
    return cloner.clone_voice_and_speak(
        text=text,
        ref_audio_path=ref_audio_path,
        ref_text=ref_text
    )


# Interactive demo
def demo():
    """Interactive demo of voice cloning capabilities."""
    print("🎙️  Voice Cloning Demo")
    print("=" * 50)

    # Initialize cloner
    cloner = VoiceCloner(auto_start_service=True)

    # Show available voices
    print("\n📋 Available preset voices:")
    voices = cloner.get_available_voices()
    for voice in voices.get('voices', []):
        print(f"  • {voice['id']}: {voice['name']}")

    # Show audio devices
    print("\n🎤 Available audio devices:")
    devices = cloner.get_audio_devices()
    for device in devices.get('devices', []):
        print(f"  • {device['id']}: {device['name']}")

    # Interactive cloning
    print("\n🎯 Let's clone your voice!")
    text_to_speak = input("\nEnter text to speak with your cloned voice: ")

    if not text_to_speak:
        text_to_speak = "Hello, this is my cloned voice speaking. How does it sound?"

    print("\n🎙️  Starting voice recording...")
    print("Speak clearly and naturally when prompted.")

    try:
        # Record and clone
        audio = cloner.record_and_clone(
            text_to_speak=text_to_speak,
            auto_stop=False,  # Manual stop for better control
            duration_hint=10.0
        )

        # Save the result
        output_file = "cloned_voice_output.wav"
        with open(output_file, 'wb') as f:
            f.write(audio)

        print(f"\n✅ Success! Cloned voice saved to: {output_file}")
        print(f"   Audio size: {len(audio)} bytes")

    except KeyboardInterrupt:
        print("\n⏹️  Recording cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    demo()