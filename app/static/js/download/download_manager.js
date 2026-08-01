/**
 * -------------------------------------------------------
 * Converigo
 * Download Manager
 * Version : 1.3.0
 *
 * Responsibilities:
 * - Normalize and validate download payloads
 * - Cache download metadata for the current session
 * - Dispatch download-ready events for runtime consumers
 * - Preserve legacy DOM-based download button and batch download support
 *
 * Categories:
 * - BUSINESS: validation, normalization, event dispatch
 * - DOM: existing page download button and batch link rendering
 * - LEGACY: compatibility helpers for current homepage/workspace flows
 * -------------------------------------------------------
 */

class DownloadManager {
    constructor(downloadButtonId = "downloadBtn") {
        this.button = document.getElementById(downloadButtonId);
        this.lastDownloadItems = [];
        this.processingDuration = 0;

        console.log("Download Manager Loaded");

        if (this.button) {
            this.clear();
        }
    }

    // BUSINESS: normalize the converter response into canonical download items
    _normalizeDownloadResult(result) {
        if (!result || typeof result !== 'object') {
            return [];
        }

        const items = [];
        if (Array.isArray(result.results)) {
            result.results.forEach((item) => {
                if (!item || item.status !== 'success') {
                    return;
                }
                if (item.filename && item.download_path) {
                    items.push({
                        filename: String(item.filename),
                        download_path: String(item.download_path),
                        original: item,
                    });
                }
            });
        } else if (result.filename && result.download_path) {
            items.push({
                filename: String(result.filename),
                download_path: String(result.download_path),
                original: result,
            });
        }

        return items;
    }

    // BUSINESS: ensure normalized items are valid for download
    _validateDownloadItems(items) {
        return Array.isArray(items) && items.length > 0 && items.every((item) => {
            return item && item.filename && item.download_path;
        });
    }

    // BUSINESS: dispatch an explicit runtime event for download readiness
    _dispatchDownloadReady(items, originalResult) {
        const eventName = (window.ConverigoEvents && window.ConverigoEvents.DOWNLOAD_READY) ? window.ConverigoEvents.DOWNLOAD_READY : 'download-ready';
        window.dispatchEvent(new CustomEvent(eventName, {
            detail: {
                items,
                originalResult,
                processingDuration: this.processingDuration,
            }
        }));
    }

    // LEGACY: preserve the existing homepage/workspace download button behavior
    _prepareLegacyDownloadUI(items) {
        if (!this.button || !this._validateDownloadItems(items)) {
            return;
        }

        if (items.length === 1) {
            this._prepareSingleFile(items[0]);
        } else {
            this._prepareMultipleFiles(items);
        }
    }

    // PUBLIC: reset state and legacy UI
    clear() {
        this.lastDownloadItems = [];
        this.processingDuration = 0;

        if (!this.button) {
            return;
        }

        this.button.hidden = true;
        this.button.removeAttribute('href');
        this.button.removeAttribute('download');
        this.button.textContent = window.translate ? window.translate('upload.download', 'Download') : 'Download';

        const batchContainer = document.getElementById('batchDownloads');
        if (batchContainer) {
            batchContainer.innerHTML = '';
            batchContainer.style.display = 'none';
        }
    }

    // PUBLIC: prepare download payloads for runtime and legacy UI
    prepare(result) {
        if (!result) {
            console.warn('Download result missing');
            return;
        }

        const items = this._normalizeDownloadResult(result);
        if (!this._validateDownloadItems(items)) {
            console.warn('No valid downloadable items found');
            return;
        }

        this.lastDownloadItems = items;
        this._dispatchDownloadReady(items, result);
        this._prepareLegacyDownloadUI(items);
    }

  _prepareLegacyDownloadUI(items) {
        if ((window.__ENABLE_DOWNLOAD_V2__ === true || (window.ConverigoFlags && window.ConverigoFlags.ENABLE_DOWNLOAD_V2)) ) {
            if (typeof console !== 'undefined' && typeof console.debug === 'function') {
                console.debug('[DownloadManager] Download V2 enabled; skipping legacy UI rendering.');
            }
            return;
        }

        if (!this.button || !this._validateDownloadItems(items)) {
            return;
        }

        if (items.length === 1) {
            this._prepareSingleFile(items[0]);
        } else {
            this._prepareMultipleFiles(items);
        }
    }

