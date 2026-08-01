/* =========================================================
   CONVERIGO — Transition Controller
   Landing Page (State 1)  →  Workspace Mode (State 2)
   ========================================================= */

const body = document.body;
// Support both prototype IDs and main-app IDs
const dropzone = document.getElementById('dropzone') || document.getElementById('dropZone');
const workspace = document.getElementById('workspace') || document.querySelector('.workspace');
const uploadCard = document.getElementById('uploadCard') || document.querySelector('.upload-card');
const fileInput = document.getElementById('fileInput') || document.querySelector('input[type=file]');
const fileInputMore = document.getElementById('fileInputMore');
const btnPilihFile = document.getElementById('btnPilihFile') || document.getElementById('chooseFile');
const btnAddMore = document.getElementById('btnAddMore') || document.querySelector('.workspace-add-files');
const fileList = document.getElementById('fileList');
const fileListPanel = document.getElementById('fileListPanel');
const actionBar = document.getElementById('actionBar');
const fileCountEl = document.getElementById('fileCount');
const uploadToast = document.getElementById('uploadToast');
const uploadToastText = document.getElementById('uploadToastText');
const conversionResult = document.getElementById('conversionResult');
const resultList = document.getElementById('resultList');
const downloadBadge = document.getElementById('downloadBadge');
const downloadTitle = document.getElementById('downloadTitle');
const downloadSubtitle = document.getElementById('downloadSubtitle');
const downloadFileName = document.getElementById('downloadFileName');
const downloadFileMeta = document.getElementById('downloadFileMeta');
const btnDownloadMain = document.getElementById('btnDownloadMain');
const btnConvertAnother = document.getElementById('btnConvertAnother');
const btnRetryConversion = document.getElementById('btnRetryConversion');
const stepItems = Array.from(document.querySelectorAll('.step-item'));
const workspaceErrorState = document.getElementById('workspaceErrorState');
const workspaceErrorMessage = document.getElementById('workspaceErrorMessage');
const workspaceEmptyState = document.getElementById('workspaceEmptyState');
const btnEmptyAddFiles = document.getElementById('btnEmptyAddFiles');
const btnClearWorkspace = document.getElementById('btnClearWorkspace');
const downloadStage = document.getElementById('downloadStage');
const downloadWorkspaceScreen = document.getElementById('downloadWorkspaceScreen');

let hasEnteredWorkspace = false;
let allFiles = []; // {name, size}
let workspaceConversionResults = [];

if (btnPilihFile) {
  btnPilihFile.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    fileInput?.click();
  });
}

if (btnAddMore && fileInputMore) {
  btnAddMore.addEventListener('click', () => fileInputMore.click());
}

if (btnEmptyAddFiles && fileInputMore) {
  btnEmptyAddFiles.addEventListener('click', () => fileInputMore.click());
}

if (btnClearWorkspace) {
  btnClearWorkspace.addEventListener('click', () => {
    resetWorkspaceExperience();
  });
}

if (btnConvertAnother) {
  btnConvertAnother.addEventListener('click', () => {
    // hide download workspace and restore workspace screen
    hideDownloadStage();
    const btn = document.getElementById('btnConvert');
    if (btn) {
      btn.disabled = false;
      btn.style.opacity = '1';
    }
  });
}

if (fileInputMore) {
  fileInputMore.addEventListener('change', (e) => {
    const files = e.target.files;
    if (!files || !files.length) return;
    if (window.uploadManager && typeof window.uploadManager.handleFiles === 'function') {
      window.uploadManager.handleFiles(files);
    } else {
      handleFiles(files);
    }
    e.target.value = '';
  });
}

// When the main app UploadManager dispatches `file-selected`, enter workspace mode
window.addEventListener('file-selected', (e) => {
  const files = e?.detail?.files || (e?.detail?.file ? [e.detail.file] : []);
  if (files && files.length) {
    // Only trigger transition once per session
    if (!hasEnteredWorkspace) {
      enterWorkspaceMode(files);
    }
  }
});

