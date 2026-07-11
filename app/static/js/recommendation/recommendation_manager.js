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





        const choices = [];



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



                    if(this.convertButton){

                        this.convertButton.disabled =
                            false;

                    }


                };





                this.formatContainer.appendChild(
                    button
                );



            }
        );




    }




}







document.addEventListener(

    "DOMContentLoaded",

    ()=>{


        window.RecommendationManager =
            new RecommendationManager();


    }

);