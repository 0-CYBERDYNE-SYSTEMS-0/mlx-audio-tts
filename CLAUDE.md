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
```

## Architecture Overview

**MLX-Audio TTS Generator** - Web-based text-to-speech using Apple Silicon-optimized MLX-Audio with Kokoro-82M model.

### Backend Architecture
- **FastAPI application** with auto-reload for development
- **Service layer pattern**: `TTSService` handles MLX-Audio integration, `FileService` manages file operations
- **Background cleanup**: APScheduler automatically removes temporary files every hour
- **Lifespan management**: Proper startup/shutdown handling for MLX-Audio model

### Frontend Architecture
- **Vanilla JavaScript/HTML5/CSS3** - No build process required
- **Modular structure**: `api.js` (HTTP client), `app.js` (main logic), `ui.js` (DOM helpers)
- **File upload handling** with audio format validation
- **Real-time UI updates** during TTS generation

### Key Technical Constraints

1. **Python Environment**: Must use `/Users/scrimwiggins/miniconda3/bin/python` - MLX-Audio requires specific miniconda3 setup
2. **Apple Silicon Only**: MLX-Audio optimized for macOS on Apple Silicon
3. **Audio Processing**:
   - Input formats: WAV, MP3, FLAC, M4A, OGG
   - Output formats: WAV, MP3, FLAC
   - Reference audio for voice cloning: 10-30 seconds recommended
4. **Model Behavior**: Kokoro-82M auto-downloads on first use, may generate gibberish for very short text

### File Organization

- **Backend**: `backend/` with FastAPI app, services, API routes, and utilities
- **Frontend**: `frontend/` serving static files from root path
- **Temporary Storage**: `uploads/` (reference audio), `outputs/` (generated TTS)
- **Configuration**: Centralized in `backend/config.py` with voice presets and parameter limits

### API Patterns

- **RESTful endpoints** following `/api/` convention
- **File uploads** via multipart form data to `/api/upload`
- **Voice modes**: `preset` (built-in voices) or `clone` (custom voice from uploaded audio)
- **Consistent error responses** with proper HTTP status codes

### Development Notes

- **Auto-reload enabled** - changes to backend files trigger automatic restart
- **Frontend changes** require browser refresh
- **No formal test suite** - manual testing via curl commands and browser interface
- **Static assets** served at `/assets/` path
- **CORS configured** to allow frontend-backend communication