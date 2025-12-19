"""
File management service for handling uploads and outputs.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from backend.config import UPLOADS_DIR, OUTPUTS_DIR, UPLOAD_CLEANUP_HOURS, OUTPUT_CLEANUP_HOURS


class FileService:
    """Service for managing file uploads, outputs, and cleanup."""

    @staticmethod
    def save_upload(file_content: bytes, original_filename: str) -> tuple[str, str]:
        """
        Save uploaded file to uploads directory.

        Returns:
            Tuple of (file_id, filename)
        """
        # Generate unique ID
        file_id = str(uuid.uuid4())

        # Get file extension
        file_ext = Path(original_filename).suffix.lower()

        # Generate new filename
        filename = f"reference-{file_id}{file_ext}"
        file_path = os.path.join(UPLOADS_DIR, filename)

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        return file_id, filename

    @staticmethod
    def get_upload_path(file_id: str) -> Optional[str]:
        """Get path to uploaded file by ID."""
        # Search for file with this ID
        for filename in os.listdir(UPLOADS_DIR):
            if file_id in filename:
                return os.path.join(UPLOADS_DIR, filename)
        return None

    @staticmethod
    def save_output(audio_data: bytes, file_ext: str = '.wav') -> str:
        """
        Save generated audio to outputs directory.

        Returns:
            Generated filename
        """
        file_id = str(uuid.uuid4())
        filename = f"output-{file_id}{file_ext}"
        file_path = os.path.join(OUTPUTS_DIR, filename)

        with open(file_path, 'wb') as f:
            f.write(audio_data)

        return filename

    @staticmethod
    def cleanup_old_files(directory: str, max_age_hours: int) -> int:
        """
        Remove files older than max_age_hours.

        Returns:
            Number of files removed
        """
        if not os.path.exists(directory):
            return 0

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_mtime < cutoff_time:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except Exception:
                        pass  # Ignore errors during cleanup

        return removed_count

    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get file size in bytes."""
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0

    @staticmethod
    def get_audio_duration(filepath: str) -> float:
        """Get audio duration in seconds using soundfile."""
        try:
            import soundfile as sf
            info = sf.info(filepath)
            return float(info.duration)
        except Exception:
            return 0.0
