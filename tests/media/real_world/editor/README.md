# Editor Samples

## Purpose
Store media samples exported by common editing tools.

## Sample naming convention
Use the pattern: editor_<editor_name>_<container>_<codec>_<audio>.<ext>

## Required metadata
- editor name
- export preset
- container
- codec
- audio
- expected validator result

## Priority
- P0: common editor outputs
- P1: advanced editor workflows
- P2: rare or legacy editor outputs

## Future regression policy
Any editor-specific incompatibility should be preserved as a regression sample.
