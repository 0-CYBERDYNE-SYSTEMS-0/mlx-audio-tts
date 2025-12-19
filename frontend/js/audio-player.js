/**
 * Enhanced Audio Player Controller
 */

class AudioPlayerController {
    constructor() {
        this.audioElement = null;
        this.isPlaying = false;
        this.currentSpeed = 1.0;
        this.volume = 0.7;
        this.downloadUrl = '';
        this.filename = '';

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.audioElement = document.getElementById('audio-player');
        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.downloadDirectBtn = document.getElementById('download-direct-btn');
        this.volumeBtn = document.getElementById('volume-btn');
        this.volumeSlider = document.getElementById('volume-slider');
        this.volumeInput = document.getElementById('volume-input');
        this.speedBtn = document.getElementById('speed-control-btn');
        this.speedMenu = document.getElementById('speed-menu');
        this.progressBar = document.getElementById('progress-bar');
        this.progressFill = document.getElementById('progress-fill');
        this.progressHandle = document.getElementById('progress-handle');
        this.currentTimeDisplay = document.getElementById('current-time');
        this.totalTimeDisplay = document.getElementById('total-time');
        this.waveform = document.getElementById('waveform');
        this.waveformProgress = document.getElementById('waveform-progress');
        this.waveBars = document.querySelectorAll('.wave-bar');

        // Additional action buttons
        this.copyLinkBtn = document.getElementById('copy-link-btn');
        this.shareBtn = document.getElementById('share-btn');
        this.newTabBtn = document.getElementById('new-tab-btn');

        // Download info elements
        this.downloadFormat = document.getElementById('download-format');
        this.downloadSize = document.getElementById('download-size');
        this.detailFormat = document.getElementById('detail-format');
        this.detailDuration = document.getElementById('detail-duration');
    }

