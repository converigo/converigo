/**
 * -------------------------------------------------------
 * Convertin
 * Upload Manager
 * Version : 3.0.0
 *
 * Handles:
 * - File selection
 * - File information display
 * - Trigger recommendation engine
 *
 * -------------------------------------------------------
 */


class UploadManager {


    constructor(
        fileInputId = "fileInput",
        chooseButtonId = "chooseFile"
    ){


        this.fileInput =
            document.getElementById(
                fileInputId
            );


        this.chooseButton =
            document.getElementById(
                chooseButtonId
            );


        this.fileName =
            document.getElementById(
                "fileName"
            );


        this.fileSize =
            document.getElementById(
                "fileSize"
            );


        this.convertBtn =
            document.getElementById(
                "convertBtn"
            );


        this.init();


    }








    init(){



        console.log(
            "Upload Manager Loaded"
        );



        if(
            !this.fileInput ||
            !this.chooseButton
        ){

            console.error(
                "Upload elements missing"
            );


            return;


        }




        this.bindEvents();



    }









    bindEvents(){



        this.chooseButton.addEventListener(

            "click",

            ()=>{


                console.log(
                    "Choose File Clicked"
                );


                this.fileInput.click();


            }

        );







        this.fileInput.addEventListener(

            "change",

            ()=>{


                const file =
                    this.getFile();




                if(!file){

                    return;

                }



                this.updateFileInfo(
                    file
                );



                this.runRecommendation(
                    file
                );



            }

        );



    }









    updateFileInfo(file){



        if(this.fileName){


            this.fileName.textContent =
                file.name;


        }






        if(this.fileSize){


            this.fileSize.textContent =

                (

                    file.size /
                    1024 /
                    1024

                ).toFixed(2)
                + " MB";


        }






        if(this.convertBtn){


            this.convertBtn.hidden =
                false;


        }



    }









    async runRecommendation(file){



        if(
            !window.RecommendationManager
        ){


            console.warn(

                "RecommendationManager not loaded"

            );


            return;


        }





        await window.RecommendationManager

            .analyzeFile(
                file
            );



    }









    getFile(){



        if(!this.fileInput){


            return null;


        }



        return this.fileInput.files[0];



    }









    getExtension(){



        const file =
            this.getFile();




        if(!file){


            return "";

        }




        return file.name

            .split(".")

            .pop()

            .toLowerCase();



    }



}







document.addEventListener(

    "DOMContentLoaded",

    ()=>{


        window.uploadManager =
            new UploadManager();



    }

);