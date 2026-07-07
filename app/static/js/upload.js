document.addEventListener("DOMContentLoaded", () => {

    const chooseButton = document.getElementById("chooseFile");
    const fileInput = document.getElementById("fileInput");
    const selectedFile = document.getElementById("selectedFile");
    const convertButton = document.getElementById("convertButton");

    if (!chooseButton || !fileInput || !selectedFile) return;

    chooseButton.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {

        const file = fileInput.files[0];

        if (!file) return;

        selectedFile.textContent =
            `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;

        if (convertButton) {
            convertButton.hidden = false;
        }

    });

});