/* Converigo Tool-Page Result Widget V2 (Option A) — self-contained, namespace "tv2-".
   Pilot scope: /tools/tar-extract only.
   CORE logic ported from app/static/js/widgets/result_widget_v2.js (homepage widget,
   left untouched). Removed: morph badge, orbit field, marquee (buildOrbit/buildMarquee),
   body.has-jobs global class, #toastHost dependency, JSZip download-all.
   Every DOM reference is guarded. Wrapped in an IIFE with an early return so loading
   this file on any page without the component is a no-op.
   Endpoint contract (Step 0): POST /convert with target_format="tar" + operation="tar-extract". */
(function () {
  'use strict';

  var root = document.getElementById('tv2-root');
  if (!root) return; // component not present — do nothing

  var CONFIG = {
    operation: (root.dataset.operation || '').trim().toLowerCase(),
    targetFormat: (root.dataset.targetFormat || '').trim().toLowerCase()
  };

  var CATEGORY = {
    image:    {color:'#5B4FE9', exts:['jpg','jpeg','png','webp','gif','svg','bmp','tiff','heic']},
    document: {color:'#FF6B4A', exts:['pdf','docx','doc','txt','pptx','ppt','xlsx','xls','csv','html','md','rtf']},
    audio:    {color:'#12B3A0', exts:['mp3','wav','ogg','flac','m4a','aac']},
    video:    {color:'#F59E0B', exts:['mp4','mov','avi','webm','mkv','flv']},
    archive:  {color:'#6C7599', exts:['zip','rar','7z','tar','gz']},
    other:    {color:'#9333EA', exts:[]}
  };

  /* D5: the capability map is injected by the server as data-target-map on this
     mount element (components/tool_result_widget_v2.html, fed by
     app/routers/tools.py from app/services/target_capability.py). The widget used
     to carry its own copy of the homepage map and that copy had drifted: it still
     offered pdf -> WORD (a placeholder-backed pair), kept .doc/.xls/.ppt source
     rows PR-1 had honestly disabled, and was missing rows the homepage had. There
     is now exactly one source of truth. An absent or unparseable payload yields
     "no advertised targets" - never a fallback literal, because a silently stale
     map is the failure mode D5 exists to remove. */
  var STATIC_TARGET_MAP = (function () {
    var raw = (root.dataset.targetMap || '').trim();
    if (!raw) return {};
    try {
      var parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (err) {
      return {};
    }
  })();

  function getValidTargets(ext){
    return STATIC_TARGET_MAP[(ext || '').toLowerCase()] || [];
  }
  function categoryOf(ext){
    ext = (ext || '').toLowerCase();
    for (var key in CATEGORY){
      if (CATEGORY[key].exts.indexOf(ext) !== -1) return key;
    }
    return 'other';
  }

  var jobs = [];
  var uid = 0;

  function splitName(filename){
    var idx = filename.lastIndexOf('.');
    if (idx <= 0) return {base:filename, ext:''};
    return {base:filename.slice(0, idx), ext:filename.slice(idx + 1)};
  }
  function fmtSize(bytes){
    if (bytes < 1024) return bytes + ' B';
    var kb = bytes / 1024;
    if (kb < 1024) return kb.toFixed(2) + ' KB';
    return (kb / 1024).toFixed(2) + ' MB';
  }
  function esc(s){
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function t(key, fallback){
    try { return (window.translate ? window.translate(key, fallback) : fallback) || fallback; }
    catch (e) { return fallback; }
  }
  function toast(msg, icon){
    var host = document.getElementById('tv2-toastHost');
    if (!host){ try { console.log('[tv2]', msg); } catch (e) {} return; }
    var el = document.createElement('div');
    el.className = 'tv2-toast';
    el.textContent = (icon || '✔️') + ' ' + msg;
    host.appendChild(el);
    setTimeout(function(){ try { el.remove(); } catch (e) {} }, 2700);
  }
  function setHasJobs(flag){
    /* component-local state class only; never touches document.body */
    root.classList.toggle('tv2-has-jobs', !!flag);
  }

  function addFiles(fileList){
    var files = Array.prototype.slice.call(fileList || [], 0, 50);
    if (!files.length) return;
    files.forEach(function(file){
      var parts = splitName(file.name);
      var ext = parts.ext;
      var cat = categoryOf(ext);
      var targets = getValidTargets(ext);
      var target = targets.filter(function(x){ return x.toLowerCase() !== ext.toLowerCase(); })[0] || targets[0];
      if (CONFIG.targetFormat) target = CONFIG.targetFormat.toUpperCase();
      jobs.push({
        id: 'tv2j' + (uid++),
        file: file, name: file.name, size: file.size, ext: (ext.toUpperCase() || 'FILE'),
        category: cat, target: target, status: 'pending', progress: 0, quality: 80
      });
    });
    setHasJobs(jobs.length > 0);
    render();
    toast(files.length + ' file ditambahkan');
  }
  function badgeStyle(cat){
    var c = (CATEGORY[cat] || CATEGORY.other).color;
    return 'background:' + c + ';';
  }

  function rowTemplate(job){
    var validTargets = getValidTargets(job.ext);
    var rightHTML = '';

    if (job.status === 'pending'){
      rightHTML = (validTargets.length
        ? '<select class="tv2-fmt" data-action="target" data-id="' + job.id + '">' +
            validTargets.map(function(x){
              return '<option value="' + x + '"' + (x === job.target ? ' selected' : '') + '>' + x + '</option>';
            }).join('') +
          '</select>'
        : '<span class="tv2-no-converter" title="Tidak ada converter untuk format ini">— Tidak ada converter</span>') +
        '<button class="tv2-icon-btn danger" data-action="remove" data-id="' + job.id + '" title="Hapus" aria-label="Hapus">✖</button>';
    } else if (job.status === 'processing' || job.status === 'converting'){
      rightHTML = '<div class="tv2-converting-pill"><span class="tv2-spin"></span>Mengekstrak…</div>' +
        '<button class="tv2-icon-btn danger" data-action="remove" data-id="' + job.id + '" title="Hapus" aria-label="Hapus">✖</button>';
    } else if (job.status === 'error'){
      rightHTML = '<div class="tv2-status-pill tv2-status-pill-error">❌ Gagal</div>' +
        '<div class="tv2-row-error">' + esc(job.errorMessage || 'Konversi gagal') + '</div>' +
        '<button class="tv2-retry-btn" data-action="retry" data-id="' + job.id + '" type="button">↻ Coba lagi</button>' +
        '<button class="tv2-icon-btn danger" data-action="remove" data-id="' + job.id + '" title="Hapus" aria-label="Hapus">✖</button>';
    } else {
      rightHTML = '<div class="tv2-status-pill">✔️ Selesai</div>' +
        '<div class="tv2-dl-split"><button class="tv2-dl-main" data-action="download" data-id="' + job.id + '">⬇️ Unduh</button></div>' +
        '<button class="tv2-icon-btn danger" data-action="remove" data-id="' + job.id + '" title="Hapus" aria-label="Hapus">✖</button>';
    }

    var progressHTML = (job.status === 'converting' || job.status === 'processing')
      ? '<div class="tv2-progress-track"><div class="tv2-progress-fill" id="tv2-fill-' + job.id + '"></div></div>'
      : '';

    return '<div class="tv2-row" data-row="' + job.id + '">' +
      '<div class="tv2-badge" style="' + badgeStyle(job.category) + '">' + job.ext.slice(0, 4) + '</div>' +
      '<div class="tv2-row-info">' +
        '<div class="tv2-row-name">' + esc(job.name) + '</div>' +
        '<div class="tv2-row-meta">' +
          '<span>' + fmtSize(job.size) + '</span>' +
          '<span class="tv2-arrow-tag">' + job.ext + ' → <b>' + (job.target || 'TAR') + '</b></span>' +
        '</div>' +
      '</div>' +
      '<div class="tv2-row-controls">' + rightHTML + '</div>' +
      progressHTML +
    '</div>';
  }
  function render(){
    var rowsEl = document.getElementById('tv2-rows');
    if (rowsEl) rowsEl.innerHTML = jobs.map(rowTemplate).join('');

    var allDone = jobs.length > 0 && jobs.every(function(j){ return j.status === 'done' || j.status === 'error'; });
    var pending = jobs.filter(function(j){ return j.status === 'pending'; });

    var footerPre = document.getElementById('tv2-footerPre');
    if (footerPre) footerPre.style.display = allDone ? 'none' : 'flex';
    var footerPost = document.getElementById('tv2-footerPost');
    if (footerPost) footerPost.classList.toggle('show', allDone);

    var pendingCountEl = document.getElementById('tv2-pendingCount');
    if (pendingCountEl) pendingCountEl.textContent = pending.length;

    var goBtn = document.getElementById('tv2-goBtn');
    if (goBtn) goBtn.disabled = pending.length === 0 || jobs.some(function(j){ return j.status === 'converting' || j.status === 'processing'; });

    jobs.filter(function(j){ return j.status === 'converting' || j.status === 'processing'; }).forEach(function(j){
      var fill = document.getElementById('tv2-fill-' + j.id);
      if (fill){
        requestAnimationFrame(function(){
          fill.style.transitionDuration = (j._duration || 900) + 'ms';
          fill.style.width = '100%';
        });
      }
    });

    buildGlobalFmt();
  }
  function buildGlobalFmt(){
    var sel = document.getElementById('tv2-globalFmt');
    var label = document.getElementById('tv2-footerLabel');
    if (!sel) return;
    var pending = jobs.filter(function(j){ return j.status !== 'done'; });
    var pendingTargets = pending.map(function(j){ return j.target; }).filter(function(v, i, a){ return a.indexOf(v) === i; });
    var sameTarget = pending.length > 0 && pendingTargets.length === 1;

    if (sameTarget){
      /* D5: options are always the intersection of what each pending row can
         really reach. The cross-category branch used to substitute a hardcoded
         six-format guess that was valid for none of the rows in a mixed batch,
         so picking it turned one upload set into N doomed requests. */
      var opts = pending.map(function(j){ return getValidTargets(j.ext); })
        .reduce(function(a, b){ return a.filter(function(x){ return b.indexOf(x) !== -1; }); }, getValidTargets(pending[0].ext));
      var current = sel.value;
      sel.innerHTML = opts.map(function(x){ return '<option value="' + x + '">' + x + '</option>'; }).join('');
      if (opts.indexOf(current) !== -1){
        sel.value = current;
      } else if (opts.length){
        var sourceFormats = pending.map(function(j){ return String(j.ext || '').toLowerCase().replace(/^\./, ''); });
        sel.value = opts.filter(function(o){ return sourceFormats.indexOf(o.toLowerCase()) === -1; })[0] || opts[0];
      }
      if (label) label.innerHTML = t('upload.conversion_instruction', 'Ekstrak semua file ke:') + ' (<span id="tv2-pendingCount">' + pending.length + '</span>)';
      sel.style.display = '';
    } else {
      sel.innerHTML = '';
      sel.style.display = 'none';
      if (label) label.innerHTML = t('upload.conversion_instruction', 'Ekstrak semua file ke:') + ' (<span id="tv2-pendingCount">' + pending.length + '</span>)';
    }
  }
  function conversionErrorMessage(data, response){
    if (data){
      if (typeof data === 'string') return data;
      if (Array.isArray(data.detail)){
        return data.detail.map(function(item){ return typeof item === 'string' ? item : (item.msg || JSON.stringify(item)); }).join('; ');
      }
      if (typeof data.detail === 'string') return data.detail;
      if (typeof data.message === 'string') return data.message;
      if (typeof data.error === 'string') return data.error;
      if (typeof data.code === 'string') return data.code;
    }
    return (response && response.statusText) || ('HTTP ' + (response ? response.status : '?'));
  }

  function conversionDownloadPath(data){
    if (!data || typeof data !== 'object') return '';
    if (typeof data.download_path === 'string' && data.download_path) return data.download_path;
    if (Array.isArray(data.results)){
      var found = data.results.filter(function(item){ return item && typeof item.download_path === 'string' && item.download_path; })[0];
      return found ? found.download_path : '';
    }
    return '';
  }

  async function convertJob(job, targetFormat){
    var formData = new FormData();
    formData.append('file', job.file);
    formData.append('target_format', (CONFIG.targetFormat || targetFormat || '').toLowerCase());
    if (CONFIG.operation) formData.append('operation', CONFIG.operation);

    try {
      var response = await fetch('/convert', { method: 'POST', body: formData });
      var data = await response.json().catch(function(){ return null; });
      if (!response.ok){
        throw new Error(conversionErrorMessage(data, response));
      }
      var downloadPath = conversionDownloadPath(data);
      if (!downloadPath){
        throw new Error('Conversion response did not include download_path');
      }
      job.downloadPath = downloadPath;
      job.status = 'done';
      job.errorMessage = '';
    } catch (error) {
      job.status = 'error';
      job.errorMessage = (error && error.message) ? error.message : String(error);
      job.downloadPath = '';
    }
    render();
  }

  function convertAll(){
    var pending = jobs.filter(function(j){ return j.status === 'pending'; });
    if (!pending.length) return;

    var globalFormat = document.getElementById('tv2-globalFmt');
    var requests = pending.map(function(job){
      var row = document.querySelector('[data-row="' + job.id + '"]');
      var rowSelect = row ? row.querySelector('select.tv2-fmt') : null;
      var rowFormat = rowSelect ? rowSelect.value : job.target;
      var targetFormat = (globalFormat && globalFormat.offsetParent !== null && globalFormat.value)
        ? globalFormat.value
        : (rowFormat || job.target || CONFIG.targetFormat);

      job.target = targetFormat || job.target;
      job.status = 'processing';
      job._duration = 900;
      return {job: job, targetFormat: targetFormat};
    });

    render();
    requests.forEach(function(req){ convertJob(req.job, req.targetFormat); });
  }
  function convertedBlobName(job){
    var parts = splitName(job.name);
    var ext = (CONFIG.targetFormat || job.target || 'tar').toLowerCase();
    return parts.base + '.' + ext;
  }
  async function downloadJob(job){
    if (!job || !job.downloadPath) return;
    try {
      var response = await fetch(job.downloadPath);
      if (!response.ok){ toast('Unduhan gagal', '❌'); return; }
      var blob = await response.blob();
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = convertedBlobName(job);
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function(){ try { URL.revokeObjectURL(url); } catch (e) {} }, 4000);
      toast('Mengunduh ' + convertedBlobName(job));
    } catch (error) {
      toast('Unduhan gagal', '❌');
    }
  }

  /* Download-all: NO JSZip dependency. Each finished file is downloaded
     individually (sequential). Rationale: avoids the homepage-only JSZip CDN
     include and keeps this tool-page component fully self-contained. */
  async function downloadAll(){
    var done = jobs.filter(function(j){ return j.status === 'done'; });
    if (!done.length) return;
    for (var i = 0; i < done.length; i++){
      await downloadJob(done[i]);
    }
  }

  function resetAll(){
    jobs = [];
    setHasJobs(false);
    render();
  }
  var rowsEl = document.getElementById('tv2-rows');
  if (rowsEl){
    rowsEl.addEventListener('click', function(e){
      var btn = e.target.closest('[data-action]');
      if (!btn) return;
      var id = btn.dataset.id;
      var job = null;
      for (var i = 0; i < jobs.length; i++){ if (jobs[i].id === id){ job = jobs[i]; break; } }
      if (!job) return;
      var action = btn.dataset.action;

      if (action === 'remove'){
        jobs = jobs.filter(function(j){ return j.id !== id; });
        if (!jobs.length) setHasJobs(false);
        render();
      } else if (action === 'download'){
        downloadJob(job);
      } else if (action === 'retry'){
        job.status = 'processing';
        job.errorMessage = '';
        job.downloadPath = '';
        job._duration = 900;
        render();
        convertJob(job, job.target);
      }
    });
    rowsEl.addEventListener('change', function(e){
      var el = e.target.closest('[data-action]');
      if (!el) return;
      var job = null;
      for (var i = 0; i < jobs.length; i++){ if (jobs[i].id === el.dataset.id){ job = jobs[i]; break; } }
      if (!job) return;
      if (el.dataset.action === 'target'){ job.target = el.value; render(); }
    });
  }

  var goBtn = document.getElementById('tv2-goBtn');
  if (goBtn) goBtn.addEventListener('click', convertAll);
  var newBtn = document.getElementById('tv2-newBtn');
  if (newBtn) newBtn.addEventListener('click', resetAll);
  var dlAllBtn = document.getElementById('tv2-dlAllBtn');
  if (dlAllBtn) dlAllBtn.addEventListener('click', downloadAll);

  var fileInput = document.getElementById('tv2-fileInput');
  var browseBtn = document.getElementById('tv2-browseBtn');
  if (browseBtn && fileInput) browseBtn.addEventListener('click', function(e){ e.stopPropagation(); fileInput.click(); });
  var addMoreBtn = document.getElementById('tv2-addMoreBtn');
  if (addMoreBtn && fileInput) addMoreBtn.addEventListener('click', function(){ fileInput.click(); });
  if (fileInput) fileInput.addEventListener('change', function(e){ addFiles(e.target.files); fileInput.value = ''; });

  var dz = document.getElementById('tv2-dropzone');
  if (dz){
    dz.addEventListener('click', function(){ if (fileInput) fileInput.click(); });
    dz.addEventListener('keydown', function(e){
      if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); if (fileInput) fileInput.click(); }
    });
    ['dragenter','dragover'].forEach(function(evt){
      dz.addEventListener(evt, function(e){ e.preventDefault(); dz.classList.add('drag'); });
    });
    ['dragleave','drop'].forEach(function(evt){
      dz.addEventListener(evt, function(e){ e.preventDefault(); dz.classList.remove('drag'); });
    });
    dz.addEventListener('drop', function(e){
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
    });
  }

  render();
})();