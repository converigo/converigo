document.addEventListener('DOMContentLoaded', function () {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }

    const navToggle = document.getElementById('navToggle');
    const primaryNav = document.getElementById('primaryNav');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileSelect = document.getElementById('fileSelect');
    const fileName = document.getElementById('fileName');
    const progressBar = document.querySelector('.progress-bar');
    const faqItems = document.querySelectorAll('.faq-item');

    if (navToggle && primaryNav) {
        navToggle.addEventListener('click', function () {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', String(!expanded));
            primaryNav.classList.toggle('open');
        });
    }

    function setProgress(percentage) {
        if (progressBar) {
            progressBar.style.width = Math.min(100, percentage) + '%';
        }
    }

    const clearFile = document.getElementById('clearFile');
    const fileSize = document.getElementById('fileSize');
    const uploadStatus = document.getElementById('uploadStatus');

    function updateFileName(file) {
        if (!fileName) return;
        fileName.textContent = file ? `${file.name}` : 'No file selected yet';
        if (fileSize) {
            fileSize.textContent = file ? `${Math.round(file.size / 1024)} KB` : '0 KB';
        }
        if (uploadStatus) {
            uploadStatus.textContent = file ? 'Ready to convert' : 'Waiting for your file';
        }
        if (clearFile) {
            clearFile.hidden = !file;
        }
    }

    function startProgressSimulation() {
        if (!progressBar) return;
        let progress = 0;
        setProgress(0);

        const timer = window.setInterval(function () {
            progress += Math.floor(Math.random() * 18) + 12;
            setProgress(progress);
            if (progress >= 100) {
                window.clearInterval(timer);
                setProgress(100);
            }
        }, 220);
    }

    if (fileSelect && fileInput) {
        fileSelect.addEventListener('click', function () {
            fileInput.click();
        });
    }

    if (clearFile) {
        clearFile.addEventListener('click', function () {
            if (!fileInput) return;
            fileInput.value = '';
            updateFileName(null);
            setProgress(0);
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const file = this.files && this.files[0];
            updateFileName(file);
            if (file) {
                startProgressSimulation();
            } else {
                setProgress(0);
            }
        });
    }

    if (dropzone && fileInput) {
        ['dragenter', 'dragover'].forEach(function (eventName) {
            dropzone.addEventListener(eventName, function (event) {
                event.preventDefault();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(function (eventName) {
            dropzone.addEventListener(eventName, function (event) {
                event.preventDefault();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', function (event) {
            const dataTransfer = event.dataTransfer;
            if (dataTransfer && dataTransfer.files && dataTransfer.files[0]) {
                fileInput.files = dataTransfer.files;
                fileInput.dispatchEvent(new Event('change'));
            }
        });

        dropzone.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                fileInput.click();
            }
        });
    }

    window.addEventListener('scroll', function () {
        const header = document.querySelector('.site-header');
        if (!header) return;

        if (window.scrollY > 20) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    faqItems.forEach(function (item) {
        const button = item.querySelector('.faq-question');
        if (!button) return;

        button.addEventListener('click', function () {
            const isActive = item.classList.contains('active');
            faqItems.forEach(function (element) {
                element.classList.remove('active');
            });

            if (!isActive) {
                item.classList.add('active');
            }
        });
    });

    updateFileName(null);
});
