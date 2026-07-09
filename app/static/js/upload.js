/*
 * -------------------------------------------------------
 * Convertin
 * upload.js
 * Version : 2.2.0
 *
 * Upload Controller
 * -------------------------------------------------------
 */


console.log("UPLOAD JS LOADED");



document.addEventListener(
    "DOMContentLoaded",
    () => {


        console.log("UPLOAD DOM READY");



        const chooseButton =
            document.getElementById(
                "chooseFile"
            );



        const fileInput =
            document.getElementById(
                "fileInput"
            );



        const fileName =
            document.getElementById(
                "fileName"
            );



        const fileSize =
            document.getElementById(
                "fileSize"
            );



        const convertBtn =
            document.getElementById(
                "convertBtn"
            );





        console.log(
            "chooseButton:",
            chooseButton
        );


        console.log(
            "fileInput:",
            fileInput
        );






        if(
            !chooseButton ||
            !fileInput
        ){

            console.error(
                "Upload elements not found"
            );

            return;

        }








        chooseButton.addEventListener(

            "click",

            (event)=>{


                console.log(
                    "Choose File clicked"
                );


                event.preventDefault();



                fileInput.click();


            }

        );









        fileInput.addEventListener(

            "change",

            ()=>{


                console.log(
                    "File selected"
                );



                const file =
                    fileInput.files[0];



                if(!file){

                    return;

                }






                console.log(
                    file.name
                );








                if(fileName){


                    fileName.textContent =
                        file.name;


                }








                if(fileSize){


                    fileSize.textContent =

                        (
                            file.size /
                            1024 /
                            1024

                        ).toFixed(2)
                        + " MB";


                }








                if(convertBtn){


                    convertBtn.hidden =
                        false;


                }





            }

        );





    }

);