/**
 * UI Helper Functions for KREO TTS
 */

/**
 * Toggle voice mode UI based on selection
 */
function toggleVoiceModeUI() {
    const presetGroup = document.getElementById('preset-group');
    const cloneGroup = document.getElementById('clone-group');
    const activeVoiceOption = document.querySelector('.voice-option.active');
    const selectedMode = activeVoiceOption ? activeVoiceOption.dataset.mode : 'preset';

    if (selectedMode === 'preset') {
        if (presetGroup) presetGroup.classList.remove('hidden');
        if (cloneGroup) cloneGroup.classList.add('hidden');
    } else {
        if (presetGroup) presetGroup.classList.add('hidden');
        if (cloneGroup) cloneGroup.classList.remove('hidden');
    }
}

/**
 * Update character count
 */
function updateCharCount() {
    const textInput = document.getElementById('text-input');
    const charCount = document.getElementById('char-count');

    if (textInput && charCount) {
        const currentLength = textInput.value.length;
        charCount.textContent = currentLength;

        // Change color based on character count
        if (currentLength > 4500) {
            charCount.style.color = 'var(--error)';
        } else if (currentLength > 4000) {
            charCount.style.color = 'var(--warning)';
        } else {
            charCount.style.color = 'var(--text-tertiary)';
        }
    }
}

/**
 * Update slider values
 */
function updateSliderValues() {
    updateSliderValue('speed');
    updateSliderValue('temperature');
}

/**
 * Update individual slider value
 */
function updateSliderValue(type) {
    const slider = document.getElementById(`${type}-slider`);
    const valueDisplay = document.getElementById(`${type}-value`);
    const sliderFill = slider?.parentElement?.querySelector('.slider-fill');

    if (slider && valueDisplay) {
        const value = parseFloat(slider.value);
        let displayValue;

        if (type === 'speed') {
            displayValue = value.toFixed(1) + 'x';
        } else {
            displayValue = value.toFixed(1);
        }

        valueDisplay.textContent = displayValue;

        // Update slider fill
        if (sliderFill) {
            const min = parseFloat(slider.min);
            const max = parseFloat(slider.max);
            const percentage = ((value - min) / (max - min)) * 100;
            sliderFill.style.width = `${percentage}%`;
        }
    }
}

/**
 * Show loading state
 */
function showLoading() {
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn?.querySelector('.btn-text');

    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');
    }

    if (btnText) {
        btnText.textContent = 'Generating...';
    }

    // Hide results section
    hideResults();
}

/**
 * Hide loading state
 */
function hideLoading() {
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn?.querySelector('.btn-text');

    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.classList.remove('loading');
    }

    if (btnText) {
        btnText.textContent = 'Generate Speech';
    }
}

/**
 * Show error message
 */
