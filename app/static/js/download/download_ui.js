class DownloadUI {
  constructor(containerSelector = '#downloadScreenBlueprint') {
    this.containerSelector = containerSelector;
    this.container = null;
    this.payload = null;
    this.enabled = Boolean(window.ConverigoFlags && window.ConverigoFlags.ENABLE_DOWNLOAD_V2);
  }

  mount() {
    if (!this.enabled) {
      return;
    }

    this.container = document.querySelector(this.containerSelector);
    if (!this.container) {
      return;
    }

    this.container.hidden = true;
  }

  render() {
    if (!this.enabled || !this.container) {
      return;
    }

    const filenameEl = this.container.querySelector('#downloadSummaryFilename');
    const formatEl = this.container.querySelector('#downloadSummaryFormat');
    const sizeEl = this.container.querySelector('#downloadSummarySize');
    const statusEl = this.container.querySelector('#downloadSummaryStatus');

    if (filenameEl) {
      filenameEl.textContent = this.payload?.filename || 'example-file.pdf';
    }
    if (formatEl) {
      formatEl.textContent = this.payload?.format || 'PDF';
    }
    if (sizeEl) {
      sizeEl.textContent = this.payload?.size || '2.4 MB';
    }
    if (statusEl) {
      statusEl.textContent = this.payload?.status || 'Ready to download';
    }
  }

  show() {
    if (!this.enabled || !this.container) {
      return;
    }

    this.container.hidden = false;
  }

  update(payload = {}) {
    if (!this.enabled) {
      return;
    }

    this.payload = payload;
    this.render();
  }

  hide() {
    if (!this.enabled || !this.container) {
      return;
    }

    this.container.hidden = true;
  }

  destroy() {
    if (!this.enabled) {
      return;
    }

    this.payload = null;
    if (this.container) {
      this.container.hidden = true;
      this.container = null;
    }
  }
}

window.DownloadUI = DownloadUI;
