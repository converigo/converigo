# Regression Samples

## Purpose
Store permanent regression cases for previously discovered media compatibility issues.

## Sample naming convention
Use the pattern: regression_<issue_id>_<container>_<codec>.<ext>

## Required metadata
- issue ID
- failure summary
- original bug context
- expected validator result
- expected conversion result

## Priority
- P0: current production regressions
- P1: recently fixed issues
- P2: historical cases retained for auditability

## Future regression policy
Every production bug or known compatibility issue must be preserved here as a permanent regression sample.
