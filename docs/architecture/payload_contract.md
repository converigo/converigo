# Payload Contract

This document defines the payload shapes used across Converigo frontend flows.

## UploadPayload

Represents the file selection state.

### Fields
- `file`: File object or null.
- `files`: array of File objects.
- `inputFormat`: optional inferred source format string.
- `fileCount`: optional count of selected files.

## ConversionPayload

Represents the conversion request/response lifecycle.

### Fields
- `files`: array of File objects sent to the backend.
- `target_format`: string output format selected by the user.
- `success`: boolean whether conversion succeeded.
- `total`: numeric total file count in the response.
- `successful`: numeric successful file count.
- `results`: optional array of conversion result objects.
- `filename`: optional top-level filename for single-file conversion.
- `download_path`: optional top-level download URL path.
- `message`: optional backend message or error details.

## DownloadPayload

Represents normalized download metadata.

### Fields
- `items`: array of download item objects.
- `processingDuration`: optional numeric duration.
- `originalResult`: original converter response object.

### Download Item
- `filename`: string file name.
- `download_path`: string URL or path to download asset.
- `original`: original item object from backend response.

## WorkspacePayload

Represents workspace file and conversion session state.

### Fields
- `files`: array of File objects currently in workspace.
- `fileKeys`: array of stable identifiers for each file.
- `selectedFormats`: optional mapping of file keys to target formats.
- `workspaceConversionResults`: array of result objects from workspace conversions.
- `status`: string workspace sub-state.
- `errors`: optional array of error details.

## HistoryPayload

Represents a historical session entry.

### Fields
- `sessionId`: string unique workspace session id.
- `timestamp`: ISO string or numeric epoch.
- `files`: array of file metadata objects.
- `results`: array of conversion result metadata.
- `selectedFormat`: string output format for the session.
- `status`: string final session state.

## FuturePayload

Placeholder for future data structures.

### Fields
- `cloudStatus`: optional `idle` | `syncing` | `failed` | `completed`.
- `editorState`: optional editor context object.
- `featureFlags`: optional feature flag map.
- `metadata`: optional arbitrary metadata.

## Notes

- These payload shapes are intentionally high-level and frontend-focused.
- Backend payloads may include additional fields, but frontend contracts should consume only the documented keys.
- Future flows should extend these contracts rather than invent parallel payload shapes.
