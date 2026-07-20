/*
Upload Manager
- Dispatches `file-selected` {file}
- Triggers RecommendationManager.analyzeFile(file)
- Clears DownloadManager on new upload
*/

class UploadManager {
    constructor() {
        this.fileInput = document.getElementById('fileInput');
        this.chooseButton = document.getElementById('chooseFile');
        this.dropZone = document.getElementById('dropZone');

        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.selectedStatus = document.getElementById('selectedStatus');
        this.uploadHint = document.getElementById('uploadHint');
        this.fileList = document.getElementById('fileList');

        this.previewContainer = document.getElementById('previewContainer');
        this.previewCard = null;
        this.previewMedia = null;
        this.previewImage = null;
        this.previewName = null;
        this.previewSize = null;
        this.previewStatus = null;
        this.fileType = document.getElementById('fileType');
        this.fileStatus = this.selectedStatus ? this.selectedStatus.querySelector('.file-status') : null;
        this.downloadBtn = document.getElementById('downloadBtn');
        this.wrapper = document.querySelector('.upload-wrapper');
        this.resultCard = null;
        this.resultFileName = null;
        this.errorCard = null;
        this.errorMessage = null;
        this.tryAgainBtn = null;

        this.files = [];
        this.file = null;

        this.init();
    }

    init(){
        if(!this.fileInput) {
            console.error('upload manager: fileInput missing');
            return;
        }
        this.bindEvents();
        this.createDynamicCards();
        this.resetUpload();
        if(this.resultCard){
            this.resultCard.hidden = true;
            this.resultCard.style.display = 'none';
        }
        if(this.errorCard){
            this.errorCard.hidden = true;
            this.errorCard.style.display = 'none';
        }
        if(this.downloadBtn){
            this.downloadBtn.hidden = true;
            this.downloadBtn.style.display = 'none';
        }
    }

    bindEvents(){
        if(this.chooseButton){
            this.chooseButton.addEventListener('click', ()=>{
                if(this.fileInput){
                    this.fileInput.value = '';
                }
                this.fileInput.click();
            });
        }

        this.fileInput.addEventListener('change', ()=>{
            const files = this.fileInput.files;
            if(files && files.length){
                this.handleFiles(files);
                this.fileInput.value = '';
            }
        });

        if(this.dropZone){
            this.dropZone.addEventListener('dragover', e=>{ e.preventDefault(); this.dropZone.classList.add('drag-active'); });
            this.dropZone.addEventListener('dragleave', ()=>{ this.dropZone.classList.remove('drag-active'); });
            this.dropZone.addEventListener('drop', e=>{
                e.preventDefault();
                this.dropZone.classList.remove('drag-active');
                const files = e.dataTransfer.files;
                if(files && files.length){ this.setFiles(files); this.handleFiles(files); }
            });
        }
    }

    setFile(file){
        const dt = new DataTransfer();
        dt.items.add(file);
        this.fileInput.files = dt.files;
    }

    setFiles(fileList){
        const dt = new DataTransfer();
        Array.from(fileList).forEach(file => dt.items.add(file));
        this.fileInput.files = dt.files;
    }

    _inferInputFormat(file){
        if(!file){ return ''; }
        const type = (file.type || '').toLowerCase();
        const name = (file.name || '').toLowerCase();
        if(type.startsWith('image/')) return 'image';
        if(type.startsWith('audio/')) return 'audio';
        if(type.startsWith('video/')) return 'video';
        if(type === 'application/pdf' || name.endsWith('.pdf')) return 'pdf';
        if(type.includes('word') || name.endsWith('.docx') || name.endsWith('.doc')) return 'document';
        if(name.endsWith('.zip')) return 'archive';
        return type || 'file';
    }

    _trackUploadStarted(file){
        if(!file || !window.converigoAnalytics || typeof window.converigoAnalytics.trackEvent !== 'function'){
            return;
        }
        const context = window.converigoAnalytics.getConverterContext();
        window.converigoAnalytics.trackEvent('upload_started', {
            converter_name: context.converter_name,
            category: context.category,
            input_format: this._inferInputFormat(file)
        });
    }

