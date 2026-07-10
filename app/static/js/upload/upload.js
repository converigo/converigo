/*
====================================================
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.3.0

Upload Controller

Features:
- File picker
- File information
- Drag drop support
- Send file event to converter
====================================================
*/


console.log(
    "UPLOAD JS LOADED"
);





document.addEventListener(

    "DOMContentLoaded",

    ()=>{



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








        if(
            !chooseButton ||
            !fileInput
        ){


            console.error(
                "Upload element missing"
            );


            return;


        }









        chooseButton.addEventListener(


            "click",

            ()=>{


                fileInput.click();


            }


        );









        fileInput.addEventListener(


            "change",

            ()=>{



                const file =

                    fileInput.files[0];





                if(!file){


                    return;


                }







                console.log(

                    "Selected:",

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

                        +

                        " MB";



                }









                /*
                Send file to converter
                */


                document.dispatchEvent(
                    new CustomEvent(
                        "file-selected",
                        { detail: { file: file } }
                    )
                );








                /*
                Send file to recommendation
                */


                if(window.RecommendationManager){


                    window.RecommendationManager.analyzeFile(

                        file

                    );


                }







            }


        );






    }


);