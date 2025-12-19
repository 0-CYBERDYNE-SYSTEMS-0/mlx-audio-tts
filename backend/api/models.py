"""
Pydantic models for API request/response validation.
"""
from typing import Optional
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
