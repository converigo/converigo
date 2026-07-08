document.addEventListener("DOMContentLoaded", () => {

    const chooseButton = document.getElementById("chooseFile");
    const fileInput = document.getElementById("fileInput");

    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");

    const convertBtn = document.getElementById("convertBtn");

    if (!chooseButton || !fileInput) return;

    chooseButton.addEventListener("click", () => {

        fileInput.click();

    });

    fileInput.addEventListener("change", () => {

        const file = fileInput.files[0];

        if (!file) return;

        fileName.textContent = file.name;

        fileSize.textContent =
            (file.size / 1024 / 1024).toFixed(2) + " MB";

        convertBtn.hidden = false;

    });

});