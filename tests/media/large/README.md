# Large Media Samples

## Purpose
Store large or near-limit media files for upload, memory, and streaming behavior.

## Sample naming convention
Use the pattern: large_<size_bucket>_<container>_<codec>.<ext>

## Required metadata
- size bucket
- container
- codec
- expected validator result
- expected conversion result

## Priority
- P0: near-limit and common large files
- P1: large multi-stream files
- P2: very large archival samples

## Future regression policy
Any upload or performance failure involving large media must become a regression case.
