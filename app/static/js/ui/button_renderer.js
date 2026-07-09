/**
 * -------------------------------------------------------
 * Convertin
 * Button Renderer
 * Version : 1.0.0
 * -------------------------------------------------------
 */

class ButtonRenderer {

    constructor(containerId) {

        this.container =
            document.getElementById(containerId);

    }

    clear() {

        if (!this.container) {

            return;

        }

        this.container.innerHTML = "";

    }

    render(formats, onClick) {

        this.clear();

        formats.forEach((item) => {

            const button =
                document.createElement("button");

            button.type = "button";

            button.className =
                "format-btn";

            button.dataset.format =
                item.target;

            button.textContent =
                item.target.toUpperCase();

            button.addEventListener(

                "click",

                () => {

                    this.container

                        .querySelectorAll(".format-btn")

                        .forEach((btn) => {

                            btn.classList.remove("active");

                        });

                    button.classList.add("active");

                    onClick(item.target);

                }

            );

            this.container.appendChild(button);

        });

    }

}

window.ButtonRenderer =
    ButtonRenderer;