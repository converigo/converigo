/* Converigo canonical result widget (V2) - extracted verbatim from main/converigo_main.html (F2). Loaded only when feature flag result_widget_v2 is enabled. */
/* ---------------- data model ---------------- */
const CATEGORY = {
  image:    {color:'#5B4FE9', light:'#ECE9FF', targets:['JPG','PNG','WEBP','GIF','SVG','BMP'], exts:['jpg','jpeg','png','webp','gif','svg','bmp','tiff','heic']},
  document: {color:'#FF6B4A', light:'#FFE9E2', targets:['PDF','DOCX','TXT','PPTX','XLSX','CSV','HTML'], exts:['pdf','docx','doc','txt','pptx','ppt','xlsx','xls','csv','html','md','rtf']},
  audio:    {color:'#12B3A0', light:'#DEF7F3', targets:['MP3','WAV','OGG','FLAC','M4A'], exts:['mp3','wav','ogg','flac','m4a','aac']},
  video:    {color:'#F59E0B', light:'#FEF3DA', targets:['MP4','MOV','WEBM','MKV','GIF'], exts:['mp4','mov','avi','webm','mkv','flv']},
  archive:  {color:'#6C7599', light:'#E8EAF3', targets:['ZIP','RAR','7Z','TAR'], exts:['zip','rar','7z','tar','gz']},
  other:    {color:'#9333EA', light:'#F3E8FF', targets:['PDF','JPG','PNG','TXT','ZIP'], exts:[]}
};

/* ---------------- static source-to-targets map (P1a) ---------------- */
/* Dihasilkan dari registry dump aktual per source-format.
   Self-conversions (source===target) dihapus karena tidak berguna
   sebagai opsi konversi di dropdown.
   Fallback: array kosong → "tidak ada converter". */
const STATIC_TARGET_MAP = {
  // image sources
  jpg:['ICO','PDF','PNG','TIFF','WEBP'],  jpeg:['ICO','PDF','PNG','TIFF','WEBP'],
  png:['BMP','ICO','JPEG','JPG','PDF','TIFF','WEBP'],  webp:['ICO','JPEG','JPG','PNG','TIFF'],  // Batch 2: png +PDF via png-to-pdf
  bmp:['JPEG','JPG','PNG','WEBP'],  tiff:['JPEG','JPG','PNG'],
  svg:['PNG'],  heic:['JPEG','JPG'],  heif:['JPEG','JPG'],  avif:['JPEG','JPG'],
  gif:[],  // tidak ada registered converter
  // document sources
  pdf:['DOC','DOCX','JPEG','JPG','ODT','PNG','PPT','PPTX','WORD','XLS','XLSX'],  // Batch 2: +PNG via pdf-to-png
  docx:['JPEG','JPG','PDF','POWERPOINT','PPT','PPTX','SPREADSHEET','XLS','XLSX'],
  doc:['JPEG','JPG','PDF','POWERPOINT','PPT','PPTX','SPREADSHEET','XLS','XLSX'],
  pptx:['DOC','DOCX','JPEG','JPG','PDF','SPREADSHEET','WORD','XLS','XLSX'],
  ppt:['DOC','DOCX','JPEG','JPG','PDF','SPREADSHEET','WORD','XLS','XLSX'],
  xlsx:['CSV','DOC','DOCX','HTML','JSON','ODS','PDF','POWERPOINT','PPT','PPTX','WORD'],
  xls:['DOC','DOCX','PDF','POWERPOINT','PPT','PPTX','WORD','XLSX'],
  txt:['PDF'],  csv:['JSON','PDF','XLSX'],  json:['CSV','XLSX'],  ods:['XLSX'],  odt:['PDF'],
  powerpoint:['DOC','DOCX','JPEG','JPG','SPREADSHEET','WORD','XLS','XLSX'],
  spreadsheet:['DOC','DOCX','POWERPOINT','PPT','PPTX','WORD'],
  word:['JPEG','JPG','PDF','POWERPOINT','PPT','PPTX','SPREADSHEET','XLS','XLSX'],
  html:[],  md:[],  rtf:[],  // tidak ada registered converter
  // audio sources
  mp3:['WAV'],  wav:['MP3'],  ogg:[],  flac:['MP3'],  m4a:['MP3'],  aac:['MP3'],
  // video sources
  mp4:['AAC','FLAC','GIF','M4A','MP3','OGG','WAV'],  mov:[],  avi:[],  webm:[],  mkv:[],  flv:[],
  // archive sources (self-conversions dihapus — hanya extract operation)
  gz:['GZIP'],  gzip:['GZ'],  zip:[],  '7z':[],  rar:[],  tar:[],
};

