"""
Voice recording service for capturing audio from device microphone.
Supports real-time recording, audio processing, and format conversion.
"""
import os
import io
import wave
import logging
import numpy as np
import soundfile as sf
from typing import Optional, Tuple, Union
from pathlib import Path
import threading
import queue
import time

# Configure logging
logger = logging.getLogger(__name__)

# Try to import audio libraries
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available. Install with: pip install pyaudio")

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    logger.warning("SoundDevice not available. Install with: pip install sounddevice")


class AudioRecorder:
    """
    Audio recorder supporting multiple backends.
    Can record from device microphone with real-time monitoring.
    """

    def __init__(
        self,
        sample_rate: int = 22050,
        channels: int = 1,
        chunk_size: int = 1024,
        format: str = "int16"
    ):
        """
        Initialize audio recorder.

        Args:
            sample_rate: Audio sample rate (Hz)
            channels: Number of audio channels (1=mono, 2=stereo)
            chunk_size: Buffer size for recording
            format: Audio format ("int16", "float32")
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = format
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.audio_data = []

        # Determine audio backend
        self.backend = self._get_backend()

    def _get_backend(self) -> str:
        """Determine the best available audio backend."""
        if SOUNDDEVICE_AVAILABLE:
            return "sounddevice"
        elif PYAUDIO_AVAILABLE:
            return "pyaudio"
        else:
            raise RuntimeError(
                "No audio backend available. Install either sounddevice or pyaudio:\n"
                "pip install sounddevice  # Recommended\n"
                "or\n"
                "pip install pyaudio"
            )

    def get_available_devices(self) -> list:
        """Get list of available audio input devices."""
        if self.backend == "sounddevice":
            return sd.query_devices()
        elif self.backend == "pyaudio":
            p = pyaudio.PyAudio()
            devices = []
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices.append(info)
            p.terminate()
            return devices
        return []

    def record(
        self,
        duration: Optional[float] = None,
        device: Optional[Union[int, str]] = None
    ) -> np.ndarray:
        """
        Record audio from microphone.

        Args:
            duration: Recording duration in seconds. If None, records until stop() is called.
            device: Input device ID or name. If None, uses default device.

        Returns:
            Recorded audio data as numpy array
        """
        if self.is_recording:
            raise RuntimeError("Already recording")

        self.is_recording = True
        self.audio_data = []

        if self.backend == "sounddevice":
            return self._record_sounddevice(duration, device)
        elif self.backend == "pyaudio":
            return self._record_pyaudio(duration, device)

    def _record_sounddevice(
        self,
        duration: Optional[float],
        device: Optional[Union[int, str]]
    ) -> np.ndarray:
        """Record using sounddevice backend."""
        try:
            def callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Recording status: {status}")
                if self.is_recording:
                    self.audio_queue.put(indata.copy())

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.format,
                device=device,
                callback=callback,
                blocksize=self.chunk_size
            ):
                if duration:
                    sd.sleep(int(duration * 1000))
                else:
                    # Record until stop() is called
                    while self.is_recording:
                        sd.sleep(100)

            # Collect all audio data
            audio_chunks = []
            while not self.audio_queue.empty():
                audio_chunks.append(self.audio_queue.get())

            if audio_chunks:
                audio_data = np.concatenate(audio_chunks, axis=0)
                return audio_data
            else:
                return np.array([])

        except Exception as e:
            logger.error(f"Recording error: {e}")
            self.is_recording = False
            raise

    def _record_pyaudio(
        self,
        duration: Optional[float],
        device: Optional[Union[int, str]]
    ) -> np.ndarray:
        """Record using pyaudio backend."""
        p = pyaudio.PyAudio()

        try:
            # Find device index if name provided
            if isinstance(device, str):
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    if device in info['name']:
                        device = i
                        break

            stream = p.open(
                format=pyaudio.paInt16 if self.format == "int16" else pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device,
                frames_per_buffer=self.chunk_size
            )

            logger.info("Recording started...")
            frames = []

            if duration:
                # Record for specified duration
                for _ in range(int(self.sample_rate * duration / self.chunk_size)):
                    if not self.is_recording:
                        break
                    data = stream.read(self.chunk_size)
                    frames.append(data)
            else:
                # Record until stop() is called
                while self.is_recording:
                    try:
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames.append(data)
                    except Exception as e:
                        logger.warning(f"Stream read error: {e}")

            stream.stop_stream()
            stream.close()

            # Convert frames to numpy array
            if frames:
                audio_bytes = b''.join(frames)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16 if self.format == "int16" else np.float32)
                return audio_data
            else:
                return np.array([])

        finally:
            p.terminate()

    def start_recording(self, device: Optional[Union[int, str]] = None):
        """Start recording in a separate thread."""
        if self.is_recording:
            raise RuntimeError("Already recording")

        self.is_recording = True
        self.recording_thread = threading.Thread(
            target=self._record_thread,
            args=(device,)
        )
        self.recording_thread.start()

    def _record_thread(self, device: Optional[Union[int, str]]):
        """Recording thread for continuous recording."""
        try:
            self.audio_data = self.record(duration=None, device=device)
        except Exception as e:
            logger.error(f"Recording thread error: {e}")
        finally:
            self.is_recording = False

    def stop_recording(self) -> np.ndarray:
        """
        Stop recording and return audio data.

        Returns:
            Recorded audio data as numpy array
        """
        if not self.is_recording:
            raise RuntimeError("Not recording")

        self.is_recording = False

        if self.recording_thread:
            self.recording_thread.join(timeout=5)
            self.recording_thread = None

        # Collect audio data
        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())

        if audio_chunks:
            return np.concatenate(audio_chunks, axis=0)
        elif self.audio_data.size > 0:
            return self.audio_data
        else:
            return np.array([])

    def save_audio(
        self,
        audio_data: np.ndarray,
        filename: str,
        format: str = "wav"
    ) -> str:
        """
        Save audio data to file.

        Args:
            audio_data: Audio data as numpy array
            filename: Output filename
            format: Audio format (wav, mp3, flac)

        Returns:
            Path to saved file
        """
        # Ensure directory exists
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save using soundfile
        sf.write(
            str(filepath),
            audio_data,
            self.sample_rate,
            format=format,
            subtype='PCM_16' if format == 'wav' and self.format == 'int16' else None
        )

        logger.info(f"Audio saved to {filepath}")
        return str(filepath)

    def get_audio_bytes(self, audio_data: np.ndarray, format: str = "wav") -> bytes:
        """
        Convert audio data to bytes.

        Args:
            audio_data: Audio data as numpy array
            format: Audio format

        Returns:
            Audio data as bytes
        """
        buffer = io.BytesIO()

        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2 if self.format == "int16" else 4)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        buffer.seek(0)
        return buffer.getvalue()

    def process_audio(
        self,
        audio_data: np.ndarray,
        normalize: bool = True,
        trim_silence: bool = True,
        noise_reduce: bool = False
    ) -> np.ndarray:
        """
        Process recorded audio for better voice cloning results.

        Args:
            audio_data: Input audio data
            normalize: Normalize audio amplitude
            trim_silence: Remove silence from beginning and end
            noise_reduce: Apply basic noise reduction

        Returns:
            Processed audio data
        """
        if len(audio_data) == 0:
            return audio_data

        processed = audio_data.copy()

        # Convert to float if needed
        if processed.dtype == np.int16:
            processed = processed.astype(np.float32) / 32768.0

        # Normalize audio
        if normalize and np.max(np.abs(processed)) > 0:
            processed = processed / np.max(np.abs(processed)) * 0.95

        # Basic noise reduction (simple high-pass filter)
        if noise_reduce:
            # Simple high-pass filter to remove low-frequency noise
            from scipy import signal
            sos = signal.butter(4, 80, btype='high', fs=self.sample_rate, output='sos')
            processed = signal.sosfilt(sos, processed)

        # Trim silence
        if trim_silence:
            # Find audio above threshold
            threshold = 0.01
            above_threshold = np.abs(processed) > threshold

            if np.any(above_threshold):
                # Find first and last samples above threshold
                first = np.argmax(above_threshold)
                last = len(above_threshold) - np.argmax(above_threshold[::-1])
                processed = processed[first:last]

        # Convert back to original format
        if audio_data.dtype == np.int16:
            processed = (processed * 32767).astype(np.int16)

        return processed


# Convenience functions
def record_voice(
    duration: float = 5.0,
    sample_rate: int = 22050,
    output_file: Optional[str] = None,
    process: bool = True
) -> Union[np.ndarray, str]:
    """
    Quick function to record voice.

    Args:
        duration: Recording duration in seconds
        sample_rate: Sample rate
        output_file: If provided, save to this file
        process: Whether to process the audio

    Returns:
        Audio data (numpy array) or file path if output_file provided
    """
    recorder = AudioRecorder(sample_rate=sample_rate)

    try:
        # Record audio
        logger.info(f"Recording for {duration} seconds...")
        audio_data = recorder.record(duration=duration)

        # Process audio
        if process:
            audio_data = recorder.process_audio(audio_data)

        # Save if requested
        if output_file:
            return recorder.save_audio(audio_data, output_file)

        return audio_data

    except Exception as e:
        logger.error(f"Recording failed: {e}")
        raise