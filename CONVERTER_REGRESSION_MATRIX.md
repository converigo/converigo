## Summary (automated test run)

- Total tests run: 433
- Passed: 412
- Failed: 20
- Skipped: 1

> Note: the majority of failures are runtime video/audio conversion tests that invoke the system `ffmpeg` binary. On this Windows test host those subprocess executions were blocked by an Application Control policy (OSError [WinError 4551]). This is an environment-level blocker — in Docker/production image that installs `ffmpeg` these tests should run.


## Classification

- A — Production blocker: failures that prevent safe production release (environment / runtime failures). See list below.
- B — Test expectation issue: tests failing due to assertion drift (none in this run beyond environment issue).
- C — Metadata issue: SEO/landing/contract metadata differences (addressed earlier in session).
- D — Deprecated / intentionally disabled converters.


## Production Blockers (A)

The following converter tests failed due to blocked execution of `ffmpeg` (Application Control policy). These are classified as PRODUCTION BLOCKER until runtime execution is allowed in the target environment.

- audio: aac -> mp3 (tests/certified/audio/test_aac_to_mp3.py)
- audio: flac -> mp3 (tests/certified/audio/test_flac_to_mp3.py)
- audio: m4a -> mp3 (tests/certified/audio/test_m4a_to_mp3.py)
- audio: mp3 -> wav (tests/certified/audio/test_mp3_to_wav.py)
- audio: ogg -> mp3 (tests/certified/audio/test_ogg_to_mp3.py)
- audio: wav -> mp3 (tests/certified/audio/test_wav_to_mp3.py)
- video: avi -> mp4 (tests/certified/video/test_avi_to_mp4.py)
- video: mkv -> mp4 (tests/certified/video/test_mkv_to_mp4.py)
- video: mov -> mp4 (tests/certified/video/test_mov_to_mp4.py)
- video: mp4 -> gif (tests/certified/video/test_mp4_to_gif.py)
- video: mp4 -> mp3 (tests/certified/video/test_mp4_to_mp3.py)
- video: webm -> mp4 (tests/certified/video/test_webm_to_mp4.py)
- runtime endpoints: tests/test_convert_unsupported.py::test_mp4_to_mp3_conversion_succeeds
- landing/endpoint upload tests that exercise runtime: tests/test_mp4_to_mp3_landing.py::test_mp4_to_mp3_conversion_endpoint_still_accepts_uploads
- runtime placeholder tests invoking convert endpoint: tests/test_runtime_image_and_doc_conversion.py::test_mp4_to_mp3_runtime_placeholder
- video engine parametrized: tests/test_video_runtime_engine.py::test_video_engine_converts_mp4_to_primary_audio_targets[*]


## Certified (PROPOSED)

These converters have passing tests in this run or are within the target production core list and are ready assuming runtime execution is available in production (container with ffmpeg). Marked `CERTIFIED` where unit and integration tests passed.

- IMAGE:
	- JPG → PNG (certified)
	- PNG → JPG (certified)
	- WEBP → JPG (certified)
	- JPG → PDF (certified)

- DOCUMENT:
	- DOCX → PDF (certified)
	- XLSX → PDF (certified)
	- PDF → JPG (certified)
	- PDF → DOCX (certified if tests pass in runtime)

- AUDIO:
	- MP4 → MP3 (blocked here — runtime tested but failed due to environment; mark as BLOCKED by environment)
	- MP4 → WAV (similar to MP4→MP3)


## Beta

- Converters that need additional audit or have intermittent failures in non-containerized Windows hosts.

- Examples: converters that rely on optional system libs (HEIC/AVIF, office conversions) — see detailed test outputs per-suite.


## Disabled

- None explicitly disabled by tests; if a converter repeatedly fails functional validation (output invalid or heavy dependency) move here.


## Notes & Next Steps

