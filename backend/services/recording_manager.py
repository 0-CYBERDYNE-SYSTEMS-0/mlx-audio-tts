"""
Recording manager for handling multiple concurrent recordings.
Manages recording sessions and provides safe access to recording operations.
"""
import uuid
import time
import threading
import logging
from typing import Dict, Optional, List
from pathlib import Path
import numpy as np

from backend.services.voice_recorder import AudioRecorder
from backend.services.file_service import FileService
from backend.config import UPLOADS_DIR

logger = logging.getLogger(__name__)


class RecordingSession:
    """Represents an active recording session."""

    def __init__(self, session_id: str, recorder: AudioRecorder):
        """Initialize recording session."""
        self.session_id = session_id
        self.recorder = recorder
        self.start_time = time.time()
        self.audio_data = None
        self.duration = None
        self.is_active = True
        self.lock = threading.Lock()

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return audio data."""
        with self.lock:
            if not self.is_active:
                raise RuntimeError("Recording session is not active")

            self.audio_data = self.recorder.stop_recording()
            self.duration = time.time() - self.start_time
            self.is_active = False

            return self.audio_data


class RecordingManager:
    """
    Manages multiple recording sessions.
    Thread-safe implementation for concurrent recordings.
    """

    def __init__(self):
        """Initialize recording manager."""
        self.sessions: Dict[str, RecordingSession] = {}
        self.lock = threading.Lock()
        self.file_service = FileService()

    def start_recording(
        self,
        device_id: Optional[str] = None,
        sample_rate: int = 22050,
        channels: int = 1,
        format: str = "int16"
    ) -> str:
        """
        Start a new recording session.

        Args:
            device_id: Audio device ID
            sample_rate: Sample rate
            channels: Number of channels
            format: Audio format

        Returns:
            Session ID for the recording
        """
        with self.lock:
            # Generate unique session ID
            session_id = str(uuid.uuid4())

            # Create recorder
            recorder = AudioRecorder(
                sample_rate=sample_rate,
                channels=channels,
                format=format
            )

            # Create session
            session = RecordingSession(session_id, recorder)

            # Start recording
            try:
                recorder.start_recording(device=device_id)
                self.sessions[session_id] = session
                logger.info(f"Started recording session {session_id}")
                return session_id
            except Exception as e:
                logger.error(f"Failed to start recording: {e}")
                raise

    def stop_recording(
        self,
        session_id: str,
        process_audio: bool = True,
        normalize: bool = True,
        trim_silence: bool = True,
        noise_reduce: bool = False,
        save_to_file: bool = True
    ) -> Dict:
        """
        Stop a recording session and save audio.

        Args:
            session_id: Recording session ID
            process_audio: Whether to process the audio
            normalize: Normalize audio amplitude
            trim_silence: Trim silence from audio
            noise_reduce: Apply noise reduction
            save_to_file: Whether to save to file

        Returns:
            Dictionary with recording information
        """
        with self.lock:
            if session_id not in self.sessions:
                raise ValueError(f"Recording session {session_id} not found")

            session = self.sessions[session_id]

            try:
                # Stop recording
                audio_data = session.stop_recording()

                # Process audio if requested
                if process_audio and len(audio_data) > 0:
                    audio_data = session.recorder.process_audio(
                        audio_data,
                        normalize=normalize,
                        trim_silence=trim_silence,
                        noise_reduce=noise_reduce
                    )

                # Save to file if requested
                ref_audio_id = None
                filename = None
                if save_to_file and len(audio_data) > 0:
                    # Convert to bytes
                    audio_bytes = session.recorder.get_audio_bytes(audio_data)

                    # Save using file service
                    ref_audio_id, filename = self.file_service.save_upload(
                        audio_bytes,
                        f"recording_{session_id[:8]}.wav"
                    )

                result = {
                    "session_id": session_id,
                    "duration": session.duration,
                    "sample_rate": session.recorder.sample_rate,
                    "channels": session.recorder.channels,
                    "audio_length": len(audio_data),
                    "ref_audio_id": ref_audio_id,
                    "filename": filename
                }

                # Remove session
                del self.sessions[session_id]
                logger.info(f"Stopped recording session {session_id}")

                return result

            except Exception as e:
                logger.error(f"Error stopping recording {session_id}: {e}")
                # Clean up session even on error
                if session_id in self.sessions:
                    del self.sessions[session_id]
                raise

    def get_active_recordings(self) -> List[Dict]:
        """
        Get list of active recording sessions.

        Returns:
            List of active recording information
        """
        with self.lock:
            active = []
            for session_id, session in self.sessions.items():
                active.append({
                    "session_id": session_id,
                    "start_time": session.start_time,
                    "duration": time.time() - session.start_time,
                    "sample_rate": session.recorder.sample_rate,
                    "channels": session.recorder.channels
                })
            return active

    def is_recording_active(self, session_id: str) -> bool:
        """Check if a recording session is active."""
        with self.lock:
            return session_id in self.sessions

    def stop_all_recordings(self) -> int:
        """
        Stop all active recordings.

        Returns:
            Number of recordings stopped
        """
        with self.lock:
            session_ids = list(self.sessions.keys())
            stopped = 0

            for session_id in session_ids:
                try:
                    self.stop_recording(session_id)
                    stopped += 1
                except Exception as e:
                    logger.error(f"Error stopping recording {session_id}: {e}")

            return stopped


# Global recording manager instance
recording_manager = RecordingManager()