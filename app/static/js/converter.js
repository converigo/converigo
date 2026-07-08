/**
 * converter.js
 * Convertin
 */

class FileConverter {

    constructor() {

        this.convertBtn = document.getElementById("convertBtn");
        this.downloadBtn = document.getElementById("downloadBtn");
        this.convertMessage = document.getElementById("convertMessage");
        this.fileInput = document.getElementById("fileInput");
        this.progressBar = document.querySelector(".progress-bar");

        this.currentDownloadPath = null;
        this.isConverting = false;

        this.init();

    }

    init() {

        if (!this.convertBtn) {
            console.error("Convert button not found.");
            return;
        }

        this.convertBtn.addEventListener("click", () => {

            this.handleConvert();

        });

    }

    async handleConvert() {

        if (this.isConverting) return;

        const file = this.fileInput.files[0];

        if (!file) {

            this.convertMessage.textContent =
                "Please choose a file.";

            return;

        }

        this.isConverting = true;

        this.convertBtn.disabled = true;

        this.progressBar.style.width = "15%";

        const formData = new FormData();

        formData.append("file", file);

        try {

            const response = await fetch("/convert", {

                method: "POST",

                body: formData

            });

            this.progressBar.style.width = "60%";

            const data = await response.json();

            console.log(data);

            if (!response.ok) {

                throw new Error(
                    data.detail || "Conversion failed."
                );

            }

            this.progressBar.style.width = "100%";

            this.convertMessage.textContent =
                data.message;

            this.currentDownloadPath =
                data.download_path;

            this.downloadBtn.hidden = false;

            this.downloadBtn.href =
                data.download_path;

            this.downloadBtn.download =
                data.filename;

            this.downloadBtn.textContent =
                "Download " + data.filename;

        }

        catch (error) {

            console.error(error);

            this.convertMessage.textContent =
                error.message;

        }

        finally {

            this.convertBtn.disabled = false;

            this.isConverting = false;

        }

    }

}

document.addEventListener("DOMContentLoaded", () => {

    new FileConverter();

});