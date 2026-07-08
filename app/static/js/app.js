document.addEventListener("DOMContentLoaded", () => {

    if (window.lucide && typeof window.lucide.createIcons === "function") {
        window.lucide.createIcons();
    }

    const navToggle = document.getElementById("navToggle");
    const primaryNav = document.getElementById("primaryNav");

    if (navToggle && primaryNav) {

        navToggle.addEventListener("click", () => {

            const expanded =
                navToggle.getAttribute("aria-expanded") === "true";

            navToggle.setAttribute(
                "aria-expanded",
                String(!expanded)
            );

            primaryNav.classList.toggle("open");

        });

    }

    window.addEventListener("scroll", () => {

        const header = document.querySelector(".site-header");

        if (!header) return;

        if (window.scrollY > 20) {

            header.classList.add("scrolled");

        } else {

            header.classList.remove("scrolled");

        }

    });

    document.querySelectorAll(".faq-item").forEach((item) => {

        const button = item.querySelector(".faq-question");

        if (!button) return;

        button.addEventListener("click", () => {

            const active = item.classList.contains("active");

            document.querySelectorAll(".faq-item").forEach((el) => {

                el.classList.remove("active");

            });

            if (!active) {

                item.classList.add("active");

            }

        });

    });

});