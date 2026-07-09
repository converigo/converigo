/**
 * -------------------------------------------------------
 * Convertin
 * converter.js
 * Version : 4.0.0
 *
 * Handles conversion process only.
 * Upload handled by UploadManager.
 * Dynamic format handled by ButtonRenderer.
 * -------------------------------------------------------
 */


class FileConverter {



    constructor(){


        this.fileInput =
            document.getElementById(
                "fileInput"
            );



        this.convertBtn =
            document.getElementById(
                "convertBtn"
            );



        this.downloadBtn =
            document.getElementById(
                "downloadBtn"
            );



        this.convertMessage =
            document.getElementById(
                "convertMessage"
            );



        this.progressBar =
            document.querySelector(
                ".progress-bar"
            );



        this.formatContainer =
            document.getElementById(
                "formatContainer"
            );



        this.selectedFormat =
            null;



        this.bindEvents();


    }








    bindEvents(){



        /*
         * Dynamic format button handler
         *
         * Button dibuat oleh ButtonRenderer,
         * jadi gunakan event delegation.
         */


        if(this.formatContainer){


            this.formatContainer.addEventListener(

                "click",

                (event)=>{


                    const button =
                        event.target.closest(
                            ".format-btn"
                        );



                    if(!button){

                        return;

                    }





                    this.formatContainer

                        .querySelectorAll(
                            ".format-btn"
                        )

                        .forEach(

                            (btn)=>{


                                btn.classList.remove(
                                    "active"
                                );


                            }

                        );






                    button.classList.add(
                        "active"
                    );





                    this.selectedFormat =
                        button.dataset.format;





                    console.log(

                        "Selected format:",
                        this.selectedFormat

                    );



                }

            );


        }








        if(this.convertBtn){



            this.convertBtn.addEventListener(

                "click",

                ()=>{


                    this.handleConvert();



                }

            );



        }



    }









    getFile(){



        if(!this.fileInput){


            return null;


        }




        return this.fileInput.files[0];



    }









    async handleConvert(){



        const file =
            this.getFile();





        if(!file){



            this.showMessage(

                "Please choose a file."

            );


            return;


        }






        if(!this.selectedFormat){



            this.showMessage(

                "Please choose target format."

            );


            return;


        }







        this.setLoading(true);




        this.updateProgress(
            20
        );







        const formData =
            new FormData();





        formData.append(

            "file",

            file

        );





        formData.append(

            "target_format",

            this.selectedFormat

        );







        try {



            const response =
                await fetch(

                    "/convert",

                    {

                        method:"POST",

                        body:formData

                    }

                );







            const data =
                await response.json();







            if(!response.ok){



                throw new Error(

                    data.detail ||
                    "Conversion failed."

                );



            }







            this.updateProgress(
                100
            );








            this.showMessage(

                data.message ||
                "Conversion complete."

            );







            this.showDownload(

                data

            );






        }



        catch(error){



            console.error(
                error
            );




            this.showMessage(

                error.message

            );





            this.updateProgress(
                0
            );



        }





        finally{


            this.setLoading(false);


        }



    }









    showDownload(data){



        if(!this.downloadBtn){


            return;


        }






        this.downloadBtn.hidden =
            false;






        this.downloadBtn.href =
            data.download_path;






        this.downloadBtn.download =
            data.filename;






        this.downloadBtn.textContent =

            "Download " +
            data.filename;



    }









    setLoading(state){



        if(this.convertBtn){



            this.convertBtn.disabled =
                state;



        }


    }









    updateProgress(value){



        if(this.progressBar){



            this.progressBar.style.width =
                value + "%";



        }


    }









    showMessage(message){



        if(this.convertMessage){



            this.convertMessage.textContent =
                message;



        }


    }





}








document.addEventListener(

    "DOMContentLoaded",

    ()=>{


        window.converter =
            new FileConverter();



    }

);