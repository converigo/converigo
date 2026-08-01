/* =========================================================
   CONVERIGO — Transition Controller
   Landing Page (State 1)  →  Workspace Mode (State 2)
   ========================================================= */

const body = document.body;
const dropzone = document.getElementById('dropzone');
const workspace = document.getElementById('workspace');
const uploadCard = document.getElementById('uploadCard');
const fileInput = document.getElementById('fileInput');
const fileInputMore = document.getElementById('fileInputMore');
const btnPilihFile = document.getElementById('btnPilihFile');
const btnAddMore = document.getElementById('btnAddMore');
const fileList = document.getElementById('fileList');
const actionBar = document.getElementById('actionBar');
const fileCountEl = document.getElementById('fileCount');
const uploadToast = document.getElementById('uploadToast');
const uploadToastText = document.getElementById('uploadToastText');
const conversionResult = document.getElementById('conversionResult');
const resultList = document.getElementById('resultList');
const downloadStage = document.getElementById('downloadStage');
const downloadBadge = document.getElementById('downloadBadge');
const downloadTitle = document.getElementById('downloadTitle');
const downloadSubtitle = document.getElementById('downloadSubtitle');
const downloadFileName = document.getElementById('downloadFileName');
const downloadFileMeta = document.getElementById('downloadFileMeta');
const btnDownloadMain = document.getElementById('btnDownloadMain');
const btnConvertAnother = document.getElementById('btnConvertAnother');
const stepItems = Array.from(document.querySelectorAll('.step-item'));

let hasEnteredWorkspace = false;
let allFiles = []; // {name, size}

btnPilihFile.addEventListener('click', () => fileInput.click());
btnAddMore.addEventListener('click', () => fileInputMore.click());

fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
fileInputMore.addEventListener('change', (e) => handleFiles(e.target.files));

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function handleFiles(fileListInput) {
  const files = Array.from(fileListInput || []);
  if (!files.length) return;

  if (!hasEnteredWorkspace) {
    enterWorkspaceMode(files);
  } else {
    appendFiles(files);
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

  // Step 1 + 2: trigger morph (CSS transition via class)
  body.classList.add('workspace-mode');

  // Step 3: after the card morph settles, replace the dropzone with the workspace
  const cardTransitionMs = 720;
  setTimeout(() => {
    dropzone.setAttribute('hidden', '');
    workspace.removeAttribute('hidden');
    renderFileRows(files, true);
  }, cardTransitionMs * 0.72);
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
    row.style.animationDelay = (i * 0.08) + 's';

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
        }, 420);
      }
    }, 650 + i * 180);
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
  actionBar.removeAttribute('hidden');
  requestAnimationFrame(() => actionBar.classList.add('is-visible'));
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderConversionResult() {
  const rows = Array.from(document.querySelectorAll('.file-row'));
  conversionResult.hidden = false;

  if (!rows.length) {
    resultList.innerHTML = '<li class="result-empty">Belum ada berkas yang dipilih.</li>';
    return;
  }

  const items = rows.map((row, index) => {
    const name = row.querySelector('.file-name')?.textContent || `Berkas ${index + 1}`;
    const select = row.querySelector('.output-select');
    const format = select ? select.value : 'JPG';
    return `<li><span>${escapeHtml(name)}</span><strong>→ ${escapeHtml(format)}</strong></li>`;
  });

  resultList.innerHTML = items.join('');
}

function updateDownloadPreview() {
  const row = document.querySelector('.file-row');
  const selectedFormat = document.querySelector('.output-select')?.value || 'JPG';
  const primaryName = allFiles[0]?.name || row?.querySelector('.file-name')?.textContent || 'Berkas siap';
  downloadFileName.textContent = primaryName;
  downloadFileMeta.textContent = `${Math.max(1, allFiles.length || 1)} file • ${selectedFormat}`;
}

function setDownloadState(state) {
  updateDownloadPreview();
  conversionResult.hidden = true;
  downloadStage.hidden = false;
  requestAnimationFrame(() => downloadStage.classList.add('is-visible'));

  stepItems.forEach((item) => item.classList.remove('is-active', 'is-complete'));

  if (state === 'converting') {
    downloadBadge.textContent = 'Converting';
    downloadTitle.textContent = 'Converting your files';
    downloadSubtitle.textContent = 'The conversion sequence is now in progress and the next step will appear automatically.';
    stepItems[0].classList.add('is-active');
    btnDownloadMain.disabled = true;
    btnDownloadMain.textContent = 'Download';
    return;
  }

  if (state === 'preparing') {
    downloadBadge.textContent = 'Preparing Download';
    downloadTitle.textContent = 'Preparing Download';
    downloadSubtitle.textContent = 'The completed file is being prepared so the download experience can begin.';
    stepItems[0].classList.add('is-complete');
    stepItems[1].classList.add('is-active');
    btnDownloadMain.disabled = true;
    btnDownloadMain.textContent = 'Preparing…';
    return;
  }

  downloadBadge.textContent = 'Download Experience';
  downloadTitle.textContent = 'Download Experience';
  downloadSubtitle.textContent = 'Your file is ready. The download experience is now available.';
  stepItems[0].classList.add('is-complete');
  stepItems[1].classList.add('is-complete');
  stepItems[2].classList.add('is-active');
  btnDownloadMain.disabled = false;
  btnDownloadMain.textContent = 'Download';
}

function resetDownloadExperience() {
  downloadStage.classList.remove('is-visible');
  setTimeout(() => {
    downloadStage.hidden = true;
  }, 220);
  btnDownloadMain.disabled = true;
  btnDownloadMain.textContent = 'Download Sekarang';
  stepItems.forEach((item) => item.classList.remove('is-active', 'is-complete'));
  stepItems[0].classList.add('is-active');
}

/* Tombol "Mengubah" — di prototipe ini hanya simulasi visual */
document.getElementById('btnConvert').addEventListener('click', () => {
  const btn = document.getElementById('btnConvert');
  const original = btn.innerHTML;
  btn.innerHTML = 'Converting…';
  btn.style.opacity = '.75';
  btn.disabled = true;
  renderConversionResult();
  setDownloadState('converting');

  setTimeout(() => {
    setDownloadState('preparing');
  }, 1100);

  setTimeout(() => {
    setDownloadState('ready');
    btn.innerHTML = original;
    btn.style.opacity = '1';
    btn.disabled = false;
  }, 2200);
});

btnDownloadMain.addEventListener('click', () => {
  btnDownloadMain.disabled = true;
  btnDownloadMain.textContent = 'Downloading…';
  downloadBadge.textContent = 'Download in progress';
  downloadTitle.textContent = 'Download in progress';
  downloadSubtitle.textContent = 'The file download is now being initiated.';

  setTimeout(() => {
    btnDownloadMain.disabled = false;
    btnDownloadMain.textContent = 'Download';
    downloadBadge.textContent = 'Download Experience';
    downloadTitle.textContent = 'Download Experience';
    downloadSubtitle.textContent = 'Your file is ready. The download experience is now available.';
  }, 900);
});

btnConvertAnother.addEventListener('click', () => {
  resetDownloadExperience();
  document.getElementById('btnConvert').disabled = false;
  document.getElementById('btnConvert').innerHTML = 'Mengubah <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10m0 0-4-4m4 4-4 4" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  document.getElementById('btnConvert').style.opacity = '1';
});
