/*
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation Manager

Handles smart converter suggestions.
*/


class RecommendationManager {


    constructor(){


        this.endpoint = "/recommend";


        this.smartPanel =
            document.getElementById(
                "smartPanel"
            );


        this.detectedFile =
            document.getElementById(
                "detectedFile"
            );


        this.recommendedFormat =
            document.getElementById(
                "recommendedFormat"
            );


        this.otherFormats =
            document.getElementById(
                "otherFormats"
            );


        this.formatContainer =
            document.getElementById(
                "formatContainer"
            );


    }





    async getRecommendation(format){


        try{


            const response =
                await fetch(
                    `${this.endpoint}/${format}`
                );


            if(!response.ok){

                return null;

            }


            return await response.json();


        }
        catch(error){


            console.error(
                error
            );


            return null;

        }


    }








    async analyzeFile(file){


        if(!file){

            return;

        }



        const extension =
            file.name
            .split(".")
            .pop()
            .toLowerCase();



        const result =
            await this.getRecommendation(
                extension
            );



        if(!result){

            return;

        }



        this.smartPanel.hidden =
            false;



        this.renderDetected(
            file,
            extension
        );



        this.renderRecommendation(
            result
        );



        this.renderAlternatives(
            result
        );


        this.autoSelectBest(
            result
        );


    }








    renderDetected(
        file,
        extension
    ){


        this.detectedFile.innerHTML = `

        <div class="detected-card">

            📄

            <strong>
            ${file.name}
            </strong>

            <br>

            Type:
            ${extension.toUpperCase()}

            <br>

            Size:
            ${(file.size / 1024 / 1024).toFixed(2)}
            MB

        </div>

        `;


    }









    renderRecommendation(data){


        const best =
            data.best_choice;



        this.recommendedFormat.innerHTML = `

        <div class="recommend-card">


            <h3>

            ${best.icon}

            ${best.title}

            </h3>


            <span class="badge">

            ${best.badge}

            </span>


            <p>

            ${best.description}

            </p>


        </div>

        `;


    }









    renderAlternatives(data){


        this.otherFormats.innerHTML = "";



        data.alternatives.forEach(

            item=>{


                this.createFormatButton(
                    item.target
                );


            }

        );


    }









    autoSelectBest(data){


        const best =
            data.best_choice.target;



        this.createFormatButton(
            best,
            true
        );



        if(window.converter){


            window.converter.selectedFormat =
                best;



            console.log(
                "Auto selected:",
                best
            );


        }


    }









    createFormatButton(
        format,
        active=false
    ){


        if(!this.formatContainer){

            return;

        }



        const exists =
            this.formatContainer.querySelector(
                `[data-format="${format}"]`
            );



        if(exists){

            return;

        }



        const button =
            document.createElement(
                "button"
            );


        button.type =
            "button";


        button.className =
            "format-btn";



        button.dataset.format =
            format;



        button.textContent =
            format.toUpperCase();



        if(active){

            button.classList.add(
                "active"
            );

        }



        this.formatContainer.appendChild(
            button
        );


    }



}





window.RecommendationManager =
    new RecommendationManager();