# DOCKERFILE DEPENDENCY AUDIT REPORT

## Base Image
- `python:3.11-slim`
- Minimal Python base image appropriate for a lightweight FastAPI application.

## Installed Packages
- `ffmpeg`
- `libreoffice`
- `p7zip-full`
- `unrar-free`
- `libcairo2`
- `libpango-1.0-0`
- `libgdk-pixbuf-xlib-2.0-0`
- `librsvg2-dev`
- `libheif1`
- `libheif-dev`
- `libavif-dev`
- `libffi-dev`
- `libjpeg-dev`

Python dependencies installed from `requirements.txt` include:
- `fastapi`
- `uvicorn[standard]`
- `jinja2`
- `python-multipart`
- `Pillow`
- `python-docx`
- `pymupdf`
- `reportlab`
- `pdf2docx`
- `pdfplumber`
- `openpyxl`
- `python-pptx`
- `odfpy`
- `pytest-asyncio`
- `pillow-heif`
- `pillow-avif-plugin`
- `cairosvg`

## Missing Packages
Required runtime binaries expected for the converter stack:
- `ffmpeg`: installed ✅
- `libreoffice`: installed ✅
- `poppler-utils`: missing ❌

The Dockerfile does not install `poppler-utils` or any equivalent Poppler utilities such as `pdftoppm` / `pdfinfo`.

## Converter Impact
### IMAGE
- JPG: supported by Python imaging libraries; no direct Docker package requirement beyond `libjpeg-dev` and `Pillow`.
- PNG: supported by Python imaging libraries; no direct Docker package issue.
- WEBP: supported by `Pillow` and `libwebp`-linked libraries, though no explicit `libwebp` package is installed. The existing `libjpeg-dev` and `libavif-dev` packages suggest image support is intended.

### AUDIO
- MP4/MP3/WAV: `ffmpeg` is installed, satisfying audio/video conversion runtime requirements.

### DOCUMENT
- PDF: core PDF processing in Python may work, but `poppler-utils` is commonly required for reliable PDF rasterization and conversion to images. The absence of `poppler-utils` is a risk for PDF→JPG and other PDF rendering paths.
- DOCX/XLSX: `libreoffice` is installed, which supports office document conversion flows used by the application.

## Recommendation
- Add `poppler-utils` to the Dockerfile package install list to ensure Poppler binaries are available for PDF rendering / rasterization use cases.
- Verify whether `libwebp-dev` or additional image codec packages are needed for full WebP support in the container.
- Keep `ffmpeg` and `libreoffice` installed as currently specified.
- Confirm the production image also includes any Poppler-dependent binaries if PDF→image or PDF metadata extraction is required by the app.
