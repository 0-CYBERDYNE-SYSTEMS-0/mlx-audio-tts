"""
TTS service wrapping mlx-audio functionality.
"""
import os
import sys
import re
from typing import Optional, Dict, Any, List

# Add mlx-audio to path if not found
try:
    from mlx_audio.tts.generate import generate_audio
except ImportError:
    # Try using miniconda3 Python
    miniconda_python = "/Users/scrimwiggins/miniconda3/bin/python3"
    if os.path.exists(miniconda_python):
        os.execv(miniconda_python, [miniconda_python] + sys.argv)

from backend.config import DEFAULT_MODEL, MAX_CHARS_PER_GENERATION, MIN_CHARS_PER_SEGMENT, SENTENCE_SPLIT_CHARS, CLAUSE_SPLIT_CHARS


class TTSService:
    """Service for text-to-speech generation using mlx-audio."""

    def __init__(self):
        """Initialize TTS service and load model."""
        self.model_path = DEFAULT_MODEL
        print(f"Initialized TTS service with model: {self.model_path}")

    def split_text_intelligently(self, text: str) -> List[str]:
        """
        Intelligently split text into segments for TTS generation.
        Prioritizes natural breaking points like sentences and clauses.
        """
        if len(text) <= MAX_CHARS_PER_GENERATION:
            return [text]

        segments = []

        # First, try to split by sentences
        sentences = re.split(f'([{SENTENCE_SPLIT_CHARS}])', text)
        current_segment = ""

        for i, part in enumerate(sentences):
            if part in SENTENCE_SPLIT_CHARS:
                # Add punctuation to previous word
                current_segment += part

                # Check if current segment is getting too long
                if len(current_segment) >= MAX_CHARS_PER_GENERATION * 0.8:
                    segments.append(current_segment.strip())
                    current_segment = ""
            else:
                # Check if adding this part would exceed the limit
                if len(current_segment + part) > MAX_CHARS_PER_GENERATION:
                    if current_segment.strip():
                        segments.append(current_segment.strip())
                    current_segment = part
                else:
                    current_segment += part

        # Add any remaining text
        if current_segment.strip():
            segments.append(current_segment.strip())

        # If we still have segments that are too long, split by clauses
        final_segments = []
        for segment in segments:
            if len(segment) <= MAX_CHARS_PER_GENERATION:
                final_segments.append(segment)
            else:
                # Split by clauses for very long segments
                clauses = re.split(f'([{CLAUSE_SPLIT_CHARS}])', segment)
                current_clause = ""

                for i, part in enumerate(clauses):
                    if part in CLAUSE_SPLIT_CHARS:
                        current_clause += part

                        if len(current_clause) >= MAX_CHARS_PER_GENERATION * 0.6:
                            final_segments.append(current_clause.strip())
                            current_clause = ""
                    else:
                        if len(current_clause + part) > MAX_CHARS_PER_GENERATION:
                            if current_clause.strip():
                                final_segments.append(current_clause.strip())
                            current_clause = part
                        else:
                            current_clause += part

                if current_clause.strip():
                    final_segments.append(current_clause.strip())

        # If we still have very long segments, split them at word boundaries
        ultra_fine_segments = []
        for segment in final_segments:
            if len(segment) <= MAX_CHARS_PER_GENERATION:
                ultra_fine_segments.append(segment)
            else:
                words = segment.split()
                current_words = []
                current_length = 0

                for word in words:
                    if current_length + len(word) + 1 > MAX_CHARS_PER_GENERATION:
                        if current_words:
                            ultra_fine_segments.append(' '.join(current_words))
                        current_words = [word]
                        current_length = len(word)
                    else:
                        current_words.append(word)
                        current_length += len(word) + 1

                if current_words:
                    ultra_fine_segments.append(' '.join(current_words))

        # Filter out empty or too short segments
        filtered_segments = [
            seg for seg in ultra_fine_segments
            if len(seg.strip()) >= MIN_CHARS_PER_SEGMENT
        ]

        return filtered_segments if filtered_segments else [text[:MAX_CHARS_PER_GENERATION]]

    def merge_audio_segments(self, audio_segments: List[bytes], audio_format: str = 'wav') -> bytes:
        """
        Merge multiple audio segments into a single audio file.
        """
        if len(audio_segments) == 1:
            return audio_segments[0]

        import tempfile
        import soundfile as sf
        import numpy as np

        try:
            # Load all audio segments
            audio_data = []
            sample_rates = []

            temp_files = []
            for i, segment in enumerate(audio_segments):
                with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp:
                    tmp.write(segment)
                    temp_files.append(tmp.name)

            # Read all audio files
            for temp_file in temp_files:
                data, sr = sf.read(temp_file)
                audio_data.append(data)
                sample_rates.append(sr)

            # Ensure all sample rates are the same
            if len(set(sample_rates)) > 1:
                # Resample if needed (for simplicity, we'll use the first sample rate)
                target_sr = sample_rates[0]
                print(f"Warning: Different sample rates found. Using {target_sr} Hz")

            # Concatenate audio data
            if len(audio_data[0].shape) == 1:
                # Mono audio
                combined_audio = np.concatenate(audio_data)
            else:
                # Multi-channel audio
                combined_audio = np.concatenate(audio_data, axis=0)

            # Create output file
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as output_tmp:
                sf.write(output_tmp.name, combined_audio, sample_rates[0])
                with open(output_tmp.name, 'rb') as f:
                    result = f.read()

            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

            try:
                os.remove(output_tmp.name)
            except Exception:
                pass

            return result

        except Exception as e:
            print(f"Error merging audio segments: {e}")
            # Fallback: return first segment
            return audio_segments[0] if audio_segments else b''

    def generate_with_preset(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        temperature: float = 0.7,
        audio_format: str = 'wav'
    ) -> Dict[str, Any]:
        """
        Generate audio using a preset voice.
        Automatically splits long text and merges results.

        Returns:
            Dictionary with audio data and metadata
        """
        import tempfile
        import soundfile as sf
        import time

        # Split text into manageable segments
        text_segments = self.split_text_intelligently(text)
        print(f"Split text into {len(text_segments)} segments")

        # Generate audio for each segment
        audio_segments = []
        total_duration = 0.0

        for i, segment in enumerate(text_segments):
            print(f"Generating segment {i+1}/{len(text_segments)} ({len(segment)} chars)")

            # Create temporary output file for this segment
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp:
                temp_prefix = tmp.name.rsplit('.', 1)[0]

            try:
                # Generate audio using mlx-audio
                generate_audio(
                    text=segment,
                    model_path=self.model_path,
                    voice=voice,
                    speed=speed,
                    temperature=temperature,
                    file_prefix=temp_prefix,
                    audio_format=audio_format,
                    verbose=False
                )

                # Read generated audio (MLX-Audio adds _000 suffix)
                output_file = f"{temp_prefix}_000.{audio_format}"

                if not os.path.exists(output_file):
                    raise RuntimeError(f"Audio generation failed - no output file created at {output_file}")

                # Read raw bytes for saving
                with open(output_file, 'rb') as f:
                    audio_bytes = f.read()

                audio_segments.append(audio_bytes)

                # Get metadata for this segment
                audio_data, sample_rate = sf.read(output_file)
                segment_duration = float(len(audio_data) / sample_rate)
                total_duration += segment_duration

            finally:
                # Cleanup temporary file (MLX-Audio adds _000 suffix)
                try:
                    temp_file = f"{temp_prefix}_000.{audio_format}"
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass

        # Merge all segments
        if len(audio_segments) > 1:
            print(f"Merging {len(audio_segments)} audio segments...")
            merged_audio = self.merge_audio_segments(audio_segments, audio_format)
        else:
            merged_audio = audio_segments[0]

        # Get final duration from the merged audio
        try:
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp:
                tmp.write(merged_audio)
                tmp.flush()

                audio_data, sample_rate = sf.read(tmp.name)
                final_duration = float(len(audio_data) / sample_rate)

                # Cleanup
                os.remove(tmp.name)
        except Exception:
            # Fallback to calculated duration
            final_duration = total_duration

        return {
            'success': True,
            'audio_data': merged_audio,
            'duration': final_duration,
            'sample_rate': sample_rate if 'sample_rate' in locals() else 24000,
            'format': audio_format,
            'segments_generated': len(text_segments)
        }

    def generate_with_cloning(
        self,
        text: str,
        ref_audio_path: str,
        ref_text: Optional[str] = None,
        speed: float = 1.0,
        temperature: float = 0.7,
        audio_format: str = 'wav'
    ) -> Dict[str, Any]:
        """
        Generate audio using voice cloning with reference audio.
        Automatically splits long text and merges results.

        Returns:
            Dictionary with audio data and metadata
        """
        import tempfile
        import soundfile as sf

        # Split text into manageable segments
        text_segments = self.split_text_intelligently(text)
        print(f"Split text into {len(text_segments)} segments for cloning")

        # Generate audio for each segment
        audio_segments = []
        total_duration = 0.0

        for i, segment in enumerate(text_segments):
            print(f"Generating cloned segment {i+1}/{len(text_segments)} ({len(segment)} chars)")

            # Create temporary output file for this segment
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp:
                temp_prefix = tmp.name.rsplit('.', 1)[0]

            try:
                # Generate audio using mlx-audio with reference audio
                generate_audio(
                    text=segment,
                    model_path=self.model_path,
                    ref_audio=ref_audio_path,
                    ref_text=ref_text,
                    speed=speed,
                    temperature=temperature,
                    file_prefix=temp_prefix,
                    audio_format=audio_format,
                    verbose=False
                )

                # Read generated audio (MLX-Audio adds _000 suffix)
                output_file = f"{temp_prefix}_000.{audio_format}"

                if not os.path.exists(output_file):
                    raise RuntimeError(f"Audio generation failed - no output file created at {output_file}")

                # Read raw bytes for saving
                with open(output_file, 'rb') as f:
                    audio_bytes = f.read()

                audio_segments.append(audio_bytes)

                # Get metadata for this segment
                audio_data, sample_rate = sf.read(output_file)
                segment_duration = float(len(audio_data) / sample_rate)
                total_duration += segment_duration

            finally:
                # Cleanup temporary file (MLX-Audio adds _000 suffix)
                try:
                    temp_file = f"{temp_prefix}_000.{audio_format}"
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass

        # Merge all segments
        if len(audio_segments) > 1:
            print(f"Merging {len(audio_segments)} cloned audio segments...")
            merged_audio = self.merge_audio_segments(audio_segments, audio_format)
        else:
            merged_audio = audio_segments[0]

        # Get final duration from the merged audio
        try:
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp:
                tmp.write(merged_audio)
                tmp.flush()

                audio_data, sample_rate = sf.read(tmp.name)
                final_duration = float(len(audio_data) / sample_rate)

                # Cleanup
                os.remove(tmp.name)
        except Exception:
            # Fallback to calculated duration
            final_duration = total_duration

        return {
            'success': True,
            'audio_data': merged_audio,
            'duration': final_duration,
            'sample_rate': sample_rate if 'sample_rate' in locals() else 24000,
            'format': audio_format,
            'segments_generated': len(text_segments)
        }
