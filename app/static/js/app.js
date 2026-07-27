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
    const dropZoneElement = document.getElementById('dropZone');
    let dropZoneCompleteTimer = null;

    const getResultCard = () => document.getElementById('resultCard');
    const getErrorCard = () => document.getElementById('errorCard');

    const trackAnalytics = (eventName, params = {}) => {
        if (window.converigoAnalytics && typeof window.converigoAnalytics.trackEvent === 'function') {
            window.converigoAnalytics.trackEvent(eventName, params);
        }
    };

    const emitLandingSignals = () => {
        const path = window.location.pathname || '/';
        if (path === '/') {
            trackAnalytics('homepage_view', {
                page_path: path,
                page_title: document.title || 'Converigo',
                event_status: 'success',
            });
        }

        const params = new URLSearchParams(window.location.search);
        const searchQuery = params.get('q') || params.get('search') || '';
        if (searchQuery) {
            trackAnalytics('search_query', {
                page_path: path,
                search_query: searchQuery,
                event_status: 'success',
            });
        }

        const referrer = (document.referrer || '').toLowerCase();
        if (referrer && /(?:google|bing|duckduckgo|yahoo|ecosia|brave)\./.test(referrer)) {
            trackAnalytics('organic_entry', {
                page_path: path,
                entry_type: 'organic',
                event_status: 'success',
            });
        }
    };

    const initPerformanceTracking = () => {
        if (!window.PerformanceObserver || !window.performance) {
            return;
        }

        const path = window.location.pathname || '/';
        let clsValue = 0;
        let lcpValue = 0;
        let inpValue = 0;
        let fcpSent = false;

        const emitMetric = (metricName, metricValue) => {
            if (metricValue === null || metricValue === undefined || Number.isNaN(metricValue)) {
                return;
            }
            trackAnalytics('performance_metric', {
                page_path: path,
                metric_name: metricName,
                metric_value: metricValue,
                event_status: 'success',
            });
        };

        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            emitMetric('ttfb', Math.max(0, Math.round(navigation.responseStart)));
        }

        try {
            const paintObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    if (entry.name === 'first-contentful-paint' && !fcpSent) {
                        fcpSent = true;
                        emitMetric('fcp', Math.max(0, Math.round(entry.startTime)));
                    }
                });
            });
            paintObserver.observe({ type: 'paint', buffered: true });
        } catch (error) {
            void error;
        }

        try {
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                if (lastEntry) {
                    lcpValue = Math.max(lcpValue, Math.round(lastEntry.startTime));
                }
            });
            lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
        } catch (error) {
            void error;
        }

        try {
            const clsObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value || 0;
                    }
                });
            });
            clsObserver.observe({ type: 'layout-shift', buffered: true });
        } catch (error) {
            void error;
        }

        try {
            const eventObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    if (entry.interactionId > 0) {
                        inpValue = Math.max(inpValue, Math.round(entry.duration || 0));
                    }
                });
            });
            eventObserver.observe({ type: 'event', buffered: true, durationThreshold: 40 });
        } catch (error) {
            void error;
        }

        window.addEventListener('pagehide', () => {
            emitMetric('lcp', lcpValue);
            emitMetric('cls', Number(clsValue.toFixed(3)));
            emitMetric('inp', inpValue);
        }, { once: true });

        window.setTimeout(() => {
            emitMetric('lcp', lcpValue);
            emitMetric('cls', Number(clsValue.toFixed(3)));
            emitMetric('inp', inpValue);
        }, 3000);
    };

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

    const syncDropZoneVisualState = () => {
        if (!dropZoneElement) return;

        dropZoneElement.classList.remove('is-converting');

        if (dropZoneCompleteTimer) {
            clearTimeout(dropZoneCompleteTimer);
            dropZoneCompleteTimer = null;
        }

        if (currentConversionState === ConversionState.CONVERTING) {
            dropZoneElement.classList.remove('is-complete');
            dropZoneElement.classList.add('is-converting');
            return;
        }

        if (currentConversionState === ConversionState.SUCCESS) {
            dropZoneElement.classList.add('is-complete');
            dropZoneCompleteTimer = setTimeout(() => {
                dropZoneElement.classList.remove('is-complete');
                dropZoneCompleteTimer = null;
            }, 1000);
            return;
        }

        dropZoneElement.classList.remove('is-complete');
    };

    const renderConversionState = () => {
        updateConversionAreaVisibility();
        updateConvertButtonVisibility();
        updateResultErrorVisibility();
        syncDropZoneVisualState();

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
                    trackAnalytics('faq_expand', {
                        page_path: window.location.pathname || '/',
                        faq_id: answerId || '',
                        event_status: 'success',
                    });
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
    emitLandingSignals();
    initPerformanceTracking();

    document.addEventListener('click', (event) => {
        const anchor = event.target.closest ? event.target.closest('a') : null;
        if (!anchor || !anchor.href) {
            return;
        }

        if (anchor.hasAttribute('download')) {
            return;
        }

        const href = anchor.getAttribute('href') || '';
        if (!href || href.startsWith('#')) {
            return;
        }

        try {
            const url = new URL(anchor.href, window.location.origin);
            if (url.origin !== window.location.origin) {
                return;
            }
            trackAnalytics('internal_link_click', {
                page_path: window.location.pathname || '/',
                link_href: href,
                event_status: 'success',
            });
        } catch (error) {
            void error;
        }
    }, true);

    // ================================================
    // UX-S2-005 Premium Recommendation Experience
    // ================================================

    const recommendationSection = document.getElementById('recommendationSection');
    const recommendationGrid = document.getElementById('recommendationGrid');

    const hideRecommendations = () => {
        if (!recommendationSection) return;
        recommendationSection.hidden = true;
        if (recommendationGrid) recommendationGrid.innerHTML = '';
    };

    const showRecommendations = () => {
        if (!recommendationSection) return;
        recommendationSection.hidden = false;
        recommendationSection.style.removeProperty('display');
    };

    const fetchRecommendations = async (fileExtension) => {
        if (!fileExtension || !recommendationGrid) return;

        try {
            const response = await fetch(`/recommend/${fileExtension}`);
            if (!response.ok) throw new Error('No recommendations');

            const data = await response.json();
            if (!data || !data.best_choice) {
                hideRecommendations();
                return;
            }

            renderRecommendationCards(data);
        } catch (error) {
            // Silently hide recommendations if API fails
            hideRecommendations();
        }
    };

    const getRecommendationSlug = (source, target) => {
        if (!source || !target) return '';
        const s = String(source).toLowerCase().trim();
        const t = String(target).toLowerCase().trim();
        return `/tools/${s}-to-${t}`;
    };

    const getIconForFormat = (format) => {
        const iconMap = {
            'pdf': '📄',
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'png': '🖼️',
            'webp': '🖼️',
            'gif': '🖼️',
            'svg': '🖼️',
            'mp4': '🎬',
            'mp3': '🎵',
            'wav': '🎵',
            'aac': '🎵',
            'flac': '🎵',
            'ogg': '🎵',
            'm4a': '🎵',
            'doc': '📝',
            'docx': '📝',
            'xls': '📊',
            'xlsx': '📊',
            'ppt': '📑',
            'pptx': '📑',
            'txt': '📃',
            'csv': '📊',
            'zip': '🗜️',
            'ico': '🔷',
            'tiff': '🖼️',
            'tif': '🖼️',
            'bmp': '🖼️',
            'heic': '🖼️',
            'avif': '🖼️',
        };
        const clean = String(format || '').toLowerCase().trim();
        return iconMap[clean] || '📄';
    };

    const renderRecommendationCards = (data) => {
        if (!recommendationGrid) return;

        recommendationGrid.innerHTML = '';

        const items = [];
        if (data.best_choice) {
            items.push({ ...data.best_choice, badge: 'Best Choice' });
        }
        if (data.alternatives && Array.isArray(data.alternatives)) {
            data.alternatives.forEach(alt => {
                items.push({ ...alt, badge: '' });
            });
        }

        if (items.length === 0) {
            hideRecommendations();
            return;
        }

        // Limit to 4 cards max
        const cardsToRender = items.slice(0, 4);

        cardsToRender.forEach((item, index) => {
            const source = item.source || '';
            const target = item.target || '';
            const title = item.title || `${String(source).toUpperCase()} → ${String(target).toUpperCase()}`;
            const description = item.description || `Convert ${String(source).toUpperCase()} to ${String(target).toUpperCase()}`;
            const icon = item.icon || getIconForFormat(target);
            const badge = item.badge || '';
            const slug = getRecommendationSlug(source, target);

            const card = document.createElement('a');
            card.className = 'recommendation-card';
            card.href = slug || '#';
            card.setAttribute('role', 'listitem');
            card.setAttribute('tabindex', '0');

            if (badge) {
                const badgeEl = document.createElement('span');
                badgeEl.className = 'recommendation-card-badge';
                badgeEl.textContent = badge;
                card.appendChild(badgeEl);
            }

            const iconEl = document.createElement('div');
            iconEl.className = 'recommendation-card-icon';
            iconEl.textContent = icon;
            card.appendChild(iconEl);

            const titleEl = document.createElement('h4');
            titleEl.className = 'recommendation-card-title';
            titleEl.textContent = title;
            card.appendChild(titleEl);

            const descEl = document.createElement('p');
            descEl.className = 'recommendation-card-desc';
            descEl.textContent = description;
            card.appendChild(descEl);

            const ctaEl = document.createElement('span');
            ctaEl.className = 'recommendation-card-cta';
            ctaEl.innerHTML = `Convert <span class="recommendation-card-cta-arrow">→</span>`;
            card.appendChild(ctaEl);

            // Stagger animation - add class after a micro delay
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    card.classList.add('recommendation-visible');
                });
            });

            recommendationGrid.appendChild(card);
        });

        showRecommendations();
    };

    // Handle download completion to trigger recommendations
    const initRecommendationOnDownload = () => {
        const downloadBtnEl = document.getElementById('downloadBtn');
        if (!downloadBtnEl) return;

        // Observe download button for href changes (signals download ready)
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.type === 'attributes' &&
                    (mutation.attributeName === 'href' || mutation.attributeName === 'hidden')) {
                    // Check if download is visible and has a href
                    if (!downloadBtnEl.hidden && downloadBtnEl.getAttribute('href')) {
                        // Use the file extension from the download filename
                        const downloadAttr = downloadBtnEl.getAttribute('download') || '';
                        const ext = downloadAttr.split('.').pop().toLowerCase();
                        if (ext && ext !== downloadAttr) {
                            fetchRecommendations(ext);
                        }
                        observer.disconnect();
                        return;
                    }
                }
            }
        });

        observer.observe(downloadBtnEl, {
            attributes: true,
            attributeFilter: ['href', 'hidden', 'download']
        });
    };

    // Also listen for conversion completion to trigger recommendations
    window.addEventListener('conversion-completed', (e) => {
        const ext = e?.detail?.outputFormat || '';
        if (ext) {
            fetchRecommendations(ext);
        }
    });

    // Reset recommendations when new file is selected
    window.addEventListener('file-selected', () => {
        hideRecommendations();
        // Re-init the observer for the new download cycle
        setTimeout(initRecommendationOnDownload, 100);
    });

    // Initialize recommendation observer on page load
    hideRecommendations();
    setTimeout(initRecommendationOnDownload, 500);

    initializeUI();

});
