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

    const ConversionState = {
        IDLE: 'IDLE',
        FILE_SELECTED: 'FILE_SELECTED',
        CONVERTING: 'CONVERTING',
        SUCCESS: 'SUCCESS',
        ERROR: 'ERROR'
    };

    let selectedFile = null;
    let selectedFormat = null;
    let progressTimer = null;
    let currentConversionState = ConversionState.IDLE;
    let convertButtonReady = false;
    let hasFormatChoices = false;

    const conversionArea = document.getElementById('conversionArea');
    const convertButtonElement = document.getElementById('convertButton');

    const getResultCard = () => document.getElementById('resultCard');
    const getErrorCard = () => document.getElementById('errorCard');

    const setVisibility = (element, visible) => {
        if (!element) return;
        element.hidden = !visible;
        if (visible) {
            element.style.removeProperty('display');
        } else {
            element.style.display = 'none';
        }
    };

    const updateConversionAreaVisibility = () => {
        const shouldShow = hasFormatChoices && (
            currentConversionState === ConversionState.FILE_SELECTED ||
            currentConversionState === ConversionState.CONVERTING
        );
        setVisibility(conversionArea, shouldShow);
    };

    const updateConvertButtonVisibility = () => {
        if (!convertButtonElement) return;
        const shouldShow = hasFormatChoices && (
            currentConversionState === ConversionState.CONVERTING ||
            (currentConversionState === ConversionState.FILE_SELECTED && convertButtonReady)
        );
        setVisibility(convertButtonElement, shouldShow);
    };

    const updateResultErrorVisibility = () => {
        setVisibility(getResultCard(), currentConversionState === ConversionState.SUCCESS);
        setVisibility(getErrorCard(), currentConversionState === ConversionState.ERROR);
        setVisibility(downloadBtn, currentConversionState === ConversionState.SUCCESS);
    };

    const renderConversionState = () => {
        updateConversionAreaVisibility();
        updateConvertButtonVisibility();
        updateResultErrorVisibility();

        if (currentConversionState === ConversionState.IDLE) {
            clearConvertMessage();
            stopProgress();
        }

        if (currentConversionState === ConversionState.SUCCESS || currentConversionState === ConversionState.ERROR) {
            stopProgress();
        }
    };

    const setConversionState = (state) => {
        if (!Object.values(ConversionState).includes(state)) {
            console.warn('Invalid conversion state:', state);
            return;
        }
        currentConversionState = state;
        if (state === ConversionState.IDLE) {
            convertButtonReady = false;
        }
        renderConversionState();
    };

    const setFormatChoicesAvailable = (available) => {
        hasFormatChoices = Boolean(available);
        renderConversionState();
    };

    const setConvertReady = (ready) => {
        convertButtonReady = Boolean(ready);
        if (convertButtonElement) {
            convertButtonElement.disabled = !convertButtonReady;
        }
        updateConvertButtonVisibility();
    };

    window.conversionStateController = {
        ConversionState,
        setConversionState,
        setFormatChoicesAvailable,
        setConvertReady,
        getCurrentState: () => currentConversionState,
    };

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

    const hideResultCard = () => {
        const resultCard = document.getElementById('resultCard');
        if (resultCard) {
            resultCard.hidden = true;
        }
    };

    const hideErrorCard = () => {
        const errorCard = document.getElementById('errorCard');
        if (errorCard) {
            errorCard.hidden = true;
        }
    };

    const hideDownloadCard = () => {
        if (downloadBtn) {
            downloadBtn.hidden = true;
        }
    };

    const hideConvertButton = () => {
        if (window.conversionStateController) {
            window.conversionStateController.setConvertReady(false);
        } else if (convertBtn) {
            setVisibility(convertBtn, false);
        }
    };

    const showConvertButton = () => {
        if (window.conversionStateController) {
            window.conversionStateController.setConvertReady(true);
        } else if (convertBtn) {
            setVisibility(convertBtn, true);
        }
    };

    const hidePreviewCard = () => {
        const previewContainer = document.getElementById('previewContainer');
        if (previewContainer) {
            previewContainer.hidden = true;
        }
    };

    const clearConvertMessage = () => {
        if (convertMessage) {
            convertMessage.textContent = '';
            convertMessage.classList.remove('success', 'error');
        }
        if (convertProgress) {
            convertProgress.hidden = true;
            convertProgress.setAttribute('aria-hidden', 'true');
        }
        if (progressBar) {
            progressBar.style.width = '0%';
        }
    };

    const showConversionArea = () => {
        if (window.conversionStateController) {
            window.conversionStateController.setFormatChoicesAvailable(true);
            window.conversionStateController.setConversionState(ConversionState.FILE_SELECTED);
        } else {
            const conversionArea = document.getElementById('conversionArea');
            if (conversionArea) {
                conversionArea.hidden = false;
            }
        }
        const uploadMain = document.querySelector('.upload-main');
        if (uploadMain) {
            uploadMain.classList.remove('upload-initial');
            uploadMain.classList.add('upload-active');
        }
    };

    const hideConversionArea = () => {
        if (window.conversionStateController) {
            window.conversionStateController.setConversionState(ConversionState.IDLE);
            window.conversionStateController.setFormatChoicesAvailable(false);
        } else {
            const conversionArea = document.getElementById('conversionArea');
            if (conversionArea) {
                conversionArea.hidden = true;
            }
        }
        const uploadMain = document.querySelector('.upload-main');
        if (uploadMain) {
            uploadMain.classList.remove('upload-active');
            uploadMain.classList.add('upload-initial');
        }
    };

    const resetConverterState = () => {
        if (window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
            window.conversionStateController.setConversionState(ConversionState.IDLE);
            window.conversionStateController.setFormatChoicesAvailable(false);
        }
        if (window.converter && typeof window.converter.reset === 'function') {
            window.converter.reset();
        }
        if (window.uploadManager && typeof window.uploadManager.resetUpload === 'function') {
            window.uploadManager.resetUpload();
        }
        if (convertMessage) {
            convertMessage.textContent = '';
            convertMessage.classList.remove('success', 'error');
        }
        if (progressBar) {
            progressBar.style.width = '0%';
        }
        if (convertProgress) {
            convertProgress.hidden = true;
            convertProgress.setAttribute('aria-hidden', 'true');
        }
    };

    const initializeUI = () => {
        hideResultCard();
        hideErrorCard();
        hideDownloadCard();
        hideConvertButton();
        hidePreviewCard();
        if (window.conversionStateController) {
            window.conversionStateController.setFormatChoicesAvailable(false);
            window.conversionStateController.setConversionState(ConversionState.IDLE);
        } else {
            hideConversionArea();
        }
        clearConvertMessage();
        resetConverterState();
    };

    // File selected by UploadManager
    window.addEventListener("file-selected", (e) => {
        try {
            selectedFile = e?.detail?.file || e?.detail?.files?.[0] || null;
            if (hasConverterController()) {
                if (selectedFile && window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function') {
                    window.conversionStateController.setConversionState(ConversionState.FILE_SELECTED);
                }
                return;
            }

            if (selectedFile && convertBtn) {
                convertBtn.disabled = false;
                convertBtn.textContent = window.translate('upload.convert', 'Convert');
                showStatus("");
                if (downloadBtn) downloadBtn.hidden = true;
                showConvertButton();
                showConversionArea();
            }
        } catch (err) {
            console.error(err);
        }
    });

    // Format selected by RecommendationManager or format UI
    window.addEventListener("format-selected", (e) => {
        try {
            if (hasConverterController()) return;

            const fmt = e?.detail?.target;
            if (fmt) selectedFormat = String(fmt).toLowerCase();
            console.log("FORMAT SELECTED:", selectedFormat);
            if (selectedFile && selectedFormat && convertBtn) {
                showConvertButton();
            }
        } catch (err) {
            console.error(err);
        }
    });

    // When ConverterController is loaded, it manages the conversion lifecycle and progress UI.
    // `app.js` keeps upload and format helpers available for non-controller pages.

    if (window.converigoAnalytics && typeof window.converigoAnalytics.trackEvent === 'function' && window.converigoAnalytics.isConverterRoute()) {
        window.converigoAnalytics.trackEvent('converter_view', window.converigoAnalytics.getConverterContext());
    }

    const initConverterAccordion = () => {
        const accordion = document.getElementById('converterAccordion');
        if (!accordion) return;

        const items = accordion.querySelectorAll('.accordion-item');
        items.forEach(item => {
            const button = item.querySelector('.accordion-toggle');
            const panelId = button?.getAttribute('data-target');
            const panel = panelId ? document.getElementById(panelId) : null;
            if (!button || !panel) return;

            button.setAttribute('aria-expanded', 'false');
            panel.hidden = true;

            button.addEventListener('click', () => {
                const isOpen = button.getAttribute('aria-expanded') === 'true';
                items.forEach(otherItem => {
                    const otherButton = otherItem.querySelector('.accordion-toggle');
                    const otherPanelId = otherButton?.getAttribute('data-target');
                    const otherPanel = otherPanelId ? document.getElementById(otherPanelId) : null;
                    if (otherButton && otherPanel) {
                        otherButton.setAttribute('aria-expanded', 'false');
                        otherPanel.hidden = true;
                        otherButton.classList.remove('active');
                        const otherArrow = otherButton.querySelector('.accordion-arrow');
                        if (otherArrow) otherArrow.textContent = '+';
                    }
                });

                if (!isOpen) {
                    button.setAttribute('aria-expanded', 'true');
                    panel.hidden = false;
                    button.classList.add('active');
                    const arrow = button.querySelector('.accordion-arrow');
                    if (arrow) arrow.textContent = '−';
                }
            });
        });
    };

    const initFaqAccordion = () => {
        const faqButtons = document.querySelectorAll('.faq-question');
        faqButtons.forEach(button => {
            const answerId = button.getAttribute('aria-controls');
            const answer = answerId ? document.getElementById(answerId) : null;
            if (!answer) return;

            button.addEventListener('click', () => {
                const isOpen = button.getAttribute('aria-expanded') === 'true';
                faqButtons.forEach(otherButton => {
                    const otherAnswerId = otherButton.getAttribute('aria-controls');
                    const otherAnswer = otherAnswerId ? document.getElementById(otherAnswerId) : null;
                    if (otherAnswer) {
                        otherAnswer.hidden = true;
                    }
                    otherButton.setAttribute('aria-expanded', 'false');
                    const toggle = otherButton.querySelector('.faq-toggle');
                    if (toggle) {
                        toggle.textContent = '+';
                    }
                });

                if (!isOpen) {
                    button.setAttribute('aria-expanded', 'true');
                    answer.hidden = false;
                    const toggle = button.querySelector('.faq-toggle');
                    if (toggle) {
                        toggle.textContent = '−';
                    }
                }
            });
        });
    };

    const initMobileNav = () => {
        const navToggle = document.getElementById('navToggle');
        const primaryNav = document.getElementById('primaryNav');

        if (!navToggle || !primaryNav) return;

        navToggle.addEventListener('click', () => {
            const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', String(!isOpen));
            primaryNav.classList.toggle('open', !isOpen);
        });
    };

    initConverterAccordion();
    initFaqAccordion();
    initMobileNav();

    initializeUI();

});
