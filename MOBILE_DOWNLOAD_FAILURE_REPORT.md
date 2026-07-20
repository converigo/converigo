# Mobile Download Failure Audit Report

Date: 2026-07-21
Status: Audit completed. No implementation changes made.

## Executive Summary

The current mobile download flow is likely failing because the app does not force a server-side file download response for generated files. Instead, the frontend relies on a plain anchor link pointing to a static file path under /outputs, while the backend serves those files through a generic static mount with no explicit Content-Disposition header.

On Android browsers, this often results in the browser treating the file as an inline/previewable asset rather than a forced download, so the file does not appear in the device Download folder as expected.

## Reproduction Summary

Attempted flow:
1. Open Converigo in Android-style browser context.
2. Upload a file.
3. Convert to completion.
4. Click Download.
5. Check whether the file appears in device Downloads.

Environment note:
- This workspace did not have a direct Android browser session available for live device testing.
- The audit below is based on code inspection, frontend flow analysis, and live local HTTP verification against the running app.

## Backend Audit

### 1. Download endpoint / file serving path

The app does not expose a dedicated download endpoint for converted files. Generated files are served through the static files mount defined in [app/main.py](app/main.py):

- /outputs is mounted with StaticFiles
- Files are therefore served as ordinary static assets, not as explicit download responses

### 2. Response headers

I verified the local server response for a sample file using curl:

- Request: http://127.0.0.1:8000/outputs/audit-test.pdf
- Observed response: HTTP/1.1 200 OK
- Observed headers:
  - content-type: application/pdf
  - accept-ranges: bytes
  - content-length: 6
  - last-modified: ...

Important finding: there was no Content-Disposition header in the response.

### 3. Content-Disposition

Result: missing.

This is the strongest backend signal for the mobile download issue. Without Content-Disposition: attachment, browsers are left to decide whether to display the file inline or save it. On mobile browsers, that behavior is inconsistent and often leads to preview/open behavior instead of a true saved download.

### 4. Content-Type

For PDF files, the backend returns a correct content type:

- application/pdf

That part is fine. However, correct content-type alone is not enough to force a browser download on mobile.

### 5. Filename handling

The backend does not provide a server-side filename hint through the response. The filename is only supplied by the frontend through the anchor's download attribute in [app/static/js/download/download_manager.js](app/static/js/download/download_manager.js).

That means the browser must infer or use the client-side attribute, while the backend does not actively participate in the download contract.

## Frontend Audit

### 1. Download manager implementation

The download flow is controlled by [app/static/js/download/download_manager.js](app/static/js/download/download_manager.js).

Audit findings:
- It uses a normal anchor element.
- It sets href to the generated download path.
- It sets the anchor's download attribute to the output filename.
- It does not use blob URLs.
- It does not use fetch-based download streaming.
- It does not use window.open.
- It does not implement a mobile-specific fallback.

### 2. Anchor download mechanism

The UI prepares the button like this:

- set href = result.download_path
- set download = filename

This is a standard browser navigation pattern. It works only if the browser accepts the file as a downloadable asset and the server response is compatible.

### 3. Blob URL / fetch / window.open

No evidence of any of the following in the current frontend download path:
- createObjectURL
- fetch download flow
- window.open
- custom blob-based download manager

That means the browser is handling the download as a plain link navigation to a static URL.

### 4. User gesture handling

The click handler in [app/static/js/download/download_manager.js](app/static/js/download/download_manager.js) only attaches a passive analytics event listener. It does not do any special download orchestration or protect the action against mobile browser restrictions.

This is important because mobile browsers are stricter about download initiation, especially when the action is not clearly a direct user-initiated navigation and the response is not explicitly marked for download.

## Test Matrix and Expected Impact

### Chrome Android

Likely impact:
- Files may open inline or in a preview tab instead of being saved to Downloads.
- The current implementation lacks a backend directive to force a save action.

### Brave Android

Likely impact:
- Similar to Chrome Android, and possibly more restrictive depending on the browser's download/privacy policy.
- The absence of attachment headers increases the chance that the browser will not persist the file to Downloads.

### Desktop Chrome (comparison)

Desktop Chrome is generally more forgiving and may still download or open files depending on MIME behavior.
However, the current code still depends on browser heuristics rather than an explicit server-side download contract, so it is not a robust cross-platform solution.

## Root Cause

The most likely root cause is a combination of two issues:

1. Backend issue: files served under /outputs are not returned with Content-Disposition: attachment.
2. Frontend issue: the download UI uses a plain anchor-based navigation flow without a mobile-safe fallback.

This combination is a common reason for mobile browsers failing to place files into the device Download folder even though the file exists and the conversion succeeded.

## Conclusion

The failure is most likely not caused by conversion itself. The conversion completes and the generated file exists on disk. The problem is in the transfer/download phase:

- the server does not explicitly tell the browser to download the file as an attachment
- the frontend does not use a more robust mobile-safe download mechanism

## Recommended Next Step

The next implementation step should be to introduce an explicit download route or response handler that returns:

- Content-Disposition: attachment; filename=...
- A correct Content-Type for the file
- A predictable download filename from the server side

This should be implemented after the root cause is confirmed and before any broader frontend changes.
