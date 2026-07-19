# POPPLER DEPENDENCY FIX REPORT

## Problem
The Docker image did not include Poppler utilities, which are required to support the PDF conversion pipeline.

## Root Cause
The `Dockerfile` apt install list omitted `poppler-utils`, so the production container would lack `pdfinfo` and `pdftoppm` binaries.

## Change
Added `poppler-utils` to the `apt-get install -y --no-install-recommends` section of `Dockerfile`.

## Validation
- Docker CLI availability check: failed (`docker` command not found on the current host).
- Build: could not be executed because Docker is unavailable.
- Binary checks inside the container: not performed.
- Smoke tests for PDF → JPG and JPG → PDF: not performed.

## Result
- `Dockerfile` updated with `poppler-utils`.
- Build and validation are pending until Docker is available on the host.
