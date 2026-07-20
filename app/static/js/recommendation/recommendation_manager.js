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


        this.formatContainer =
            document.getElementById(
                "formatOptions"
            );


        this.conversionArea =
            document.getElementById(
                "conversionArea"
            );


        this.convertButton =
            document.getElementById(
                "convertButton"
            );


        this.selectedFormat = null;



    }






    async analyzeFile(file){


        console.log(
            "Analyzing:",
            file.name
        );



        const extension =
            file.name
            .split(".")
            .pop()
            .toLowerCase();



        try{


            const response =
                await fetch(
                    `/recommend/${extension}`
                );



            if(!response.ok){


                throw new Error(
                    "No recommendation"
                );


            }




            const data =
                await response.json();



            console.log(
                "Recommendation:",
                data
            );



            this.renderFormats(
                data
            );



        }

        catch(error){


            console.error(
                "Recommendation failed:",
                error
            );


        }


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



                button.textContent =
                    option.target
                    .toUpperCase();



                button.dataset.target =
                    option.target;





                button.onclick = ()=>{


                    document
                    .querySelectorAll(
                        ".format-chip"
                    )
                    .forEach(
                        btn => btn.classList.remove("active")
                    );



                    button.classList.add(
                        "active"
                    );



                    this.selectedFormat =
                        option.target;




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