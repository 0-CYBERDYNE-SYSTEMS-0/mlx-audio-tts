/**
 * Main application logic for MLX-Audio TTS Generator
 */

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎤 MLX-Audio TTS Generator Initializing...');

    // Initialize application
    await initApp();

    // Setup event listeners
    setupEventListeners();

    console.log('✅ Application ready');
});

/**
 * Initialize the application
 */
async function initApp() {
    try {
        // Load available voices
        console.log('Loading voices...');
        const voices = await fetchVoices();
        populateVoices(voices);
        console.log(`✅ Loaded ${voices.length} voices`);

        // Set initial UI state
        toggleVoiceModeUI();
        updateSliderValues();
        updateCharCount();
        initializeFormatButtons();
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showError('Failed to load voices. Please refresh the page.');
    }
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Voice mode cards
    const modeCards = document.querySelectorAll('.mode-card');
    modeCards.forEach(card => {
        card.addEventListener('click', () => {
            // Remove active class from all cards
            modeCards.forEach(c => c.classList.remove('active'));
            // Add active class to clicked card
            card.classList.add('active');

            // Update hidden radio button
            const radio = card.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }

            toggleVoiceModeUI();
        });
    });

    // Text input with character count
    const textInput = document.getElementById('text-input');
    if (textInput) {
        textInput.addEventListener('input', updateCharCount);

        // Keyboard shortcut: Ctrl+Enter to generate
        textInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                document.getElementById('tts-form').dispatchEvent(new Event('submit'));
            }
        });
    }

    // Sliders
    const speedSlider = document.getElementById('speed-slider');
    const temperatureSlider = document.getElementById('temperature-slider');

    if (speedSlider) {
        speedSlider.addEventListener('input', () => updateSliderValue('speed'));
    }

    if (temperatureSlider) {
        temperatureSlider.addEventListener('input', () => updateSliderValue('temperature'));
    }

    // Format buttons
    const formatButtons = document.querySelectorAll('.format-btn');
    formatButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            formatButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const formatSelect = document.getElementById('format-select');
            if (formatSelect) {
                formatSelect.value = btn.dataset.format;
            }
        });
    });

    // Form submission
    const form = document.getElementById('tts-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // File upload
    const refAudioUpload = document.getElementById('ref-audio-upload');
    if (refAudioUpload) {
        refAudioUpload.addEventListener('change', handleFileUpload);
    }

    // File remove button
    const fileRemove = document.getElementById('file-remove');
    if (fileRemove) {
        fileRemove.addEventListener('click', removeUploadedFile);
    }

    // Drag and drop
    const fileUploadArea = document.getElementById('file-upload-area');
    if (fileUploadArea) {
        setupDragAndDrop(fileUploadArea);
    }
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop(dropArea) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove('drag-over');
        }, false);
    });

    dropArea.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    const fileInput = document.getElementById('ref-audio-upload');
    if (fileInput && files.length > 0) {
        fileInput.files = files;
        handleFileUpload({ target: fileInput });
    }
}

/**
 * Handle file upload
 */
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        validateFileUpload(file);
        displayUploadedFile(file);
        hideError();
        console.log(`✅ File validated: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
    } catch (error) {
        showError(error.message);
        e.target.value = ''; // Clear file input
    }
}

/**
 * Display uploaded file info
 */
function displayUploadedFile(file) {
    const fileUploadArea = document.getElementById('file-upload-area');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');

    if (fileUploadArea && fileInfo && fileName && fileSize) {
        fileUploadArea.classList.add('hidden');
        fileInfo.classList.remove('hidden');

        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
    }
}

/**
 * Remove uploaded file
 */
function removeUploadedFile() {
    const fileUploadArea = document.getElementById('file-upload-area');
    const fileInfo = document.getElementById('file-info');
    const fileInput = document.getElementById('ref-audio-upload');

    if (fileUploadArea && fileInfo && fileInput) {
        fileUploadArea.classList.remove('hidden');
        fileInfo.classList.add('hidden');
        fileInput.value = '';
        fileInput.dataset.fileId = '';
    }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    // Hide previous results and errors
    hideError();
    hideResults();

    try {
        // Show loading state
        showLoading();

        // Collect form data
        const formData = collectFormData();

        // Validate inputs
        validateInputs(formData);

        // Generate audio
        const result = await performGeneration(formData);

        // Show results
        showResults(result);

        console.log('✅ Audio generated successfully');

    } catch (error) {
        console.error('Generation error:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

/**
 * Collect form data
 */
function collectFormData() {
    // Get the active mode card instead of radio button
    const activeModeCard = document.querySelector('.mode-card.active');
    const voiceMode = activeModeCard ? activeModeCard.dataset.mode : 'preset';

    return {
        text: document.getElementById('text-input').value.trim(),
        mode: voiceMode,
        voice: voiceMode === 'preset' ? document.getElementById('voice-select').value : null,
        ref_audio_id: voiceMode === 'clone' ? document.getElementById('ref-audio-upload').dataset.fileId : null,
        ref_text: document.getElementById('ref-text-input').value.trim() || null,
        speed: parseFloat(document.getElementById('speed-slider').value),
        temperature: parseFloat(document.getElementById('temperature-slider').value),
        audio_format: document.getElementById('format-select').value
    };
}

/**
 * Validate form inputs
 */
function validateInputs(data) {
    if (!data.text) {
        throw new Error('Please enter text to convert');
    }

    if (data.mode === 'preset' && !data.voice) {
        throw new Error('Please select a voice preset');
    }

    if (data.mode === 'clone') {
        const file = document.getElementById('ref-audio-upload').files[0];
        if (!file) {
            throw new Error('Please upload a reference audio file');
        }
        if (!data.ref_audio_id) {
            throw new Error('Reference audio not uploaded properly');
        }
    }
}

/**
 * Perform audio generation
 */
async function performGeneration(formData) {
    // If clone mode, upload reference audio first
    if (formData.mode === 'clone') {
        console.log('Uploading reference audio...');
        const file = document.getElementById('ref-audio-upload').files[0];
        const uploadResult = await uploadReferenceAudio(file);
        formData.ref_audio_id = uploadResult.ref_audio_id;

        // Store file ID for future reference
        document.getElementById('ref-audio-upload').dataset.fileId = uploadResult.ref_audio_id;
        console.log('✅ Reference audio uploaded');
    }

    // Generate audio with progress tracking
    console.log('Generating audio...');
    const result = await generateAudio(formData, (progress) => {
        updateGenerationProgress(progress);
    });
    console.log('✅ Audio generated');

    return result;
}

/**
 * Update generation progress display
 */
function updateGenerationProgress(progress) {
    console.log('Progress:', progress.message);

    // Update loading text to show progress
    const btnText = document.querySelector('#generate-btn .btn-text');
    if (btnText) {
        if (progress.type === 'segment_info') {
            btnText.textContent = `Processing ${progress.segments} segments...`;
        } else if (progress.type === 'complete') {
            btnText.textContent = 'Merging audio...';
        }
    }

    // You could also update a progress bar or other UI elements here
    // For now, we'll just update the button text
}

/**
 * Initialize format buttons
 */
function initializeFormatButtons() {
    const formatSelect = document.getElementById('format-select');
    if (formatSelect) {
        const formatValue = formatSelect.value;
        const formatBtn = document.querySelector(`[data-format="${formatValue}"]`);
        if (formatBtn) {
            formatBtn.classList.add('active');
        }
    }
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initApp,
        setupEventListeners,
        collectFormData,
        validateInputs,
        performGeneration
    };
}