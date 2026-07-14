# Quality Engineering

## 1. Vision

Converigo will treat media compatibility as a first-class quality discipline. The goal is to prevent upload, validation, and conversion regressions by maintaining a permanent corpus of real-world, edge, and regression media samples. Every production incident should become a reusable test case so the system becomes more reliable over time.

## 2. Media Compatibility Lab

The Media Compatibility Lab is the permanent home for media samples used to validate upload acceptance, validator behavior, conversion behavior, and production compatibility.

### Directory structure

- tests/media/real_world/device/
  - Purpose: Samples captured from real devices such as phones, cameras, and screen recorders.
  - Expected samples: MP4, MOV, AVI, MKV, WebM files produced by actual hardware.
  - Future maintenance: Refresh annually with new device models and updated export defaults.

- tests/media/real_world/editor/
  - Purpose: Samples exported by common editing tools such as Adobe Premiere, DaVinci Resolve, HandBrake, and iMovie.
  - Expected samples: Media produced by different editors with varying metadata and codec choices.
  - Future maintenance: Add samples whenever new editor versions or workflows introduce compatibility changes.

- tests/media/real_world/codec/
  - Purpose: Samples focused on codec-level compatibility rather than a single device or editor source.
  - Expected samples: H.264, H.265, AV1, VP9, ProRes, AAC, Opus, FLAC, PCM variants.
  - Future maintenance: Expand as new codecs become common in production traffic.

- tests/media/real_world/container/
  - Purpose: Samples that stress different containers and muxing behaviors.
  - Expected samples: MP4, MOV, AVI, MKV, WebM, MP3, WAV, M4A, FLAC, OGG files.
  - Future maintenance: Review container support quarterly and add new variants when supported by the platform.

- tests/media/real_world/audio/
  - Purpose: Audio-only compatibility samples for validator and conversion behavior.
  - Expected samples: MP3, WAV, AAC, M4A, FLAC, OGG files.
  - Future maintenance: Add audio-only cases from real workflows and customer uploads.

- tests/media/damaged/
  - Purpose: Corrupt, truncated, or malformed media samples used to verify rejection behavior.
  - Expected samples: Broken headers, partial streams, invalid files, and malformed metadata.
  - Future maintenance: Add one sample per new failure mode discovered in production.

- tests/media/edge_case/
  - Purpose: Rare but important files such as unusual metadata, empty streams, odd durations, and unusual filenames.
  - Expected samples: Minimal files, weird durations, unusual codecs, and empty or sparse content.
  - Future maintenance: Review each release for edge cases that should be locked in.

- tests/media/large/
  - Purpose: Large-file and boundary-condition samples for upload and memory handling.
  - Expected samples: Near-limit, above-limit, and large multi-minute files.
  - Future maintenance: Re-test after any upload-size or streaming changes.

- tests/media/regression/
  - Purpose: Permanent library of previously failing or previously fixed media cases.
  - Expected samples: Reproductions of known bugs and historical failures.
  - Future maintenance: Keep every production bug and every accepted fix as a permanent regression case.

## 3. Regression Library

The regression library is the durable record of quality issues that have been seen before. It is not a temporary debug folder; it is a permanent safety net.

- Each bug report becomes a dedicated regression case.
- Each case includes the original sample, the failure mode, the expected behavior, and the validation status.
- The library must be searchable by container, codec, device, editor, audio type, and bug class.

## 4. How every production bug becomes a permanent regression test

1. A production issue is reported.
2. A representative sample is preserved.
3. The failure is classified by container, codec, device, editor, audio, and symptom.
4. A regression case is placed under tests/media/regression/.
5. The case is linked to the relevant validator, upload, or conversion expectation.
6. The test is added to the automated suite and remains permanently active.

## 5. Testing workflow

### Developer
- Add or update targeted media cases for the feature being developed.
- Validate the local behavior for affected paths.
- Record any new failure mode in the regression library.

### QA
- Run compatibility checks across the curated media corpus.
- Confirm both positive and negative expected outcomes.
- Review the regression library for previously fixed issues.

### Production
- Capture representative real-world samples from new incidents.
- Preserve the media sample and the failure context.
- Promote the case into the regression library after triage.

### Regression
- Re-run the permanent regression corpus on every release.
- Ensure old failures do not recur.
- Archive or retire only cases that are obsolete and no longer relevant.

### Archive
- Move stale or superseded samples into an archive folder when they are no longer useful for active validation.
- Preserve the historical record for auditability and future investigation.

## 6. Quality KPIs

- False Negative Rate: percentage of valid media files incorrectly rejected by validation.
- Regression Coverage: percentage of known production bugs represented by regression cases.
- Compatibility Coverage: percentage of supported containers, codecs, devices, editors, and audio variants represented in the corpus.
- Upload Success Rate: percentage of legitimate media files accepted successfully.
- Mean Conversion Success: average successful conversion rate across the media corpus.
- Automation Coverage: percentage of the media corpus exercised by automated tests.
