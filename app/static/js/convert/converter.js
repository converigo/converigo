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
            this.file = event.detail.file;
            console.log("Converter file:", this.file && this.file.name);
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
        if (this.convertBtn) {
            this.convertBtn.disabled = !ready;
        }
        console.log("Convert READY:", ready);
    }

    reset() {
        this.file = null;
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
    }

    async convert() {
        if (!this.file || !this.selectedFormat) {
            console.warn("Missing conversion data");
            return;
        }

        const formData = new FormData();
        formData.append("file", this.file);
        formData.append("target_format", this.selectedFormat);

        const originalLabel = this.convertBtn ? this.convertBtn.textContent : window.translate('upload.convert', 'Convert');
        let wasSuccess = false;

        try {
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

            const data = await response.json();
            console.log("CONVERT RESPONSE:", data);

            if (!response.ok) {
                throw new Error(data.detail || window.translate('upload.conversion_failed', 'Conversion failed'));
            }

            if (this.message) {
                this.message.textContent = window.translate('upload.conversion_completed', '✓ Conversion completed');
                this.message.classList.add("success");
            }

            if (this.convertBtn) {
                this.convertBtn.textContent = window.translate('upload.conversion_completed', '✓ Conversion completed');
            }

            wasSuccess = true;

            if (window.downloadManager) {
                window.downloadManager.prepare(data);
            }
        } catch (error) {
            console.error(error);
            if (this.message) {
                this.message.textContent = window.translate('upload.conversion_failed_try_another', '❌ Conversion failed. Please try another format.');
                this.message.classList.add("error");
            }
        } finally {
            this.stopProgress(wasSuccess);
            if (this.convertBtn) {
                this.convertBtn.classList.remove("loading");
                this.convertBtn.disabled = false;
                if (!wasSuccess) {
                    this.convertBtn.textContent = originalLabel;
                } else {
                    if (this.convertBtn) {
                        this.convertBtn.textContent = window.translate('upload.ready_to_download', 'Ready to download');
                    }
                }
            }
        }
    }
}

window.converter = new ConverterController();
