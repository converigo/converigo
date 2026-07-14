# Converigo Project Checkpoint

## Project Vision

Converigo provides reliable media conversion workflows with a clear upload, validation, and conversion pipeline for production use.

## Current Production Status

The MP4 upload investigation has been completed. The upload pipeline was verified end to end. The stream pointer behavior was verified. The UploadFile object remained unchanged before validation. A false-negative is suspected in the current media signature validation path. The current validator uses a heuristic-based check rather than structural media parsing.

## Repository Status

The repository is in a production-focused state with the upload and conversion workflow actively under review. The current work is centered on media validation accuracy and production reliability.

## Infrastructure
- GitHub
- Railway
- Cloudflare
- Domain

## Released Features

The current release set includes upload-based conversion workflows, file validation, and conversion execution for supported media formats.

## Batch History

Batch work has focused on upload validation, MP4 compatibility, and production reliability review.

## Current Critical Issue

The MP4 upload investigation completed with the following verified findings:

- MP4 upload investigation completed
- Upload pipeline verified
- Stream pointer verified
- UploadFile unchanged
- False-negative suspected in media signature validation
- Current validator uses heuristic
- PMV v1 approved as next architecture

## Approved Architecture

Describe PMV v1:

Security Validation

↓

FFprobe Validation

↓

FFmpeg Conversion

This architecture was chosen because it separates security checks from media container validation and relies on FFprobe as the authoritative source for audio/video container structure before conversion proceeds with FFmpeg.

## Converigo Copilot Protocol (CCP v1)

The agreed operating rules are:

- Small scope only
- Minimum files
- Evidence first
- No repository-wide scans
- No unnecessary code generation
- No commit without approval
- No push without approval
- Stop after sprint goal
- Preserve architecture

## Roadmap

P0
Production Media Validation (PMV v1)

P1
Regression testing

P2
Batch B2

Long-term

100 converters

250 converters

500+ converters

## Decision Log

Important architectural decisions are recorded here as the project evolves.

## Next Sprint

This section is intentionally left ready for future updates.

# PMV v1 Design Approved

## Architecture diagram

Security Validation

↓

FFprobe Validation

↓

FFmpeg Conversion

## Sequence diagram

Client uploads file
↓
UploadService receives UploadFile
↓
Filename validation
↓
Extension validation
↓
Size validation
↓
MIME validation
↓
FFprobe validates container and stream structure
↓
If valid, conversion proceeds with FFmpeg
↓
If invalid, upload fails with a structured media validation error

## Validation order

1. Filename validation
2. Extension validation
3. Size validation
4. MIME validation
5. FFprobe-based media container validation
6. FFmpeg conversion

## Component responsibilities

- Filename validation: enforce safe and non-empty filenames.
- Extension validation: enforce supported file types.
- Size validation: enforce upload size limits.
- MIME validation: enforce expected content-type behavior.
- FFprobe validation: confirm container validity and supported media structure.
- FFmpeg conversion: perform downstream conversion only after media validation succeeds.

## Why FFprobe is the source of truth

FFprobe is the authoritative source for audio and video container structure because it inspects the actual media stream and reports container, stream, and codec metadata. This makes it more reliable than the current heuristic-based signature check.

## Which validations remain

The following validations remain:

- Filename validation
- Extension validation
- Size validation
- MIME validation

## Which validations are removed

The current heuristic-based media signature check is removed from the validation path and replaced by FFprobe-based container validation.

## Which validations become optional

Optional validations may include:

- Advanced codec compatibility checks
- Strict stream-level policy checks
- Detailed metadata inspection beyond container validity

## Migration plan

### Phase 1

- Preserve current filename, extension, size, and MIME validation.
- Introduce FFprobe-based media validation as an additional step for audio/video uploads.
- Keep the existing upload error flow intact.
- Deploy independently with no changes to conversion logic.

### Phase 2

- Make FFprobe validation the primary gate for media container acceptance.
- Preserve existing security checks and file-type restrictions.
- Keep conversion behavior unchanged.
- Deploy independently once Phase 1 is stable.

### Phase 3

- Treat FFprobe validation as the standard production gate for all supported media uploads.
- Retain fallback behavior for non-media file types.
- Keep rollback simple by restoring the prior validation path if needed.

## Risk analysis

### Phase 1

- Security: Low risk because existing validation remains in place.
- Performance: Moderate because FFprobe adds a validation step.
- Compatibility: Low risk because FFprobe supports most common media containers.
- Rollback: Simple because the previous validation path remains available.

### Phase 2

- Security: Low risk because the security checks remain intact and media validation becomes more authoritative.
- Performance: Moderate because media validation is now a more central part of the flow.
- Compatibility: Moderate because some edge-case media files may behave differently under FFprobe-based validation.
- Rollback: Simple because the validator can be reverted to the previous mode if needed.

### Phase 3

- Security: Low risk because the gate remains explicit and media validation is structurally grounded.
- Performance: Moderate because all media uploads now incur FFprobe inspection.
- Compatibility: Moderate because some real-world media variations may need policy tuning.
- Rollback: Straightforward because the rollout can be reversed by restoring the prior validation gate.

## Implementation Plan

### Phases

#### Phase A
- Introduce an FFprobe-based media validation layer behind the existing validator entry point.
- Files affected: [app/utils/file_validator.py](app/utils/file_validator.py), [app/services/upload_service.py](app/services/upload_service.py)
- Estimated complexity: Medium
- Deployment risk: Low
- Rollback strategy: Keep the current heuristic path available behind a feature flag or fallback branch until validation is stable.

#### Phase B
- Keep existing filename, extension, size, and MIME validation unchanged.
- Route audio/video validation through FFprobe while preserving the existing upload error flow.
- Files affected: [app/utils/file_validator.py](app/utils/file_validator.py), [app/services/upload_service.py](app/services/upload_service.py)
- Estimated complexity: Medium
- Deployment risk: Medium
- Rollback strategy: Revert to the prior validator path without changing router, converter, or plugin code.

#### Phase C
- Collect runtime metrics for accepted and rejected media files.
- Files affected: [app/utils/file_validator.py](app/utils/file_validator.py), [app/services/upload_service.py](app/services/upload_service.py)
- Estimated complexity: Low
- Deployment risk: Low
- Rollback strategy: Disable metric collection and preserve the current validation behavior.

#### Phase D
- Replace the heuristic validator as the default media gate after validation results confirm compatibility.
- Files affected: [app/utils/file_validator.py](app/utils/file_validator.py), [app/services/upload_service.py](app/services/upload_service.py)
- Estimated complexity: Medium
- Deployment risk: Medium
- Rollback strategy: Restore the prior heuristic path while leaving the rest of the upload and conversion pipeline unchanged.

### Risks

- Security: Low if existing filename, extension, size, and MIME checks remain intact and FFprobe validation is introduced as an additional gate.
- Performance: Moderate because FFprobe adds a media inspection step for uploads.
- Compatibility: Moderate because some real-world media variants may require policy adjustment.
- Rollback: Low risk because the integration point is localized to the validator and upload service.

### Recommendation

Proceed with a phased rollout that starts with FFprobe validation behind the current validator flow, preserves the existing routing and conversion architecture, and only removes the heuristic path after runtime evidence confirms compatibility.
