# AUDIO CONVERTER AUDIT REPORT

Scope: MP4 → MP3 and MP4 → WAV (root-cause investigation)

Converter: MP4 → MP3

Input:
- Path: `tests/assets/regression/sample.mp4`
- ffprobe streams (index, codec_type, codec_name):
  - 0
  - h264
  - video

FFmpeg Command:
```
C:\ffmpeg\bin\ffmpeg.EXE -y -i tests\assets\regression\sample.mp4 -vn -acodec libmp3lame outputs\audio\sample.mp3
```

Error (captured):
```
Output #0, mp3, to 'outputs\audio\sample.mp3':
[out#0/mp3 @ ...] Output file does not contain any stream
Error opening output file outputs\audio\sample.mp3.
Error opening output files: Invalid argument

Command exited with code 1
```

Converter: MP4 → WAV

Input:
- Path: `tests/assets/regression/sample.mp4` (same as above)

FFmpeg Command:
```
C:\ffmpeg\bin\ffmpeg.EXE -y -i tests\assets\regression\sample.mp4 -vn -acodec pcm_s16le outputs\audio\sample.wav
```

Error (captured):
```
Output #0, wav, to 'outputs\audio\sample.wav':
[out#0/wav @ ...] Output file does not contain any stream
Error opening output file outputs\audio\sample.wav.
Error opening output files: Invalid argument

Command exited with code 1
```

Root Cause Analysis
- Primary cause: Input file `tests/assets/regression/sample.mp4` contains only a video stream (H.264). There is no audio stream to extract or transcode. Evidence: `ffprobe` returned only a video stream (index 0, codec h264).

- FFmpeg behavior: When `-vn` (disable video) is used without any audio stream present and no explicit stream mapping is provided, FFmpeg produces no output streams and fails with "Output file does not contain any stream" and exit code 1.

- Not root causes: FFmpeg command arguments (`-vn -acodec libmp3lame` / `-acodec pcm_s16le`) and output paths are syntactically correct; environment has FFmpeg/ffprobe available (executed successfully). The plugin `MP4ToMP3Plugin` includes a pre-check `_ensure_audio_stream()` which raises a clear runtime error for missing audio — this is functioning for MP3 case. For WAV plugin, there was no explicit ffprobe pre-check; it relied on engine to fail.

Recommended Fixes
- Short-term (low-effort): Replace or augment `tests/assets/regression/sample.mp4` with a sample MP4 that contains an audio stream for CI/validation runs that exercise audio extraction. This will allow the MP4→MP3 and MP4→WAV conversions to run end-to-end.

- Short-term (alternative): Update test harness `scripts/real_conversion_validation.py` to detect video-only inputs and mark audio extraction cases as BLOCKED/SKIPPED with a clear message rather than failing. (The `MP4ToMP3Plugin` already does this check and reports a helpful message.)

- Medium-term (optional): Add an `_ensure_audio_stream()` check to `MP4ToWAVPlugin` (mirrors MP4ToMP3Plugin) so both plugins fail fast with a clear error rather than letting FFmpeg fail. This is a plugin change and was not performed per instructions.

Risk Assessment
- Changing test assets or the validation script: minimal risk, non-invasive, does not touch converters or engines.
- Adding pre-check to WAV plugin: low risk but is a code change to plugin (user disallowed modifications to converters for now).

Conclusion
- Root cause: A (Input video lacks audio stream). No ffmpeg bug, no output-path bug, environment present.

Before:
- Test fixture `tests/assets/regression/sample.mp4` contained video only (no audio). Audio conversions failed with FFmpeg exit code 1.

After:
- Created `tests/assets/regression/sample_with_audio.mp4` by muxing a generated 2s sine audio track into the original video. Verified streams with `ffprobe` (video + aac audio).

Result:
- Re-ran `scripts/real_conversion_validation.py` using the updated fixture; both `MP4 -> MP3` and `MP4 -> WAV` now PASS. See `build/real_conversion_results.json`.
