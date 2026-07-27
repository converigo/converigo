/**
 * -------------------------------------------------------
 * Converigo
 *
 * Recommendation Manager
 * Version : 3.8.0
 *
 * Connect:
 * Upload
 * ->
 * Backend Recommendation API
 * ->
 * Format Selector
 *
 * -------------------------------------------------------
 */


class RecommendationManager {



    constructor(){


        console.log(
            "Recommendation Manager 3.8.0 Loaded"
        );

        console.log("Recommendation Manager 3.8.0 Loaded");

        this.formatContainer = document.getElementById("formatOptions");
        this.conversionArea = document.getElementById("conversionArea");
        this.convertButton = document.getElementById("convertButton");
        this.formatSearch = document.getElementById("formatSearch");
        this.selectedFormat = null;
        this._bindSearch();
    }

    _bindSearch(){
        if (!this.formatSearch || !this.formatContainer) return;
        this.formatSearch.hidden = false;
        this.formatSearch.addEventListener('input', () => {
            const query = this.formatSearch.value.trim().toLowerCase();
            const buttons = Array.from(this.formatContainer.querySelectorAll('.format-chip'));
            buttons.forEach(btn => {
                const text = (btn.dataset.label || btn.textContent || '').toLowerCase();
                const match = !query || text.includes(query);
                btn.hidden = !match;
                btn.style.display = match ? '' : 'none';
            });
        });
    }

    async analyzeFile(file) {
        if (!file || !file.name) return;
        console.log("Analyzing:", file.name);
        const extension = file.name.split('.').pop().toLowerCase();
        try {
            const response = await fetch(`/recommend/${extension}`);
            if (!response.ok) {
                throw new Error('No recommendation');
            }
            const data = await response.json().catch(() => null) || {};
            // Always delegate rendering to renderFormats on successful response
            try {
                this.renderFormats(data);
            } catch (e) {
                console.error('Recommendation render failed:', e);
            }
        } catch (error) {
            console.error('Recommendation failed:', error);
        }
    }




    _formatIcon(target){
        const value = (target || '').toLowerCase();
        if (value.includes('pdf')) return '📄';
        if (value.includes('doc') || value.includes('docx')) return '📝';
        if (value.includes('png') || value.includes('jpg') || value.includes('jpeg') || value.includes('webp')) return '🖼';
        if (value.includes('mp4') || value.includes('mov') || value.includes('webm')) return '🎬';
        if (value.includes('mp3') || value.includes('wav') || value.includes('flac')) return '🎵';
        if (value.includes('zip') || value.includes('rar') || value.includes('7z')) return '🗜';
        return '📦';
    }

    renderFormats(data){



        if(!this.formatContainer){

            console.warn(
                "formatOptions missing"
            );

            return;

        }





        this.formatContainer.innerHTML = "";





        if(window.conversionStateController && typeof window.conversionStateController.setFormatChoicesAvailable === 'function'){
            window.conversionStateController.setFormatChoicesAvailable(false);
        } else if(this.conversionArea){
            this.conversionArea.hidden = true;
        }

        const choices = [];
        let autoSelectButton = null;
        let autoSelectTarget = null;



        if(
            data.best_choice
        ){

            choices.push(
                data.best_choice
            );

        }







        if(
            data.alternatives
        ){

            data.alternatives.forEach(
                item=>{


                    choices.push(
                        item
                    );


                }
            );


        }







        choices.forEach(
            option=>{


                const button =
                    document.createElement(
                        "button"
                    );


                button.className =
                    "format-chip";



                const label = option.target.toUpperCase();
                const icon = this._formatIcon(option.target);
                button.innerHTML = `<span class="format-chip-icon" aria-hidden="true">${icon}</span><span class="format-chip-label">${label}</span>`;



                button.dataset.target =
                    option.target;
                button.dataset.label = label;





                button.onclick = ()=>{


                    document
                    .querySelectorAll(
                        ".format-chip"
                    )
                    .forEach(
                        btn => btn.classList.remove("active")
                    );



                    // preserve previous behaviour
                    button.classList.add('active');



                    this.selectedFormat = option.target;




                    window.dispatchEvent(

                        new CustomEvent(
                            "format-selected",
                            {
                                detail:{
                                    target:
                                    option.target
                                }
                            }
                        )

                    );



                    if(window.conversionStateController && typeof window.conversionStateController.setConvertReady === 'function'){
                        // Ensure format choices and conversion state are set as well
                        if (typeof window.conversionStateController.setFormatChoicesAvailable === 'function') {
                            window.conversionStateController.setFormatChoicesAvailable(true);
                        }
                        if (typeof window.conversionStateController.setConversionState === 'function') {
                            try {
                                const cs = window.conversionStateController.ConversionState || {};
                                const fileSelected = cs.FILE_SELECTED || 'FILE_SELECTED';
                                window.conversionStateController.setConversionState(fileSelected);
                            } catch (e) {
                                window.conversionStateController.setConversionState('FILE_SELECTED');
                            }
                        }
                        window.conversionStateController.setConvertReady(true);
                    } else if(this.convertButton){
                        this.convertButton.disabled = false;
                        this.convertButton.hidden = false;
                        this.convertButton.style.removeProperty('display');
                    }


                };





                this.formatContainer.appendChild(
                    button
                );

                if (!autoSelectButton) {
                    autoSelectButton = button;
                    autoSelectTarget = option.target;
                }


            }
        );

        if (autoSelectButton && autoSelectTarget) {
            autoSelectButton.classList.add("active");
            this.selectedFormat = autoSelectTarget;
            if (window.uploadManager && typeof window.uploadManager._updateConversionSummary === 'function') {
                window.uploadManager._updateConversionSummary();
            }
            window.dispatchEvent(
                new CustomEvent(
                    "format-selected",
                    {
                        detail:{
                            target: autoSelectTarget
                        }
                    }
                )
            );
            if(window.conversionStateController && typeof window.conversionStateController.setConvertReady === 'function'){
                if (typeof window.conversionStateController.setFormatChoicesAvailable === 'function') {
                    window.conversionStateController.setFormatChoicesAvailable(true);
                }
                if (typeof window.conversionStateController.setConversionState === 'function') {
                    try {
                        const cs = window.conversionStateController.ConversionState || {};
                        const fileSelected = cs.FILE_SELECTED || 'FILE_SELECTED';
                        window.conversionStateController.setConversionState(fileSelected);
                    } catch (e) {
                        window.conversionStateController.setConversionState('FILE_SELECTED');
                    }
                }
                window.conversionStateController.setConvertReady(true);
            } else if(this.convertButton){
                this.convertButton.disabled = false;
                this.convertButton.hidden = false;
                this.convertButton.style.removeProperty('display');
            }
        }

        if(window.conversionStateController && typeof window.conversionStateController.setFormatChoicesAvailable === 'function'){
            window.conversionStateController.setFormatChoicesAvailable(choices.length > 0);
        } else if(this.conversionArea){
            this.conversionArea.hidden = choices.length === 0;
        }


    }




}







document.addEventListener(

    "DOMContentLoaded",

    ()=>{


        window.RecommendationManager =
            new RecommendationManager();


    }

);