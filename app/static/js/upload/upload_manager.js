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

        this.previewContainer = document.getElementById('previewContainer');
        this.previewCard = document.querySelector('.preview-card');
        this.previewMedia = document.getElementById('previewMedia');
        this.previewImage = document.getElementById('previewImage');
        this.previewName = document.getElementById('previewName');
        this.previewSize = document.getElementById('previewSize');

        this.init();
    }

    init(){
        if(!this.fileInput) {
            console.error('upload manager: fileInput missing');
            return;
        }
        this.bindEvents();
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
            const file = this.fileInput.files[0];
            if(file){
                this.handleFile(file);
                this.fileInput.value = '';
            }
        });

        if(this.dropZone){
            this.dropZone.addEventListener('dragover', e=>{ e.preventDefault(); this.dropZone.classList.add('drag-active'); });
            this.dropZone.addEventListener('dragleave', ()=>{ this.dropZone.classList.remove('drag-active'); });
            this.dropZone.addEventListener('drop', e=>{
                e.preventDefault();
                this.dropZone.classList.remove('drag-active');
                const file = e.dataTransfer.files && e.dataTransfer.files[0];
                if(file){ this.setFile(file); this.handleFile(file); }
            });
        }
    }

    setFile(file){
        const dt = new DataTransfer();
        dt.items.add(file);
        this.fileInput.files = dt.files;
    }

    handleFile(file){
        this.resetConversionUI();
        this.updateFileInfo(file);
        this.showPreview(file);
        this.runRecommendation(file);
        this._emitFileSelected(file);
    }

    updateFileInfo(file){
        const size = (file.size / 1024 / 1024).toFixed(2) + ' MB';
        if(this.fileName) this.fileName.textContent = file.name;
        if(this.fileSize) this.fileSize.textContent = size;
        if(this.previewName) this.previewName.textContent = file.name;
        if(this.previewSize) this.previewSize.textContent = size;
        if(this.selectedStatus) this.selectedStatus.textContent = 'File ready';
    }

    showPreview(file){
        if(this.previewContainer) this.previewContainer.hidden = false;
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
            if(this.previewName) this.previewName.textContent = 'Audio File';
            return;
        }

        // Video: show clapper icon
        if(file.type && file.type.startsWith('video/')){
            if(iconEl) { iconEl.textContent = '🎬'; iconEl.hidden = false; }
            if(this.previewMedia) this.previewMedia.classList.add('video');
            if(this.previewName) this.previewName.textContent = 'Video File';
            return;
        }

        // PDF: show document icon
        if(file.type === 'application/pdf'){
            if(iconEl) { iconEl.textContent = '📄'; iconEl.hidden = false; }
            if(this.previewMedia) this.previewMedia.classList.add('pdf');
            if(this.previewName) this.previewName.textContent = 'PDF File';
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
            convertBtn.textContent = 'Convert';
        }

        const progress = document.querySelector('.progress');
        if(progress){
            progress.hidden = true;
        }

        const progressBar = document.querySelector('.progress-bar');
        if(progressBar){
            progressBar.style.width = '0%';
        }
    }

    _emitFileSelected(file){
        try{ if(window.downloadManager && typeof window.downloadManager.clear === 'function'){ window.downloadManager.clear(); } }catch(e){ console.warn('downloadManager.clear failed', e); }
        window.dispatchEvent(new CustomEvent('file-selected', { detail: { file: file } }));
    }

    // backward compatible
    emitFileSelected(file){ return this._emitFileSelected(file); }
}

document.addEventListener('DOMContentLoaded', ()=>{ window.uploadManager = new UploadManager(); });