window.addEventListener('workspace-files-updated', () => {
  syncWorkspaceExperience();
});

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function handleFiles(fileListInput) {
  const files = Array.from(fileListInput || []);
  if (!files.length) return;

  // If the main app already manages file rendering (fileListPanel exists), only trigger
  // the transition behavior and let UploadManager render rows.
  if (!hasEnteredWorkspace) {
    enterWorkspaceMode(files);
  } else {
    // If this is the prototype standalone file-list, append rows
    if (fileList && !fileListPanel) {
      appendFiles(files);
    }
  }
}

/* ---------------------------------------------------------
   TRANSITION SEQUENCE
   1. Ikon dekoratif fade + terbang keluar
   2. Hero mengecil, card melebar (morph)
   3. Dropzone hilang, workspace content fade in
   4. Baris file muncul satu-satu (staggered)
   5. Toast progres + action bar slide up
--------------------------------------------------------- */
function enterWorkspaceMode(files) {
  hasEnteredWorkspace = true;

  // Screen-based transition (Homepage -> Workspace)
  // 1) Animate homepage out (fade + slide left)
  // 2) After exit completes, hide homepage and unhide workspace
  // 3) Animate workspace in (fade + slide right)

  const exitMs = 320; // 250-350ms per spec
  try {
    const homepage = document.getElementById('homepageContent') || document.getElementById('homepage') || document.querySelector('.homepage-content') || document.querySelector('main') || document.body;
    const workspaceScreen = document.getElementById('workspaceScreen');

    // Animate homepage out if present and not already hidden
    if (homepage && !homepage.hidden) {
      // apply exit styles
      homepage.style.transition = `transform ${exitMs}ms ease, opacity ${exitMs}ms ease`;
      homepage.style.transform = 'translateX(-40px)';
      homepage.style.opacity = '0';

      // After animation, hide homepage and reveal workspace
      setTimeout(() => {
        try {
          homepage.hidden = true;
          // cleanup inline styles we added
          homepage.style.removeProperty('transform');
          homepage.style.removeProperty('opacity');
          homepage.style.removeProperty('transition');

          if (workspaceScreen) {
            // ensure workspace DOM is present and hidden state cleared
            workspaceScreen.hidden = false;
            // starting state for enter animation
            workspaceScreen.style.transform = 'translateX(40px)';
            workspaceScreen.style.opacity = '0';
            workspaceScreen.style.transition = `transform ${exitMs}ms ease, opacity ${exitMs}ms ease`;
            // trigger enter animation
            requestAnimationFrame(() => {
              workspaceScreen.style.transform = 'translateX(0)';
              workspaceScreen.style.opacity = '1';
            });

            // After workspace enter completes, cleanup inline styles and show workspace internals
            setTimeout(() => {
              try {
                workspaceScreen.style.removeProperty('transform');
                workspaceScreen.style.removeProperty('opacity');
                workspaceScreen.style.removeProperty('transition');

                // Reveal workspace inner container if present
                if (workspace) {
                  workspace.removeAttribute('hidden');
                }
                // Ensure file list panel (app-managed) is visible
                if (fileListPanel) {
                  fileListPanel.hidden = false;
                  fileListPanel.style.removeProperty('display');
                }

                // If app doesn't manage file list, render prototype rows
                if (!fileListPanel && fileList) {
                  renderFileRows(files, true);
                }

                syncWorkspaceExperience();
                // Reveal action bar after a short delay to match choreography
                setTimeout(() => revealActionBar(), 300);
              } catch (e) { console.warn('enterWorkspaceMode post-enter error', e); }
            }, exitMs + 40);
          } else {
            // No workspace screen found — fallback to original behavior
            if (dropzone) dropzone.setAttribute('hidden', '');
            if (workspace) workspace.removeAttribute('hidden');
            if (!fileListPanel && fileList) renderFileRows(files, true);
            syncWorkspaceExperience();
            setTimeout(() => revealActionBar(), 300);
          }
        } catch (e) {
          console.warn('enterWorkspaceMode hide homepage error', e);
        }
      }, exitMs);
    } else {
      // homepage not found or already hidden — just show workspace
      if (workspaceScreen) {
        workspaceScreen.hidden = false;
        requestAnimationFrame(() => workspaceScreen.classList.add('is-visible'));
      }
      if (workspace) workspace.removeAttribute('hidden');
      if (!fileListPanel && fileList) renderFileRows(files, true);
      syncWorkspaceExperience();
      setTimeout(() => revealActionBar(), 300);
    }
  } catch (e) {
    console.warn('enterWorkspaceMode error', e);
  }
}

