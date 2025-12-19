"""
OpenAI-style TTS client for MLX-Audio TTS Service.
Provides a familiar interface for generating speech from text.
"""
import time
import json
import logging
import requests
import asyncio
from typing import Optional, Dict, Any, Union, AsyncGenerator
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Audio:
    """Namespace for audio-related operations (OpenAI-style)."""

    def __init__(self, client):
        self.client = client
        self.speech = Speech(client)


class Speech:
    """Speech generation API (OpenAI-style)."""

    def __init__(self, client):
        self.client = client

    def create(
        self,
        text: str,
        voice: str = "af_heart",
        mode: str = "preset",
        speed: float = 1.0,
        temperature: float = 0.7,
        response_format: str = "wav",
        ref_audio_id: Optional[str] = None,
        ref_text: Optional[str] = None,
        stream: bool = False
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """
        Create speech from text.

        Args:
            text: Text to convert to speech
            voice: Voice ID or "clone" for voice cloning
            mode: "preset" or "clone"
            speed: Speech speed (0.5 - 2.0)
            temperature: Randomness (0.1 - 1.0)
            response_format: Audio format ("wav", "mp3", "flac")
            ref_audio_id: Reference audio ID for cloning
            ref_text: Reference text for cloning
            stream: Whether to stream the response

        Returns:
            Audio bytes or async generator for streaming
        """
        return self.client._generate_speech(
            text=text,
            voice=voice,
            mode=mode,
            speed=speed,
            temperature=temperature,
            response_format=response_format,
            ref_audio_id=ref_audio_id,
            ref_text=ref_text,
            stream=stream
        )


class TTSClient:
    """
    OpenAI-style client for MLX-Audio TTS Service.

    Usage:
        client = TTSClient()
        audio = client.audio.speech.create(
            text="Hello, world!",
            voice="af_heart",
            response_format="wav"
        )
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize TTS client.

        Args:
            base_url: Base URL of TTS service
            api_key: Optional API key (not used for local service)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        # Setup OpenAI-style structure
        self.audio = Audio(self)

        # Verify service is available
        if not self._health_check():
            logger.warning(f"TTS service at {self.base_url} may not be available")

    def _health_check(self) -> bool:
        """Check if the TTS service is healthy."""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            files: Files to upload

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    response = self.session.get(
                        url,
                        headers=headers,
                        timeout=self.timeout
                    )
                elif method == "POST":
                    if files:
                        headers.update({
                            'accept': 'application/json',
                        })
                        response = self.session.post(
                            url,
                            headers=headers,
                            data=data,
                            files=files,
                            timeout=self.timeout
                        )
                    else:
                        headers.update({
                            'Content-Type': 'application/json',
                        })
                        response = self.session.post(
                            url,
                            headers=headers,
                            json=data,
                            timeout=self.timeout
                        )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
        raise Exception("Max retries exceeded")

    def _generate_speech(
        self,
        text: str,
        voice: str,
        mode: str,
        speed: float,
        temperature: float,
        response_format: str,
        ref_audio_id: Optional[str],
        ref_text: Optional[str],
        stream: bool
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """
        Generate speech from text.

        Args:
            text: Text to convert
            voice: Voice selection
            mode: Generation mode
            speed: Speech speed
            temperature: Randomness
            response_format: Audio format
            ref_audio_id: Reference audio for cloning
            ref_text: Reference text for cloning
            stream: Whether to stream

        Returns:
            Audio bytes or stream generator
        """
        if stream:
            return self._stream_speech(
                text, voice, mode, speed, temperature,
                response_format, ref_audio_id, ref_text
            )
        else:
            return self._generate_speech_sync(
                text, voice, mode, speed, temperature,
                response_format, ref_audio_id, ref_text
            )

    def _generate_speech_sync(
        self,
        text: str,
        voice: str,
        mode: str,
        speed: float,
        temperature: float,
        response_format: str,
        ref_audio_id: Optional[str],
        ref_text: Optional[str]
    ) -> bytes:
        """Generate speech synchronously."""
        data = {
            "text": text,
            "mode": mode,
            "voice": voice,
            "speed": speed,
            "temperature": temperature,
            "audio_format": response_format
        }

        if mode == "clone" and ref_audio_id:
            data["ref_audio_id"] = ref_audio_id
            if ref_text:
                data["ref_text"] = ref_text

        response = self._make_request("POST", "/api/generate", data=data)
        result = response.json()

        # Download the generated audio
        audio_response = self.session.get(
            f"{self.base_url}{result['audio_url']}",
            timeout=self.timeout
        )
        audio_response.raise_for_status()

        return audio_response.content

    async def _stream_speech(
        self,
        text: str,
        voice: str,
        mode: str,
        speed: float,
        temperature: float,
        response_format: str,
        ref_audio_id: Optional[str],
        ref_text: Optional[str]
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream speech generation.

        Note: This is a simplified implementation. True streaming would require
        server-side support for chunked responses.
        """
        # For now, generate the full audio and yield it in chunks
        audio_data = self._generate_speech_sync(
            text, voice, mode, speed, temperature,
            response_format, ref_audio_id, ref_text
        )

        # Yield in chunks
        chunk_size = 8192  # 8KB chunks
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

    def upload_reference_audio(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Upload reference audio for voice cloning.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with upload information
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, 'rb') as f:
            files = {'file': (audio_path.name, f, 'audio/wav')}
            response = self._make_request("POST", "/api/upload-reference", files=files)

        return response.json()

    def list_voices(self) -> Dict[str, Any]:
        """List available preset voices."""
        response = self._make_request("GET", "/api/voices")
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        """List available TTS models."""
        response = self._make_request("GET", "/api/models")
        return response.json()


# Convenience function for quick usage
def create_speech(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    temperature: float = 0.7,
    response_format: str = "wav",
    base_url: str = "http://localhost:8000"
) -> bytes:
    """
    Quick function to generate speech.

    Args:
        text: Text to convert
        voice: Voice selection
        speed: Speech speed
        temperature: Randomness
        response_format: Audio format
        base_url: TTS service URL

    Returns:
        Audio bytes
    """
    client = TTSClient(base_url=base_url)
    return client.audio.speech.create(
        text=text,
        voice=voice,
        speed=speed,
        temperature=temperature,
        response_format=response_format
    )