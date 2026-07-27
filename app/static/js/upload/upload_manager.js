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
        this.fileListPanel = document.getElementById('fileListPanel');
        this.conversionInstructionText = document.getElementById('conversionInstructionText');
        this.conversionSummaryOutput = document.getElementById('conversionSummaryOutput');

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
        this.resultMetaName = null;
        this.resultOutputFormat = null;
        this.resultFileType = null;
        this.convertAnotherBtn = null;
        this.errorCard = null;
        this.errorMessage = null;
        this.tryAgainBtn = null;

        this.files = [];
        this.file = null;
        this.fileOutputs = {};

        this.init();
    }

    _findUploadCard() {
        return document.querySelector('.upload-card') || document.querySelector('#converter') || document.querySelector('.homepage-upload-card') || document.querySelector('.upload-wrapper');
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
                if(window.converigoAnalytics && typeof window.converigoAnalytics.trackEvent === 'function'){
                    window.converigoAnalytics.trackEvent('upload_box_interaction', {
                        page_path: window.location.pathname || '/',
                        event_status: 'success'
                    });
                }
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
                if(window.converigoAnalytics && typeof window.converigoAnalytics.trackEvent === 'function'){
                    window.converigoAnalytics.trackEvent('upload_box_interaction', {
                        page_path: window.location.pathname || '/',
                        event_status: 'success'
                    });
                }
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
        this.fileOutputs = {};
        this.file = this.files[0] || null;
        this._ensureFileOutputDefaults();

        if(this.uploadHint) this.uploadHint.hidden = true;
        // Show selected-status only when a single file is selected and no preview is visible
        let showSelected = false;
        if(this.files.length === 1){
            showSelected = true;
        }
        if(this.selectedStatus) this.selectedStatus.hidden = !showSelected;

        this.updateFileInfo(this.file);
        this.renderFileList();
        this._updateConversionInstruction();
        
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
        if(this.previewStatus) this.previewStatus.textContent = '';
        if(this.fileStatus) this.fileStatus.textContent = '';
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

        if(this.resultMetaName){
            this.resultMetaName.textContent = '';
        }

        if(this.resultOutputFormat){
            this.resultOutputFormat.textContent = '';
        }

        if(this.resultFileType){
            this.resultFileType.textContent = '';
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
        if(this.resultCard){
            this.resultCard.hidden = true;
            this.resultCard.style.display = 'none';
        }
        if(this.errorCard){
            this.errorCard.hidden = true;
            this.errorCard.style.display = 'none';
        }
        if(this.fileListPanel){
            this.fileListPanel.hidden = true;
            this.fileListPanel.style.display = 'none';
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
        // Clear any upload state indicators and restore heading
        try {
            const uploadCard = this._findUploadCard();
            if (uploadCard) {
                uploadCard.classList.remove('state-uploading', 'state-success', 'state-error');
            }
            const heading = document.querySelector('.drop-zone .drop-zone-copy h2');
            if (heading) {
                heading.textContent = window.translate('upload.drop_title', 'Drop your file here');
                heading.style.opacity = '';
            }
        } catch (e) { /* ignore */ }
    }

    renderFileList(){
        if(!this.fileList || !this.fileListPanel){
            return;
        }

        if(!this.files.length){
            this.fileListPanel.hidden = true;
            this.fileListPanel.style.display = 'none';
            this.fileList.hidden = true;
            this.fileList.style.display = 'none';
            this.fileList.innerHTML = '';
            return;
        }

        const headingText = this.files.length > 1
            ? window.translate('upload.selected_files', 'Selected files')
            : window.translate('upload.selected_file', 'Selected file');

        const fileRows = this.files.map((file) => {
            const size = (file.size / 1024 / 1024).toFixed(2) + ' MB';
            const key = this._fileKey(file);
            const outputOptions = this._outputOptionsForFile(file);
            const currentOutput = this.fileOutputs[key] || this._inferDefaultOutput(file);
            const optionMarkup = outputOptions.map(option => {
                const selected = option.toUpperCase() === currentOutput.toUpperCase() ? 'selected' : '';
                return `<option value="${option}" ${selected}>${option.toUpperCase()}</option>`;
            }).join('');
            return `
                <div class="file-item" data-file-key="${key}">
                    <div class="file-item-main">
                        <div class="file-item-meta">
                            <div class="file-item-name truncate" title="${file.name}">${file.name}</div>
                            <div class="file-item-size">${size}</div>
                        </div>
                        <div class="file-item-actions">
                            <label class="file-output-field">
                                <span class="file-output-label">${window.translate('upload.output', 'Output')}</span>
                                <select class="file-output-select" data-file-key="${key}" aria-label="${window.translate('upload.output_format', 'Output format')}">
                                    ${optionMarkup}
                                </select>
                            </label>
                            <button type="button" class="file-gear-btn" aria-label="${window.translate('upload.settings', 'Settings')}">⚙</button>
                            <button type="button" class="file-remove-btn" data-file-key="${key}" aria-label="${window.translate('upload.remove_file', 'Remove file')}">✕</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        this.fileList.innerHTML = `<div class="file-list-heading">${headingText}</div>${fileRows}`;
        this.fileList.hidden = false;
        this.fileList.style.removeProperty('display');
        this.fileListPanel.hidden = false;
        this.fileListPanel.style.removeProperty('display');

        this._bindFileListInteractions();
        this._updateConversionSummary();
    }

    _updateConversionSummary(){
        if(!this.conversionSummaryOutput) return;
        const selected = this.selectedFormat || (this.files.length ? this.fileOutputs[this._fileKey(this.files[0])] || this._inferDefaultOutput(this.files[0]) : '');
        this.conversionSummaryOutput.textContent = selected ? selected.toUpperCase() : '—';
    }

    _fileKey(file){
        return `${file.name}|${file.size}|${file.lastModified}`;
    }

    _inferDefaultOutput(file){
        if(!file) return '';
        const type = (file.type || '').toLowerCase();
        const name = (file.name || '').toLowerCase();
        if(type.startsWith('image/')) return 'JPG';
        if(type.startsWith('audio/')) return 'MP3';
        if(type.startsWith('video/')) return 'MP4';
        if(type === 'application/pdf' || name.endsWith('.pdf')) return 'PDF';
        if(type.includes('word') || name.endsWith('.docx') || name.endsWith('.doc')) return 'PDF';
        if(name.endsWith('.zip')) return 'ZIP';
        if(name.endsWith('.xlsx') || name.endsWith('.xls')) return 'CSV';
        return name.split('.').pop().toUpperCase() || 'PDF';
    }

    _outputOptionsForFile(file){
        const defaultOutput = this._inferDefaultOutput(file);
        const type = (file.type || '').toLowerCase();
        if(type.startsWith('image/')) return ['JPG', 'PNG', 'WEBP'];
        if(type.startsWith('audio/')) return ['MP3', 'WAV', 'FLAC'];
        if(type.startsWith('video/')) return ['MP4', 'MOV', 'WEBM'];
        if(type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) return ['PDF', 'JPG', 'PNG'];
        if(file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc')) return ['PDF', 'DOCX', 'TXT'];
        if(file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')) return ['CSV', 'XLSX', 'PDF'];
        if(file.name.toLowerCase().endsWith('.zip')) return ['ZIP', '7Z', 'RAR'];
        return [defaultOutput];
    }

    _ensureFileOutputDefaults(){
        this.files.forEach(file => {
            const key = this._fileKey(file);
            if(!this.fileOutputs[key]){
                this.fileOutputs[key] = this._inferDefaultOutput(file);
            }
        });
    }

    _updateConversionInstruction(){
        if(!this.conversionInstructionText) return;
        const count = this.files.length;
        if(count > 1){
            this.conversionInstructionText.textContent = window.translate('upload.convert_all_to', 'Convert all {count} files to:').replace('{count}', String(count));
        } else if(count === 1){
            this.conversionInstructionText.textContent = window.translate('upload.convert_file_to', 'Convert file to:');
        } else {
            this.conversionInstructionText.textContent = window.translate('upload.conversion_instruction', 'Convert all files to:');
        }
    }

    _bindFileListInteractions(){
        if(!this.fileList) return;
        this.fileList.querySelectorAll('.file-remove-btn').forEach(button => {
            button.addEventListener('click', event => {
                const key = event.currentTarget.dataset.fileKey;
                if(!key) return;
                this.files = this.files.filter(file => this._fileKey(file) !== key);
                delete this.fileOutputs[key];
                if(this.files.length){
                    this.file = this.files[0];
                } else {
                    this.file = null;
                }
                this.renderFileList();
                if(!this.files.length){
                    this.resetUpload();
                }
            });
        });

        this.fileList.querySelectorAll('.file-output-select').forEach(select => {
            select.addEventListener('change', event => {
                const key = event.currentTarget.dataset.fileKey;
                if(!key) return;
                this.fileOutputs[key] = event.currentTarget.value;
                this._updateConversionSummary();
            });
        });
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
            <div class="result-summary">
                <div id="resultFileName" class="result-file-name"></div>
                <dl class="result-metadata" aria-label="File details">
                    <div class="result-metadata-item">
                        <dt>${window.translate('upload.file_name', 'File name')}</dt>
                        <dd id="resultMetaName"></dd>
                    </div>
                    <div class="result-metadata-item">
                        <dt>${window.translate('upload.output_format', 'Output format')}</dt>
                        <dd id="resultOutputFormat"></dd>
                    </div>
                    <div class="result-metadata-item">
                        <dt>${window.translate('upload.file_type', 'File type')}</dt>
                        <dd id="resultFileType"></dd>
                    </div>
                </dl>
            </div>
            <div class="result-actions">
                <button id="convertAnotherBtn" class="btn btn-outline result-secondary-btn" type="button">
                    ${window.translate('upload.convert_another', 'Convert Another File')}
                </button>
                <a class="btn btn-outline result-secondary-btn" href="#uploadSection">
                    ${window.translate('upload.back_to_upload', 'Back to Upload')}
                </a>
            </div>
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
            const resultActions = resultCard.querySelector('.result-actions');
            if(resultActions){
                resultCard.insertBefore(this.downloadBtn, resultActions);
            } else {
                resultCard.appendChild(this.downloadBtn);
            }
        }

        this.wrapper.appendChild(resultCard);
        this.wrapper.appendChild(errorCard);

        this.resultCard = resultCard;
        this.resultFileName = resultCard.querySelector('#resultFileName');
        this.resultMetaName = resultCard.querySelector('#resultMetaName');
        this.resultOutputFormat = resultCard.querySelector('#resultOutputFormat');
        this.resultFileType = resultCard.querySelector('#resultFileType');
        this.convertAnotherBtn = resultCard.querySelector('#convertAnotherBtn');
        this.backToUploadBtn = resultCard.querySelector('a[href="#uploadSection"]');
        this.errorCard = errorCard;
        this.errorMessage = errorCard.querySelector('#errorMessage');
        this.tryAgainBtn = errorCard.querySelector('#tryAgainBtn');

        if(this.convertAnotherBtn){
            this.convertAnotherBtn.addEventListener('click', () => {
                this.resetUpload();
                if(this.resultCard){
                    this.resultCard.hidden = true;
                    this.resultCard.style.display = 'none';
                }
                if(this.errorCard){
                    this.errorCard.hidden = true;
                    this.errorCard.style.display = 'none';
                }
                const uploadSection = document.getElementById('uploadSection');
                if(uploadSection && typeof uploadSection.scrollIntoView === 'function'){
                    uploadSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }

        if(this.backToUploadBtn){
            this.backToUploadBtn.addEventListener('click', (event) => {
                event.preventDefault();
                const uploadSection = document.getElementById('uploadSection');
                if(uploadSection && typeof uploadSection.scrollIntoView === 'function'){
                    uploadSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }

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
                this.resultFileName.textContent = window.translate('upload.file_ready_for_download', 'File ready for download');
            }
            if(this.resultMetaName){
                this.resultMetaName.textContent = file?.name || '';
            }
            if(this.resultOutputFormat){
                const outputFormat = window.converter?.selectedFormat || '';
                this.resultOutputFormat.textContent = outputFormat ? outputFormat.toUpperCase() : '';
            }
            if(this.resultFileType){
                const fileType = file?.type || file?.name?.split('.').pop()?.toUpperCase() || '';
                this.resultFileType.textContent = fileType;
            }
            this.resultCard.hidden = false;
            this.resultCard.style.display = '';
            if(window.converigoAnalytics && typeof window.converigoAnalytics.trackEvent === 'function'){
                window.converigoAnalytics.trackEvent('success_popup_view', {
                    page_path: window.location.pathname || '/',
                    converter_name: window.converter?.selectedFormat || '',
                    event_status: 'success'
                });
            }
        }
        if(window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function'){
            window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.SUCCESS);
        }
        // Ensure upload-card reflects success state (defensive)
        try {
            const uploadCard = this._findUploadCard();
            if (uploadCard) {
                uploadCard.classList.remove('state-uploading', 'state-error');
                uploadCard.classList.add('state-success');
            }
        } catch (e) {}
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
            if(window.converigoAnalytics && typeof window.converigoAnalytics.trackEvent === 'function'){
                window.converigoAnalytics.trackEvent('error_popup_view', {
                    page_path: window.location.pathname || '/',
                    error_type: 'conversion_error',
                    event_status: 'failure'
                });
            }
        }
        if(window.conversionStateController && typeof window.conversionStateController.setConversionState === 'function'){
            window.conversionStateController.setConversionState(window.conversionStateController.ConversionState.ERROR);
        }
        // Mark upload card with error state for DevTools
        try {
            const uploadCard = this._findUploadCard();
            if (uploadCard) {
                uploadCard.classList.remove('state-uploading', 'state-success');
                uploadCard.classList.add('state-error');
            }
        } catch (e) {}
    }

    _emitFileSelected(file, files = []){
        try{ if(window.downloadManager && typeof window.downloadManager.clear === 'function'){ window.downloadManager.clear(); } }catch(e){ console.warn('downloadManager.clear failed', e); }
        window.dispatchEvent(new CustomEvent('file-selected', { detail: { file: file, files: files } }));
    }

    // backward compatible
    emitFileSelected(file){ return this._emitFileSelected(file); }
}

document.addEventListener('DOMContentLoaded', ()=>{ window.uploadManager = new UploadManager(); });
