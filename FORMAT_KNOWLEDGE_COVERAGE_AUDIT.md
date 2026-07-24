# Format Knowledge Coverage Audit

**Date:** 2026-07-21  
**Source of supported formats:** `AuthorityService` derived from active converter contracts in `app/data/converters/`

---

## Summary

| Metric | Count |
|--------|-------|
| Supported formats (from converter registry) | 29 |
| Master records present (`app/data/formats/`) | 23 |
| Knowledge files present (`app/data/format_knowledge/`) | 23 |
| Missing master records | 14 |
| Missing knowledge files | 14 |
| Orphan master records (no matching supported format) | 8 |
| Orphan knowledge files (no matching supported format) | 8 |
| **Full coverage (master + knowledge)** | **15 / 29 (52%)** |

---

## Coverage by category

### Image — 9 supported formats

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| avif | ✅ | ✅ | Complete |
| bmp | ✅ | ✅ | Complete |
| heic | ✅ | ✅ | Complete |
| jpeg | ❌ | ❌ | Missing both |
| jpg | ✅ | ✅ | Complete |
| png | ✅ | ✅ | Complete |
| svg | ✅ | ✅ | Complete |
| tiff | ✅ | ✅ | Complete |
| webp | ✅ | ✅ | Complete |

**Coverage: 8 / 9**  
**Gap:** `jpeg` — present in converter registry as an alias for `jpg`; needs a master record and knowledge file (or a redirect/alias strategy).

---

### Document — 7 supported formats

> Note: the `AuthorityService` groups document, spreadsheet, and presentation formats together under the `document` category. The sub-groupings below reflect actual format type.

**Documents**

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| docx | ✅ | ✅ | Complete |
| odt | ✅ | ✅ | Complete |
| pdf | ✅ | ✅ | Complete |

**Spreadsheets**

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| ods | ✅ | ✅ | Complete |
| xlsx | ✅ | ✅ | Complete |

**Presentations**

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| ppt | ✅ | ✅ | Complete |
| pptx | ✅ | ✅ | Complete |

**Coverage: 7 / 7 — Full**

---

### Audio — 6 supported formats

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| aac | ❌ | ❌ | Missing both |
| flac | ❌ | ❌ | Missing both |
| m4a | ❌ | ❌ | Missing both |
| mp3 | ❌ | ❌ | Missing both |
| ogg | ❌ | ❌ | Missing both |
| wav | ❌ | ❌ | Missing both |

**Coverage: 0 / 6 — No coverage**

---

### Video — 1 supported format

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| mp4 | ❌ | ❌ | Missing both |

**Coverage: 0 / 1 — No coverage**

---

### Archive — 6 supported formats

| Slug | Master record | Knowledge file | Status |
|------|:---:|:---:|--------|
| 7z | ❌ | ❌ | Missing both |
| gz | ❌ | ❌ | Missing both |
| gzip | ❌ | ❌ | Missing both |
| rar | ❌ | ❌ | Missing both |
| tar | ❌ | ❌ | Missing both |
| zip | ❌ | ❌ | Missing both |

**Coverage: 0 / 6 — No coverage**

---

## Orphan files

These files exist in `app/data/formats/` and `app/data/format_knowledge/` but have **no active converter contract** generating them as supported formats. They may represent formats that were added manually, correspond to legacy converters, or are future-planned.

| Slug | Master record | Knowledge file | Note |
|------|:---:|:---:|------|
| csv | ✅ | ✅ | No active converter contract |
| doc | ✅ | ✅ | No active converter contract (superseded by docx) |
| gif | ✅ | ✅ | No active converter contract |
| ico | ✅ | ✅ | No active converter contract |
| odp | ✅ | ✅ | No active converter contract |
| rtf | ✅ | ✅ | No active converter contract |
| txt | ✅ | ✅ | No active converter contract |
| xls | ✅ | ✅ | No active converter contract (superseded by xlsx) |

**Action required:** Either add converter contracts for these formats or remove the orphan files to keep the data layer consistent.

---

## Gaps by priority

### Priority 1 — High traffic (conversion volume)

| Slug | Category | Action |
|------|----------|--------|
| mp3 | audio | Add master record + generate knowledge file |
| mp4 | video | Add master record + generate knowledge file |
| wav | audio | Add master record + generate knowledge file |
| zip | archive | Add master record + generate knowledge file |
| aac | audio | Add master record + generate knowledge file |

### Priority 2 — Medium traffic

| Slug | Category | Action |
|------|----------|--------|
| flac | audio | Add master record + generate knowledge file |
| m4a | audio | Add master record + generate knowledge file |
| ogg | audio | Add master record + generate knowledge file |
| rar | archive | Add master record + generate knowledge file |
| tar | archive | Add master record + generate knowledge file |

### Priority 3 — Lower traffic / edge cases

| Slug | Category | Action |
|------|----------|--------|
| 7z | archive | Add master record + generate knowledge file |
| gz | archive | Add master record + generate knowledge file |
| gzip | archive | Add master record + generate knowledge file (or alias to gz) |
| jpeg | image | Add master record + generate knowledge file (or alias to jpg) |

---

## Recommended next steps

1. **Batch 03 — Audio:** Create master records for `mp3`, `wav`, `aac`, `flac`, `m4a`, `ogg` and generate knowledge files.
2. **Batch 04 — Video:** Create master record for `mp4` and generate knowledge file.
3. **Batch 05 — Archive:** Create master records for `zip`, `rar`, `tar`, `7z`, `gz`, `gzip` and generate knowledge files.
4. **Alias strategy for `jpeg`:** Decide whether `jpeg` should have its own page or redirect to `jpg`. If a separate page is needed, create the master record and generate the knowledge file.
5. **Alias strategy for `gzip`:** Decide whether `gzip` should be a separate page or an alias of `gz`.
6. **Orphan review:** Audit the 8 orphan formats and either add converter contracts or remove the orphan master/knowledge files.
