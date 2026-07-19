/**
 * -------------------------------------------------------
 * Converigo
 * Download Manager
 * Version : 1.3.0
 *
 * Handles:
 * - Prepare download button
 * - Clear old download
 * - Clean download UI
 * - Global instance
 * - Batch downloads (multiple files)
 * -------------------------------------------------------
 */


class DownloadManager {

    constructor(downloadButtonId = "downloadBtn") {
        this.button = document.getElementById(downloadButtonId);
        console.log("Download Manager Loaded");

        if(this.button){
            this.clear();
        }
    }

    clear(){
        if(!this.button){
            return;
        }

        this.button.hidden = true;
        this.button.removeAttribute("href");
        this.button.removeAttribute("download");
        this.button.textContent = "Download";

        const batchContainer = document.getElementById("batchDownloads");
        if (batchContainer) {
            batchContainer.innerHTML = "";
            batchContainer.style.display = "none";
        }
    }

    prepare(result){
        if(!this.button){
            console.warn("Download button missing");
            return;
        }

        if(!result){
            console.warn("Download result missing");
            return;
        }

        // Handle batch results (multiple files)
        if (result.results && Array.isArray(result.results)) {
            const successResults = result.results.filter(r => r.status === "success");
            
            if (successResults.length === 0) {
                console.warn("No successful conversions in batch");
                return;
            }

            // For batch: create a container with multiple download links
            if (successResults.length === 1) {
                const singleResult = successResults[0];
                this._prepareSingleFile(singleResult);
            } else {
                this._prepareMultipleFiles(successResults);
            }
            return;
        }

        // Handle single file (backward compatibility)
        this._prepareSingleFile(result);
    }

    _prepareSingleFile(result) {
        const filename = result.filename || "converted-file";
        const extension = filename.split(".").pop().toUpperCase();

        this.button.hidden = false;
        this.button.href = result.download_path;
        this.button.download = filename;

        this.button.textContent =
            window.translate('upload.download', 'Download') +
            " " +
            extension;

        console.log("Download Ready:", filename);
    }

    _prepareMultipleFiles(results) {
        let container = document.getElementById("batchDownloads");
        if (!container) {
            container = document.createElement("div");
            container.id = "batchDownloads";
            container.style.display = "flex";
            container.style.flexDirection = "column";
            container.style.gap = "8px";
            container.style.marginTop = "12px";
            
            this.button.parentNode.insertBefore(container, this.button.nextSibling);
        }

        container.innerHTML = "";
        container.style.display = "flex";

        results.forEach((result, index) => {
            const link = document.createElement("a");
            link.href = result.download_path;
            link.download = result.filename;
            link.style.padding = "8px 12px";
            link.style.backgroundColor = "#4CAF50";
            link.style.color = "white";
            link.style.borderRadius = "4px";
            link.style.textDecoration = "none";
            link.style.textAlign = "center";
            link.style.fontSize = "14px";
            link.style.cursor = "pointer";

            const extension = result.filename.split(".").pop().toUpperCase();
            link.textContent = `📥 ${result.filename} (${extension})`;
            container.appendChild(link);
        });

        this.button.hidden = true;
        console.log("Batch Downloads Ready:", results.length, "files");
    }
}

/*
================================================
Initialize Download Manager
================================================
*/

document.addEventListener("DOMContentLoaded", ()=>{
    window.downloadManager = new DownloadManager("downloadBtn");
    console.log("DownloadManager Ready");
});
