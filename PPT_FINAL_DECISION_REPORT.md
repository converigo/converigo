# PPT Converter Decision Report

## Audit Summary

Converter:

- PPTX → PDF
- PPTX → JPG
- PPTX → DOCX
- PPTX → XLSX

| Converter | Registry | Engine | Test | Decision | Reason |
|---|---|---|---|---|---|
| PPTX → PDF | `pptx-to-pdf` (active) | `document` engine | PASS — plugin `ppt-to-pdf` produced outputs/document/sample.pdf | KEEP | Plugin exists and runtime conversion succeeded locally; keep surfaced in recommendations. |
| PPTX → JPG | No registry contract / no plugin | `document` engine (no direct support) | FAIL — UnsupportedConversionError: PPTX to JPG conversion is not supported yet | DISABLE | No plugin or engine path for direct PPTX→JPG; avoid exposing a broken recommendation. |
| PPTX → DOCX | No registry contract / no plugin | `document` engine (no direct support) | FAIL — UnsupportedConversionError: PPTX to DOCX conversion is not supported yet | DISABLE | Direct conversion not supported; would require multi-step (PPTX→PDF→DOCX) which is unreliable. |
| PPTX → XLSX | No registry contract / no plugin | `document` engine (no direct support) | FAIL — UnsupportedConversionError: PPTX to XLSX conversion is not supported yet | DISABLE | No direct conversion path; converter would be misleading to users. |

Notes:

- Runtime tests executed against `tests/sample.pptx` show `pptx->pdf` success and other direct PPTX targets failing with `UnsupportedConversionError`.
- Decisions are metadata-only: do not implement new converters in this change; update registry or engine only after a separate engineering approval.
- Recommended next steps: add CI regression for `pptx->pdf` and verify production image contains `python-pptx` and related libs.
