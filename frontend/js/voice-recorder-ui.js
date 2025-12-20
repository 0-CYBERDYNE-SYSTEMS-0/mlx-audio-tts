/**
 * Voice Recorder UI Integration
 * Handles the frontend voice recording interface
 */

// Global variables
let audioRecorder = null;
let recordingTimer = null;
let recordingStartTime = null;
let visualizationFrame = null;

/**
 * Initialize voice recording functionality
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize after DOM is loaded
    console.log('DOM loaded, initializing voice recorder...');
    initializeVoiceRecorder();
});

/**
 * Initialize voice recorder
 */
async function initializeVoiceRecorder() {
    // Check if AudioRecorder class is available
    if (typeof AudioRecorder === 'undefined') {
        console.error('AudioRecorder class not loaded');
        showRecordingError('Audio recorder not available. Please refresh the page.');
        return;
    }

    // Check if recording is supported
    if (!AudioRecorder.isSupported()) {
        console.error('Audio recording is not supported in this browser');
        showRecordingError('Audio recording is not supported in this browser');
        return;
    }

    // Setup event listeners
    setupRecordingEventListeners();

    // Load audio devices
    await loadAudioDevices();

    console.log('Voice recorder initialized');
}

/**
 * Setup recording event listeners
 */
function setupRecordingEventListeners() {
    // Record button
    const recordBtn = document.getElementById('record-btn');
    if (recordBtn) {
        recordBtn.addEventListener('click', toggleRecording);
    }

    // Source tabs
    const sourceTabs = document.querySelectorAll('.source-tab');
    sourceTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            const source = e.currentTarget.dataset.source;
            switchAudioSource(source);
        });
    });

    // Device selection
    const deviceSelect = document.getElementById('device-select');
    if (deviceSelect) {
        deviceSelect.addEventListener('change', (e) => {
            if (audioRecorder && audioRecorder.isRecording) {
                showRecordingError('Cannot change device while recording');
                e.target.value = audioRecorder.currentDeviceId || '';
            }
        });
    }

    // Voice mode switching
    const modeCards = document.querySelectorAll('.mode-card');
    modeCards.forEach(card => {
        card.addEventListener('click', () => {
            setTimeout(() => {
                handleVoiceModeChange();
            }, 100);
        });
    });
}

/**
 * Handle voice mode change (preset/clone)
 */
function handleVoiceModeChange() {
    const activeModeCard = document.querySelector('.mode-card.active');
    if (!activeModeCard) return;

    const mode = activeModeCard.dataset.mode;
    const cloneVoiceGroup = document.getElementById('clone-voice-group');

    if (mode === 'clone' && cloneVoiceGroup) {
        // Clone mode selected - show recording interface by default
        const recordingInterface = document.getElementById('recording-interface');
        const uploadInterface = document.getElementById('upload-interface');

        if (recordingInterface && uploadInterface) {
            // Make sure interfaces are visible
            cloneVoiceGroup.classList.remove('hidden');

            // Set recording tab as active
            switchAudioSource('record');
        }
    }
}

/**
 * Load available audio devices
 */