function appendFiles(files) {
  renderFileRows(files, false);
}

function renderFileRows(files, isFirstBatch) {
  showToast(0, files.length);

  files.forEach((file, i) => {
    allFiles.push(file);

    const row = document.createElement('div');
    row.className = 'file-row';
    row.style.animationDelay = (i * 0.09) + 's';

    row.innerHTML = `
      <div class="file-info">
        <div class="file-name">${escapeHtml(file.name)}</div>
        <div class="file-size">${formatSize(file.size)}</div>
      </div>
      <div class="file-actions">
        <span class="output-label">Keluaran:</span>
        <div class="select-wrap slot-${i}"><div class="mini-spinner"></div></div>
        <button class="icon-btn" title="Pengaturan" type="button">
          <svg width="17" height="17" viewBox="0 0 17 17" fill="none"><path d="M8.5 10.6a2.1 2.1 0 1 0 0-4.2 2.1 2.1 0 0 0 0 4.2Z" stroke="currentColor" stroke-width="1.3"/><path d="M13.6 8.5c0 .3 0 .6-.07.9l1.2.9-1.1 1.9-1.4-.5c-.4.4-.9.7-1.4.9l-.2 1.5H8.4l-.2-1.5c-.5-.2-1-.5-1.4-.9l-1.4.5-1.1-1.9 1.2-.9a4 4 0 0 1 0-1.8l-1.2-.9 1.1-1.9 1.4.5c.4-.4.9-.7 1.4-.9l.2-1.5h1.9l.2 1.5c.5.2 1 .5 1.4.9l1.4-.5 1.1 1.9-1.2.9c.07.3.07.6.07.9Z" stroke="currentColor" stroke-width="1.1"/></svg>
        </button>
        <button class="icon-btn" title="Hapus" type="button">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M3 3l9 9M12 3l-9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
      </div>
    `;

    row.querySelector('.icon-btn[title="Hapus"]').addEventListener('click', () => {
      row.remove();
      updateFileCount(-1);
    });

    fileList.appendChild(row);

    // Simulasikan proses "membaca" file lalu tampilkan dropdown format
    const slot = row.querySelector(`.slot-${i}`);
    setTimeout(() => {
      slot.innerHTML = `
        <select class="output-select">
          <option>JPG</option>
          <option>PNG</option>
          <option>WEBP</option>
          <option>PDF</option>
        </select>`;
      updateFileCount(1);
      showToast(i + 1, files.length);

      if (i === files.length - 1) {
        setTimeout(() => {
          hideToast();
          revealActionBar();
        }, 350);
      }
    }, 500 + i * 220);
  });
}

function updateFileCount(delta) {
  const current = parseInt(fileCountEl.textContent, 10) || 0;
  fileCountEl.textContent = Math.max(0, current + delta);
}

function showToast(done, total) {
  uploadToast.removeAttribute('hidden');
  requestAnimationFrame(() => uploadToast.classList.add('is-visible'));
  uploadToastText.textContent = `Menambahkan ${done} dari ${total} file`;
}

