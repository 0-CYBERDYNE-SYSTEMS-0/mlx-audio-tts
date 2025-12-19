"""
Configuration constants for the TTS web application.
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# TTS Configuration
DEFAULT_MODEL = "mlx-community/Kokoro-82M-bf16"
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
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
UPLOAD_CLEANUP_HOURS = 24
OUTPUT_CLEANUP_HOURS = 1

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True
