# Container Samples

## Purpose
Store samples that stress container handling and muxing behavior.

## Sample naming convention
Use the pattern: container_<container_name>_<codec>_<audio>.<ext>

## Required metadata
- container
- codec
- audio
- muxing notes
- expected validator result

## Priority
- P0: core containers
- P1: less common containers
- P2: niche or legacy containers

## Future regression policy
Any container parsing issue should be preserved as a regression sample.
