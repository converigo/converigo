# DOCKER_FIX_REVIEW

Problem:
- Railway build for the Docker image failed due to incorrect / missing system package names required by binary image processing libraries.

Root Cause:
- The package names installed by `apt-get` were incorrect for the target base image / distribution on Railway. The Dockerfile now uses the corrected package names:
  - `libpango-1.0-0` (replaces `libpango1.0-0`)
  - `libgdk-pixbuf-xlib-2.0-0` (replaces `libgdk-pixbuf2.0-0`)

Review:
- Current `Dockerfile` (project root) contains the corrected package names in the `apt-get install` list.
- The `Dockerfile` excerpt:

```
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libreoffice \
        p7zip-full \
        unrar-free \
        libcairo2 \
        libpango-1.0-0 \
        libgdk-pixbuf-xlib-2.0-0 \
        librsvg2-dev \
        ...
```

- Git history for the Dockerfile shows the most recent Docker-related commit (`47da988`) updated `EXPOSE`/`CMD` for Railway; that commit did not change application code or `requirements.txt`.
- No application code or converter modules were modified as part of the Dockerfile commit chain inspected; application changes in the current branch are limited to the PDF engine path fix (separate PR changes), not Dockerfile edits.
- `requirements.txt` was not modified in the Dockerfile commits reviewed.
- Dockerfile syntax is valid for standard Docker builds: `apt-get update` + `apt-get install -y --no-install-recommends` pattern; `rm -rf /var/lib/apt/lists/*` present to reduce image size; `CMD` uses `sh -c` wrapping and `PORT` env fallback which is compatible with Railway.

Risk:
- Impact: LOW to MEDIUM
  - LOW: The change is a package name correction to match Debian/Ubuntu package names and should fix build failures without impacting application logic.
  - MEDIUM: Installing additional system libraries increases image size and the attack surface slightly; ensure image scanning and minimal packages policy is acceptable.

Recommendation:
- Approve the Dockerfile package-name fix for merge/deploy.
- Optional: pin apt package versions or use `--no-install-recommends` (already present) and verify image size/scan in CI.
- Optional: add a small CI job that builds the Docker image (or uses `docker buildx`) to catch such issues early in future.

STOP
