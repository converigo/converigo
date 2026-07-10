/*
====================================================
Project : Convertin
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

        // ensure button disabled on load
        if (this.convertBtn) {
            this.convertBtn.disabled = true;
        }

        this.init();
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

    async convert() {
        if (!this.file || !this.selectedFormat) {
            console.warn("Missing conversion data");
            return;
        }

        const formData = new FormData();
        formData.append("file", this.file);
        formData.append("target_format", this.selectedFormat);

        const originalLabel = this.convertBtn ? this.convertBtn.textContent : "Convert";
        let wasSuccess = false;

        try {
            if (this.convertBtn) {
                this.convertBtn.disabled = true;
                this.convertBtn.classList.add("loading");
                this.convertBtn.textContent = "Converting...";
            }

            if (this.message) {
                this.message.textContent = "Converting...";
                this.message.classList.remove("success", "error");
            }

            const response = await fetch("/convert", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            console.log("CONVERT RESPONSE:", data);

            if (!response.ok) {
                throw new Error(data.detail || "Conversion failed");
            }

            if (this.message) {
                this.message.textContent = "✓ Conversion completed";
                this.message.classList.add("success");
            }

            if (this.convertBtn) {
                this.convertBtn.textContent = "✓ Conversion completed";
            }

            wasSuccess = true;

            if (window.downloadManager) {
                window.downloadManager.prepare(data);
            }
        } catch (error) {
            console.error(error);
            if (this.message) {
                this.message.textContent = "❌ " + error.message;
                this.message.classList.add("error");
            }
        } finally {
            if (this.convertBtn) {
                this.convertBtn.classList.remove("loading");
                this.convertBtn.disabled = false;
                if (!wasSuccess) {
                    this.convertBtn.textContent = originalLabel;
                }
            }
        }
    }
}

window.converter = new ConverterController();