function getValidTargets(ext){
  return STATIC_TARGET_MAP[(ext||'').toLowerCase()] || [];
}

function categoryOf(ext){
  ext = (ext||'').toLowerCase();
  for(const key in CATEGORY){
    if(CATEGORY[key].exts.includes(ext)) return key;
  }
  return 'other';
}

let jobs = [];
let uid = 0;

/* ---------------- helpers ---------------- */
function splitName(filename){
  const idx = filename.lastIndexOf('.');
  if(idx <= 0) return {base:filename, ext:''};
  return {base:filename.slice(0,idx), ext:filename.slice(idx+1)};
}
function fmtSize(bytes){
  if(bytes < 1024) return bytes + ' B';
  const kb = bytes/1024;
  if(kb < 1024) return kb.toFixed(2) + ' KB';
  return (kb/1024).toFixed(2) + ' MB';
}
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function toast(msg, icon){
  const host = document.getElementById('toastHost');
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = (icon||'✔️') + ' ' + msg;
  host.appendChild(el);
  setTimeout(()=> el.remove(), 2700);
}

/* ---------------- add files ---------------- */
function addFiles(fileList){
  const files = Array.from(fileList).slice(0, 50);
  if(!files.length) return;
  files.forEach(file=>{
    const {ext} = splitName(file.name);
    const cat = categoryOf(ext);
    const targets = getValidTargets(ext);
    let target = targets.find(t => t.toLowerCase() !== ext.toLowerCase()) || targets[0];
    jobs.push({
      id: 'j'+(uid++),
      file, name:file.name, size:file.size, ext: ext.toUpperCase() || 'FILE',
      category:cat, target, status:'pending', progress:0, settingsOpen:false, codeOpen:false, quality:80
    });
  });
  document.body.classList.add('has-jobs');
  render();
  toast(files.length + ' file ditambahkan');
}

/* ---------------- render ---------------- */
function badgeStyle(cat){ return 'background:'+CATEGORY[cat].color+';'; }

