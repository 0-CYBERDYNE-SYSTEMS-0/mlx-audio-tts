"""
Recording manager for handling recording sessions.
Since recording happens on the frontend, this manager handles the session management only.
"""
import uuid
import time
import logging
from typing import Dict, Optional, List
from pathlib import Path

from backend.services.file_service import FileService
from backend.config import UPLOADS_DIR

logger = logging.getLogger(__name__)


class RecordingSession:
    """Represents an active recording session."""

    def __init__(self, session_id: str):
        """Initialize recording session."""
        self.session_id = session_id
        self.start_time = time.time()
        self.audio_data = None
        self.duration = None
        self.is_active = True
        self.ref_audio_id = None
        self.filename = None


class RecordingManager:
    """
    Manages recording sessions for frontend audio recording.

    Note: The actual audio recording happens on the frontend using Web Audio API.
    This manager only tracks sessions and handles the uploaded audio files.
    """

    def __init__(self):
        """Initialize recording manager."""
        self.sessions: Dict[str, RecordingSession] = {}
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
            device_id: Audio device ID (not used for backend)
            sample_rate: Sample rate (not used for backend)
            channels: Number of channels (not used for backend)
            format: Audio format (not used for backend)

        Returns:
            Session ID for the recording
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create session
        session = RecordingSession(session_id)
        self.sessions[session_id] = session

        logger.info(f"Started recording session {session_id}")
        return session_id

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
        Stop a recording session and prepare for file upload.

        Args:
            session_id: Recording session ID
            process_audio: Whether to process the audio (frontend will handle)
            normalize: Normalize audio amplitude (frontend will handle)
            trim_silence: Trim silence from audio (frontend will handle)
            noise_reduce: Apply noise reduction (frontend will handle)
            save_to_file: Whether to save to file (frontend will upload separately)

        Returns:
            Dictionary with recording information
        """
        if session_id not in self.sessions:
            raise ValueError(f"Recording session {session_id} not found")

        session = self.sessions[session_id]

        try:
            # Update session info
            session.duration = time.time() - session.start_time
            session.is_active = False

            result = {
                "session_id": session_id,
                "duration": session.duration,
                "audio_length": 0,  # Will be set when audio is uploaded
                "ref_audio_id": None,  # Will be set when audio is uploaded
                "filename": None  # Will be set when audio is uploaded
            }

            # Note: The actual audio file will be uploaded via the /api/upload-reference endpoint
            # by the frontend after stopping the recording

            logger.info(f"Stopped recording session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Error stopping recording {session_id}: {e}")
            raise
        finally:
            # Clean up session
            if session_id in self.sessions:
                del self.sessions[session_id]

    def get_active_recordings(self) -> List[Dict]:
        """
        Get list of active recording sessions.

        Returns:
            List of active recording information
        """
        active = []
        for session_id, session in self.sessions.items():
            active.append({
                "session_id": session_id,
                "start_time": session.start_time,
                "duration": time.time() - session.start_time
            })
        return active

    def is_recording_active(self, session_id: str) -> bool:
        """Check if a recording session is active."""
        return session_id in self.sessions

    def stop_all_recordings(self) -> int:
        """
        Stop all active recordings.

        Returns:
            Number of recordings stopped
        """
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