function hideToast() {
  uploadToast.classList.remove('is-visible');
  setTimeout(() => uploadToast.setAttribute('hidden', ''), 250);
}

function revealActionBar() {
  if (!actionBar) return;
  actionBar.removeAttribute('hidden');
  requestAnimationFrame(() => actionBar.classList.add('is-visible'));
}

function hideActionBar() {
  if (!actionBar) return;
  actionBar.classList.remove('is-visible');
  actionBar.hidden = true;
}

function showConversionResult(results) {
  if (!conversionResult || !resultList) return;
  const items = Array.isArray(results) ? results : [results];
  conversionResult.hidden = false;
  conversionResult.classList.add('is-visible');
  resultList.innerHTML = '';

  if (!items.length) {
    const emptyItem = document.createElement('li');
    emptyItem.innerHTML = '<span class="result-name">No files were produced.</span><span class="result-meta">Try again</span>';
    resultList.appendChild(emptyItem);
    return;
  }

  items.forEach((item) => {
    const li = document.createElement('li');
    const filename = item?.filename || 'Converted file';
    const target = (item?.target_format || item?.output_format || '').toString().toUpperCase();
    li.innerHTML = `<span class="result-name">${escapeHtml(filename)}</span><span class="result-meta">${escapeHtml(target || 'READY')}</span>`;
    resultList.appendChild(li);
  });
}

function hideConversionResult() {
  if (!conversionResult || !resultList) return;
  conversionResult.classList.remove('is-visible');
  conversionResult.hidden = true;
  resultList.innerHTML = '';
}

function setDownloadExperienceState(state) {
  if (!downloadStage) return;

  // Prepare content values
  const firstResult = window.workspaceConversionResults?.[0];
  const displayName = firstResult?.filename || 'Berkas siap';
  const targetFormat = firstResult?.target_format || firstResult?.output_format || 'JPG';

  // Transition: hide the existing workspace first, then show the dedicated Download Workspace screen
  try {
    const workspaceScreen = document.getElementById('workspaceScreen');
    const workspaceExitMs = 320; // match requested 250-350ms
    if (workspaceScreen) {
      workspaceScreen.classList.add('leaving');
      // after the workspace exit animation completes, hide it and then reveal download workspace
      setTimeout(() => {
        workspaceScreen.hidden = true;
        workspaceScreen.classList.remove('leaving');

        // Now reveal the download workspace container (only after workspace hidden)
        if (downloadWorkspaceScreen) {
          downloadWorkspaceScreen.hidden = false;
          // ensure starting state (translateX(40px) opacity 0) is applied by CSS
          requestAnimationFrame(() => downloadWorkspaceScreen.classList.add('is-visible'));
        }
      }, workspaceExitMs);
    } else {
      // If no workspaceScreen element, show download immediately
      if (downloadWorkspaceScreen) {
        downloadWorkspaceScreen.hidden = false;
        requestAnimationFrame(() => downloadWorkspaceScreen.classList.add('is-visible'));
      }
    }
  } catch (e) {
    console.warn('download workspace transition error', e);
  }

  // Reveal stage content
  downloadStage.hidden = false;
  downloadStage.classList.add('is-visible');
  stepItems.forEach((item) => item.classList.remove('is-active', 'is-complete'));

  if (downloadBadge) downloadBadge.textContent = state === 'ready' ? 'Download Experience' : state === 'preparing' ? 'Preparing Download' : 'Converting';
  if (downloadTitle) downloadTitle.textContent = state === 'ready' ? 'Download Experience' : state === 'preparing' ? 'Preparing Download' : 'Converting your files';
  if (downloadSubtitle) downloadSubtitle.textContent = state === 'ready'
    ? 'Your file is ready. The download experience is now available.'
    : state === 'preparing'
      ? 'The completed file is being prepared so the download experience can begin.'
      : 'The conversion sequence is now in progress and the next step will appear automatically.';
  if (downloadFileName) downloadFileName.textContent = displayName;
  if (downloadFileMeta) downloadFileMeta.textContent = `${Math.max(1, window.workspaceConversionResults?.length || 1)} file • ${String(targetFormat).toUpperCase()}`;

  if (state === 'converting') {
    if (btnDownloadMain) {
      btnDownloadMain.disabled = true;
      btnDownloadMain.textContent = 'Download Sekarang';
    }
    stepItems[0]?.classList.add('is-active');
    return;
  }

  if (state === 'preparing') {
    if (btnDownloadMain) {
      btnDownloadMain.disabled = true;
      btnDownloadMain.textContent = 'Preparing…';
    }
    stepItems[0]?.classList.add('is-complete');
    stepItems[1]?.classList.add('is-active');
    return;
  }

  if (btnDownloadMain) {
    btnDownloadMain.disabled = false;
    btnDownloadMain.textContent = 'Download Sekarang';
  }
  stepItems[0]?.classList.add('is-complete');
  stepItems[1]?.classList.add('is-complete');
  stepItems[2]?.classList.add('is-active');
}

