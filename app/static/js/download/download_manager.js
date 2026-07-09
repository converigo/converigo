/**
 * -------------------------------------------------------
 * Convertin
 * Download Manager
 * Version : 1.0.0
 * -------------------------------------------------------
 */

class DownloadManager {

    constructor(downloadButtonId) {

        this.button =
            document.getElementById(downloadButtonId);

    }

    clear() {

        if (!this.button) {

            return;

        }

        this.button.hidden = true;

        this.button.removeAttribute("href");

        this.button.removeAttribute("download");

        this.button.textContent = "Download";

    }

    prepare(result) {

        if (!this.button) {

            return;

        }

        this.button.hidden = false;

        this.button.href =
            result.download_path;

        this.button.download =
            result.filename;

        this.button.textContent =
            "Download " + result.filename;

    }

}

window.DownloadManager =
    DownloadManager;