# Edge Case Samples

## Purpose
Store unusual but valid media cases that stress edge handling and boundary conditions.

## Sample naming convention
Use the pattern: edge_<condition>_<container>.<ext>

## Required metadata
- edge condition
- container or format
- expected validator result
- expected conversion result

## Priority
- P0: common edge conditions
- P1: unusual metadata or stream layouts
- P2: rare boundary cases

## Future regression policy
Any edge-condition issue discovered in production should be preserved here.