function rowTemplate(job){
  const cat = CATEGORY[job.category];
  const validTargets = getValidTargets(job.ext);
  let rightHTML = '';

  if(job.status === 'pending'){
    rightHTML = `\n` + (validTargets.length
      ? `<select class="fmt" data-action="target" data-id="${job.id}">
        ${validTargets.map(t=>`<option value="${t}" ${t===job.target?'selected':''}>${t}</option>`).join('')}
      </select>`
      : `<span class="no-converter" title="Tidak ada converter untuk format ini">— Tidak ada converter</span>`) + `
      <button class="icon-btn" data-action="settings" data-id="${job.id}" title="Pengaturan" aria-label="Pengaturan">⚙️</button>
      <button class="icon-btn" data-action="code" data-id="${job.id}" title="Lihat API" aria-label="Lihat API">&lt;/&gt;</button>
      <button class="icon-btn danger" data-action="remove" data-id="${job.id}" title="Hapus" aria-label="Hapus">✖</button>`;
  } else if(job.status === 'processing' || job.status === 'converting'){
    rightHTML = `<div class="converting-pill"><span class="spin"></span>Mengonversi…</div>
      <button class="icon-btn danger" data-action="remove" data-id="${job.id}" title="Hapus" aria-label="Hapus">✖</button>`;
  } else if(job.status === 'error'){
    rightHTML = `
      <div class="status-pill">❌ Gagal</div>
      <div class="row-error">${esc(job.errorMessage || 'Konversi gagal')}</div>
      <button class="icon-btn danger" data-action="remove" data-id="${job.id}" title="Hapus" aria-label="Hapus">✖</button>`;
  } else {
    rightHTML = `
      <div class="status-pill">✔️ Selesai</div>
      <div class="dl-split">
        <button class="dl-main" data-action="download" data-id="${job.id}">⬇️ Unduh</button>
        <button class="dl-caret" data-action="settings" data-id="${job.id}" aria-label="Opsi unduh">▾</button>
      </div>
      <button class="icon-btn danger" data-action="remove" data-id="${job.id}" title="Hapus" aria-label="Hapus">✖</button>`;
  }

  const progressHTML = job.status === 'converting' || job.status === 'processing'
    ? `<div class="progress-track"><div class="progress-fill" id="fill-${job.id}"></div></div>` : '';

  const sub = `
    <div class="subpanel ${job.settingsOpen ? 'open':''}" data-sub="settings-${job.id}">
      <div class="subpanel-inner">
        <label>Kualitas Output: <b>${job.quality}%</b></label>
        <input type="range" min="10" max="100" value="${job.quality}" data-action="quality" data-id="${job.id}">
      </div>
    </div>
    <div class="subpanel ${job.codeOpen ? 'open':''}" data-sub="code-${job.id}">
      <div class="subpanel-inner" style="display:block;">
        <div class="code-box">curl -X POST https://api.ubah.in/v1/convert \\
  -F "file=@${job.name}" \\
  -F "target=${(job.target||'').toLowerCase()}"<button class="code-copy" data-action="copy" data-id="${job.id}">Salin</button></div>
      </div>
    </div>`;

  return `
    <div class="row" data-row="${job.id}">
      <div class="badge" style="${badgeStyle(job.category)}">${job.ext.slice(0,4)}</div>
      <div class="row-info">
        <div class="row-name">${esc(job.name)}</div>
        <div class="row-meta">
          <span>${fmtSize(job.size)}</span>
          <span class="arrow-tag">${job.ext} → <b>${job.status==='done' ? job.target : job.target}</b></span>
        </div>
      </div>
      <div class="row-controls">${rightHTML}</div>
      ${progressHTML}
    </div>
    ${sub}
  `;
}

function render(){
  const rowsEl = document.getElementById('rows');
  rowsEl.innerHTML = jobs.map(rowTemplate).join('');

  const allDone = jobs.length>0 && jobs.every(j=>j.status==='done' || j.status==='error');
  const pending = jobs.filter(j=>j.status==='pending');

  document.getElementById('footerPre').style.display = allDone ? 'none' : 'flex';
  document.getElementById('footerPost').classList.toggle('show', allDone);

  const pendingCountEl = document.getElementById('pendingCount');
  if(pendingCountEl) pendingCountEl.textContent = pending.length;
  const goBtn = document.getElementById('goBtn');
  goBtn.disabled = pending.length === 0 || jobs.some(j=>j.status==='converting' || j.status==='processing');

  // start any newly-converting progress bars
  jobs.filter(j=>j.status==='converting').forEach(j=>{
    const fill = document.getElementById('fill-'+j.id);
    if(fill){
      requestAnimationFrame(()=>{
        fill.style.transitionDuration = j._duration + 'ms';
        fill.style.width = '100%';
      });
    }
  });

  buildGlobalFmt();
}

function buildGlobalFmt(){
  const sel = document.getElementById('globalFmt');
  const label = document.getElementById('footerLabel');
  const pending = jobs.filter(j=>j.status!=='done');
  const pendingTargets = [...new Set(pending.map(j => j.target))];
  const sameTarget = pending.length > 0 && pendingTargets.length === 1;

  if(sameTarget){
    const cats = [...new Set(pending.map(j=>j.category))];
    let opts = [];
    if(cats.length === 1){
      opts = pending.map(j => getValidTargets(j.ext))
                    .reduce((a,b) => a.filter(t => b.includes(t)), getValidTargets(pending[0].ext));
    } else {
      opts = ['JPG','PNG','PDF','MP3','MP4','ZIP'];
    }
    const current = sel.value;
    sel.innerHTML = opts.map(t=>`<option value="${t}">${t}</option>`).join('');
    if(opts.includes(current)) {
      sel.value = current;
    } else {
      const sourceFormats = new Set(
        pending.map(j => String(j.ext || '').toLowerCase().replace(/^\./, ''))
      );
      sel.value = opts.find(option => !sourceFormats.has(option.toLowerCase())) || opts[0];
    }
    label.innerHTML = `${window.translate('upload.conversion_instruction', 'Convert all files to:')} (<span id="pendingCount">${pending.length}</span>)`;
    sel.style.display = '';
  } else {
    sel.innerHTML = '';
    sel.style.display = 'none';
    label.innerHTML = `${window.translate('upload.conversion_instruction', 'Convert all files to:')} (<span id="pendingCount">${pending.length}</span>)`;
  }
}

