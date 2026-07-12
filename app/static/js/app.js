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
    const convertProgress = document.getElementById("convertProgress");
    const progressBar = convertProgress?.querySelector(".progress-bar");

    const hasConverterController = () => Boolean(window.converter);

    let selectedFile = null;
    let selectedFormat = null;
    let progressTimer = null;

    const setProgress = (value) => {
        if (progressBar) {
            progressBar.style.width = `${Math.min(100, Math.max(0, value))}%`;
        }
    };

    const startProgress = () => {
        if (convertProgress) {
            convertProgress.hidden = false;
            convertProgress.setAttribute("aria-hidden", "false");
        }
        setProgress(10);
        clearInterval(progressTimer);
        progressTimer = setInterval(() => {
            const current = parseInt(progressBar?.style.width || '0', 10) || 0;
            const next = current + (current < 70 ? 8 : 2);
            setProgress(next);
            if (current >= 90) {
                clearInterval(progressTimer);
            }
        }, 300);
    };

    const stopProgress = (complete = false) => {
        clearInterval(progressTimer);
        progressTimer = null;
        if (complete) {
            setProgress(100);
        }
        if (convertProgress) {
            convertProgress.hidden = true;
            convertProgress.setAttribute("aria-hidden", "true");
        }
    };

    const showStatus = (message, type = "") => {
        if (!convertMessage) return;
        convertMessage.textContent = message;
        convertMessage.classList.remove("success", "error");
        if (type) convertMessage.classList.add(type);
    };

    // File selected by UploadManager
    document.addEventListener("file-selected", (e) => {
        try {
            if (hasConverterController()) return;

            selectedFile = e?.detail?.file || null;
            if (selectedFile && convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = window.translate('upload.convert', 'Convert');
                showStatus("");
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

    // When ConverterController is loaded, it manages the conversion lifecycle and progress UI.
    // `app.js` keeps upload and format helpers available for non-controller pages.

});