function hideDownloadStage() {
  if (!downloadStage) return;
  downloadStage.classList.remove('is-visible');
  downloadStage.hidden = true;
  // hide and slide back to workspace
  if (downloadWorkspaceScreen) {
    downloadWorkspaceScreen.classList.remove('is-visible');
    setTimeout(() => {
      downloadWorkspaceScreen.hidden = true;
      // restore workspace screen
      const workspaceScreen = document.getElementById('workspaceScreen');
      if (workspaceScreen) {
        workspaceScreen.hidden = false;
        workspaceScreen.classList.remove('leaving');
      }
    }, 420);
  }
}

function showWorkspaceError(message) {
  if (!workspaceErrorState) return;
  if (workspaceErrorMessage) {
    workspaceErrorMessage.textContent = message || 'Silakan coba lagi dalam beberapa saat.';
  }
  workspaceErrorState.hidden = false;
  workspaceErrorState.classList.add('is-visible');
  hideConversionResult();
  hideDownloadStage();
}

function hideWorkspaceError() {
  if (!workspaceErrorState) return;
  workspaceErrorState.classList.remove('is-visible');
  workspaceErrorState.hidden = true;
}

function setWorkspaceEmptyState(isEmpty) {
  if (!workspaceEmptyState) return;
  if (isEmpty) {
    workspaceEmptyState.hidden = false;
    workspaceEmptyState.classList.add('is-visible');
  } else {
    workspaceEmptyState.classList.remove('is-visible');
    workspaceEmptyState.hidden = true;
  }
}

function syncWorkspaceExperience() {
  const hasFiles = Boolean(window.uploadManager?.files?.length);
  if (!hasFiles) {
    hideActionBar();
    hideConversionResult();
    setWorkspaceEmptyState(true);
    return;
  }

  setWorkspaceEmptyState(false);
}

