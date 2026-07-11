/**
 * -------------------------------------------------------
 * Converigo
 * Convert Manager
 * Version : 1.0.0
 * -------------------------------------------------------
 */

class ConvertManager {

    async convert(file, targetFormat) {

        const formData = new FormData();

        formData.append(
            "file",
            file
        );

        formData.append(
            "target_format",
            targetFormat
        );

        const response = await fetch(
            "/convert",
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(

                data.detail ||

                window.translate('upload.conversion_failed', 'Conversion failed.')

            );

        }

        return data;

    }

}

window.ConvertManager =
    ConvertManager;