# Audio Samples

## Purpose
Store audio-only media samples for validator and converter compatibility coverage.

## Sample naming convention
Use the pattern: audio_<format>_<channel_layout>.<ext>

## Required metadata
- audio format
- sample rate
- channel layout
- expected validator result
- expected conversion result

## Priority
- P0: common audio formats
- P1: lossless and advanced formats
- P2: niche or unusual audio variants

## Future regression policy
Any audio validation or conversion failure becomes a regression case.
