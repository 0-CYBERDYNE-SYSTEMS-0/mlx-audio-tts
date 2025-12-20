"""
Configuration constants for the TTS web application.
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
PID_DIR = os.path.join(BASE_DIR, 'pids')

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(PID_DIR, exist_ok=True)

# TTS Configuration
DEFAULT_MODEL = "mlx-community/Kokoro-82M-bf16"
CLONE_MODEL = os.getenv("TTS_CLONE_MODEL", "sesame/csm-1b")
AVAILABLE_VOICES = [
    {"id": "af_heart", "name": "Heart (Female, Warm)", "gender": "female", "accent": "american"},
    {"id": "af_bella", "name": "Bella (Female, Clear)", "gender": "female", "accent": "american"},
    {"id": "af_sarah", "name": "Sarah (Female, Professional)", "gender": "female", "accent": "american"},
    {"id": "am_adam", "name": "Adam (Male, Deep)", "gender": "male", "accent": "american"},
    {"id": "am_michael", "name": "Michael (Male, Neutral)", "gender": "male", "accent": "american"},
    {"id": "bf_emma", "name": "Emma (British Female)", "gender": "female", "accent": "british"},
    {"id": "bm_george", "name": "George (British Male)", "gender": "male", "accent": "british"},
]

# Generation Parameters
DEFAULT_SPEED = 1.0
MIN_SPEED = 0.5
MAX_SPEED = 2.0

DEFAULT_TEMPERATURE = 0.7
MIN_TEMPERATURE = 0.1
MAX_TEMPERATURE = 1.0

# Text Splitting Configuration
MAX_CHARS_PER_GENERATION = 300  # Maximum characters per TTS generation
MIN_CHARS_PER_SEGMENT = 50     # Minimum characters for a segment
SENTENCE_SPLIT_CHARS = '.!?'    # Characters that end sentences
CLAUSE_SPLIT_CHARS = ',;:'     # Characters that split clauses

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm'}
UPLOAD_CLEANUP_HOURS = 24
OUTPUT_CLEANUP_HOURS = 1

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True

# Production Configuration
PRODUCTION_MODE = os.getenv("TTS_PRODUCTION", "false").lower() == "true"
LOG_LEVEL = os.getenv("TTS_LOG_LEVEL", "INFO")
SERVER_HOST = os.getenv("TTS_HOST", "127.0.0.1")  # Localhost only for production
SERVER_PORT = int(os.getenv("TTS_PORT", "8000"))

# Service Management
PID_FILE = os.path.join(PID_DIR, "tts_service.pid")
LOG_FILE = os.path.join(LOGS_DIR, "tts_service.log")
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
