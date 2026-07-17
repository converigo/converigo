# Converigo

> Convert Files in Seconds.

Converigo adalah web application modern untuk mengubah berbagai format file dengan cepat, aman, dan mudah digunakan.

---

## Vision

Menjadi website file converter yang paling modern, cepat, dan mudah digunakan.

---

## MVP Features

- Video Converter
- Audio Converter
- Document Converter

---

## Tech Stack

### Backend

- Python 3.14
- FastAPI

### Frontend

- HTML5
- CSS3
- Vanilla JavaScript

---

## Image Converter Dependencies

Converigo's image converters use optional runtime backends for HEIC, AVIF, and SVG. The Python packages are installed from the project requirements, but some formats also depend on native system libraries.

### HEIC
- Python package: pillow-heif
- Purpose: enables Pillow to read and write HEIC/HEIF files.
- Native requirement: libheif may be required by the underlying runtime on some platforms.
- If the native library is unavailable, HEIC-based conversion may fail and certified tests may skip.

### AVIF
- Python package: pillow-avif-plugin
- Imported module: pillow_avif
- Purpose: enables Pillow to work with AVIF images.
- Native requirement: libavif may be needed on some systems.
- If the backend is unavailable, AVIF-certified tests may skip.

### SVG
- Python packages: CairoSVG and pycairo
- Purpose: renders SVG images to raster formats such as PNG.
- Native requirement: Cairo runtime (libcairo / cairo) must be installed and discoverable.
- If the native Cairo runtime is missing, SVG conversion may fail and certified SVG tests may skip.

### Platform notes
- Windows: install the Python packages from the project requirements and ensure the required native runtime is available. In some setups, the Python wheels for pycairo are enough, but the Cairo library still needs to be discoverable by the runtime.
- Linux: install the matching system packages for Cairo and, if needed, libheif/libavif through your package manager (for example with apt, dnf, or yum).
- macOS: install Cairo and native image libraries with Homebrew when required.

These dependencies are optional at the Python-package level, but the certified image tests are intentionally tolerant: they skip when the host environment cannot load the required backend or native library.

---

## Project Structure

```
Converigo/

app/

static/

templates/

uploads/

outputs/

.ai/

docs/
```

---

## Development Team

Founder

- Jhevito

Chief Software Architect

- ChatGPT

Software Engineer

- VS Code Agent

---

## Current Status

Season 1

Sprint 001

Genesis

Project initialization.