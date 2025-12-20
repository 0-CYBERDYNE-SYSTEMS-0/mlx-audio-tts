"""
Main FastAPI application for TTS web service.
"""
import os
import sys
import argparse
import logging
import signal
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import (
    HOST, PORT, UPLOADS_DIR, OUTPUTS_DIR, OUTPUT_CLEANUP_HOURS,
    UPLOAD_CLEANUP_HOURS, PRODUCTION_MODE, LOG_LEVEL, SERVER_HOST, SERVER_PORT
)
from backend.api.routes import setup_routes
from backend.services.file_service import FileService
from backend.services.tts_service import TTSService

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if PRODUCTION_MODE else None
)
logger = logging.getLogger(__name__)

# Global TTS service instance for production mode
tts_service: Optional[TTSService] = None
shutdown_requested = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global tts_service, shutdown_requested

    # Startup
    if PRODUCTION_MODE:
        logger.info("Starting TTS Service in production mode...")
    else:
        print("Starting TTS Web Application...")

    # Create directories
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # Initialize TTS service in production mode for model warmup
    if PRODUCTION_MODE:
        try:
            tts_service = TTSService()
            logger.info("TTS model warmed up and ready")
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")

    # Start cleanup scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: FileService().cleanup_old_files(OUTPUTS_DIR, OUTPUT_CLEANUP_HOURS),
        'interval',
        minutes=30,
        id='cleanup_outputs'
    )
    scheduler.add_job(
        lambda: FileService().cleanup_old_files(UPLOADS_DIR, UPLOAD_CLEANUP_HOURS),
        'interval',
        minutes=60,
        id='cleanup_uploads'
    )
    scheduler.start()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        global shutdown_requested
        if PRODUCTION_MODE:
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_requested = True
        scheduler.shutdown(wait=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if PRODUCTION_MODE:
        logger.info("✅ TTS Service started successfully")
        logger.info(f"📡 Server running on http://{SERVER_HOST}:{SERVER_PORT}")
    else:
        print("✅ Application started successfully")
        print(f"📡 Server running on http://{HOST}:{PORT}")

    yield

    # Shutdown
    if PRODUCTION_MODE:
        logger.info("Shutting down application...")
    else:
        print("Shutting down application...")

    scheduler.shutdown()

    if PRODUCTION_MODE:
        logger.info("✅ Application shutdown complete")
    else:
        print("✅ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="MLX-Audio TTS API",
    description="Text-to-speech generation using MLX-Audio",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
if PRODUCTION_MODE:
    # In production, only allow localhost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
else:
    # In development, allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files (frontend) - available in both dev and production
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, 'assets')), name="assets")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, 'css')), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, 'js')), name="js")

# Setup API routes
setup_routes(app)


@app.get("/")
async def root():
    """Serve the main application."""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return FileResponse(os.path.join(frontend_dir, 'index.html'))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mlx-tts",
        "mode": "production" if PRODUCTION_MODE else "development",
        "model_loaded": tts_service is not None
    }


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="MLX-Audio TTS Service")
    parser.add_argument("--production", action="store_true", help="Run in production mode")
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    args = parser.parse_args()

    # Set production mode if flag is provided
    if args.production:
        os.environ["TTS_PRODUCTION"] = "true"

    if not PRODUCTION_MODE:
        print("\n" + "="*50)
        print("🚀 MLX-Audio TTS Web Application")
        print("="*50)
        print(f"📂 Frontend: {frontend_dir if not PRODUCTION_MODE else 'Disabled in production'}")
        print(f"🔧 Host: {HOST}")
        print(f"🔌 Port: {PORT}")
        print("="*50 + "\n")

    uvicorn.run(
        "backend.main:app",
        host=SERVER_HOST if PRODUCTION_MODE else args.host or HOST,
        port=SERVER_PORT if PRODUCTION_MODE else args.port or PORT,
        reload=False if PRODUCTION_MODE else True,
        reload_dirs=None if PRODUCTION_MODE else ["backend", "frontend"],
        access_log=PRODUCTION_MODE,
        log_level="info" if PRODUCTION_MODE else "debug"
    )
