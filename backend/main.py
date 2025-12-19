"""
Main FastAPI application for TTS web service.
"""
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import HOST, PORT, UPLOADS_DIR, OUTPUTS_DIR, OUTPUT_CLEANUP_HOURS, UPLOAD_CLEANUP_HOURS
from backend.api.routes import setup_routes
from backend.services.file_service import FileService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting TTS Web Application...")

    # Create directories
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

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

    print("✅ Application started successfully")
    print(f"📡 Server running on http://{HOST}:{PORT}")

    yield

    # Shutdown
    print("Shutting down application...")
    scheduler.shutdown()
    print("✅ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="MLX-Audio TTS API",
    description="Text-to-speech generation using MLX-Audio",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, 'assets')), name="assets")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, 'css')), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, 'js')), name="js")

# Setup API routes
setup_routes(app)


@app.get("/")
async def root():
    """Serve the main application."""
    return FileResponse(os.path.join(frontend_dir, 'index.html'))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mlx-tts"}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*50)
    print("🚀 MLX-Audio TTS Web Application")
    print("="*50)
    print(f"📂 Frontend: {frontend_dir}")
    print(f"🔧 Host: {HOST}")
    print(f"🔌 Port: {PORT}")
    print("="*50 + "\n")

    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=True,
        reload_dirs=["backend", "frontend"]
    )
