/**
 * -------------------------------------------------------
 * Converigo
 * Download Page Flow Controller
 * Version : 1.0.0
 *
 * Wires the blueprint-certified Download Page (Stage 1 + Stage 2,
 * #downloadWorkspaceScreen) to the EXISTING upload/convert/download
 * engine using EXISTING events only:
 *   - file-selected      (dispatched by UploadManager)
 *   - format-selected    (dispatched here, consumed by ConverterController)
 *   - upload-finished    (dispatched by ConverterController)
 *   - download-ready     (dispatched by DownloadManager, consumed by DownloadAdapter)
 *
 * No new conversion or download engine is created here — this file only
 * shows/hides existing DOM (Homepage sections vs #downloadWorkspaceScreen,
 * Stage 1 vs Stage 2) and forwards user actions to window.converter /
 * window.uploadManager / window.downloadAdapter, which already exist.
 *
 * The multi-file "#workspace" concept is never touched and never shown.
 * -------------------------------------------------------
 */
(function () {
    function homepageSections() {
        const hero = document.querySelector('section.hero.homepage-hero');
        const result = [];
        let afterHero = false;

        Array.from(document.body.children).forEach((el) => {
            if (afterHero) {
                if (el.tagName === 'SCRIPT') return;
                if (el.id === 'downloadWorkspaceScreen') return;
                result.push(el);
            }
            if (el === hero) {
                afterHero = true;
            }
        });

        return result;
    }

    function hideHomepageUploadCard() {
        document.querySelectorAll('.homepage-hero .homepage-upload-card').forEach((el) => {
            el.hidden = true;
        });
    }

    function showHomepageUploadCard() {
        document.querySelectorAll('.homepage-hero .homepage-upload-card').forEach((el) => {
            el.hidden = false;
        });
    }

    function showDownloadWorkspace() {
        homepageSections().forEach((el) => { el.hidden = true; });
        hideHomepageUploadCard();
        const screen = document.getElementById('downloadWorkspaceScreen');
        if (screen) {
            screen.hidden = false;
            requestAnimationFrame(() => screen.classList.add('is-visible'));
        }
    }

    function showHomepage() {
        const screen = document.getElementById('downloadWorkspaceScreen');
        if (screen) {
            screen.classList.remove('is-visible');
            screen.hidden = true;
        }
        showHomepageUploadCard();
        homepageSections().forEach((el) => { el.hidden = false; });
    }

    function showStage1() {
        const stage1 = document.getElementById('downloadFormatStage');
        const stage2 = document.getElementById('downloadStage');
        if (stage2) {
            stage2.classList.remove('is-visible');
            stage2.hidden = true;
        }
        if (stage1) {
            stage1.hidden = false;
        }
    }

    function showStage2() {
        const stage1 = document.getElementById('downloadFormatStage');
        if (stage1) {
            stage1.hidden = true;
        }
        if (window.downloadAdapter && typeof window.downloadAdapter.showStage === 'function') {
            window.downloadAdapter.showStage();
            window.downloadAdapter.setStep('converting');
        } else {
            const stage2 = document.getElementById('downloadStage');
            if (stage2) {
                stage2.hidden = false;
                stage2.classList.add('is-visible');
            }
        }
    }

    function formatFileSize(bytes) {
        if (typeof bytes !== 'number' || Number.isNaN(bytes)) {
            return '';
        }
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }

    function populateStage1(file) {
        const nameEl = document.getElementById('downloadFileNameLabel');
        const sizeEl = document.getElementById('downloadFileSizeLabel');
        if (nameEl) nameEl.textContent = file ? file.name : '—';
        if (sizeEl) sizeEl.textContent = file ? formatFileSize(file.size) : '';
    }

    function resetStage1Labels() {
        const nameEl = document.getElementById('downloadFileNameLabel');
        const sizeEl = document.getElementById('downloadFileSizeLabel');
        if (nameEl) nameEl.textContent = '—';
        if (sizeEl) sizeEl.textContent = '';
        const formatSelect = document.getElementById('globalFormat');
        if (formatSelect) formatSelect.selectedIndex = 0;
    }

    function resetConvertButton() {
        const btn = document.getElementById('btnConvert');
        if (btn) {
            btn.disabled = false;
        }
    }

    function resetStage2() {
        const stage2 = document.getElementById('downloadStage');
        if (stage2) {
            stage2.classList.remove('is-visible');
            stage2.hidden = true;
        }
        document.querySelectorAll('#downloadStage .step-item').forEach((item) => {
            item.classList.remove('is-active', 'is-complete');
        });
        const firstStep = document.querySelector('#downloadStage .step-item[data-step="converting"]');
        if (firstStep) firstStep.classList.add('is-active');

        const btnDownloadMain = document.getElementById('btnDownloadMain');
        if (btnDownloadMain) {
            btnDownloadMain.disabled = true;
            btnDownloadMain.textContent = 'Download Sekarang';
        }
        const badge = document.getElementById('downloadBadge');
        const title = document.getElementById('downloadTitle');
        const subtitle = document.getElementById('downloadSubtitle');
        if (badge) badge.textContent = 'Menyiapkan unduhan';
        if (title) title.textContent = 'Mengonversi berkas Anda';
        if (subtitle) subtitle.textContent = 'Kami sedang menyiapkan file hasil untuk Anda unduh.';

        if (window.downloadAdapter && typeof window.downloadAdapter._clearTimers === 'function') {
            window.downloadAdapter._clearTimers();
        }
    }

    function resetAll() {
        resetStage2();
        resetStage1Labels();
        resetConvertButton();
        currentFile = null;

        if (window.converter && typeof window.converter.reset === 'function') {
            window.converter.reset();
        }
        if (window.uploadManager && typeof window.uploadManager.resetUpload === 'function') {
            window.uploadManager.resetUpload();
        }

        showStage1();
        showHomepage();
    }

    let currentFile = null;

    // Keep the Stage 1 <select> truthful to whichever format the existing
    // engine actually holds — regardless of whether it was set by this file
    // (initial/on-change dispatch) or by the existing RecommendationManager's
    // own auto-suggested format (both use the same `format-selected` event).
    window.addEventListener('format-selected', (event) => {
        const target = event?.detail?.target;
        if (!target) return;
        const formatSelect = document.getElementById('globalFormat');
        if (!formatSelect) return;
        const match = Array.from(formatSelect.options).find(
            (option) => option.value.toLowerCase() === String(target).toLowerCase()
        );
        if (match) {
            formatSelect.value = match.value;
        }
    });

    // Homepage -> Choose File -> native file picker -> file-selected (existing event)
    window.addEventListener('file-selected', (event) => {
        const detail = event.detail || {};
        currentFile = detail.file || (detail.files && detail.files[0]) || null;
        if (!currentFile) return;

        populateStage1(currentFile);
        showStage1();
        showDownloadWorkspace();

        // Feed the currently selected output format into the existing
        // converter engine using the same event other pickers use.
        const formatSelect = document.getElementById('globalFormat');
        if (formatSelect) {
            window.dispatchEvent(new CustomEvent('format-selected', { detail: { target: formatSelect.value } }));
        }
    });

    // If the existing engine reports a failed conversion, return to Stage 1
    // instead of leaving the user stuck on a Stage 2 that never becomes ready.
    window.addEventListener('upload-finished', (event) => {
        const success = Boolean(event.detail && event.detail.success);
        if (!success) {
            resetConvertButton();
            showStage1();
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
        const formatSelect = document.getElementById('globalFormat');
        if (formatSelect) {
            formatSelect.addEventListener('change', () => {
                window.dispatchEvent(new CustomEvent('format-selected', { detail: { target: formatSelect.value } }));
            });
        }

        const btnConvert = document.getElementById('btnConvert');
        if (btnConvert) {
            btnConvert.addEventListener('click', () => {
                if (!window.converter || typeof window.converter.convert !== 'function') {
                    return;
                }
                btnConvert.disabled = true;
                showStage2();
                window.converter.convert();
            });
        }

        const btnConvertAnother = document.getElementById('btnConvertAnother');
        if (btnConvertAnother) {
            btnConvertAnother.addEventListener('click', () => {
                resetAll();
            });
        }
    });
})();
