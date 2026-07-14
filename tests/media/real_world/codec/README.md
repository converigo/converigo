# Codec Samples

## Purpose
Store samples that isolate codec compatibility concerns independent of device or editor source.

## Sample naming convention
Use the pattern: codec_<codec_name>_<container>_<audio>.<ext>

## Required metadata
- codec family
- container
- audio
- expected validator result
- expected conversion result

## Priority
- P0: common codec families
- P1: modern and emerging codecs
- P2: uncommon codec variants

## Future regression policy
Any codec-related validation failure becomes a regression case.
