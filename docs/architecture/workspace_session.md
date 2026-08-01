# Workspace Session Blueprint

This document defines the future workspace session model for Converigo.

## Objective

Provide a blueprint for workspace session persistence and session-aware flows.

## Session ID

- Unique identifier for a user workspace session.
- Could be generated client-side using UUID or server-side by the application.
- Used to correlate files, results, history, and recovery.

## Files

### Fields
- `fileId`: stable identifier for each file.
- `name`: original file name.
- `size`: file size in bytes.
- `type`: MIME type or inferred format.
- `lastModified`: timestamp from file metadata.
- `status`: `selected` | `queued` | `uploaded` | `converted` | `error`.
- `selectedFormat`: output format chosen for the file.
- `targetFormat`: optional normalized format target.
- `preview`: optional UI preview metadata.

## Results

### Fields
- `resultId`: unique result identifier.
- `fileId`: linked file identifier.
- `filename`: converted file name.
- `download_path`: path or URL to the converted asset.
- `status`: `success` | `failed` | `partial`.
- `error`: optional error message.
- `duration`: optional conversion time.
- `size`: output file size.

## History

### Fields
- `entries`: array of session history entries.
- `timestamp`: session completion or checkpoint timestamp.
- `summary`: high-level session outcome.
- `files`: file metadata snapshots.
- `results`: conversion result snapshots.
- `selectedFormat`: selected output for the session.
- `status`: final state of the historical session.

## Selected Format

- Stored at both file-level and session-level.
- `selectedFormat` is used to populate conversion readiness and download targets.
- Should support bulk selection and per-file overrides.

## Metadata

### Fields
- `createdAt`: session creation timestamp.
- `updatedAt`: last update timestamp.
- `sessionOwner`: optional user identifier.
- `source`: `landing` | `workspace`.
- `featureFlags`: optional feature flag context.
- `cloudSync`: optional cloud persistence metadata.

## Persistence

### Options
- Local storage / IndexedDB for client-side session recovery.
- Server-side session store for authenticated users.
- Memory-only session state for transient anonymous workflows.

### Requirements
- Restore workspace state after page refresh when possible.
- Preserve file selection and format targets for uncompleted sessions.
- Support history snapshots without exposing raw files.
- Enable future cloud sync and cross-device session continuation.

## Notes

- Current implementation does not yet persist workspace sessions.
- This blueprint is intentionally abstract and frontend-focused.
- Actual persistence layer should avoid storing file contents unless encrypted and approved.
