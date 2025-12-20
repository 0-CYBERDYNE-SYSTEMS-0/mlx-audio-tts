/**
 * Web Audio Recorder Module
 * Provides audio recording capabilities using the Web Audio API
 */

class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.stream = null;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.recordingSessionId = null;
    }

    /**
     * Initialize audio recording
     */
    async initialize(deviceId = null) {
        try {
            // Request microphone access
            const constraints = {
                audio: deviceId ? { deviceId: { exact: deviceId } } : true,
                video: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);

            // Setup audio context for visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            this.microphone = this.audioContext.createMediaStreamSource(this.stream);
            this.microphone.connect(this.analyser);

            // Setup MediaRecorder
            const options = {
                mimeType: this.getSupportedMimeType()
            };

            this.mediaRecorder = new MediaRecorder(this.stream, options);

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                    console.debug('MediaRecorder chunk', {
                        size: event.data.size,
                        type: event.data.type,
                        chunks: this.audioChunks.length
                    });
                }
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.isRecording = false;
            };

            return true;
        } catch (error) {
            console.error('Error initializing audio recorder:', error);
            throw error;
        }
    }

    /**
     * Get supported audio MIME type
     */
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/wav',
            'audio/mp4'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return 'audio/webm'; // Fallback
    }

    /**
     * Start recording
     */
    async start() {
        if (!this.mediaRecorder) {
            throw new Error('Recorder not initialized. Call initialize() first.');
        }

        if (this.isRecording) {
            throw new Error('Already recording');
        }

        console.debug('Starting recording', {
            mimeType: this.getSupportedMimeType()
        });

        // Start recording on server
        try {
            const response = await fetch('/api/recording/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sample_rate: 22050,
                    channels: 1,
                    format: 'int16'
                })
            });

            const result = await response.json();
            if (result.status !== 'success') {
                throw new Error(result.message || 'Failed to start recording on server');
            }

            this.recordingSessionId = result.recording_id;
            console.debug('Recording session started', {
                sessionId: this.recordingSessionId
            });
        } catch (error) {
            console.error('Error starting server recording:', error);
            throw error;
        }

        // Clear previous chunks
        this.audioChunks = [];

        // Start local recording
        this.mediaRecorder.start(100); // Collect data every 100ms
        this.isRecording = true;

        console.log('Recording started');
    }

    /**
     * Stop recording
     */
    async stop() {
        if (!this.isRecording) {
            throw new Error('Not recording');
        }

        console.debug('Stopping recording', {
            sessionId: this.recordingSessionId,
            chunks: this.audioChunks.length
        });

        // Stop local recording
        this.mediaRecorder.stop();
        this.isRecording = false;

        // Wait for recording to finish
        await new Promise(resolve => {
            this.mediaRecorder.onstop = resolve;
        });

        console.debug('MediaRecorder stopped', {
            chunks: this.audioChunks.length
        });

        // Stop server recording
        if (this.recordingSessionId) {
            try {
                const response = await fetch('/api/recording/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        recording_id: this.recordingSessionId,
                        process_audio: true,
                        normalize: true,
                        trim_silence: true,
                        noise_reduce: false
                    })
                });

                const result = await response.json();
                console.log('Recording stopped on server:', result);
                return result;
            } catch (error) {
                console.error('Error stopping server recording:', error);
                throw error;
            }
        }

        return { status: 'success' };
    }

    /**
     * Get audio blob
     */
    getAudioBlob() {
        if (this.audioChunks.length === 0) {
            return null;
        }

        const mimeType = this.getSupportedMimeType();
        const blob = new Blob(this.audioChunks, { type: mimeType });
        console.debug('Built audio blob', {
            size: blob.size,
            type: blob.type
        });
        return blob;
    }

    /**
     * Get audio data as base64
     */
    async getAudioBase64() {
        const blob = this.getAudioBlob();
        if (!blob) {
            return null;
        }

        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
    }

    /**
     * Upload audio for voice cloning
     */
    async uploadForCloning(blob = null) {
        const audioBlob = blob || this.getAudioBlob();
        if (!audioBlob) {
            throw new Error('No audio to upload');
        }

        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.wav');

        try {
            const response = await fetch('/api/upload-reference', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.status !== 'success') {
                throw new Error(result.message || 'Failed to upload audio');
            }

            return result;
        } catch (error) {
            console.error('Error uploading audio:', error);
            throw error;
        }
    }

    /**
     * Get audio level for visualization
     */
    getAudioLevel() {
        if (!this.analyser) {
            return 0;
        }

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);

        // Calculate average level
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }

        return sum / dataArray.length;
    }

    /**
     * Get frequency data for visualization
     */
    getFrequencyData() {
        if (!this.analyser) {
            return new Uint8Array(0);
        }

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);
        return dataArray;
    }

    /**
     * Get available audio devices
     */
    static async getAudioDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices
                .filter(device => device.kind === 'audioinput')
                .map(device => ({
                    id: device.deviceId,
                    name: device.label || `Microphone ${device.deviceId.slice(0, 5)}...`,
                    capabilities: device.getCapabilities ? device.getCapabilities() : null
                }));
        } catch (error) {
            console.error('Error getting audio devices:', error);
            return [];
        }
    }

    /**
     * Check if recording is supported
     */
    static isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && MediaRecorder);
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.mediaRecorder = null;
        this.analyser = null;
        this.microphone = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingSessionId = null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioRecorder;
}

// Expose to browser global scope
if (typeof window !== 'undefined') {
    window.AudioRecorder = AudioRecorder;
}