    handleFiles(fileList){
        const files = Array.from(fileList || []);
        const seen = new Set();
        const uniqueFiles = files.filter(file => {
            const key = `${file.name}|${file.size}|${file.lastModified}`;
            if(seen.has(key)) return false;
            seen.add(key);
            return true;
        });

        if(!uniqueFiles.length){
            return;
        }

        this.resetConversionUI();

        this.files = uniqueFiles;
        this.file = this.files[0] || null;

        if(this.uploadHint) this.uploadHint.hidden = true;
        // Show selected-status only when a single file is selected and no preview is visible
        let showSelected = false;
        if(this.files.length === 1){
            showSelected = true;
        }
        if(this.selectedStatus) this.selectedStatus.hidden = !showSelected;

        this.updateFileInfo(this.file);
        this.renderFileList();
        
        // Update layout class for modern converter UI
        const uploadMain = document.querySelector('.upload-main');
        if(uploadMain){
            uploadMain.classList.remove('upload-initial');
            uploadMain.classList.add('upload-active');
        }

        if(this.file){
            this.runRecommendation(this.file);
        }

        this._trackUploadStarted(this.file);
        this._emitFileSelected(this.file, this.files);
    }

    handleFile(file){
        this.handleFiles([file]);
    }

    updateFileInfo(file){
        const size = (file.size / 1024 / 1024).toFixed(2) + ' MB';
        const typeLabel = file.type || file.name.split('.').pop().toUpperCase();
        if(this.fileName) { this.fileName.textContent = file.name; this.fileName.title = file.name; }
        if(this.fileSize) this.fileSize.textContent = size;
        if(this.fileType) this.fileType.textContent = typeLabel;
        if(this.previewName) { this.previewName.textContent = file.name; this.previewName.title = file.name; }
        if(this.previewSize) this.previewSize.textContent = size;
        if(this.previewType) this.previewType.textContent = typeLabel;
        if(this.previewStatus) this.previewStatus.textContent = window.translate('upload.ready', 'Ready');
        if(this.fileStatus) this.fileStatus.textContent = window.translate('upload.ready', 'Ready');
    }

    showPreview(file){
        if(this.previewContainer){
            this.previewContainer.hidden = false;
            this.previewContainer.style.display = '';
            this.previewContainer.classList.add('preview-container--single');
        }
        if(this.previewMedia){
            this.previewMedia.classList.remove('audio','video','pdf');
        }

        // Reset preview elements
        if(this.previewImage){
            this.previewImage.hidden = true;
            this.previewImage.src = '';
            this.previewImage.style.display = 'none';
        }
        const iconEl = document.getElementById('previewIcon');
        if(iconEl){ iconEl.hidden = false; iconEl.textContent = '📄'; }

        // Image: show thumbnail
        if(file.type && file.type.startsWith('image/') && this.previewImage){
            const reader = new FileReader();
            reader.onload = e=>{
                if(this.previewImage){
                    this.previewImage.src = e.target.result;
                    this.previewImage.hidden = false;
                    this.previewImage.style.display = 'block';
                }
                if(iconEl) iconEl.hidden = true;
            };
            reader.readAsDataURL(file);
            // restore real filename in preview
            if(this.previewName) this.previewName.textContent = file.name;
            return;
        }

        // Audio: show music icon
        if(file.type && file.type.startsWith('audio/')){
            if(iconEl) { iconEl.textContent = '🎵'; iconEl.hidden = false; }
            if(this.previewMedia) this.previewMedia.classList.add('audio');
            if(this.previewName) this.previewName.textContent = window.translate('upload.file_type_audio', 'Audio File');
            return;
        }

        // Video: show clapper icon
        if(file.type && file.type.startsWith('video/')){
            if(iconEl) { iconEl.textContent = '🎬'; iconEl.hidden = false; }
            if(this.previewMedia) this.previewMedia.classList.add('video');
            if(this.previewName) this.previewName.textContent = window.translate('upload.file_type_video', 'Video File');
            return;
        }

        // PDF: show document icon
        if(file.type === 'application/pdf'){
            if(iconEl) { iconEl.textContent = '📄'; iconEl.hidden = false; }
            if(this.previewMedia) this.previewMedia.classList.add('pdf');
            if(this.previewName) this.previewName.textContent = window.translate('upload.file_type_pdf', 'PDF File');
            return;
        }

        // Fallback: keep generic icon
        if(iconEl) iconEl.textContent = '📄';
    }

