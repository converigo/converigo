/*
Project : Converigo
App Controller
Version : 3.0.0

Responsibility:
- Listen for `fileSelected` and `formatSelected` events
- Handle convert request lifecycle
- Update convert/download UI and messages
*/

document.addEventListener("DOMContentLoaded", () => {

    const convertBtn = document.getElementById("convertButton");
    const downloadBtn = document.getElementById("downloadBtn");
    const convertMessage = document.getElementById("convertMessage");

    const hasConverterController = () => Boolean(window.converter);

    let selectedFile = null;
    let selectedFormat = null;

    // File selected by UploadManager
    document.addEventListener("file-selected", (e) => {
        try {
            if (hasConverterController()) return;

            selectedFile = e?.detail?.file || null;
            if (selectedFile && convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = "Convert";
                if (convertMessage) {
                    convertMessage.textContent = "";
                    convertMessage.classList.remove("success", "error");
                }
                if (downloadBtn) downloadBtn.hidden = true;
            }
        } catch (err) {
            console.error(err);
        }
    });

    // Format selected by RecommendationManager or format UI
    document.addEventListener("format-selected", (e) => {
        try {
            if (hasConverterController()) return;

            const fmt = e?.detail?.target;
            if (fmt) selectedFormat = String(fmt).toLowerCase();
            console.log("FORMAT SELECTED:", selectedFormat);
        } catch (err) {
            console.error(err);
        }
    });

    // Convert button handler
    if (!hasConverterController && convertBtn) {
        convertBtn.addEventListener("click", async () => {
            if (!selectedFile) return;
            if (!selectedFormat) {
                if (convertMessage) convertMessage.textContent = "❌ Select a target format first.";
                return;
            }

            convertBtn.disabled = true;
            const originalText = convertBtn.textContent;
            convertBtn.textContent = "Converting...";

            const formData = new FormData();
            formData.append("file", selectedFile);
            formData.append("target_format", selectedFormat);

            try {
                const response = await fetch("/convert", { method: "POST", body: formData });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    console.error("Convert error", err);
                    if (convertMessage) convertMessage.textContent = "❌ Conversion failed. Please try another format.";
                    return;
                }

                const result = await response.json();

                if (result.status === "success") {
                    if (convertMessage) convertMessage.textContent = "✓ Conversion completed successfully";
                    if (downloadBtn) {
                        downloadBtn.href = result.download_path;
                        if (result.filename) downloadBtn.download = result.filename;
                        downloadBtn.hidden = false;
                        // Update button state to indicate ready-to-download
                        if (convertBtn) convertBtn.textContent = "Download Ready";
                    }
                } else {
                    console.error("Convert failed", result);
                    if (convertMessage) convertMessage.textContent = "❌ Conversion failed. Please try another format.";
                }

            } catch (error) {
                console.error(error);
                if (convertMessage) convertMessage.textContent = "❌ Conversion failed. Please try again later.";
            } finally {
                convertBtn.disabled = false;
                convertBtn.textContent = originalText || "Convert";
            }
        });
    }

});
