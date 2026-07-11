/**
 * -------------------------------------------------------
 * Converigo
 * Download Manager
 * Version : 1.2.0
 *
 * Handles:
 * - Prepare download button
 * - Clear old download
 * - Clean download UI
 * - Global instance
 * -------------------------------------------------------
 */


class DownloadManager {


    constructor(downloadButtonId = "downloadBtn") {


        this.button =

            document.getElementById(
                downloadButtonId
            );


        console.log(
            "Download Manager Loaded"
        );

        // Ensure the download button is hidden and cleaned on load
        if(this.button){
            this.clear();
        }

    }

    
    








    clear(){



        if(!this.button){

            return;

        }




        this.button.hidden = true;




        this.button.removeAttribute(
            "href"
        );




        this.button.removeAttribute(
            "download"
        );




        this.button.textContent =

            "Download";



    }









    prepare(result){



        if(!this.button){


            console.warn(

                "Download button missing"

            );


            return;


        }





        if(!result){


            console.warn(

                "Download result missing"

            );


            return;


        }






        const filename =

            result.filename ||

            "converted-file";







        const extension =

            filename

            .split(".")

            .pop()

            .toUpperCase();







        this.button.hidden = false;







        this.button.href =

            result.download_path;








        this.button.download =

            filename;









        /*
        Premium clean button text
        */


        this.button.textContent =

            "Download " +

            extension;








        console.log(

            "Download Ready:",

            filename

        );



    }



}









/*
================================================
Initialize Download Manager
================================================
*/


document.addEventListener(


    "DOMContentLoaded",


    ()=>{


        window.downloadManager =


            new DownloadManager(

                "downloadBtn"

            );





        console.log(

            "DownloadManager Ready"

        );



    }


);