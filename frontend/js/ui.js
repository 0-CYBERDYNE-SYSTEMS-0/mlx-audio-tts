/**
 * UI Helper Functions
 */

/**
 * Toggle voice mode UI based on selection
 */
function toggleVoiceModeUI() {
    const presetGroup = document.getElementById('preset-voice-group');
    const cloneGroup = document.getElementById('clone-voice-group');
    const activeModeCard = document.querySelector('.mode-card.active');
    const selectedMode = activeModeCard ? activeModeCard.dataset.mode : 'preset';

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
            charCount.style.color = 'var(--primary)';
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
    const spinner = document.getElementById('loading-spinner');
    const btnText = generateBtn?.querySelector('.btn-text');

    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');
    }

    if (spinner) {
        spinner.classList.remove('hidden');
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
    const spinner = document.getElementById('loading-spinner');
    const btnText = generateBtn?.querySelector('.btn-text');

    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.classList.remove('loading');
    }

    if (spinner) {
        spinner.classList.add('hidden');
    }

    if (btnText) {
        btnText.textContent = 'Generate Audio';
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

        // Set audio player source using the enhanced audio player
        if (window.audioPlayer && result.audio_url) {
            const filename = result.filename || 'generated_audio.wav';
            const format = result.filename ? result.filename.split('.').pop() : 'wav';
            const duration = result.duration || 0;
            const estimatedSize = estimateFileSize(duration, format);

            window.audioPlayer.setAudioSource(result.audio_url, filename);
            window.audioPlayer.updateDownloadInfo(format, duration, estimatedSize);
        }

        // Update traditional stats as fallback
        const audioDuration = document.getElementById('audio-duration');
        const processingTime = document.getElementById('processing-time');
        const audioFormat = document.getElementById('audio-format');

        if (audioDuration && result.duration) {
            audioDuration.textContent = formatDuration(result.duration);
        }

        if (processingTime && result.processing_time) {
            processingTime.textContent = `${result.processing_time}s`;
        }

        if (audioFormat && result.filename) {
            const extension = result.filename.split('.').pop().toUpperCase();
            audioFormat.textContent = extension;
        }

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        // Show success notification
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
 * Setup waveform animation
 */
function setupWaveformAnimation(audioPlayer) {
    if (!audioPlayer) return;

    const waveBars = document.querySelectorAll('.wave-bar');
    if (waveBars.length === 0) return;

    // Pause all animations
    waveBars.forEach(bar => {
        bar.style.animationPlayState = 'paused';
    });

    // Play/pause animations based on audio state
    audioPlayer.addEventListener('play', () => {
        waveBars.forEach((bar, index) => {
            bar.style.animationPlayState = 'running';
            // Randomize animation delay for more realistic effect
            bar.style.animationDelay = `${Math.random() * 0.5}s`;
        });
    });

    audioPlayer.addEventListener('pause', () => {
        waveBars.forEach(bar => {
            bar.style.animationPlayState = 'paused';
        });
    });

    audioPlayer.addEventListener('ended', () => {
        waveBars.forEach(bar => {
            bar.style.animationPlayState = 'paused';
        });
    });
}

/**
 * Initialize typewriter effect for subtitle
 */
function initializeTypewriter() {
    const subtitle = document.querySelector('.typewriter');
    const text = subtitle?.textContent;

    if (subtitle && text) {
        subtitle.textContent = '';
        let index = 0;

        function typeChar() {
            if (index < text.length) {
                subtitle.textContent += text[index];
                index++;
                setTimeout(typeChar, 100);
            }
        }

        // Start typing after a short delay
        setTimeout(typeChar, 1000);
    }
}

/**
 * Add glitch effect to elements on hover
 */
function initializeGlitchEffects() {
    const glitchElements = document.querySelectorAll('.glitch-text');

    glitchElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            element.classList.add('glitch-active');
        });

        element.addEventListener('mouseleave', () => {
            element.classList.remove('glitch-active');
        });
    });
}

/**
 * Validate file upload
 */
function validateFileUpload(file) {
    // Check file type
    const allowedTypes = ['audio/wav', 'audio/mp3', 'audio/flac', 'audio/m4a', 'audio/ogg'];
    const allowedExtensions = ['.wav', '.mp3', '.flac', '.m4a', '.ogg'];

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
 * Show notification (fallback if audio player not available)
 */
function showNotification(message, type = 'info') {
    if (window.audioPlayer) {
        window.audioPlayer.showNotification(message, type);
    } else {
        // Simple fallback notification
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
            font-family: var(--font-body);
            z-index: 1000;
            animation: slide-in-right 0.3s ease-out;
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
}

// Initialize UI enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeTypewriter();
    initializeGlitchEffects();
});

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
        validateFileUpload
    };
}