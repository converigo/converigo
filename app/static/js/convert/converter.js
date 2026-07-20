/*
====================================================
Project : Converigo
Author  : Pico Lala & ChatGPT

Converter Controller

Version : 3.9.0

Connect:
Upload Manager
Recommendation Manager
Backend Convert API

====================================================
*/

console.log("CONVERTER JS 3.9.0 LOADED");

class ConverterController {
    constructor() {
        this.file = null;
        this.files = [];
        this.selectedFormat = null;

        this.convertBtn = document.getElementById("convertButton");
        this.message = document.getElementById("convertMessage");
        this.convertProgress = document.getElementById("convertProgress");
        this.progressBar = this.convertProgress?.querySelector(".progress-bar");
        this.progressTimer = null;

        // ensure button disabled on load
        if (this.convertBtn) {
            this.convertBtn.disabled = true;
        }

        if (this.convertProgress) {
            this.convertProgress.hidden = true;
            this.convertProgress.setAttribute("aria-hidden", "true");
        }

        this.init();
    }

    setProgress(value) {
        if (!this.progressBar) {
            return;
        }
        const width = `${Math.min(100, Math.max(0, value))}%`;
        this.progressBar.style.width = width;
        this.progressBar.setAttribute('aria-valuenow', String(Math.min(100, Math.max(0, value))));
    }

    startProgress() {
        if (this.convertProgress) {
            this.convertProgress.hidden = false;
            this.convertProgress.setAttribute("aria-hidden", "false");
        }
        this.setProgress(10);
        clearInterval(this.progressTimer);
        this.progressTimer = setInterval(() => {
            const current = parseInt(this.progressBar?.style.width || '0', 10) || 0;
            const next = current + (current < 70 ? 8 : 2);
            this.setProgress(next);
            if (current >= 90) {
                clearInterval(this.progressTimer);
            }
        }, 300);
    }

    stopProgress(complete = false) {
        clearInterval(this.progressTimer);
        this.progressTimer = null;
        if (complete) {
            this.setProgress(100);
        }
        if (this.convertProgress) {
            this.convertProgress.hidden = true;
            this.convertProgress.setAttribute("aria-hidden", "true");
        }
    }

    init() {
        console.log("Converter controller ready");

        if (this.convertBtn) {
            this.convertBtn.addEventListener("click", () => {
                this.convert();
            });
        }

        /* FILE EVENT */
        window.addEventListener("file-selected", (event) => {
            this.files = event.detail.files || [];
            this.file = event.detail.file || event.detail.files?.[0] || null;
            console.log("Converter files:", this.files.length, "files selected");
            this.checkReady();
        });

        /* FORMAT EVENT */
        window.addEventListener("format-selected", (event) => {
            this.selectedFormat = event.detail.target;
            console.log("Converter format:", this.selectedFormat);
            this.checkReady();
        });
    }

    checkReady() {
        const ready = Boolean(this.file && this.selectedFormat && this.convertBtn);
        if (window.conversionStateController && typeof window.conversionStateController.setConvertReady === 'function') {
            // Primary API: inform central controller
            window.conversionStateController.setConvertReady(ready);
            // Defensive: ensure DOM is visible for this button instance
            if (this.convertBtn) {
                this.convertBtn.disabled = !ready;
                if (ready) {
                    try { this.convertBtn.hidden = false; } catch (e) {}
                    try { this.convertBtn.style.removeProperty('display'); } catch (e) {}
                    // Defensive: also attempt to remove hidden after brief delay
                    try { setTimeout(() => { this.convertBtn.hidden = false; this.convertBtn.style.removeProperty('display'); }, 80); } catch (e) {}
                } else {
                    try { this.convertBtn.hidden = true; } catch (e) {}
                    try { this.convertBtn.style.display = 'none'; } catch (e) {}
                }
            }
        } else if (this.convertBtn) {
            this.convertBtn.disabled = !ready;
            if (ready) {
                this.convertBtn.hidden = false;
                this.convertBtn.style.removeProperty('display');
            } else {
                this.convertBtn.hidden = true;
                this.convertBtn.style.display = 'none';
            }
        }
        console.log("Convert READY:", ready);
    }

