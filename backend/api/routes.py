"""
API routes for the TTS web application.
"""
import os
import time
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (
    GenerateRequest,
    GenerateResponse,
    UploadResponse,
    VoicesResponse,
    ModelsResponse,
    ErrorResponse,
)
from backend.config import AVAILABLE_VOICES, DEFAULT_MODEL
from backend.services.tts_service import TTSService
from backend.services.file_service import FileService
from backend.utils.validators import (
    validate_text,
    validate_speed,
    validate_temperature,
    validate_voice_mode,
    validate_audio_file,
)

# Initialize services
tts_service = TTSService()
file_service = FileService()


def setup_routes(app: FastAPI):
    """Configure API routes."""

    @app.get("/api/voices", response_model=VoicesResponse)
    async def get_voices():
        """Get list of available preset voices."""
        return VoicesResponse(voices=AVAILABLE_VOICES)

    @app.get("/api/models", response_model=ModelsResponse)
    async def get_models():
        """Get list of available TTS models."""
        models = [
            {
                "id": "kokoro-82m",
                "name": "Kokoro 82M",
                "description": "Fast, lightweight model for high-quality speech synthesis",
                "status": "loaded",
                "path": DEFAULT_MODEL
            }
        ]
        return ModelsResponse(models=models)

    @app.post("/api/upload-reference", response_model=UploadResponse)
    async def upload_reference(file: UploadFile = File(...)):
        """Upload reference audio file for voice cloning."""
        try:
            # Read file content
            content = await file.read()

            # Validate file
            import tempfile
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(content)
                tmp.flush()
                validate_audio_file(tmp.name, len(content))

            # Save file
            file_id, filename = file_service.save_upload(content, file.filename)

            # Get duration
            file_path = file_service.get_upload_path(file_id)
            duration = file_service.get_audio_duration(file_path)

            return UploadResponse(
                status="success",
                ref_audio_id=file_id,
                filename=filename,
                duration=duration
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @app.post("/api/generate", response_model=GenerateResponse)
    async def generate_audio(request: GenerateRequest):
        """Generate TTS audio from text."""
        start_time = time.time()

        try:
            # Validate inputs
            text = validate_text(request.text)
            speed = validate_speed(request.speed)
            temperature = validate_temperature(request.temperature)

            # Validate voice mode
            voice_params = validate_voice_mode(
                request.mode,
                request.voice,
                request.ref_audio_id
            )

            # Generate audio based on mode
            if request.mode == 'preset':
                result = tts_service.generate_with_preset(
                    text=text,
                    voice=request.voice,
                    speed=speed,
                    temperature=temperature,
                    audio_format=request.audio_format
                )
            else:  # clone mode
                # Get reference audio path
                ref_audio_path = file_service.get_upload_path(request.ref_audio_id)
                if not ref_audio_path:
                    raise HTTPException(status_code=404, detail="Reference audio not found")

                result = tts_service.generate_with_cloning(
                    text=text,
                    ref_audio_path=ref_audio_path,
                    ref_text=request.ref_text,
                    speed=speed,
                    temperature=temperature,
                    audio_format=request.audio_format
                )

            if not result['success']:
                raise HTTPException(status_code=500, detail="Audio generation failed")

            # Save output file
            filename = file_service.save_output(
                result['audio_data'],
                f".{request.audio_format}"
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            return GenerateResponse(
                status="success",
                audio_url=f"/api/download/{filename}",
                filename=filename,
                duration=result['duration'],
                processing_time=round(processing_time, 2)
            )

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    @app.get("/api/download/{filename}")
    async def download_audio(filename: str):
        """Download generated audio file."""
        file_path = f"/Users/scrimwiggins/_test/outputs/{filename}"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/wav'
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=str(exc),
                code="INTERNAL_ERROR"
            ).dict()
        )
