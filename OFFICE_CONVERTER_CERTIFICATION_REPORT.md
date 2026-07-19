# Office Converter Certification Report

This report summarizes certification status for key office converters after audit and runtime checks.

| Converter | Registered | Engine | Manual Test | Status |
|---|---:|---|---:|---|
| XLSX→PDF | YES | document | PASS | CERTIFIED |
| XLSX→ODS | YES | document | FAIL | REVIEW |
| PPT→PDF | YES | document | FAIL (external) / PASS (local) | REVIEW |

Notes:
- `XLSX→ODS` plugin exists (`xlsx-to-ods`) but the `DocumentEngine` does not support `ods` as a target — conversion attempts raise an `UnsupportedConversionError` (engine mapping issue).
- `PPT→PDF` plugin exists and local runtime conversion (created `tests/sample.pptx`) produced `outputs/document/sample.pdf` successfully. The user's manual run reported failure — likely environment-specific (missing dependency or runtime permissions). Further investigation recommended before certifying.
