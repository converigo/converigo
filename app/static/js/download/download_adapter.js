/**
 * Download Adapter
 *
 * Bridges legacy DownloadManager events to the existing Download V2 stage.
 * When the feature flag is enabled, legacy download button rendering is
 * suppressed and the workspace download stage is powered by the adapter.
 */
class DownloadAdapter {
  constructor(options = {}) {
    this.enabled = window.__ENABLE_DOWNLOAD_V2__ === true || Boolean(window.ConverigoFlags && window.ConverigoFlags.ENABLE_DOWNLOAD_V2);
    this.downloadManager = options.downloadManager || window.downloadManager;
    this.blueprint = document.getElementById('downloadScreenBlueprint');
    this.stage = document.getElementById('downloadStage') || this.blueprint;
    this.primaryButton = document.getElementById('btnDownloadMain') || this.blueprint?.querySelector('.download-screen__button--primary');
    this.stepItems = Array.from((this.stage ? this.stage.querySelectorAll('.step-item, .download-screen__step') : document.querySelectorAll('.step-item, .download-screen__step')));
    this.fileNameEl = document.getElementById('downloadFileName') || document.getElementById('downloadSummaryFilename');
    this.fileMetaEl = document.getElementById('downloadFileMeta');
    this.summaryFilenameEl = document.getElementById('downloadSummaryFilename');
    this.summaryFormatEl = document.getElementById('downloadSummaryFormat');
    this.summarySizeEl = document.getElementById('downloadSummarySize');
    this.summaryStatusEl = document.getElementById('downloadSummaryStatus');
    this.badgeEl = document.getElementById('downloadBadge') || this.blueprint?.querySelector('.download-screen__eyebrow');
    this.titleEl = document.getElementById('downloadTitle') || this.blueprint?.querySelector('.download-screen__title');
    this.subtitleEl = document.getElementById('downloadSubtitle') || this.blueprint?.querySelector('.download-screen__subtitle');
    this.currentItems = [];
    this.currentResult = null;
    this.stepTimers = [];
    this.eventName = (window.ConverigoEvents && window.ConverigoEvents.DOWNLOAD_READY) || 'download-ready';

    this.handleDownloadReady = this.handleDownloadReady.bind(this);
    this.handlePrimaryClick = this.handlePrimaryClick.bind(this);
  }

  initialize() {
    if (!this.enabled) {
      this._debug('Download V2 is disabled. Legacy download flow remains active.');
      return;
    }

    if (!this.stage || !this.primaryButton) {
      this._debug('Download V2 stage not available on this page. Legacy flow remains unchanged.');
      return;
    }

    window.addEventListener(this.eventName, this.handleDownloadReady, false);
    this.primaryButton.addEventListener('click', this.handlePrimaryClick);
    this._patchLegacyDownloadManager();
    this._debug('Download V2 adapter initialized.');
  }

  _patchLegacyDownloadManager() {
    if (!this.downloadManager || typeof this.downloadManager._prepareLegacyDownloadUI !== 'function') {
      return;
    }

    this.downloadManager._prepareLegacyDownloadUI = () => {
      this._debug('Legacy DownloadManager UI rendering suppressed by DownloadAdapter.');
    };
  }

  handleDownloadReady(event) {
    if (!this.enabled) {
      return;
    }

    const detail = event?.detail || {};
    const items = Array.isArray(detail.items) ? detail.items : [];

    if (!items.length) {
      this._debug('Download-ready event received with no download items.');
      return;
    }

    this.currentItems = items;
    this.currentResult = detail.originalResult || {};

    this.hideLegacyDownloadExperience();
    this.updateStageContent();
    this.showStage();
    this.setStep('converting');
    this.primaryButton.disabled = true;
    this.primaryButton.textContent = 'Download';

    this._clearTimers();
    this.stepTimers.push(window.setTimeout(() => this.setStep('preparing'), 220));
    this.stepTimers.push(window.setTimeout(() => {
      this.setStep('ready');
      this.primaryButton.disabled = false;
    }, 1120));
  }

  updateStageContent() {
    const firstItem = this.currentItems[0] || {};
    const filename = String(firstItem.filename || 'example-file.pdf');
    const format = this._getTargetFormat() || this._getExtension(filename) || 'PDF';
    const sizeText = this._getSizeText();

    if (this.fileNameEl) {
      this.fileNameEl.textContent = filename;
    }

    if (this.fileMetaEl) {
      this.fileMetaEl.textContent = `${this.currentItems.length} file${this.currentItems.length > 1 ? 's' : ''} • ${String(format).toUpperCase()}`;
    }

    if (this.summaryFilenameEl) {
      this.summaryFilenameEl.textContent = filename;
    }

    if (this.summaryFormatEl) {
      this.summaryFormatEl.textContent = String(format).toUpperCase();
    }

    if (this.summarySizeEl) {
      this.summarySizeEl.textContent = this._getSizeText();
    }

    if (this.summaryStatusEl) {
      this.summaryStatusEl.textContent = 'Ready to download';
    }

    if (this.badgeEl) {
      this.badgeEl.textContent = 'Menyiapkan unduhan';
    }

    if (this.titleEl) {
      this.titleEl.textContent = 'Mengonversi berkas Anda';
    }

    if (this.subtitleEl) {
      this.subtitleEl.textContent = 'Kami sedang menyiapkan file hasil untuk Anda unduh.';
    }
  }

