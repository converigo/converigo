/**
 * Converter Module
 * Handles file upload, conversion, and download
 */

class FileConverter {
    constructor() {
        this.convertBtn = document.getElementById('convertBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.convertMessage = document.getElementById('convertMessage');
        this.fileInput = document.getElementById('fileInput');
        this.progressBar = document.querySelector('.progress-bar');
        this.isConverting = false;
        this.currentDownloadPath = null;

        this.init();
    }

    init() {
        if (this.convertBtn) {
            this.convertBtn.addEventListener('click', () => this.handleConvert());
        }

        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', (e) => this.handleDownload(e));
        }
    }

    /**
     * Handle the convert button click
     */
    async handleConvert() {
        const file = this.fileInput?.files?.[0];

        if (!file) {
            this.showMessage('Please select a file first.', 'error');
            return;
        }

        // Check file type - only MP4 for now (based on backend)
        if (!file.name.toLowerCase().endsWith('.mp4')) {
            this.showMessage('Only MP4 files are supported for conversion.', 'error');
            return;
        }

        // Check file size (optional - adjust as needed)
        const maxSizeMB = 500;
        if (file.size > maxSizeMB * 1024 * 1024) {
            this.showMessage(`File size exceeds ${maxSizeMB}MB limit.`, 'error');
            return;
        }

        await this.convertFile(file);
    }

    /**
     * Convert file by uploading to backend
     */
    async convertFile(file) {
        if (this.isConverting) {
            this.showMessage('Conversion already in progress.', 'error');
            return;
        }

        this.isConverting = true;
        this.convertBtn.disabled = true;
        this.resetDownloadButton();
        this.setProgress(0);
        this.showMessage('Starting conversion...', 'info');

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Simulate progress for upload phase (0-40%)
            const uploadPromise = this.simulateProgress(0, 40, 2000);

            const response = await fetch('/convert', {
                method: 'POST',
                body: formData,
            });

            await uploadPromise; // Ensure progress reaches 40%

            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData?.detail || 'Conversion failed.';
                throw new Error(errorMessage);
            }

            const data = await response.json();

            if (data.status === 'success') {
                // Simulate conversion phase (40-100%)
                await this.simulateProgress(40, 100, 2000);

                this.currentDownloadPath = data.download_path;
                this.showMessage(
                    `Conversion completed! File: ${data.filename}`,
                    'success'
                );
                this.showDownloadButton(data.filename);
                this.verifyFileExists(data.download_path);
            } else {
                throw new Error(data.message || 'Conversion failed.');
            }
        } catch (error) {
            console.error('Conversion error:', error);
            this.showMessage(
                `Conversion failed: ${error.message}`,
                'error'
            );
            this.setProgress(0);
        } finally {
            this.isConverting = false;
            this.convertBtn.disabled = false;
        }
    }

    /**
     * Simulate progress bar movement
     */
    simulateProgress(startPercent, endPercent, duration) {
        return new Promise((resolve) => {
            const startTime = Date.now();
            const interval = setInterval(() => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(
                    endPercent,
                    startPercent + ((elapsed / duration) * (endPercent - startPercent))
                );

                this.setProgress(progress);

                if (elapsed >= duration) {
                    clearInterval(interval);
                    this.setProgress(endPercent);
                    resolve();
                }
            }, 100);
        });
    }

    /**
     * Set progress bar width
     */
    setProgress(percentage) {
        if (this.progressBar) {
            this.progressBar.style.width = Math.min(100, percentage) + '%';
        }
    }

    /**
     * Show message to user
     */
    showMessage(message, type = 'info') {
        if (!this.convertMessage) return;

        this.convertMessage.textContent = message;
        this.convertMessage.className = `muted ${type}`;

        // Auto-clear success/info messages after 5 seconds
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                if (this.convertMessage.textContent === message) {
                    this.convertMessage.textContent = '';
                    this.convertMessage.className = 'muted';
                }
            }, 5000);
        }
    }

    /**
     * Show download button
     */
    showDownloadButton(filename) {
        if (!this.downloadBtn) return;

        this.downloadBtn.textContent = `Download ${filename}`;
        this.downloadBtn.removeAttribute('hidden');
        this.downloadBtn.href = this.currentDownloadPath;
    }

    /**
     * Reset download button to hidden state
     */
    resetDownloadButton() {
        if (!this.downloadBtn) return;

        this.downloadBtn.setAttribute('hidden', '');
        this.downloadBtn.href = '#';
        this.currentDownloadPath = null;
    }

    /**
     * Handle download button click
     */
    handleDownload(e) {
        if (!this.currentDownloadPath) {
            e.preventDefault();
            this.showMessage('Download path not available.', 'error');
            return;
        }

        // The browser will handle the actual download
        // since we have href and download attributes set
    }

    /**
     * Verify that the converted file exists on the server
     */
    async verifyFileExists(downloadPath) {
        try {
            const response = await fetch(downloadPath, {
                method: 'HEAD',
            });

            if (!response.ok) {
                console.warn('File verification failed:', response.status);
                this.showMessage(
                    'Warning: File verification failed. Download may not work.',
                    'error'
                );
            }
        } catch (error) {
            console.warn('File verification error:', error);
        }
    }
}

// Initialize converter when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    new FileConverter();
});