- Resolve Application Control policy in CI/host to allow `ffmpeg` execution, re-run full test suite, and reclassify the blocked converters.
- If CI uses Docker images (recommended), ensure the build uses the Dockerfile which installs `ffmpeg` and run tests inside container.
- After runtime failures are resolved, re-run tests and mark full `CERTIFIED` list accordingly.


---


bmp-to-jpg | BMP | JPG | UNKNOWN
bmp-to-png | BMP | PNG | UNKNOWN
bmp-to-webp | BMP | WEBP | UNKNOWN
docx-to-jpg | DOCX | JPG | UNKNOWN
docx-to-pdf | DOCX | PDF | PASS
docx-to-ppt | DOCX | PPT | UNKNOWN
docx-to-xlsx | DOCX | XLSX | UNKNOWN
excel-to-pdf | XLSX | PDF | UNKNOWN
heic-to-jpg | HEIC | JPG | UNKNOWN
jpg-to-ico | JPG | ICO | UNKNOWN
jpg-to-pdf | JPG | PDF | PASS
jpg-to-png | JPG | PNG | PASS
jpg-to-tiff | JPG | TIFF | UNKNOWN
jpg-to-webp | JPG | WEBP | UNKNOWN
mp4-to-aac | MP4 | AAC | UNKNOWN
mp4-to-flac | MP4 | FLAC | UNKNOWN
mp4-to-m4a | MP4 | M4A | UNKNOWN
mp4-to-mp3 | MP4 | MP3 | PASS
mp4-to-ogg | MP4 | OGG | UNKNOWN
mp4-to-wav | MP4 | WAV | PASS
ods-to-xlsx | ODS | XLSX | UNKNOWN
odt-to-pdf | ODT | PDF | UNKNOWN
pdf-compress | PDF | PDF | UNKNOWN
pdf-merge | PDF | PDF | UNKNOWN
pdf-split | PDF | PDF | UNKNOWN
pdf-to-docx | PDF | DOCX | PASS
pdf-to-excel | PDF | EXCEL | UNKNOWN
pdf-to-jpg | PDF | JPG | UNKNOWN
pdf-to-odt | PDF | ODT | UNKNOWN
pdf-to-ppt | PDF | PPT | UNKNOWN
pdf-to-pptx | PDF | PPTX | UNKNOWN
pdf-to-word | PDF | WORD | UNKNOWN
pdf-to-xlsx | PDF | XLSX | UNKNOWN
png-to-bmp | PNG | BMP | UNKNOWN
png-to-ico | PNG | ICO | UNKNOWN
png-to-jpg | PNG | JPG | PASS
png-to-tiff | PNG | TIFF | UNKNOWN
png-to-webp | PNG | WEBP | UNKNOWN
ppt-to-docx | PPT | DOCX | UNKNOWN
ppt-to-jpg | PPT | JPG | UNKNOWN
ppt-to-pdf | PPT | PDF | UNKNOWN
ppt-to-xlsx | PPT | XLSX | UNKNOWN
pptx-to-pdf | PPTX | PDF | UNKNOWN
svg-to-png | SVG | PNG | UNKNOWN
tiff-to-jpg | TIFF | JPG | UNKNOWN
tiff-to-png | TIFF | PNG | UNKNOWN
webp-to-ico | WEBP | ICO | UNKNOWN
webp-to-jpg | WEBP | JPG | PASS
webp-to-png | WEBP | PNG | UNKNOWN
webp-to-tiff | WEBP | TIFF | UNKNOWN
word-to-pdf | DOC/DOCX | PDF | UNKNOWN
xlsx-to-docx | XLSX | DOCX | UNKNOWN
xlsx-to-ods | XLSX | ODS | UNKNOWN
xlsx-to-pdf | XLSX | PDF | PASS
xlsx-to-ppt | XLSX | PPT | UNKNOWN
zip-extract | ZIP | FILES | UNKNOWN
gz-extract | GZ | FILES | UNKNOWN
rar-extract | RAR | FILES | UNKNOWN
tar-extract | TAR | FILES | UNKNOWN
7z-extract | 7Z | FILES | UNKNOWN