  _getTargetFormat() {
    if (!this.currentResult) {
      return null;
    }

    return this.currentResult.target_format || this.currentResult.output_format || this.currentResult.format;
  }

  _getExtension(filename) {
    if (!filename || typeof filename !== 'string') {
      return null;
    }

    const parts = filename.split('.');
    return parts.length > 1 ? parts.pop() : null;
  }

  _getSizeText() {
    const totalBytes = this.currentItems.reduce((sum, item) => {
      const original = item?.original;
      if (!original) {
        return sum;
      }
      if (typeof original.size === 'number') {
        return sum + original.size;
      }
      if (typeof original.file_size === 'number') {
        return sum + original.file_size;
      }
      if (typeof original.filesize === 'number') {
        return sum + original.filesize;
      }
      return sum;
    }, 0);

    if (totalBytes > 0) {
      return this._formatBytes(totalBytes);
    }

    return `${this.currentItems.length} file${this.currentItems.length > 1 ? 's' : ''}`;
  }

  _formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  hideLegacyDownloadExperience() {
    const legacyButton = document.getElementById('downloadBtn');
    if (legacyButton) {
      legacyButton.hidden = true;
    }

    const batchContainer = document.getElementById('batchDownloads');
    if (batchContainer) {
      batchContainer.style.display = 'none';
    }

    if (this.downloadManager && typeof this.downloadManager.clear === 'function') {
      this.downloadManager.clear();
    }
  }

  showStage() {
    if (!this.stage) {
      return;
    }

    this.stage.hidden = false;
    if (this.blueprint) {
      this.blueprint.hidden = false;
    }
    requestAnimationFrame(() => this.stage.classList.add('is-visible'));
  }

  setStep(step) {
    if (!this.stepItems.length) {
      return;
    }

    this.stepItems.forEach((item) => {
      item.classList.remove('is-active');
      item.classList.remove('is-complete');
      item.classList.remove('download-screen__step--active');
    });

    const activeIndex = ['converting', 'preparing', 'ready'].indexOf(step);
    this.stepItems.forEach((item, index) => {
      const itemStep = item.dataset.step;
      if (index < activeIndex) {
        item.classList.add('is-complete');
      }
      if (itemStep === step) {
        item.classList.add('is-active');
        if (item.classList.contains('download-screen__step')) {
          item.classList.add('download-screen__step--active');
        }
      }
    });

    if (this.badgeEl) {
      if (step === 'converting') {
        this.badgeEl.textContent = 'Converting';
      } else if (step === 'preparing') {
        this.badgeEl.textContent = 'Preparing Download';
      } else {
        this.badgeEl.textContent = 'Download Experience';
      }
    }

    if (this.titleEl) {
      if (step === 'converting') {
        this.titleEl.textContent = 'Converting your files';
      } else if (step === 'preparing') {
        this.titleEl.textContent = 'Preparing Download';
      } else {
        this.titleEl.textContent = 'Download Experience';
      }
    }

    if (this.subtitleEl) {
      if (step === 'converting') {
        this.subtitleEl.textContent = 'The conversion sequence is now in progress and the next step will appear automatically.';
      } else if (step === 'preparing') {
        this.subtitleEl.textContent = 'The completed file is being prepared so the download experience can begin.';
      } else {
        this.subtitleEl.textContent = 'Your file is ready. The download experience is now available.';
      }
    }
  }

  handlePrimaryClick(event) {
    if (this.primaryButton.disabled) {
      return;
    }

    event.preventDefault();

    const items = Array.isArray(this.currentItems) ? this.currentItems : [];
    if (!items.length) {
      return;
    }

    const downloadItem = (item) => {
      if (!item || !item.download_path) {
        return;
      }

      if (this.downloadManager && typeof this.downloadManager._triggerDownload === 'function' && items.length === 1) {
        this.downloadManager._triggerDownload(item.download_path, item.filename || 'download');
        return;
      }

      const anchor = document.createElement('a');
      anchor.href = item.download_path;
      anchor.download = item.filename || '';
      anchor.rel = 'noopener noreferrer';
      anchor.style.display = 'none';
      document.body.appendChild(anchor);
      try {
        anchor.click();
      } catch (error) {
        console.warn('[DownloadAdapter] direct download click failed', error);
      }
      window.setTimeout(() => {
        if (anchor.parentNode) {
          anchor.remove();
        }
      }, 300);
    };

    if (items.length === 1) {
      downloadItem(items[0]);
      return;
    }

    items.forEach(downloadItem);
  }

  _clearTimers() {
    this.stepTimers.forEach((timer) => window.clearTimeout(timer));
    this.stepTimers = [];
  }

  _debug(message) {
    if (typeof console !== 'undefined' && typeof console.debug === 'function') {
      console.debug(`[DownloadAdapter] ${message}`);
    }
  }
}

window.DownloadAdapter = DownloadAdapter;

document.addEventListener('DOMContentLoaded', () => {
  const adapter = new DownloadAdapter();
  adapter.initialize();
  window.downloadAdapter = adapter;
});
