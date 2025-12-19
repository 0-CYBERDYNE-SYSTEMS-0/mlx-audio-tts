"""
Pydantic models for API request/response validation.
"""
from typing import Optional, List, Union
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request model for TTS generation."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    mode: str = Field(..., description="Generation mode: 'preset' or 'clone'")
    voice: Optional[str] = Field(None, description="Voice preset (required if mode=preset)")
    ref_audio_id: Optional[str] = Field(None, description="Reference audio ID (required if mode=clone)")
    ref_text: Optional[str] = Field(None, description="Reference audio transcription (optional for clone mode)")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Playback speed multiplier")
    temperature: float = Field(0.7, ge=0.1, le=1.0, description="Generation temperature")
    audio_format: str = Field('wav', description="Output audio format")


class GenerateResponse(BaseModel):
    """Response model for TTS generation."""
    status: str
    audio_url: Optional[str] = None
    filename: Optional[str] = None
    duration: Optional[float] = None
    processing_time: Optional[float] = None
    message: Optional[str] = None


class UploadResponse(BaseModel):
    """Response model for file upload."""
    status: str
    ref_audio_id: str
    filename: str
    duration: float


class VoicesResponse(BaseModel):
    """Response model for available voices."""
    voices: list[dict]


class ModelsResponse(BaseModel):
    """Response model for available models."""
    models: list[dict]


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = "error"
    message: str
    code: Optional[str] = None


# Recording-related models
class AudioDevice(BaseModel):
    """Audio device information."""
    id: Optional[Union[int, str]] = None
    name: str
    channels: int
    sample_rate: Optional[int] = None


class RecordingStartRequest(BaseModel):
    """Request model for starting recording."""
    device_id: Optional[Union[int, str]] = None
    sample_rate: int = Field(22050, ge=8000, le=48000, description="Sample rate in Hz")
    channels: int = Field(1, ge=1, le=2, description="Number of channels (1=mono, 2=stereo)")
    format: str = Field("int16", description="Audio format")


class RecordingStartResponse(BaseModel):
    """Response model for starting recording."""
    status: str
    recording_id: str
    message: str


class RecordingStopRequest(BaseModel):
    """Request model for stopping recording."""
    recording_id: str
    process_audio: bool = Field(True, description="Process audio for better cloning results")
    normalize: bool = Field(True, description="Normalize audio amplitude")
    trim_silence: bool = Field(True, description="Trim silence from beginning and end")
    noise_reduce: bool = Field(False, description="Apply basic noise reduction")


class RecordingStopResponse(BaseModel):
    """Response model for stopping recording."""
    status: str
    recording_id: str
    audio_url: Optional[str] = None
    filename: Optional[str] = None
    duration: Optional[float] = None
    ref_audio_id: Optional[str] = None
    message: Optional[str] = None


class AudioDevicesResponse(BaseModel):
    """Response model for audio devices."""
    status: str
    devices: List[AudioDevice]
    default_device: Optional[AudioDevice] = None


class RecordingStatusResponse(BaseModel):
    """Response model for recording status."""
    status: str
    is_recording: bool
    active_recordings: List[dict] = Field(default_factory=list)
