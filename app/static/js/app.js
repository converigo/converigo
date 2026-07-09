/*
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.0.0

Smart Upload + Recommendation Integration
*/


document.addEventListener(
    "DOMContentLoaded",
    () => {


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


    const uploadStatus =
        document.getElementById(
            "uploadStatus"
        );



    if(!fileInput){

        return;

    }



    fileInput.addEventListener(
        "change",
        async () => {


        const file =
            fileInput.files[0];


        if(!file){

            return;

        }



        const extension =
            file.name
            .split(".")
            .pop()
            .toLowerCase();



        const size =
            (
                file.size /
                1024 /
                1024
            )
            .toFixed(2);



        if(fileName){

            fileName.textContent =
                file.name;

        }



        if(fileSize){

            fileSize.textContent =
                `${size} MB`;

        }



        if(uploadStatus){

            uploadStatus.textContent =
                "Analyzing file...";

        }



        if(convertBtn){

            convertBtn.hidden =
                false;

        }



        await loadRecommendation(
            extension
        );



        if(uploadStatus){

            uploadStatus.textContent =
                "Ready to Convert";

        }


    });



});





async function loadRecommendation(
    extension
){

    const container =
        document.getElementById(
            "smartRecommendation"
        );


    if(!container){

        console.warn(
            "smartRecommendation container missing"
        );

        return;

    }



    const result =
        await RecommendationManager
        .getRecommendation(
            extension
        );



    if(!result){

        container.innerHTML = `

        <div class="recommend-card">

            No recommendation available.

        </div>

        `;


        return;

    }



    const best =
        result.best_choice;



    let alternatives = "";



    result.alternatives.forEach(
        item => {


        alternatives += `

        <button class="format-chip">

            ${item.title}

        </button>

        `;


    });



    container.innerHTML = `

    <div class="recommend-card">


        <div class="recommend-header">

            ${best.icon}

            Recommended

        </div>



        <h3>

            ${best.title}

        </h3>



        <span class="badge">

            ${best.badge}

        </span>



        <p>

            ${best.description}

        </p>



        <strong>

            Score:
            ${best.score}

        </strong>



        <div class="alternatives">

            ${alternatives}

        </div>



    </div>

    `;


}