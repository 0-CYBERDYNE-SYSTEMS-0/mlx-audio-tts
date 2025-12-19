/**
 * API client for backend communication
 */

const API_BASE = '';

/**
 * Fetch available voices
 */
async function fetchVoices() {
    try {
        const response = await fetch(`${API_BASE}/api/voices`);
        if (!response.ok) {
            throw new Error('Failed to fetch voices');
        }
        const data = await response.json();

        // Extract voice IDs from voice objects
        if (data.voices && Array.isArray(data.voices)) {
            return data.voices.map(voice =>
                typeof voice === 'string' ? voice : voice.id || voice.name
            ).filter(Boolean);
        }

        return data.voices || [];
    } catch (error) {
        console.error('Error fetching voices:', error);
        throw error;
    }
}

/**
 * Upload reference audio file
 */
async function uploadReferenceAudio(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/api/upload-reference`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error uploading reference audio:', error);
        throw error;
    }
}

/**
 * Generate TTS audio with progress tracking for long texts
 */
async function generateAudio(params, onProgress = null) {
    try {
        const textLength = params.text.length;
        const isLongText = textLength > 300; // Threshold for progress tracking

        if (isLongText && onProgress) {
            // Estimate number of segments
            const estimatedSegments = Math.ceil(textLength / 300);
            onProgress({
                type: 'segment_info',
                segments: estimatedSegments,
                message: `Splitting text into ${estimatedSegments} segments...`
            });
        }

        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Generation failed');
        }

        const data = await response.json();

        if (data.segments_generated && onProgress) {
            onProgress({
                type: 'complete',
                segments: data.segments_generated,
                message: `Successfully generated and merged ${data.segments_generated} audio segments`
            });
        }

        return data;
    } catch (error) {
        console.error('Error generating audio:', error);
        throw error;
    }
}

/**
 * Download audio file (client-side helper)
 */
function downloadAudio(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
