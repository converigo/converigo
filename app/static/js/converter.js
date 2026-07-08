/**
 * converter.js
 * Convertin
 * DEBUG VERSION
 */

class FileConverter {

    constructor() {

        console.log("========== FileConverter ==========");

        this.convertBtn = document.getElementById("convertBtn");
        this.downloadBtn = document.getElementById("downloadBtn");
        this.convertMessage = document.getElementById("convertMessage");
        this.fileInput = document.getElementById("fileInput");
        this.progressBar = document.querySelector(".progress-bar");

        console.log("convertBtn :", this.convertBtn);
        console.log("downloadBtn :", this.downloadBtn);
        console.log("fileInput :", this.fileInput);

        this.currentDownloadPath = null;
        this.isConverting = false;

        this.init();

    }

    init() {

        if (!this.convertBtn) {

            console.error("convertBtn tidak ditemukan");
            return;

        }

        this.convertBtn.addEventListener("click", () => {

            this.handleConvert();

        });

    }

    async handleConvert() {

        if (this.isConverting)
            return;

        const file = this.fileInput.files[0];

        if (!file) {

            this.convertMessage.textContent =
                "Please choose a file.";

            return;

        }

        this.isConverting = true;

        this.convertBtn.disabled = true;

        if (this.progressBar)
            this.progressBar.style.width = "10%";

        const formData = new FormData();

        formData.append("file", file);

        try {

            console.log("Uploading...");

            const response = await fetch("/convert", {

                method: "POST",
                body: formData

            });

            const data = await response.json();

            console.log("Response:");
            console.log(data);

            if (!response.ok) {

                throw new Error(
                    data.detail || "Conversion failed."
                );

            }

            if (this.progressBar)
                this.progressBar.style.width = "100%";

            this.currentDownloadPath =
                data.download_path;

            console.log("DOWNLOAD PATH :", this.currentDownloadPath);

            this.convertMessage.textContent =
                data.message;

            if (this.downloadBtn) {

                this.downloadBtn.hidden = false;

                this.downloadBtn.href =
                    data.download_path;

                this.downloadBtn.download =
                    data.filename;

                this.downloadBtn.textContent =
                    "Download " + data.filename;

                console.log("Download Button:");
                console.log(this.downloadBtn);

                console.log("hidden =", this.downloadBtn.hidden);
                console.log("href =", this.downloadBtn.href);
                console.log("download =", this.downloadBtn.download);

                this.downloadBtn.onclick = (e) => {

                    console.log("DOWNLOAD DIKLIK");

                    console.log("href =", this.downloadBtn.href);

                    if (!this.downloadBtn.href) {

                        e.preventDefault();

                        alert("Download path kosong!");

                        return;

                    }

                    window.location.href =
                        this.downloadBtn.href;

                };

            }

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

    console.log("converter.js loaded");

    window.converter = new FileConverter();

    console.log(window.converter);

});