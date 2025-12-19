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
    RecordingStartRequest,
    RecordingStartResponse,
    RecordingStopRequest,
    RecordingStopResponse,
    AudioDevicesResponse,
    RecordingStatusResponse,
)
from backend.config import AVAILABLE_VOICES, DEFAULT_MODEL
from backend.services.tts_service import TTSService
from backend.services.file_service import FileService
from backend.services.recording_manager import recording_manager
from backend.services.voice_recorder import AudioRecorder
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

    # Recording endpoints
    @app.get("/api/recording/devices", response_model=AudioDevicesResponse)
    async def get_audio_devices():
        """Get list of available audio input devices."""
        try:
            recorder = AudioRecorder()
            devices = recorder.get_available_devices()

            # Convert devices to response format
            device_list = []
            default_device = None

            for i, device in enumerate(devices):
                if isinstance(device, dict):
                    # Sounddevice format
                    if device.get('max_input_channels', 0) > 0:
                        device_info = AudioDevice(
                            id=i,
                            name=device.get('name', f'Device {i}'),
                            channels=device.get('max_input_channels', 0),
                            sample_rate=device.get('default_samplerate')
                        )
                        device_list.append(device_info)

                        # Check if this is the default device
                        if device.get('name', '').lower() in ['default', 'built-in']:
                            default_device = device_info
                else:
                    # PyAudio format
                    if device['maxInputChannels'] > 0:
                        device_info = AudioDevice(
                            id=device['index'],
                            name=device['name'],
                            channels=device['maxInputChannels']
                        )
                        device_list.append(device_info)

            return AudioDevicesResponse(
                status="success",
                devices=device_list,
                default_device=default_device
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get audio devices: {str(e)}")

    @app.post("/api/recording/start", response_model=RecordingStartResponse)
    async def start_recording(request: RecordingStartRequest):
        """Start a new recording session."""
        try:
            session_id = recording_manager.start_recording(
                device_id=request.device_id,
                sample_rate=request.sample_rate,
                channels=request.channels,
                format=request.format
            )

            return RecordingStartResponse(
                status="success",
                recording_id=session_id,
                message="Recording started successfully"
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")

    @app.post("/api/recording/stop", response_model=RecordingStopResponse)
    async def stop_recording(request: RecordingStopRequest):
        """Stop a recording session and save audio."""
        try:
            result = recording_manager.stop_recording(
                session_id=request.recording_id,
                process_audio=request.process_audio,
                normalize=request.normalize,
                trim_silence=request.trim_silence,
                noise_reduce=request.noise_reduce
            )

            # Prepare response
            response = RecordingStopResponse(
                status="success",
                recording_id=request.recording_id,
                duration=result.get('duration'),
                ref_audio_id=result.get('ref_audio_id'),
                filename=result.get('filename')
            )

            # Add audio URL if file was saved
            if result.get('filename'):
                response.audio_url = f"/api/download/{result['filename']}"

            return response

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop recording: {str(e)}")

    @app.get("/api/recording/status", response_model=RecordingStatusResponse)
    async def get_recording_status():
        """Get current recording status and active sessions."""
        try:
            active_recordings = recording_manager.get_active_recordings()
            is_recording = len(active_recordings) > 0

            return RecordingStatusResponse(
                status="success",
                is_recording=is_recording,
                active_recordings=active_recordings
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get recording status: {str(e)}")

    @app.post("/api/record-and-clone")
    async def record_and_clone(
        text: str,
        speed: float = 1.0,
        temperature: float = 0.7,
        audio_format: str = "wav"
    ):
        """
        One-stop endpoint to record voice and generate TTS with cloning.

        Args:
            text: Text to generate speech with cloned voice
            speed: Speech speed
            temperature: Generation temperature
            audio_format: Output audio format

        Returns:
            Generated TTS audio with cloned voice
        """
        try:
            # Step 1: Start recording
            session_id = recording_manager.start_recording()

            # Return recording session info to client
            return {
                "status": "recording",
                "recording_id": session_id,
                "message": "Recording started. Stop recording when ready.",
                "next_step": f"POST /api/recording/stop-and-clone with recording_id={session_id}"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")

    @app.post("/api/recording/stop-and-clone")
    async def stop_recording_and_clone(
        recording_id: str,
        text: str,
        speed: float = 1.0,
        temperature: float = 0.7,
        audio_format: str = "wav",
        ref_text: Optional[str] = None
    ):
        """
        Stop recording and immediately generate TTS with the recorded voice.

        Args:
            recording_id: Active recording session ID
            text: Text to generate speech with cloned voice
            speed: Speech speed
            temperature: Generation temperature
            audio_format: Output audio format
            ref_text: Optional reference text for the recorded audio

        Returns:
            Generated TTS audio with cloned voice
        """
        start_time = time.time()

        try:
            # Step 1: Stop recording and get reference audio
            recording_result = recording_manager.stop_recording(
                session_id=recording_id,
                process_audio=True,
                normalize=True,
                trim_silence=True,
                noise_reduce=True
            )

            if not recording_result.get('ref_audio_id'):
                raise HTTPException(status_code=500, detail="Failed to save reference audio")

            # Step 2: Generate TTS with cloned voice
            result = tts_service.generate_with_cloning(
                text=text,
                ref_audio_path=file_service.get_upload_path(recording_result['ref_audio_id']),
                ref_text=ref_text,
                speed=speed,
                temperature=temperature,
                audio_format=audio_format
            )

            if not result['success']:
                raise HTTPException(status_code=500, detail="Failed to generate TTS with cloned voice")

            # Step 3: Save output file
            filename = file_service.save_output(
                result['audio_data'],
                f".{audio_format}"
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            return {
                "status": "success",
                "message": "Voice cloned and TTS generated successfully",
                "recording_duration": recording_result.get('duration'),
                "audio_url": f"/api/download/{filename}",
                "filename": filename,
                "duration": result['duration'],
                "processing_time": round(processing_time, 2),
                "ref_audio_id": recording_result.get('ref_audio_id')
            }

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clone voice and generate TTS: {str(e)}")

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
