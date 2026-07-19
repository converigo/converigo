## CLASS A — FIX NOW

Converter: JPG -> PDF
Status: FAIL (produced PDF, validation failed)
Root cause: Validation step misclassified the case as `image` and attempts to open the produced PDF with Pillow. The `jpg-to-pdf` plugin correctly produces a PDF using ReportLab; the validation logic expects an image file.
Priority: High — affects automated validation and reporting for image→document conversions


## CLASS B — INVESTIGATE

Converter: MP4 -> MP3
Reason: Conversion aborted with explicit runtime error: "The selected MP4 file does not contain an audio stream." Root cause is the test asset `tests/assets/regression/sample.mp4` appears to be video-only; plugin correctly validates presence of audio.

Converter: MP4 -> WAV
Reason: FFmpeg conversion failed due to input lacking an audio stream (ffmpeg stderr shows only a video stream). Either the plugin should pre-check for audio (as MP4->MP3 does) or CI assets must be replaced with audio-containing samples.


## CLASS C — DISABLE

Converter: None at this time.
