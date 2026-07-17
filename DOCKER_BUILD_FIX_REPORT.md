# DOCKER_BUILD_FIX_REPORT

## Problem
Railway Docker build gagal pada tahap apt-get install:
- `E: Unable to locate package libpango1.0-0`
- `E: Package 'libgdk-pixbuf2.0-0' has no installation candidate`

## Root Cause
Nama paket Debian (Trixie) berubah sehingga package lama `libpango1.0-0` dan `libgdk-pixbuf2.0-0` tidak lagi tersedia.

## Changed
**File:** `Dockerfile`

**Replace hanya paket system dependency (tanpa mengubah code/converter/requirements):**
- `libpango1.0-0` -> `libpango-1.0-0`
- `libgdk-pixbuf2.0-0` -> `libgdk-pixbuf-xlib-2.0-0`

## Testing
- Tidak dapat menjalankan `docker build` di environment saat ini karena binary `docker` tidak tersedia.
- Langkah uji yang disarankan setelah ini (di mesin yang punya Docker):
  - `docker build -t converigo:test .`


## Risk
Low.
- Perubahan hanya pada nama paket system libs untuk memenuhi dependency OS.
- Tidak mengubah application logic.

STOP

