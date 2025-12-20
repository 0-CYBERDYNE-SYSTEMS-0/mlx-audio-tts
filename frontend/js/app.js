/**
 * Main application logic for KREO TTS Generator
 */

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎤 KREO TTS Generator Initializing...');

    // Initialize application
    await initApp();

    // Setup event listeners
    setupEventListeners();

    // Initialize waveform bars
    initializeWaveform();

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
    const voiceOptions = document.querySelectorAll('.voice-option');
    voiceOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Remove active class from all options
            voiceOptions.forEach(opt => opt.classList.remove('active'));
            // Add active class to clicked option
            option.classList.add('active');

            toggleVoiceModeUI();

            if (option.dataset.mode === 'preset') {
                const audioUpload = document.getElementById('audio-upload');
                if (audioUpload) {
                    audioUpload.dataset.fileId = '';
                    audioUpload.value = '';
                }
            }
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

    // Source tabs for voice cloning
    const sourceTabs = document.querySelectorAll('.source-tab');
    sourceTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const source = tab.dataset.source;

            // Update active tab
            sourceTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide interfaces
            const recordingInterface = document.getElementById('recording-interface');
            const uploadInterface = document.getElementById('upload-interface');

            if (source === 'record') {
                recordingInterface?.classList.remove('hidden');
                uploadInterface?.classList.add('hidden');
            } else {
                recordingInterface?.classList.add('hidden');
                uploadInterface?.classList.remove('hidden');
            }
        });
    });

    // Form submission
    const form = document.getElementById('tts-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // File upload
    const audioUpload = document.getElementById('audio-upload');
    if (audioUpload) {
        audioUpload.addEventListener('change', handleFileUpload);
    }

    // File remove button
    const fileRemove = document.getElementById('file-remove');
    if (fileRemove) {
        fileRemove.addEventListener('click', removeUploadedFile);
    }

    // Drag and drop
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        setupDragAndDrop(uploadArea);
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

    const fileInput = document.getElementById('audio-upload');
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
    const uploadArea = document.getElementById('upload-area');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');

    if (uploadArea && fileInfo && fileName && fileSize) {
        uploadArea.classList.add('hidden');
        fileInfo.classList.remove('hidden');

        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
    }
}

/**
 * Remove uploaded file
 */
function removeUploadedFile() {
    const uploadArea = document.getElementById('upload-area');
    const fileInfo = document.getElementById('file-info');
    const fileInput = document.getElementById('audio-upload');

    if (uploadArea && fileInfo && fileInput) {
        uploadArea.classList.remove('hidden');
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
    // Get the active voice option
    const activeVoiceOption = document.querySelector('.voice-option.active');
    const audioUpload = document.getElementById('audio-upload');
    const audioId = audioUpload?.dataset.fileId || null;
    const voiceMode = activeVoiceOption ? activeVoiceOption.dataset.mode : 'preset';

    return {
        text: document.getElementById('text-input').value.trim(),
        mode: voiceMode,
        voice: voiceMode === 'preset' ? document.getElementById('voice-select').value : null,
        ref_audio_id: voiceMode === 'clone' ? audioId : null,
        ref_text: document.getElementById('ref-text').value.trim() || null,
        speed: parseFloat(document.getElementById('speed-slider').value),
        temperature: parseFloat(document.getElementById('temperature-slider').value),
        audio_format: document.getElementById('format-select').value
    };
}

/**
 * Validate form inputs
 */
function validateInputs(data) {
    console.debug('Validate inputs', {
        mode: data.mode,
        ref_audio_id: data.ref_audio_id,
        fileInputExists: Boolean(document.getElementById('audio-upload')),
        fileSelected: Boolean(document.getElementById('audio-upload')?.files?.length)
    });

    if (!data.text) {
        throw new Error('Please enter text to convert');
    }

    if (data.mode === 'preset' && !data.voice) {
        throw new Error('Please select a voice preset');
    }

    if (data.mode === 'clone') {
        const file = document.getElementById('audio-upload').files[0];
        if (!file && !data.ref_audio_id) {
            console.debug('Clone validation failed: missing file and ref_audio_id');
            throw new Error('Please upload a reference audio file');
        }
        if (file && !data.ref_audio_id) {
            console.debug('Clone validation failed: file present but ref_audio_id missing');
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
        const fileInput = document.getElementById('audio-upload');
        const file = fileInput.files[0];

        if (!formData.ref_audio_id && file) {
            console.log('Uploading reference audio...');
            const uploadResult = await uploadReferenceAudio(file);
            formData.ref_audio_id = uploadResult.ref_audio_id;

            // Store file ID for future reference
            fileInput.dataset.fileId = uploadResult.ref_audio_id;
            console.log('✅ Reference audio uploaded');
        } else if (formData.ref_audio_id) {
            console.log('✅ Using existing reference audio');
        }
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
            btnText.textContent = 'Finalizing...';
        }
    }
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

/**
 * Initialize waveform bars
 */
function initializeWaveform() {
    const waveBars = document.getElementById('wave-bars');
    if (!waveBars) return;

    // Create 50 wave bars with random heights
    for (let i = 0; i < 50; i++) {
        const bar = document.createElement('div');
        bar.className = 'wave-bar';
        bar.style.height = `${Math.random() * 80 + 20}%`;
        bar.style.animationDelay = `${i * 0.02}s`;
        waveBars.appendChild(bar);
    }
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initApp,
        setupEventListeners,
        collectFormData,
        validateInputs,
        performGeneration,
        initializeWaveform
    };
}