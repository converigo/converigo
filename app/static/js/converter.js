/**
 * DEBUG VERSION
 * converter.js
 */

class FileConverter {

    constructor() {

        console.log("========== CONVERTER ==========");
        console.log("Constructor berjalan");

        this.convertBtn = document.getElementById("convertBtn");
        this.downloadBtn = document.getElementById("downloadBtn");
        this.convertMessage = document.getElementById("convertMessage");
        this.fileInput = document.getElementById("fileInput");
        this.progressBar = document.querySelector(".progress-bar");

        console.log("convertBtn :", this.convertBtn);
        console.log("downloadBtn :", this.downloadBtn);
        console.log("fileInput :", this.fileInput);
        console.log("message :", this.convertMessage);
        console.log("progress :", this.progressBar);

        this.isConverting = false;
        this.currentDownloadPath = null;

        this.init();

    }

    init() {

        console.log("init() dipanggil");

        if (!this.convertBtn) {

            console.error("convertBtn TIDAK DITEMUKAN");

            return;

        }

        console.log("Event click dipasang");

        this.convertBtn.addEventListener("click", () => {

            console.log("=================================");
            console.log("TOMBOL CONVERT DIKLIK");

            this.handleConvert();

        });

    }

    async handleConvert() {

        console.log("handleConvert()");

        alert("handleConvert dipanggil");

        const file = this.fileInput.files[0];

        console.log(file);

        if (!file) {

            alert("Tidak ada file");

            console.error("Tidak ada file");

            return;

        }

        alert("File ditemukan");

        if (!file.name.toLowerCase().endsWith(".mp4")) {

            alert("Bukan MP4");

            console.error("Bukan MP4");

            return;

        }

        console.log("Memulai upload...");

        const formData = new FormData();
        formData.append("file", file);

        try {

            const response = await fetch("/convert", {

                method: "POST",
                body: formData

            });

            console.log("Status :", response.status);

            const data = await response.json();

            console.log(data);

            if (response.ok) {

                alert("BERHASIL");

                console.log("SUCCESS");

                this.convertMessage.textContent =
                    "Conversion Success";

            } else {

                alert("ERROR");

                console.error(data);

                this.convertMessage.textContent =
                    JSON.stringify(data);

            }

        }

        catch (e) {

            alert("FETCH ERROR");

            console.error(e);

        }

    }

}

document.addEventListener("DOMContentLoaded", () => {

    console.log("converter.js berhasil dimuat");

    window.converter = new FileConverter();

});