    async runRecommendation(file){
        if(window.RecommendationManager && typeof window.RecommendationManager.analyzeFile === 'function'){
            try{ await window.RecommendationManager.analyzeFile(file); }catch(e){ console.error('recommendation error', e); }
        }
    }

    resetConversionUI(){
        const messageEl = document.getElementById('convertMessage');
        if(messageEl){
            messageEl.textContent = '';
            messageEl.classList.remove('success','error');
        }

        if(window.downloadManager && typeof window.downloadManager.clear === 'function'){
            window.downloadManager.clear();
        }

        if(window.converter && typeof window.converter.reset === 'function'){
            window.converter.reset();
        }

        const convertBtn = document.getElementById('convertButton');
        if(convertBtn){
            convertBtn.disabled = true;
            convertBtn.classList.remove('loading');
            convertBtn.textContent = window.translate('upload.convert', 'Convert');
            convertBtn.hidden = true;
            convertBtn.style.display = 'none';
        }

        const progress = document.querySelector('.progress');
        if(progress){
            progress.hidden = true;
            progress.style.display = 'none';
        }

        const progressBar = document.querySelector('.progress-bar');
        if(progressBar){
            progressBar.style.width = '0%';
        }

        const formatOptions = document.getElementById('formatOptions');
        if(formatOptions){
            formatOptions.innerHTML = '';
        }

        if(this.resultCard){
            this.resultCard.hidden = true;
            this.resultCard.style.display = 'none';
        }

        if(this.errorCard){
            this.errorCard.hidden = true;
            this.errorCard.style.display = 'none';
        }

        if(this.resultFileName){
            this.resultFileName.textContent = '';
        }

        if(this.errorMessage){
            this.errorMessage.textContent = '';
        }

        if(this.downloadBtn){
            this.downloadBtn.hidden = true;
            this.downloadBtn.style.display = 'none';
        }

        if(this.fileList){
            this.fileList.hidden = true;
            this.fileList.style.display = 'none';
            this.fileList.innerHTML = '';
        }

        if(window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function'){
            window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.IDLE);
            window.conversionStateController.setFormatChoicesAvailable(false);
        } else {
            const conversionArea = document.getElementById('conversionArea');
            if(conversionArea){
                conversionArea.hidden = true;
                conversionArea.style.display = 'none';
            }
        }

