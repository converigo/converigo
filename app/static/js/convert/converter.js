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
            // Emit progress events for DevTools verification
            try { window.dispatchEvent(new CustomEvent('upload-progress', { detail: { progress: Math.min(100, next) } })); } catch (e) {}
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
        // Dispatch upload-finished for observability with success flag
        try { window.dispatchEvent(new CustomEvent('upload-finished', { detail: { success: !!complete } })); } catch (e) {}
    }

    init() {
        console.log("Converter controller ready");

        this._findUploadCard = function() {
            return document.querySelector('.upload-card') || document.querySelector('#converter') || document.querySelector('.homepage-upload-card') || document.querySelector('.upload-wrapper');
        };

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

    _trackConversionCompleted(){
        if(!window.converigoAnalytics || typeof window.converigoAnalytics.trackEvent !== 'function'){
            return;
        }
        const context = window.converigoAnalytics.getConverterContext();
        window.converigoAnalytics.trackEvent('conversion_success', {
            converter_name: context.converter_name,
            output_format: this.selectedFormat || '',
            event_status: 'success'
        });
    }

    _trackConversionStarted(){
        if(!window.converigoAnalytics || typeof window.converigoAnalytics.trackEvent !== 'function'){
            return;
        }
        const context = window.converigoAnalytics.getConverterContext();
        window.converigoAnalytics.trackEvent('conversion_start', {
            converter_name: context.converter_name,
            output_format: this.selectedFormat || '',
            event_status: 'started'
        });
    }

    _trackConversionFailed(errorMessage){
        if(!window.converigoAnalytics || typeof window.converigoAnalytics.trackEvent !== 'function'){
            return;
        }
        const context = window.converigoAnalytics.getConverterContext();
        window.converigoAnalytics.trackEvent('conversion_failed', {
            converter_name: context.converter_name,
            output_format: this.selectedFormat || '',
            error_type: errorMessage || 'conversion_error',
            event_status: 'failure'
        });
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

        // Include the URL slug as `operation` when on a /tools/* page so the
        // server can disambiguate converters that share the same format pair
        // (e.g. pdf-compress vs pdf-split for pdf -> pdf).
        const pathParts = (window.location.pathname || "").split("/").filter(Boolean);
        if (pathParts.length >= 2 && pathParts[0] === "tools") {
            const opSlug = pathParts[1].toLowerCase();
            if (opSlug) {
                formData.append("operation", opSlug);
            }
        }

        const originalLabel = this.convertBtn ? this.convertBtn.textContent : window.translate('upload.convert', 'Convert');
        let wasSuccess = false;

        try {
            if (window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
                window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.CONVERTING);
            }

            // UI: indicate uploading/processing state on the upload card
            try {
                const uploadCard = (this._findUploadCard && typeof this._findUploadCard === 'function') ? this._findUploadCard() : (document.querySelector('.upload-card') || document.querySelector('#converter') || document.querySelector('.homepage-upload-card') || document.querySelector('.upload-wrapper'));
                if (uploadCard) {
                    uploadCard.classList.remove('state-success');
                    uploadCard.classList.add('state-uploading');
                }
                // Broadcast an explicit upload-started event for runtime observability
                try { window.dispatchEvent(new CustomEvent('upload-started', { detail: { files: this.files } })); } catch (e) {}
                // fade the primary heading to indicate work in progress
                const heading = document.querySelector('.drop-zone .drop-zone-copy h2');
                if (heading) {
                    heading.style.transition = 'opacity 220ms ease';
                    heading.style.opacity = '0.4';
                }
            } catch (e) { /* non-fatal UI enhancement */ }
            this._trackConversionStarted();
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
                        } else if (data.detail && typeof data.detail === 'object' && typeof data.detail.message === 'string') {
                            // Structured error detail, e.g. {code: 'UNSUPPORTED_CONVERSION', message: '...'}
                            errorMsg = data.detail.message;
                            if (data.detail.code === 'UNSUPPORTED_CONVERSION') {
                                errorMsg = window.translate('upload.not_available', errorMsg);
                            }
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
            if (successCount > 0) {
                this._trackConversionCompleted();
            }

            if (window.downloadManager) {
                window.downloadManager.prepare(data);
            }

            // UX-S2-005: Dispatch conversion-completed event for recommendations
            window.dispatchEvent(
                new CustomEvent('conversion-completed', {
                    detail: {
                        outputFormat: this.selectedFormat || '',
                        success: true
                    }
                })
            );
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
            this._trackConversionFailed(errorMessage);
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
            // UI: mark success state and show "Ready to Convert" in heading without layout shift
            try {
                const uploadCard = (this._findUploadCard && typeof this._findUploadCard === 'function') ? this._findUploadCard() : (document.querySelector('.upload-card') || document.querySelector('#converter') || document.querySelector('.homepage-upload-card') || document.querySelector('.upload-wrapper'));
                if (uploadCard) {
                    uploadCard.classList.remove('state-uploading');
                    uploadCard.classList.add('state-success');
                }
                const heading = document.querySelector('.drop-zone .drop-zone-copy h2');
                if (heading) {
                    // smooth text swap: fade out, change, fade in
                    heading.style.transition = 'opacity 260ms ease';
                    heading.style.opacity = '0';
                    setTimeout(() => {
                        try {
                            heading.textContent = window.translate('upload.ready_to_convert', 'Ready to Convert');
                            heading.style.opacity = '1';
                        } catch (e) {}
                    }, 260);
                }
                // conversion-ready event for final UI-ready state
                try { window.dispatchEvent(new CustomEvent('conversion-ready', { detail: { outputFormat: this.selectedFormat || '', success: wasSuccess } })); } catch (e) {}
            } catch (e) { /* non-fatal UI enhancement */ }
        }
    }
}

window.converter = new ConverterController();