    reset() {
        this.file = null;
        this.files = [];
        this.selectedFormat = null;
        if (this.convertBtn) {
            this.convertBtn.disabled = true;
            this.convertBtn.classList.remove("loading");
            this.convertBtn.textContent = window.translate('upload.convert', 'Convert');
        }
        if (this.message) {
            this.message.textContent = "";
            this.message.classList.remove("success", "error");
        }
        if (window.downloadManager && typeof window.downloadManager.clear === "function") {
            window.downloadManager.clear();
        }
        if (window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
            window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.IDLE);
        }
    }

    async convert() {
        if (!this.files || this.files.length === 0 || !this.selectedFormat) {
            console.warn("Missing conversion data");
            return;
        }

        const formData = new FormData();
        
        // Append all files
        for (const file of this.files) {
            formData.append("file", file);
        }
        formData.append("target_format", this.selectedFormat);

        const originalLabel = this.convertBtn ? this.convertBtn.textContent : window.translate('upload.convert', 'Convert');
        let wasSuccess = false;

        try {
            if (window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
                window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.CONVERTING);
            }
            if (this.convertBtn) {
                this.convertBtn.disabled = true;
                this.convertBtn.classList.add("loading");
                this.convertBtn.textContent = window.translate('upload.converting', 'Converting...');
            }

            if (this.message) {
                this.message.textContent = window.translate('upload.converting', 'Converting...');
                this.message.classList.remove("success", "error");
            }

            this.startProgress();

            const response = await fetch("/convert", {
                method: "POST",
                body: formData,
            });

            const data = await response.json().catch(() => null);
            console.log("CONVERT RESPONSE:", data);

            if (!response.ok) {
                // Robust extraction of readable error messages
                let errorMsg = window.translate('upload.conversion_failed', 'Conversion failed. Please try again.');
                try {
                    if (data) {
                        // Common FastAPI error shape: {'detail': '...'} or {'detail': [...]}
                        if (typeof data === 'string') {
                            errorMsg = data;
                        } else if (Array.isArray(data.detail)) {
                            // detail as list of errors
                            errorMsg = data.detail
                                .map(d => (typeof d === 'string' ? d : d.msg || JSON.stringify(d)))
                                .join('; ');
                        } else if (data.detail && typeof data.detail === 'string') {
                            errorMsg = data.detail;
                        } else if (data.message && typeof data.message === 'string') {
                            errorMsg = data.message;
                        } else if (data.error && typeof data.error === 'string') {
                            errorMsg = data.error;
                        } else if (typeof data === 'object') {
                            // Fallback: pick any top-level string value
                            const candidate = Object.values(data).find(v => typeof v === 'string');
                            if (candidate) errorMsg = candidate;
                            else errorMsg = JSON.stringify(data);
                        }
                    }
                } catch (e) {
                    console.warn('Error parsing error response', e);
                }

                throw new Error(errorMsg || window.translate('upload.conversion_failed', 'Conversion failed.'));
            }

            // Handle batch results
            const successCount = data.successful || 0;
            const totalCount = data.total || this.files.length;
            
            if (this.message) {
                if (successCount === totalCount) {
                    this.message.textContent = window.translate('upload.conversion_completed', '✓ Conversion completed') + ` (${successCount}/${totalCount})`;
                } else if (successCount === 0) {
                    this.message.textContent = window.translate('upload.conversion_all_failed', '❌ All conversions failed');
                } else {
                    const partialMessage = window.translate('upload.conversion_partial_success', '⚠️ {success}/{total} files converted');
                    this.message.textContent = partialMessage
                        .replace('{success}', successCount)
                        .replace('{total}', totalCount);
                }
                this.message.classList.add("success");
            }

            if (this.convertBtn) {
                this.convertBtn.textContent = window.translate('upload.conversion_completed', '✓ Conversion completed');
            }

            wasSuccess = true;

            if (window.downloadManager) {
                window.downloadManager.prepare(data);
            }
            if (window.uploadManager && typeof window.uploadManager.showResult === 'function') {
                // Show result for all converted files
                for (const file of this.files) {
                    window.uploadManager.showResult(file);
                }
            }
        } catch (error) {
            console.error(error);
            let errorMessage = window.translate('upload.conversion_failed_try_another', 'Conversion failed. Please try again.');

            // Prefer explicit string messages, fallbacks handled below
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error && error.message && typeof error.message === 'string' && error.message !== '[object Object]') {
                errorMessage = error.message;
            } else if (error && typeof error === 'object') {
                try {
                    // Try to extract useful fields
                    if (error.detail && typeof error.detail === 'string') errorMessage = error.detail;
                    else if (Array.isArray(error.detail)) errorMessage = error.detail.map(d => (typeof d === 'string' ? d : d.msg || JSON.stringify(d))).join('; ');
                    else if (error.message && typeof error.message === 'string') errorMessage = error.message;
                    else if (error.error && typeof error.error === 'string') errorMessage = error.error;
                    else errorMessage = JSON.stringify(error);
                } catch (e) {
                    errorMessage = window.translate('upload.conversion_failed_try_another', 'Conversion failed. Please try again.');
                }
            }

            if (this.message) {
                this.message.textContent = errorMessage;
                this.message.classList.add("error");
            }
            if (window.uploadManager && typeof window.uploadManager.showError === 'function') {
                window.uploadManager.showError(errorMessage);
            }
        } finally {
            if (!wasSuccess && window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
                window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.ERROR);
            }
            this.stopProgress(wasSuccess);
            if (this.convertBtn) {
                this.convertBtn.classList.remove("loading");
                this.convertBtn.disabled = false;
                if (!wasSuccess) {
                    this.convertBtn.textContent = originalLabel;
                } else {
                    this.convertBtn.textContent = window.translate('upload.ready_to_download', 'Ready to download');
                }
            }
            if (wasSuccess && window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
                window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.SUCCESS);
            }
        }
    }
}

window.converter = new ConverterController();
