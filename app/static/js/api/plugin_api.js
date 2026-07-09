/**
 * -------------------------------------------------------
 * Convertin
 * Plugin API
 * Version : 2.0.0
 * -------------------------------------------------------
 */


class PluginAPI {



    async getSupportedFormats(sourceFormat) {


        const response = await fetch(

            `/api/plugins?source=${encodeURIComponent(sourceFormat)}`

        );


        if(!response.ok){


            throw new Error(
                "Failed to load supported converters."
            );


        }


        return await response.json();


    }







    async getRecommendation(sourceFormat){



        const response = await fetch(

            `/recommend/${encodeURIComponent(sourceFormat)}`

        );



        if(!response.ok){


            throw new Error(

                "Failed to load recommendation."

            );


        }



        return await response.json();



    }



}





window.PluginAPI =
    PluginAPI;