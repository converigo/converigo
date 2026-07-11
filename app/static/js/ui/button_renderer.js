/*
====================================================
Converigo
Button Renderer
Version : 1.1.1
====================================================
*/

class ButtonRenderer {
    constructor(containerId){
        this.container = document.getElementById(containerId);
    }

    clear(){
        if(this.container) this.container.innerHTML = "";
    }

    render(formats, onClick){
        if(!this.container) return;
        this.clear();

        formats.forEach(format => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "format-chip";
            btn.textContent = format.target.toUpperCase();

            btn.addEventListener("click", () => {
                document.querySelectorAll('.format-chip').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                window.dispatchEvent(new CustomEvent('format-selected', { detail: { target: format.target } }));

                if(onClick) onClick(format.target);
            });

            this.container.appendChild(btn);
        });
    }
}

window.ButtonRenderer = ButtonRenderer;
