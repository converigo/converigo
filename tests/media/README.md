# Media Compatibility Lab

## Purpose
This directory is the permanent home for media compatibility evidence used by Converigo quality engineering.

## Sample naming convention
Use descriptive, lowercase names with category and format markers, for example:
- device_smartphone_h264_aac.mp4
- editor_premiere_hevc_aac.mov
- codec_av1_opus.mkv
- container_webm_vp9_opus.webm
- audio_mp3_stereo.mp3

## Required metadata
Each sample should be documented with:
- source
- container
- codec
- audio
- device or editor if applicable
- expected validator outcome
- expected conversion outcome

## Priority
- P0: core real-world and regression samples
- P1: extended compatibility and editor-specific samples
- P2: edge and long-tail cases

## Future regression policy
Any production failure or compatibility issue must be preserved as a regression sample and linked to the relevant test case.