    // LEGACY: analytics-only helper
    _trackDownloadCompleted() {
        if (!window.converigoAnalytics || typeof window.converigoAnalytics.trackEvent !== 'function') {
            return;
        }
        const context = window.converigoAnalytics.getConverterContext();
        window.converigoAnalytics.trackEvent('download_button_click', {
            converter_name: context.converter_name,
            page_path: window.location.pathname || '/',
            event_status: 'success',
        });
    }

    // LEGACY: attach click behavior to the current download button or links
    _attachDownloadHandler(element) {
        if (!element || element.dataset.ga4Bound === 'true') {
            return;
        }

        element.addEventListener('click', (event) => {
            this._trackDownloadCompleted();
            const downloadUrl = element.getAttribute('href') || '';
            const filename = element.getAttribute('download') || '';
            if (downloadUrl) {
                event.preventDefault();
                this._triggerDownload(downloadUrl, filename);
            }
        }, { passive: false });

        element.dataset.ga4Bound = 'true';
    }

    // LEGACY: perform the browser download and fallback navigation
    _triggerDownload(downloadUrl, filename = '') {
        if (!downloadUrl) {
            return;
        }

        const anchor = document.createElement('a');
        anchor.href = downloadUrl;
        anchor.download = filename;
        anchor.rel = 'noopener noreferrer';
        anchor.target = '_self';
        anchor.style.display = 'none';
        document.body.appendChild(anchor);

        try {
            anchor.click();
        } catch (error) {
            console.warn('Direct download click failed', error);
        } finally {
            anchor.remove();
        }

        window.setTimeout(() => {
            try {
                window.location.assign(downloadUrl);
            } catch (error) {
                console.warn('Fallback download navigation failed', error);
            }
        }, 350);
    }

    // LEGACY: set up the single-file download button
    _prepareSingleFile(item) {
        if (!this.button) {
            return;
        }

        const filename = item.filename || 'converted-file';
        const extension = filename.split('.').pop().toUpperCase();

        this.button.hidden = false;
        this._attachDownloadHandler(this.button);
        this.button.href = item.download_path;
        this.button.download = filename;

        this.button.textContent =
            window.translate('upload.download', 'Download') + ' ' + extension;

        console.log('Download Ready:', filename);
    }

    // LEGACY: create a batch download list for multiple files
    _prepareMultipleFiles(items) {
        if (!this.button) {
            return;
        }

        let container = document.getElementById('batchDownloads');
        if (!container) {
            container = document.createElement('div');
            container.id = 'batchDownloads';
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.gap = '8px';
            container.style.marginTop = '12px';
            this.button.parentNode.insertBefore(container, this.button.nextSibling);
        }

        container.innerHTML = '';
        container.style.display = 'flex';

        items.forEach((item) => {
            const link = document.createElement('a');
            link.href = item.download_path;
            link.download = item.filename;
            link.style.padding = '8px 12px';
            link.style.backgroundColor = '#4CAF50';
            link.style.color = 'white';
            link.style.borderRadius = '4px';
            link.style.textDecoration = 'none';
            link.style.textAlign = 'center';
            link.style.fontSize = '14px';
            link.style.cursor = 'pointer';

        const extension = item.filename.split('.').pop().toUpperCase();
            link.textContent = `📥 ${item.filename} (${extension})`;
            this._attachDownloadHandler(link);
            container.appendChild(link);
        });

        this.button.hidden = true;
        console.log('Batch Downloads Ready:', items.length, 'files');
    }
}

/*
================================================
Initialize Download Manager
================================================
*/

document.addEventListener('DOMContentLoaded', () => {
    window.downloadManager = new DownloadManager('downloadBtn');
    console.log('DownloadManager Ready');
});