    bindEvents() {
        // Play/Pause button
        this.playPauseBtn?.addEventListener('click', () => this.togglePlayPause());

        // Volume controls
        this.volumeBtn?.addEventListener('click', () => this.toggleVolumeSlider());
        this.volumeInput?.addEventListener('input', (e) => this.setVolume(e.target.value / 100));

        // Speed controls
        this.speedBtn?.addEventListener('click', () => this.toggleSpeedMenu());
        this.speedMenu?.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                this.setSpeed(parseFloat(e.target.dataset.speed));
            }
        });

        // Progress bar
        this.progressBar?.addEventListener('click', (e) => this.seekTo(e));

        // Audio element events
        this.audioElement?.addEventListener('timeupdate', () => this.updateProgress());
        this.audioElement?.addEventListener('loadedmetadata', () => this.onMetadataLoaded());
        this.audioElement?.addEventListener('ended', () => this.onAudioEnded());

        // Download buttons
        this.downloadDirectBtn?.addEventListener('click', () => this.downloadAudio());
        this.copyLinkBtn?.addEventListener('click', () => this.copyDownloadLink());
        this.shareBtn?.addEventListener('click', () => this.shareAudio());
        this.newTabBtn?.addEventListener('click', () => this.openInNewTab());

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => this.handleOutsideClick(e));

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    setAudioSource(url, filename = '') {
        if (this.audioElement && url) {
            this.audioElement.src = url;
            this.audioElement.load();
            this.downloadUrl = url;
            this.filename = filename || 'generated_audio.wav';

            // Update download buttons
            if (this.downloadBtn) {
                this.downloadBtn.href = url;
                this.downloadBtn.download = this.filename;
            }

            if (this.downloadDirectBtn) {
                this.downloadDirectBtn.dataset.url = url;
                this.downloadDirectBtn.dataset.filename = this.filename;
            }
        }
    }

    togglePlayPause() {
        if (!this.audioElement) return;

        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        if (this.audioElement) {
            this.audioElement.play();
            this.isPlaying = true;
            this.updatePlayPauseButton();
            this.animateWaveform(true);
        }
    }

    pause() {
        if (this.audioElement) {
            this.audioElement.pause();
            this.isPlaying = false;
            this.updatePlayPauseButton();
            this.animateWaveform(false);
        }
    }

    updatePlayPauseButton() {
        const playIcon = document.getElementById('play-icon');
        const pauseIcon = document.getElementById('pause-icon');

        if (this.playPauseBtn) {
            if (this.isPlaying) {
                this.playPauseBtn.classList.add('playing');
                if (playIcon) playIcon.style.display = 'none';
                if (pauseIcon) pauseIcon.style.display = 'block';
            } else {
                this.playPauseBtn.classList.remove('playing');
                if (playIcon) playIcon.style.display = 'block';
                if (pauseIcon) pauseIcon.style.display = 'none';
            }
        }
    }

    toggleVolumeSlider() {
        if (this.volumeSlider) {
            this.volumeSlider.classList.toggle('hidden');
        }
    }

    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.audioElement) {
            this.audioElement.volume = this.volume;
        }
        if (this.volumeInput) {
            this.volumeInput.value = this.volume * 100;
        }
    }

    toggleSpeedMenu() {
        if (this.speedMenu) {
            this.speedMenu.classList.toggle('hidden');
        }
    }

    setSpeed(speed) {
        this.currentSpeed = speed;
        if (this.audioElement) {
            this.audioElement.playbackRate = speed;
        }

        // Update active button
        const speedButtons = this.speedMenu?.querySelectorAll('button');
        speedButtons?.forEach(btn => {
            btn.classList.remove('active');
            if (parseFloat(btn.dataset.speed) === speed) {
                btn.classList.add('active');
            }
        });
    }

    seekTo(event) {
        if (!this.audioElement || !this.progressBar) return;

        const rect = this.progressBar.getBoundingClientRect();
        const percent = (event.clientX - rect.left) / rect.width;
        const time = percent * this.audioElement.duration;

        this.audioElement.currentTime = time;
        this.updateProgress();
    }

    updateProgress() {
        if (!this.audioElement) return;

        const currentTime = this.audioElement.currentTime;
        const duration = this.audioElement.duration;

        if (!isNaN(duration)) {
            const percent = (currentTime / duration) * 100;

            if (this.progressFill) {
                this.progressFill.style.width = `${percent}%`;
            }

            if (this.progressHandle) {
                this.progressHandle.style.left = `${percent}%`;
            }

            if (this.waveformProgress) {
                this.waveformProgress.style.width = `${percent}%`;
            }

            this.updateWaveformBars(percent);
        }

        if (this.currentTimeDisplay) {
            this.currentTimeDisplay.textContent = this.formatTime(currentTime);
        }
    }

    updateWaveformBars(percent) {
        if (!this.waveBars.length) return;

        const totalBars = this.waveBars.length;
        const playedBars = Math.floor((percent / 100) * totalBars);

        this.waveBars.forEach((bar, index) => {
            if (index < playedBars) {
                bar.classList.add('played');
                bar.classList.remove('unplayed');
            } else {
                bar.classList.add('unplayed');
                bar.classList.remove('played');
            }
        });
    }

    onMetadataLoaded() {
        if (!this.audioElement) return;

        const duration = this.audioElement.duration;
        if (this.totalTimeDisplay) {
            this.totalTimeDisplay.textContent = this.formatTime(duration);
        }
    }

    onAudioEnded() {
        this.isPlaying = false;
        this.updatePlayPauseButton();
        this.animateWaveform(false);
    }

    animateWaveform(animate) {
        if (!this.waveBars.length) return;

        this.waveBars.forEach(bar => {
            if (animate) {
                bar.style.animationPlayState = 'running';
            } else {
                bar.style.animationPlayState = 'paused';
            }
        });
    }

    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';

        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    downloadAudio() {
        if (this.downloadUrl) {
            const link = document.createElement('a');
            link.href = this.downloadUrl;
            link.download = this.filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    copyDownloadLink() {
        if (this.downloadUrl) {
            navigator.clipboard.writeText(window.location.origin + this.downloadUrl).then(() => {
                this.showNotification('Download link copied to clipboard!', 'success');
            }).catch(() => {
                this.showNotification('Failed to copy link', 'error');
            });
        }
    }

    shareAudio() {
        if (navigator.share && this.downloadUrl) {
            navigator.share({
                title: 'Generated Audio',
                text: 'Check out this generated audio!',
                url: window.location.origin + this.downloadUrl
            }).catch(() => {
                this.copyDownloadLink();
            });
        } else {
            this.copyDownloadLink();
        }
    }

    openInNewTab() {
        if (this.downloadUrl) {
            window.open(this.downloadUrl, '_blank');
        }
    }

    updateDownloadInfo(format, duration, size) {
        if (this.downloadFormat) {
            this.downloadFormat.textContent = format.toUpperCase();
        }
        if (this.detailFormat) {
            this.detailFormat.textContent = format.toUpperCase();
        }
        if (this.detailDuration) {
            this.detailDuration.textContent = this.formatTime(duration);
        }
        if (this.downloadSize) {
            this.downloadSize.textContent = size;
        }
    }

    handleOutsideClick(event) {
        if (!event.target.closest('#volume-btn') && !event.target.closest('#volume-slider')) {
            this.volumeSlider?.classList.add('hidden');
        }

        if (!event.target.closest('#speed-control-btn') && !event.target.closest('#speed-menu')) {
            this.speedMenu?.classList.add('hidden');
        }
    }

    handleKeyboardShortcuts(event) {
        if (event.target.tagName === 'TEXTAREA' || event.target.tagName === 'INPUT') {
            return; // Don't interfere with text input
        }

        switch (event.code) {
            case 'Space':
                if (this.audioElement) {
                    event.preventDefault();
                    this.togglePlayPause();
                }
                break;
            case 'ArrowLeft':
                if (this.audioElement) {
                    event.preventDefault();
                    this.audioElement.currentTime = Math.max(0, this.audioElement.currentTime - 5);
                }
                break;
            case 'ArrowRight':
                if (this.audioElement) {
                    event.preventDefault();
                    this.audioElement.currentTime = Math.min(
                        this.audioElement.duration,
                        this.audioElement.currentTime + 5
                    );
                }
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.setVolume(Math.min(1, this.volume + 0.1));
                break;
            case 'ArrowDown':
                event.preventDefault();
                this.setVolume(Math.max(0, this.volume - 0.1));
                break;
        }
    }

    showNotification(message, type = 'info') {
        // Create a simple notification (you could enhance this with a proper toast system)
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
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize the audio player when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.audioPlayer = new AudioPlayerController();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioPlayerController;
}