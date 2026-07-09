/**
 * Convertin
 * converter.js
 * Version 3.1
 */

class FileConverter {

    constructor() {

        this.fileInput = document.getElementById("fileInput");
        this.chooseFileBtn = document.getElementById("chooseFile");

        this.convertBtn = document.getElementById("convertBtn");
        this.downloadBtn = document.getElementById("downloadBtn");

        this.convertMessage = document.getElementById("convertMessage");

        this.fileName = document.getElementById("fileName");
        this.fileSize = document.getElementById("fileSize");

        this.progressBar =
            document.querySelector(".progress-bar");

        this.formatButtons =
            document.querySelectorAll(".format-btn");

        this.selectedFormat = null;

        this.currentDownloadPath = null;

        this.bindEvents();

    }

    bindEvents() {

        if (this.chooseFileBtn) {

            this.chooseFileBtn.addEventListener(
                "click",
                () => {

                    this.fileInput.click();

                }
            );

        }

        if (this.fileInput) {

            this.fileInput.addEventListener(
                "change",
                () => {

                    this.handleFileSelected();

                }
            );

        }

        this.formatButtons.forEach((button) => {

            button.addEventListener(
                "click",
                () => {

                    this.formatButtons.forEach((btn) => {

                        btn.classList.remove("active");

                    });

                    button.classList.add("active");

                    this.selectedFormat =
                        button.dataset.format;

                }
            );

        });

        if (this.convertBtn) {

            this.convertBtn.addEventListener(
                "click",
                () => {

                    this.handleConvert();

                }
            );

        }

    }

    handleFileSelected() {

        const file =
            this.fileInput.files[0];

        if (!file)
            return;

        this.fileName.textContent =
            file.name;

        this.fileSize.textContent =
            (file.size / 1024 / 1024).toFixed(2)
            + " MB";

        this.selectedFormat = null;

        this.formatButtons.forEach((btn) => {

            btn.classList.remove("active");

        });

        this.convertBtn.hidden = false;

        this.convertBtn.disabled = false;

        this.downloadBtn.hidden = true;

        this.downloadBtn.removeAttribute("href");

        this.downloadBtn.removeAttribute("download");

        this.convertMessage.textContent = "";

        if (this.progressBar) {

            this.progressBar.style.width = "0%";

        }

    }

    async handleConvert() {

        const file =
            this.fileInput.files[0];

        if (!file) {

            this.convertMessage.textContent =
                "Please choose a file.";

            return;

        }

        if (!this.selectedFormat) {

            this.convertMessage.textContent =
                "Please choose target format.";

            return;

        }

        this.convertBtn.disabled = true;

        if (this.progressBar) {

            this.progressBar.style.width = "20%";

        }

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        formData.append(
            "target_format",
            this.selectedFormat
        );

        try {

            const response =
                await fetch(
                    "/convert",
                    {
                        method: "POST",
                        body: formData
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(

                    data.detail ||
                    "Conversion failed."

                );

            }

            if (this.progressBar) {

                this.progressBar.style.width = "100%";

            }

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

            if (this.progressBar) {

                this.progressBar.style.width = "0%";

            }

        }

        finally {

            this.convertBtn.disabled = false;

        }

    }

}

document.addEventListener(

    "DOMContentLoaded",

    () => {

        window.converter =
            new FileConverter();

    }

);  