async function loadAudioDevices() {
    try {
        const devices = await AudioRecorder.getAudioDevices();
        const deviceSelect = document.getElementById('device-select');

        if (deviceSelect && devices.length > 0) {
            // Clear existing options
            deviceSelect.innerHTML = '<option value="">Default Microphone</option>';

            // Add device options
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = device.name;
                deviceSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading audio devices:', error);
    }
}

/**
 * Switch between audio sources (record/upload)
 */
function switchAudioSource(source) {
    // Update tab states
    const sourceTabs = document.querySelectorAll('.source-tab');
    sourceTabs.forEach(tab => {
        if (tab.dataset.source === source) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Show/hide interfaces
    const recordingInterface = document.getElementById('recording-interface');
    const uploadInterface = document.getElementById('upload-interface');

    if (source === 'record') {
        recordingInterface.classList.remove('hidden');
        uploadInterface.classList.add('hidden');
    } else {
        recordingInterface.classList.add('hidden');
        uploadInterface.classList.remove('hidden');
    }
}

/**
 * Toggle recording state
 */
async function toggleRecording() {
    console.log('Toggle recording clicked. Current state:', {
        hasRecorder: !!audioRecorder,
        isRecording: audioRecorder?.isRecording
    });

    if (!audioRecorder || !audioRecorder.isRecording) {
        console.log('Starting recording...');
        await startRecording();
    } else {
        console.log('Stopping recording...');
        await stopRecording();
    }
}

/**
 * Start recording
 */
async function startRecording() {
    try {
        const recordBtn = document.getElementById('record-btn');
        const deviceSelect = document.getElementById('device-select');
        const deviceId = deviceSelect.value || null;

        // Initialize recorder if needed
        if (!audioRecorder) {
            audioRecorder = new AudioRecorder();
        }

        // Initialize with selected device
        await audioRecorder.initialize(deviceId);
        audioRecorder.currentDeviceId = deviceId;

        // Start recording
        await audioRecorder.start();

        // Update UI
        recordBtn.classList.add('recording');
        recordBtn.querySelector('span').textContent = 'Stop Recording';

        // Show recording status
        showRecordingStatus(true);

        // Start timer
        startRecordingTimer();

        // Start visualization
        startVisualization();

        console.log('Recording started');

    } catch (error) {
        console.error('Error starting recording:', error);
        showRecordingError('Failed to start recording: ' + error.message);
    }
}

/**
 * Stop recording
 */
async function stopRecording() {
    try {
        const recordBtn = document.getElementById('record-btn');

        // Stop recording (handles both local MediaRecorder and server)
        const serverResult = await audioRecorder.stop();

        // Build the recorded audio blob after stop so the final chunk is included
        const audioBlob = audioRecorder.getAudioBlob();
        console.debug('Stop recording results', {
            serverResult,
            blobSize: audioBlob ? audioBlob.size : 0,
            blobType: audioBlob ? audioBlob.type : null
        });

        // Update UI
        recordBtn.classList.remove('recording');
        recordBtn.querySelector('span').textContent = 'Start Recording';

        // Hide recording status
        showRecordingStatus(false);

        // Stop timer
        stopRecordingTimer();

        // Stop visualization
        stopVisualization();

        // Upload the recorded audio
        if (audioBlob && serverResult.status === 'success') {
            console.log('Uploading recorded audio...');

            try {
                // Upload the audio
                const uploadResult = await uploadRecordedAudio(audioBlob, serverResult);

                if (uploadResult.status === 'success') {
                    // Update file upload interface to show recorded audio
                    updateFileInterfaceWithRecording({
                        ...serverResult,
                        ...uploadResult
                    }, audioBlob);

                    // Switch to clone mode if not already
                    const cloneModeCard = document.querySelector('[data-mode="clone"]');
                    if (cloneModeCard && !cloneModeCard.classList.contains('active')) {
                        cloneModeCard.click();
                    }

                    console.log('Recording uploaded successfully');
                } else {
                    showRecordingError(`Upload failed: ${uploadResult.message || 'Unknown error'}`);
                }
            } catch (uploadError) {
                console.error('Upload error:', uploadError);
                showRecordingError(`Upload error: ${uploadError.message || 'Failed to upload recording'}`);
            }
        } else {
            if (!audioBlob) {
                showRecordingError('No audio data recorded - please try again');
            } else {
                showRecordingError(`Recording error: ${serverResult.message || 'Failed to stop recording'}`);
            }
        }

    } catch (error) {
        console.error('Error stopping recording:', error);
        showRecordingError('Failed to stop recording: ' + error.message);
    }
}

/**
 * Upload recorded audio to server
 */
async function uploadRecordedAudio(audioBlob, serverResult) {
    const formData = new FormData();

    // Determine file extension from MIME type or use WEBM as default
    let fileExtension = '.webm';  // Default for MediaRecorder

    if (audioBlob.type) {
        const mimeToExt = {
            'audio/webm': '.webm',
            'audio/wav': '.wav',
            'audio/mp3': '.mp3',
            'audio/ogg': '.ogg',
            'audio/mp4': '.mp4'
        };
        fileExtension = mimeToExt[audioBlob.type] || '.webm';
    }

    const sessionId = serverResult.session_id || serverResult.recording_id;
    const filenameSuffix = sessionId ? sessionId.slice(0, 8) : Date.now();
    const filename = `recording_${filenameSuffix}${fileExtension}`;
    formData.append('file', audioBlob, filename);

    try {
        console.log(`Uploading recording: ${filename} (${formatFileSize(audioBlob.size)})`);
        console.debug('Upload payload', {
            mimeType: audioBlob.type,
            size: audioBlob.size
        });

        const response = await fetch('/api/upload-reference', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`);
        }

        const result = await response.json();
        console.log('Upload response:', result);
        return result;
    } catch (error) {
        console.error('Error uploading audio:', error);
        throw error;
    }
}

/**
 * Show/hide recording status
 */
function showRecordingStatus(show) {
    const recordingStatus = document.getElementById('recording-status');

    if (show) {
        recordingStatus.classList.remove('hidden');
    } else {
        recordingStatus.classList.add('hidden');
    }
}

/**
 * Start recording timer
 */
function startRecordingTimer() {
    recordingStartTime = Date.now();
    updateRecordingTime();

    recordingTimer = setInterval(updateRecordingTime, 100);
}

/**
 * Stop recording timer
 */
function stopRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
}

/**
 * Update recording time display
 */
function updateRecordingTime() {
    const timeElement = document.getElementById('recording-time');
    if (!timeElement || !recordingStartTime) return;

    const elapsed = Date.now() - recordingStartTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const displaySeconds = seconds % 60;

    timeElement.textContent = `${minutes.toString().padStart(2, '0')}:${displaySeconds.toString().padStart(2, '0')}`;
}

/**
 * Start audio visualization
 */
function startVisualization() {
    const canvas = document.getElementById('visualizer-canvas');
    if (!canvas || !audioRecorder) return;

    const visualizer = document.getElementById('audio-visualizer');
    visualizer.classList.remove('hidden');

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    function draw() {
        if (!audioRecorder.isRecording) return;

        visualizationFrame = requestAnimationFrame(draw);

        // Get frequency data
        const dataArray = audioRecorder.getFrequencyData();
        if (dataArray.length === 0) return;

        // Clear canvas
        ctx.fillStyle = 'rgba(10, 10, 15, 0.2)';
        ctx.fillRect(0, 0, width, height);

        // Draw bars
        const barWidth = width / dataArray.length * 2.5;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            const barHeight = (dataArray[i] / 255) * height * 0.8;

            // Create gradient
            const gradient = ctx.createLinearGradient(0, height - barHeight, 0, height);
            gradient.addColorStop(0, '#00d4ff');
            gradient.addColorStop(1, '#ff00ff');

            ctx.fillStyle = gradient;
            ctx.fillRect(x, height - barHeight, barWidth, barHeight);

            x += barWidth + 1;
        }
    }

    draw();
}

/**
 * Stop audio visualization
 */
function stopVisualization() {
    if (visualizationFrame) {
        cancelAnimationFrame(visualizationFrame);
        visualizationFrame = null;
    }

    const visualizer = document.getElementById('audio-visualizer');
    visualizer.classList.add('hidden');

    // Clear canvas
    const canvas = document.getElementById('visualizer-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
}

/**
 * Update file upload interface with recorded audio
 */
function updateFileInterfaceWithRecording(result, audioBlob = null) {
    // Switch to upload tab
    const uploadTab = document.querySelector('[data-source="upload"]');
    if (uploadTab) {
        uploadTab.click();
    }

    // Update file info - prioritize upload result data over server result
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const fileUploadArea = document.getElementById('file-upload-area');
    const fileInfo = document.getElementById('file-info');

    if (fileName && fileSize && fileUploadArea && fileInfo) {
        // Use filename from upload result if available, otherwise generate one
        const finalFilename = result.filename || `recording_${Date.now()}.wav`;
        fileName.textContent = finalFilename;

        // Calculate actual file size
        if (audioBlob && audioBlob.size) {
            // Use the actual blob size if available
            fileSize.textContent = formatFileSize(audioBlob.size);
        } else if (result.duration) {
            // Calculate estimated size based on duration and format
            // WEBM/Opus: ~24 kbps, WAV: ~705 kbps (22050 Hz * 16-bit * mono)
            const isCompressed = finalFilename && (finalFilename.endsWith('.webm') || finalFilename.endsWith('.ogg'));
            const bitrate = isCompressed ? 24000 : 22050 * 16; // bits per second
            const estimatedSize = Math.round(result.duration * (bitrate / 8)); // bytes
            fileSize.textContent = `~${formatFileSize(estimatedSize)}`;
        } else {
            // Default size estimate
            fileSize.textContent = '~500 KB';
        }

        fileInfo.classList.remove('hidden');
        fileUploadArea.classList.add('hidden');
    }

    // Store the ref_audio_id for form submission - use upload result first
    const refAudioUpload = document.getElementById('ref-audio-upload');
    if (refAudioUpload) {
        // Prioritize ref_audio_id from upload result (actual file upload)
        const refAudioId = result.ref_audio_id || null;
        if (refAudioId) {
            refAudioUpload.dataset.fileId = refAudioId;
        }
    }
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Show recording error
 */
function showRecordingError(message) {
    // Create error element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'recording-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--error);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(errorDiv);

    // Remove after 3 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    if (audioRecorder && audioRecorder.isRecording) {
        audioRecorder.cleanup();
    }
    stopRecordingTimer();
    stopVisualization();
});