function showError(message) {
    const errorElement = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    if (errorElement && errorText) {
        errorText.textContent = message;
        errorElement.classList.remove('hidden');

        // Auto-hide after 10 seconds
        setTimeout(() => {
            errorElement.classList.add('hidden');
        }, 10000);

        // Scroll to error
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Hide error message
 */
function hideError() {
    const errorElement = document.getElementById('error-message');
    if (errorElement) {
        errorElement.classList.add('hidden');
    }
}

/**
 * Show results section
 */
function showResults(result) {
    const resultsSection = document.getElementById('results-section');

    if (resultsSection) {
        resultsSection.classList.remove('hidden');

        // Set audio player source
        const audioPlayer = document.getElementById('audio-player');
        const playBtn = document.getElementById('play-btn');
        const downloadBtn = document.getElementById('download-btn');

        if (audioPlayer && result.audio_url) {
            audioPlayer.src = result.audio_url;

            // Setup play button
            if (playBtn) {
                playBtn.onclick = () => {
                    if (audioPlayer.paused) {
                        audioPlayer.play();
                        playBtn.innerHTML = `
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="6" y="4" width="4" height="16"/>
                                <rect x="14" y="4" width="4" height="16"/>
                            </svg>
                        `;
                    } else {
                        audioPlayer.pause();
                        playBtn.innerHTML = `
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="5,3 19,12 5,21 5,3"/>
                            </svg>
                        `;
                    }
                };

                // Setup download button
                if (downloadBtn) {
                    downloadBtn.onclick = () => {
                        const link = document.createElement('a');
                        link.href = result.audio_url;
                        link.download = result.filename || 'generated_speech.wav';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    };
                }

                // Update time displays
                audioPlayer.addEventListener('loadedmetadata', () => {
                    const totalTime = document.getElementById('total-time');
                    const duration = audioPlayer.duration;

                    if (totalTime && duration) {
                        totalTime.textContent = formatDuration(duration);
                    }

                    // Update audio duration stat
                    const audioDurationStat = document.getElementById('audio-duration');
                    if (audioDurationStat) {
                        audioDurationStat.textContent = formatDuration(duration);
                    }
                });

                // Update progress
                audioPlayer.addEventListener('timeupdate', () => {
                    const progressFill = document.getElementById('progress-fill');
                    const currentTimeEl = document.getElementById('current-time');
                    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;

                    if (progressFill) {
                        progressFill.style.width = `${progress}%`;
                    }

                    if (currentTimeEl) {
                        currentTimeEl.textContent = formatDuration(audioPlayer.currentTime);
                    }

                    // Update waveform
                    updateWaveform(progress);
                });

                // Reset play button when audio ends
                audioPlayer.addEventListener('ended', () => {
                    playBtn.innerHTML = `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5,3 19,12 5,21 5,3"/>
                        </svg>
                    `;
                    updateWaveform(0);
                });
            }
        }

        // Update stats
        const processingTime = document.getElementById('processing-time');
        if (processingTime && result.processing_time) {
            processingTime.textContent = `${result.processing_time}s`;
        }

        const audioFormat = document.getElementById('audio-format');
        if (audioFormat && result.filename) {
            const extension = result.filename.split('.').pop().toUpperCase();
            audioFormat.textContent = extension;
        }

        // Estimate file size
        const audioSize = document.getElementById('audio-size');
        if (audioSize && result.duration) {
            const format = result.filename ? result.filename.split('.').pop() : 'wav';
            audioSize.textContent = estimateFileSize(result.duration, format);
        }

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        // Show success notification for multi-segment audio
        if (result.segments_generated > 1) {
            showNotification(`Successfully merged ${result.segments_generated} audio segments!`, 'success');
        }
    }
}

/**
 * Hide results section
 */
function hideResults() {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.classList.add('hidden');
    }
}

/**
 * Format duration in seconds to human readable format
 */
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    if (minutes > 0) {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${remainingSeconds}s`;
    }
}

/**
 * Update waveform visualization
 */
function updateWaveform(progress) {
    const waveBars = document.querySelectorAll('.wave-bar');
    if (!waveBars.length) return;

    const barsToHighlight = Math.floor((progress / 100) * waveBars.length);

    waveBars.forEach((bar, index) => {
        if (index < barsToHighlight) {
            bar.classList.add('played');
        } else {
            bar.classList.remove('played');
        }
    });
}

/**
 * Populate voices dropdown
 */
function populateVoices(voices) {
    const voiceSelect = document.getElementById('voice-select');
    if (!voiceSelect) return;

    // Clear existing options
    voiceSelect.innerHTML = '';

    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a voice...';
    voiceSelect.appendChild(defaultOption);

    // Add voice options
    voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice;
        option.textContent = formatVoiceName(voice);
        voiceSelect.appendChild(option);
    });

    // Select first voice by default
    if (voices.length > 0) {
        voiceSelect.value = voices[0];
    }
}

/**
 * Format voice name for display
 */
function formatVoiceName(voice) {
    return voice
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Validate file upload
 */
function validateFileUpload(file) {
    // Check file type
    const allowedTypes = ['audio/wav', 'audio/mp3', 'audio/flac', 'audio/m4a', 'audio/ogg', 'audio/webm'];
    const allowedExtensions = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm'];

    const hasValidType = allowedTypes.includes(file.type);
    const hasValidExtension = allowedExtensions.some(ext =>
        file.name.toLowerCase().endsWith(ext)
    );

    if (!hasValidType && !hasValidExtension) {
        throw new Error('Invalid file type. Please upload a valid audio file.');
    }

    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        throw new Error('File size too large. Please upload a file smaller than 50MB.');
    }

    return true;
}

/**
 * Estimate file size based on duration and format
 */
function estimateFileSize(duration, format) {
    const bitRates = {
        'wav': 1411,    // kbps (CD quality)
        'mp3': 128,     // kbps (standard quality)
        'flac': 800,    // kbps (lossless compressed)
    };

    const bitRate = bitRates[format.toLowerCase()] || 128;
    const sizeInBytes = (duration * bitRate * 1000) / 8;
    const sizeInMB = sizeInBytes / (1024 * 1024);

    if (sizeInMB < 1) {
        return `~${Math.round(sizeInMB * 1024)} KB`;
    } else {
        return `~${sizeInMB.toFixed(1)} MB`;
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--primary)'};
        color: white;
        font-family: var(--font-system);
        z-index: 1000;
        animation: slide-in-right 0.3s ease-out;
        box-shadow: var(--shadow-lg);
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slide-out-right 0.3s ease-out';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Add slide animations to document
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in-right {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slide-out-right {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleVoiceModeUI,
        updateCharCount,
        updateSliderValues,
        showLoading,
        hideLoading,
        showError,
        hideError,
        showResults,
        hideResults,
        formatDuration,
        populateVoices,
        formatVoiceName,
        validateFileUpload,
        estimateFileSize,
        showNotification,
        updateWaveform
    };
}