/* ---------------- conversion logic ---------------- */
function conversionErrorMessage(data, response){
  if(data){
    if(typeof data === 'string') return data;
    if(Array.isArray(data.detail)){
      return data.detail.map(item => typeof item === 'string' ? item : item.msg || JSON.stringify(item)).join('; ');
    }
    if(typeof data.detail === 'string') return data.detail;
    if(typeof data.message === 'string') return data.message;
    if(typeof data.error === 'string') return data.error;
    if(typeof data.code === 'string') return data.code;
  }
  return response.statusText || `HTTP ${response.status}`;
}

function conversionDownloadPath(data){
  if(!data || typeof data !== 'object') return '';
  if(typeof data.download_path === 'string' && data.download_path) {
    return data.download_path;
  }
  if(Array.isArray(data.results)){
    const result = data.results.find(item => item && typeof item.download_path === 'string' && item.download_path);
    return result ? result.download_path : '';
  }
  return '';
}

async function convertJob(job, targetFormat){
  const formData = new FormData();
  formData.append('file', job.file);
  formData.append('target_format', targetFormat);

  try {
    const response = await fetch('/convert', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json().catch(() => null);

    if(!response.ok){
      throw new Error(conversionErrorMessage(data, response));
    }

    const downloadPath = conversionDownloadPath(data);
    if(!downloadPath){
      throw new Error('Conversion response did not include download_path');
    }

    job.downloadPath = downloadPath;
    job.status = 'done';
    job.errorMessage = '';
  } catch(error) {
    job.status = 'error';
    job.errorMessage = error && error.message ? error.message : String(error);
    job.downloadPath = '';
  }
  render();
}

function convertAll(){
  const pending = jobs.filter(j=>j.status==='pending');
  if(!pending.length) return;

  const globalFormat = document.getElementById('globalFmt');
  const requests = pending.map(job => {
    const row = document.querySelector(`[data-row="${job.id}"]`);
    const rowFormat = row?.querySelector('select.fmt')?.value || job.target;
    const targetFormat = globalFormat?.offsetParent !== null && globalFormat?.value
      ? globalFormat.value
      : rowFormat;

    job.target = targetFormat;
    job.status = 'processing';
    return {job, targetFormat};
  });

  render();
  Promise.all(requests.map(({job, targetFormat}) => convertJob(job, targetFormat)));
}

/* ---------------- download ---------------- */
function convertedBlobName(job){
  const {base} = splitName(job.name);
  return base + '.' + job.target.toLowerCase();
}
async function downloadJob(job){
  if(!job.downloadPath) return;

  const response = await fetch(job.downloadPath);
  if(!response.ok){
    toast('Unduhan gagal', '❌');
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = convertedBlobName(job);
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(()=>URL.revokeObjectURL(url), 4000);
  toast('Mengunduh ' + convertedBlobName(job));
}
async function downloadAll(){
  const done = jobs.filter(j=>j.status==='done');
  if(!done.length) return;
  if(done.length === 1){ downloadJob(done[0]); return; }
  toast('Menyiapkan ZIP…', '⏳');
  const zip = new JSZip();
  let includedCount = 0;
  let skippedCount = 0;
  for(const j of done){
    if(!j.downloadPath){
      skippedCount++;
      continue;
    }
    try {
      const response = await fetch(j.downloadPath);
      if(!response.ok){
        skippedCount++;
        continue;
      }
      const blob = await response.blob();
      zip.file(convertedBlobName(j), blob);
      includedCount++;
    } catch(error) {
      skippedCount++;
    }
  }
  if(!includedCount){
    toast('Tidak ada hasil konversi yang tersedia untuk ZIP', '⚠️');
    return;
  }
  const blob = await zip.generateAsync({type:'blob'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'converigo-hasil-konversi.zip';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url), 4000);
  toast(skippedCount ? `Unduhan ZIP dimulai (${skippedCount} file dilewati)` : 'Unduhan ZIP dimulai');
}

/* ---------------- reset ---------------- */
function resetAll(){
  jobs = [];
  document.body.classList.remove('has-jobs');
  render();
}

/* ---------------- event delegation ---------------- */
document.getElementById('rows').addEventListener('click', e=>{
  const btn = e.target.closest('[data-action]');
  if(!btn) return;
  const id = btn.dataset.id;
  const job = jobs.find(j=>j.id===id);
  if(!job) return;
  const action = btn.dataset.action;

  if(action==='remove'){
    jobs = jobs.filter(j=>j.id!==id);
    if(!jobs.length) document.body.classList.remove('has-jobs');
    render();
  } else if(action==='settings'){
    job.settingsOpen = !job.settingsOpen;
    job.codeOpen = false;
    render();
  } else if(action==='code'){
    job.codeOpen = !job.codeOpen;
    job.settingsOpen = false;
    render();
  } else if(action==='download'){
    downloadJob(job);
  } else if(action==='copy'){
    const code = `curl -X POST https://api.ubah.in/v1/convert -F "file=@${job.name}" -F "target=${job.target.toLowerCase()}"`;
    navigator.clipboard?.writeText(code);
    toast('Perintah disalin ke clipboard');
  }
});
document.getElementById('rows').addEventListener('change', e=>{
  const el = e.target.closest('[data-action]');
  if(!el) return;
  const id = el.dataset.id;
  const job = jobs.find(j=>j.id===id);
  if(!job) return;
  if(el.dataset.action==='target'){ job.target = el.value; render(); }
});
document.getElementById('rows').addEventListener('input', e=>{
  const el = e.target.closest('[data-action="quality"]');
  if(!el) return;
  const job = jobs.find(j=>j.id===el.dataset.id);
  if(!job) return;
  job.quality = el.value;
  const label = el.closest('.subpanel-inner').querySelector('label b');
  if(label) label.textContent = el.value + '%';
});

document.getElementById('goBtn').addEventListener('click', convertAll);
document.getElementById('newBtn').addEventListener('click', resetAll);
document.getElementById('dlAllBtn').addEventListener('click', downloadAll);

/* file input wiring */
const fileInput = document.getElementById('fileInput');
document.getElementById('browseBtn').addEventListener('click', e=>{ e.stopPropagation(); fileInput.click(); });
document.getElementById('addMoreBtn').addEventListener('click', ()=> fileInput.click());
window.handleLanguageChange = function (event) {
  const selectedLang = event.target.value;
  const params = new URLSearchParams(window.location.search);
  if (selectedLang) {
    params.set('lang', selectedLang);
  } else {
    params.delete('lang');
  }
  const query = params.toString();
  window.location.href = window.location.pathname + (query ? `?${query}` : '');
};

fileInput.addEventListener('change', e=>{ addFiles(e.target.files); fileInput.value=''; });

const dz = document.getElementById('dropzone');
dz.addEventListener('click', ()=> fileInput.click());
dz.addEventListener('keydown', e=>{ if(e.key==='Enter' || e.key===' '){ e.preventDefault(); fileInput.click(); }});
['dragenter','dragover'].forEach(evt=>{
  dz.addEventListener(evt, e=>{ e.preventDefault(); dz.classList.add('drag'); });
});
['dragleave','drop'].forEach(evt=>{
  dz.addEventListener(evt, e=>{ e.preventDefault(); dz.classList.remove('drag'); });
});
dz.addEventListener('drop', e=>{
  if(e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files);
});

/* ---------------- morph badge cycle ---------------- */
const morphCycle = [
  {label:'PDF', color:'#FF6B4A'}, {label:'JPG', color:'#5B4FE9'}, {label:'MP3', color:'#12B3A0'},
  {label:'MP4', color:'#F59E0B'}, {label:'PNG', color:'#5B4FE9'}, {label:'ZIP', color:'#6C7599'},
  {label:'DOCX', color:'#FF6B4A'}, {label:'WAV', color:'#12B3A0'}
];
let mi = 0;
const morphBadge = document.getElementById('morphBadge');
const morphLabel = document.getElementById('morphLabel');
// Pause morph updates when the user is at the bottom of the page to avoid
// layout shifts that can nudge the viewport. See bugfix rules: only add
// a minimal scroll listener and skip updates while at bottom.
let __isMorphPausedAtBottom = false;
window.addEventListener('scroll', () => {
  __isMorphPausedAtBottom = (window.innerHeight + window.scrollY) >= (document.body.scrollHeight - 5);
}, { passive: true });

setInterval(()=>{
  // compute bottom at tick to avoid race with scroll events
  const __atBottomNow = document.documentElement.scrollHeight > window.innerHeight &&
    (window.innerHeight + window.scrollY) >= (document.documentElement.scrollHeight - 5);
  if(__isMorphPausedAtBottom || __atBottomNow) return;
  mi = (mi+1) % morphCycle.length;
  morphLabel.style.opacity = 0;
  setTimeout(()=>{
    morphLabel.textContent = morphCycle[mi].label;
    morphBadge.style.background = morphCycle[mi].color;
    morphLabel.style.opacity = 1;
  }, 180);
}, 1900);

/* ---------------- orbit icons ---------------- */
const orbitExts = [
  {t:'PDF', c:'#FF6B4A'}, {t:'JPG', c:'#5B4FE9'}, {t:'MP3', c:'#12B3A0'}, {t:'MP4', c:'#F59E0B'},
  {t:'ZIP', c:'#6C7599'}, {t:'PNG', c:'#5B4FE9'}, {t:'DOCX', c:'#FF6B4A'}, {t:'WAV', c:'#12B3A0'},
  {t:'SVG', c:'#5B4FE9'}, {t:'CSV', c:'#FF6B4A'}, {t:'GIF', c:'#5B4FE9'}
];
function buildOrbit(){
  const field = document.getElementById('orbitField');
  const ring1 = document.createElement('div'); ring1.className = 'ring r1';
  const ring2 = document.createElement('div'); ring2.className = 'ring r2';
  const set1 = orbitExts.slice(0,6), set2 = orbitExts.slice(6,11);

  function place(container, items, radius){
    items.forEach((it, i)=>{
      const angle = (360/items.length) * i;
      const wrap = document.createElement('div');
      wrap.className = 'ic';
      wrap.style.transform = `rotate(${angle}deg) translate(${radius}px)`;
      wrap.innerHTML = `<div class="counter"><div class="badge" style="width:38px;height:38px;border-radius:10px 10px 10px 3px;background:${it.c};font-size:9px;">${it.t}</div></div>`;
      container.appendChild(wrap);
    });
  }
  place(ring1, set1, 150);
  place(ring2, set2, 215);
  field.appendChild(ring1);
  field.appendChild(ring2);
}
buildOrbit();

/* ---------------- format marquee build ---------------- */
function buildMarquee(){
  const all = [];
  Object.entries(CATEGORY).forEach(([key, val])=>{
    if(key==='other') return;
    val.targets.forEach(t=> all.push({t, c:val.color}));
  });
  const half = Math.ceil(all.length/2);
  const rowA = all.slice(0, half), rowB = all.slice(half);
  function build(list){
    const doubled = list.concat(list);
    return doubled.map(it=>`<div class="chip"><span class="dot2" style="background:${it.c}"></span>${it.t}</div>`).join('');
  }
  document.getElementById('trackA').innerHTML = build(rowA);
  document.getElementById('trackB').innerHTML = build(rowB);
}
buildMarquee();

render();
