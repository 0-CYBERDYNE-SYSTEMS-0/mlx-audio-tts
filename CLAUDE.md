# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application (Recommended)
```bash
# UV-based startup - fastest and most convenient
./run_with_uv.py

# Legacy shell script - handles Python path and dependencies automatically
./run.sh

# Manual startup with UV
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode (background service)
python backend/main.py --production

# Manual startup (if needed)
/Users/scrimwiggins/miniconda3/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Setup
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Add MLX-Audio (requires special handling)
uv add mlx-audio  # May fail due to miniconda3 requirements
# Fallback: Use miniconda3 for MLX-Audio specifically
```

### Code Quality
```bash
# Lint code
uv run ruff check backend/

# Format code
uv run ruff format backend/

# Run tests (when implemented)
uv run pytest
```

### API Testing
```bash
# List available voices
curl http://localhost:8000/api/voices

# Health check
curl http://localhost:8000/health

# Generate TTS with preset voice
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","mode":"preset","voice":"af_heart"}'

# Generate with custom speed/temperature
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello","mode":"preset","voice":"af_heart","speed":1.2,"temperature":0.8}'

# Upload audio for voice cloning
curl -X POST http://localhost:8000/api/upload \
  -F "file=@reference_audio.wav"

# Generate with cloned voice
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","mode":"clone","voice_id":"UPLOAD_ID"}'
```

## Architecture Overview

**MLX-Audio TTS Generator** - Web-based text-to-speech using Apple Silicon-optimized MLX-Audio with Kokoro-82M model.

### Backend Architecture
- **FastAPI application** with auto-reload for development
- **Service layer pattern**:
  - `TTSService`: Handles MLX-Audio integration, text segmentation, and audio generation
  - `FileService`: Manages file operations, cleanup, and validation
  - `VoiceRecorder`: Handles audio recording functionality
  - `RecordingManager`: Manages recording state and operations
- **Background cleanup**: APScheduler automatically removes temporary files
- **Lifespan management**: Proper startup/shutdown handling for MLX-Audio model
- **Production mode**: Can run as background service with logging and PID management

### Frontend Architecture
- **Vanilla JavaScript/HTML5/CSS3** - No build process required
- **Modular structure**:
  - `api.js`: HTTP client for backend communication
  - `app.js`: Main application logic and state management
  - `ui.js`: DOM manipulation helpers
  - `audio-player.js`: Enhanced audio player with waveform visualization
  - `audio-recorder.js`: Audio recording functionality
  - `voice-recorder-ui.js`: Voice recording interface components
- **Real-time features**: Progress tracking, audio visualization, drag-and-drop uploads

### Key Technical Constraints

1. **Python Environment**: MLX-Audio requires `/Users/scrimwiggins/miniconda3/bin/python` due to specific dependencies
2. **Apple Silicon Only**: MLX-Audio optimized for macOS on Apple Silicon with Metal acceleration
3. **Audio Processing**:
   - Input formats: WAV, MP3, FLAC, M4A, OGG, WebM
   - Output formats: WAV, MP3, FLAC
   - Reference audio for voice cloning: 10-30 seconds recommended
   - Max file size: 10MB
4. **Model Behavior**:
   - Kokoro-82M auto-downloads on first use
   - May generate gibberish for very short text (< 10 characters)
   - Text automatically segmented at 300 characters for optimal generation

### File Organization

- **Backend**: `backend/`
  - `main.py`: FastAPI application entry point
  - `config.py`: Centralized configuration and constants
  - `api/`: API routes and models
  - `services/`: Business logic (TTS, file management, recording)
- **Frontend**: `frontend/` serving static files from root path
- **Temporary Storage**: `uploads/` (reference audio), `outputs/` (generated TTS)
- **Service Management**: `logs/` and `pids/` for production mode

### API Patterns

- **RESTful endpoints** following `/api/` convention
- **Voice modes**:
  - `preset`: Built-in Kokoro-82M voices
  - `clone`: Custom voice from uploaded audio
- **Intelligent text processing**: Automatic segmentation for long texts
- **File handling**: Multipart uploads with format validation
- **Consistent error responses** with proper HTTP status codes

### Development Notes

- **Auto-reload enabled** for backend changes
- **Service scripts**: `install_tts_service.sh`, `start_tts_service.sh`, `stop_tts_service.sh` for production deployment
- **Configuration via environment variables**:
  - `TTS_PRODUCTION`: Enable production mode
  - `TTS_HOST`, `TTS_PORT`: Server binding
  - `TTS_LOG_LEVEL`: Logging verbosity
- **Static assets** served at `/assets/`, `/css/`, `/js/` paths
- **CORS configured** appropriately for development vs production