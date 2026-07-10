/*
 * -------------------------------------------------------
 * Convertin
 * upload.js
 * Version : 3.0.0
 *
 * Upload Controller
 *
 * Update:
 * - Choose File
 * - Drag & Drop
 * - File Preview
 * - Better UX
 * -------------------------------------------------------
 */


console.log("UPLOAD JS LOADED");



document.addEventListener(
    "DOMContentLoaded",
    ()=>{


        console.log(
            "UPLOAD DOM READY"
        );




        const chooseButton =
            document.getElementById(
                "chooseFile"
            );



        const fileInput =
            document.getElementById(
                "fileInput"
            );



        const dropZone =
            document.getElementById(
                "dropZone"
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







        if(
            !chooseButton ||
            !fileInput
        ){


            console.error(
                "Upload elements missing"
            );


            return;


        }








        /*
        =================================
        CHOOSE FILE
        =================================
        */


        chooseButton.addEventListener(

            "click",

            (event)=>{


                event.preventDefault();


                fileInput.click();


            }

        );









        /*
        =================================
        INPUT CHANGE
        =================================
        */


        fileInput.addEventListener(

            "change",

            ()=>{


                const file =
                    fileInput.files[0];


                if(!file){

                    return;

                }


                handleFile(
                    file
                );


            }

        );









        /*
        =================================
        DRAG EVENTS
        =================================
        */


        if(dropZone){



            [
                "dragenter",
                "dragover"

            ].forEach(


                eventName=>{


                    dropZone.addEventListener(

                        eventName,

                        (event)=>{


                            event.preventDefault();


                            event.stopPropagation();


                            dropZone.classList.add(

                                "drag-active"

                            );


                        }

                    );


                }


            );









            [
                "dragleave",
                "drop"

            ].forEach(


                eventName=>{


                    dropZone.addEventListener(

                        eventName,

                        (event)=>{


                            event.preventDefault();


                            event.stopPropagation();


                            dropZone.classList.remove(

                                "drag-active"

                            );


                        }

                    );


                }


            );









            dropZone.addEventListener(

                "drop",

                (event)=>{


                    const files =
                        event.dataTransfer.files;



                    if(
                        !files ||
                        !files.length
                    ){

                        return;

                    }





                    const file =
                        files[0];




                    fileInput.files =
                        files;




                    handleFile(
                        file
                    );



                }

            );



        }









        /*
        =================================
        FILE HANDLER
        =================================
        */


        function handleFile(file){



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








            if(convertBtn){


                convertBtn.disabled =
                    false;


            }







            /*
            Send file to recommendation
            */


            if(
                window.RecommendationManager
            ){


                window.RecommendationManager
                    .analyzeFile(
                        file
                    );


            }




        }



    }

);