function resetWorkspaceExperience() {
  hideActionBar();
  hideConversionResult();
  hideWorkspaceError();
  if (downloadStage) {
    downloadStage.classList.remove('is-visible', 'is-preparing', 'is-ready');
    downloadStage.hidden = true;
  }
  if (window.downloadManager && typeof window.downloadManager.clear === 'function') {
    window.downloadManager.clear();
  }
  if (window.uploadManager && typeof window.uploadManager.resetUpload === 'function') {
    window.uploadManager.resetUpload();
  }
  setWorkspaceEmptyState(true);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getFileKey(file) {
  return `${file.name}|${file.size}|${file.lastModified}`;
}

function collectWorkspaceTargets() {
  const selects = Array.from(document.querySelectorAll('.file-output-select[data-file-key]'));
  const groups = new Map();
  selects.forEach((select) => {
    const key = select.dataset.fileKey;
    const target = select.value;
    if (!key || !target) return;
    if (!groups.has(target)) {
      groups.set(target, []);
    }
    groups.get(target).push(key);
  });
  return groups;
}

function getFilesByKeys(keys) {
  if (!window.uploadManager || !Array.isArray(window.uploadManager.files)) {
    return [];
  }
  return window.uploadManager.files.filter((file) => keys.includes(getFileKey(file)));
}

async function runWorkspaceConversion() {
  const btn = document.getElementById('btnConvert');
  if (!btn || !window.converter || typeof window.converter.convert !== 'function') {
    return;
  }

  const groups = collectWorkspaceTargets();
  if (!groups.size) {
    showWorkspaceError('Pilih setidaknya satu format target sebelum memulai konversi.');
    return;
  }

  hideWorkspaceError();
  btn.disabled = true;
  btn.classList.add('loading');
  const originalLabel = btn.textContent;
  btn.textContent = window.translate ? window.translate('upload.converting', 'Converting...') : 'Mengonversi…';
  window.workspaceMode = true;

  try {
    window.workspaceConversionResults = [];
    for (const [targetFormat, keys] of groups.entries()) {
      const files = getFilesByKeys(keys);
      if (!files.length) continue;

      window.converter.files = files;
      window.converter.file = files[0] || null;
      window.converter.selectedFormat = targetFormat;
      try {
        const response = await window.converter.convert();
        if (response) {
          if (Array.isArray(response.results)) {
            response.results.forEach((item) => {
              if (item.filename && item.download_path) {
                window.workspaceConversionResults = window.workspaceConversionResults || [];
                window.workspaceConversionResults.push(item);
              }
            });
          } else if (response.filename && response.download_path) {
            window.workspaceConversionResults = window.workspaceConversionResults || [];
            window.workspaceConversionResults.push(response);
          }
        }
      } catch (err) {
        console.warn('Workspace conversion batch failed', err);
        showWorkspaceError(err?.message || 'Konversi gagal. Silakan coba lagi.');
      }
    }
  } finally {
    window.workspaceMode = false;
    btn.disabled = false;
    btn.classList.remove('loading');
    btn.textContent = originalLabel;
  }

  if (window.workspaceConversionResults && window.workspaceConversionResults.length && window.downloadManager && typeof window.downloadManager.prepare === 'function') {
    hideWorkspaceError();
    showConversionResult(window.workspaceConversionResults);
    setDownloadExperienceState('converting');
    window.setTimeout(() => setDownloadExperienceState('preparing'), 900);
    window.setTimeout(() => setDownloadExperienceState('ready'), 1800);
    const result = {
      results: window.workspaceConversionResults,
      total: window.workspaceConversionResults.length,
      successful: window.workspaceConversionResults.length,
      target_format: window.converter?.selectedFormat || Array.from(groups.keys())[0] || window.workspaceConversionResults[0]?.filename?.split('.').pop(),
    };
    window.downloadManager.setProcessingDuration(0);
    window.downloadManager.prepare(result);
  } else {
    showWorkspaceError('Konversi tidak menghasilkan file yang dapat diunduh.');
  }
}

const workspaceConvertButton = document.getElementById('btnConvert');
if (workspaceConvertButton) {
  workspaceConvertButton.addEventListener('click', (event) => {
    event.preventDefault();
    runWorkspaceConversion();
  });
}

const workspaceConvertAnother = document.getElementById('btnConvertAnother');
if (workspaceConvertAnother) {
  workspaceConvertAnother.addEventListener('click', (event) => {
    event.preventDefault();
    window.workspaceConversionResults = [];
    if (workspaceConvertButton) {
      workspaceConvertButton.disabled = false;
      workspaceConvertButton.classList.remove('loading');
    }
    hideDownloadStage();
    hideConversionResult();
    resetWorkspaceExperience();
  });
}

if (btnRetryConversion) {
  btnRetryConversion.addEventListener('click', (event) => {
    event.preventDefault();
    runWorkspaceConversion();
  });
}