        document.querySelectorAll('.format-chip.active').forEach(btn => btn.classList.remove('active'));
    }

    resetUpload(){
        this.resetConversionUI();
        if(this.fileInput){
            this.fileInput.value = '';
        }
        if(this.selectedStatus){
            this.selectedStatus.hidden = true;
        }
        if(this.fileName){
            this.fileName.textContent = '';
        }
        if(this.fileSize){
            this.fileSize.textContent = '';
        }
        if(this.fileType){
            this.fileType.textContent = '';
        }
        if(this.fileStatus){
            this.fileStatus.textContent = window.translate('upload.ready', 'Ready');
        }
        if(this.uploadHint){
            this.uploadHint.hidden = true;
        }

        if(this.fileList){
            this.fileList.hidden = true;
            this.fileList.style.display = 'none';
            this.fileList.innerHTML = '';
        }
        
        // Reset layout to upload-initial state
        const uploadMain = document.querySelector('.upload-main');
        if(uploadMain){
            uploadMain.classList.remove('upload-active');
            uploadMain.classList.add('upload-initial');
        }
    }

    renderFileList(){
        if(!this.fileList){
            return;
        }

        if(!this.files.length){
            this.fileList.hidden = true;
            this.fileList.style.display = 'none';
            this.fileList.innerHTML = '';
            return;
        }

        const headingText = this.files.length > 1
            ? window.translate('upload.files_ready', 'Files ready')
            : window.translate('upload.file_ready', 'File ready');

        const items = this.files.map(file => {
            const size = (file.size / 1024 / 1024).toFixed(2) + ' MB';
            const typeLabel = file.type || file.name.split('.').pop().toUpperCase();
            return `
                <div class="file-item">
                    <div class="file-item-top">
                        <div class="file-item-name truncate" title="${file.name}">${file.name}</div>
                        <span class="file-item-status">${window.translate('upload.ready', 'Ready')}</span>
                    </div>
                    <div class="file-item-meta">${size} · ${typeLabel}</div>
                </div>
            `;
        }).join('');

        this.fileList.innerHTML = `<div class="file-list-heading">${headingText}</div>${items}`;
        this.fileList.hidden = false;
        this.fileList.style.removeProperty('display');
    }

    createDynamicCards(){
        if(!this.wrapper || this.resultCard || this.errorCard){
            return;
        }

        const resultCard = document.createElement('div');
        resultCard.id = 'resultCard';
        resultCard.className = 'result-card';
        resultCard.hidden = true;
        resultCard.style.display = 'none';
        resultCard.innerHTML = `
            <div class="result-status">${window.translate('upload.conversion_complete', '✓ Conversion complete')}</div>
            <div id="resultFileName" class="result-file-name"></div>
        `;

        const errorCard = document.createElement('div');
        errorCard.id = 'errorCard';
        errorCard.className = 'error-card';
        errorCard.hidden = true;
        errorCard.style.display = 'none';
        errorCard.innerHTML = `
            <div class="error-title">${window.translate('upload.conversion_failed', 'Conversion Failed')}</div>
            <p id="errorMessage" class="error-message"></p>
            <button id="tryAgainBtn" class="btn btn-outline" type="button">${window.translate('upload.try_again', 'Try Again')}</button>
        `;

        if(this.downloadBtn){
            resultCard.appendChild(this.downloadBtn);
        }

        this.wrapper.appendChild(resultCard);
        this.wrapper.appendChild(errorCard);

        this.resultCard = resultCard;
        this.resultFileName = resultCard.querySelector('#resultFileName');
        this.errorCard = errorCard;
        this.errorMessage = errorCard.querySelector('#errorMessage');
        this.tryAgainBtn = errorCard.querySelector('#tryAgainBtn');

        if(this.tryAgainBtn){
            this.tryAgainBtn.addEventListener('click', () => this.resetUpload());
        }
    }

    showResult(file){
        if(this.errorCard){
            this.errorCard.hidden = true;
            this.errorCard.style.display = 'none';
        }
        if(this.resultCard){
            if(this.resultFileName){
                this.resultFileName.textContent = file?.name || '';
            }
            this.resultCard.hidden = false;
            this.resultCard.style.display = '';
        }
        if(window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function'){
            window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.SUCCESS);
        }
        if(this.selectedStatus){
            this.selectedStatus.hidden = false;
        }
    }

    showError(message){
        if(this.resultCard){
            this.resultCard.hidden = true;
            this.resultCard.style.display = 'none';
        }
        if(this.errorCard){
            if(this.errorMessage){
                this.errorMessage.textContent = message || window.translate('upload.conversion_failed_try_another', 'Conversion failed. Please try another format.');
            }
            this.errorCard.hidden = false;
            this.errorCard.style.display = '';
        }
        if(window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function'){
            window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.ERROR);
        }
    }

    _emitFileSelected(file, files = []){
        try{ if(window.downloadManager && typeof window.downloadManager.clear === 'function'){ window.downloadManager.clear(); } }catch(e){ console.warn('downloadManager.clear failed', e); }
        window.dispatchEvent(new CustomEvent('file-selected', { detail: { file: file, files: files } }));
    }

    // backward compatible
    emitFileSelected(file){ return this._emitFileSelected(file); }
}

document.addEventListener('DOMContentLoaded', ()=>{ window.uploadManager = new UploadManager(); });
