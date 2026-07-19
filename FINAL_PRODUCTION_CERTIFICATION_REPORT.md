# CONVERIGO FINAL PRODUCTION CERTIFICATION

## Executive Summary

This document records the results of the final automated certification audit run on the current workspace (local Windows host). A full test run (`pytest -q`) executed 433 tests: 412 passed, 20 failed, 1 skipped. The failing tests are concentrated in video/audio runtime conversions that invoke the system `ffmpeg` binary and were blocked by an Application Control policy on the test host (OSError [WinError 4551]).

Status: NOT READY — blocker detected (environmental execution policy blocking runtime `ffmpeg`).

## Test Result

- Total tests executed: 433
- Passed: 412
- Failed: 20
- Skipped: 1

Failed areas: runtime audio/video conversion tests that spawn `ffmpeg` subprocesses. Failure cause: host Application Control policy blocked executing the binary (WinError 4551). Several endpoint tests that upload and call conversion returned 500 as a result of the same root cause.

## Certified Converter (proposed)

The following converters are considered `CERTIFIED` pending runtime verification in production container (Docker) where `ffmpeg` is available and allowed:

- IMAGE:
  - JPG → PNG
  - PNG → JPG
  - WEBP → JPG
  - JPG → PDF

- DOCUMENT:
  - DOCX → PDF
  - XLSX → PDF
  - PDF → JPG
  - PDF → DOCX (subject to runtime verification)

- AUDIO / VIDEO:
  - MP4 → MP3 (currently blocked by host policy — verify in container)
  - MP4 → WAV (blocked here)

Note: Those in AUDIO/VIDEO that were exercised by tests failed on this host due to the execution policy; they are not considered certified until they pass in the intended runtime (Docker/production) or the policy is resolved in CI.

## Beta Converter

Converters that require further audit, additional test coverage, or depend on optional system libraries are listed as `BETA`. Examples include HEIC/AVIF conversion flows, certain office-to-office transforms, and less-common image formats.

## Disabled Converter

No converters were explicitly disabled by the test suite in this run. Converters that consistently fail output validation or require heavy, non-production dependencies should be added here after investigation.

## Known Limitations

- Host environment control policies may block subprocess execution of system binaries (observed as WinError 4551), causing runtime integration tests to fail even when code and Dockerfile are correct.
- Tests that rely on local system `ffmpeg` should run inside the production Docker image (which installs `ffmpeg` per Dockerfile) or in a CI environment that permits process execution.

## Deployment Validation

- Dockerfile: present and installs `ffmpeg` and required libraries (libreoffice, image libs).
- Host `ffmpeg`: present on PATH at runtime (C:\ffmpeg\bin\ffmpeg.EXE) but blocked by system policy.
- `UPLOAD_DIR` and `OUTPUT_DIR`: exist and are writable on this machine (uploads/, outputs/).
- Recommendation: run full integration tests in the Docker image or CI runner that mirrors production; do not rely on developer Windows host for runtime ffmpeg validation.

## Release Recommendation

Status: NOT READY.

Conditions to be met before marking READY:

1. Resolve Application Control policy that blocks `ffmpeg` execution in CI/host OR run all runtime tests inside the Docker image which includes `ffmpeg`.
2. Re-run the full test suite inside the approved runtime. All previously failing video/audio conversion tests must pass.
3. Confirm Docker build and run steps succeed in CI and production environment, and that upload/output directories and permissions match expected settings.

Once the above are satisfied, re-run the certification workflow and, if green, update the status to READY and publish this report.

Prepared by: automated certification agent
Date: 2026-07-19
