# Damaged Samples

## Purpose
Store malformed, truncated, or corrupt media samples to validate rejection behavior.

## Sample naming convention
Use the pattern: damaged_<failure_type>_<container>.<ext>

## Required metadata
- failure type
- container or format
- expected validator result
- expected HTTP outcome

## Priority
- P0: common corruption scenarios
- P1: partial and malformed streams
- P2: rare corruption patterns

## Future regression policy
Each production rejection bug should create a damaged-sample regression case.
