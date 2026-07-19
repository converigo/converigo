# DOCX Converter Audit

## Registry

| Input | Output | Registered | Plugin | Engine |
|---|---:|---|---|---|
| DOCX | PDF | Yes | word-to-pdf | document |
| DOCX | JPG | No | - | - |
| DOCX | XLSX | No | - | - |
| DOCX | PPT | No | - | - |
| DOCX | ODT | No | - | - |

## Recommendation

Response:
- best_choice:

```json
{
  "source": "docx",
  "target": "pdf",
  "title": "Word to PDF",
  "description": "Convert DOCX documents into PDF files.",
  "goal": "document",
  "score": 79.25,
  "badge": "Portable PDF",
  "icon": "📄"
}
```

- alternatives: []

## Runtime Test

| Converter | Result | Plugin | Engine | Output Path | Error |
|---|---:|---|---|---|---|
| DOCX → PDF | PASS | word-to-pdf | document | outputs/document/sample.pdf | - |
| DOCX → JPG | FAIL | - | - | - | No plugin: Converter docx -> jpg tidak tersedia. |
| DOCX → XLSX | FAIL | - | - | - | No plugin: Converter docx -> xlsx tidak tersedia. |
| DOCX → PPT | FAIL | - | - | - | No plugin: Converter docx -> ppt tidak tersedia. |
| DOCX → ODT | FAIL | - | - | - | No plugin: Converter docx -> odt tidak tersedia. |

## Frontend Impact

- `recommendation_manager.js` expects `best_choice.target` and `alternatives[]` entries with `target` values. The local recommendation response supplies `best_choice` with `target: "pdf"` and `alternatives: []` — compatible with the frontend contract.

## Root Cause

B. Registry belum lengkap — only `word-to-pdf` is registered for `docx` inputs. Missing plugins for `docx->jpg`, `docx->xlsx`, `docx->ppt`, and `docx->odt` explain why those conversions are unavailable.

---

Generated during read-only audit; no code changes were made.
