# Phase 19.3 — Read-Only Canonicalization Specification (Draft)

Date: 2026-08-20
Author: Supervisor-approved spec (read-only)

Scope & Constraints
-------------------
- This is a documentation-only specification for Phase 19.3 canonicalization. It defines mapping candidates, types, transformations, confidence levels, and NO-GO rules.
- Do NOT execute transformations, create canonical CSVs, modify raw Layer 1 files, or alter application/test/config/deployment/brain files.
- Canonical baseline window: 2026-07-10 → 2026-08-17 (inclusive).
- RAW Layer 1 evidence remains immutable and authoritative. Data outside the canonical baseline (notably 2026-08-18 and 2026-08-19) remain evidence-only and must not be included in canonical outputs.

Primary Candidates (Bagan files)
--------------------------------
1) GSC Performance Bagan.csv (source: seo_data/gsc/raw/https___converigo.com_-Performance-on-Search-2026-08-20 (5).zip)

Raw -> Canonical field mappings:
- `Tanggal` -> `Date` | type: date (YYYY-MM-DD) | transformation: Parse as ISO date; validate within canonical window; filter to canonical window at transformation time | confidence: High | justification: Native per-row date column present.
- `Klik` -> `Clicks` | type: integer | transformation: Trim, parse int, null->0 rule applied during transformation | confidence: High | justification: Standard GSC metric.
- `Tayangan` -> `Impressions` | type: integer | transformation: Trim, parse int | confidence: High | justification: Standard GSC metric.
- `CTR` -> `CTR` | type: decimal (0-1 or percent string normalization) | transformation: Normalize percent strings (e.g., "50%" -> 0.5) or decimals; validate range 0..1 | confidence: High | justification: Standard reporting field.
- `Posisi` -> `Position` | type: decimal | transformation: parse float, null handling | confidence: High | justification: Standard GSC metric.

Notes: Bagan.csv is a per-day series; it is the primary date-addressable Performance source and a candidate for canonicalization for rows that fall within the canonical baseline.

2) GSC Indexing/Coverage Bagan.csv (source: seo_data/indexing/raw/https___converigo.com_-Coverage-2026-08-20 (2).zip)

Raw -> Canonical field mappings:
- `Tanggal` -> `Date` | type: date | transformation: Parse ISO date; validate for canonical window; filter during canonicalization | confidence: High | justification: per-row date present and aligns with baseline end 2026-08-17.
- `Tidak diindeks` -> `NotIndexedCount` | type: integer | transformation: parse int | confidence: High | justification: coverage trend metric.
- `Terindeks` -> `IndexedCount` | type: integer | transformation: parse int | confidence: High | justification: coverage trend metric.
- `Tayangan` -> `Impressions` | type: integer | transformation: parse int | confidence: Medium | justification: coverage `Tayangan` may represent search impressions; include with caution.

Snapshot / Issue lists:
- `Masalah penting.csv` -> preserve as `CoverageIssuesCritical` (table of `Reason, Source, Validation, Page`) | type: table (string fields) | transformation: none (preserve) | confidence: High | justification: snapshot evidence of indexing issues.
- `Masalah non-kritis.csv` -> `CoverageIssuesNonCritical` | type: table | transformation: preserve | confidence: High
- `Metadata.csv` -> `CoverageMetadata` (key/value) | transformation: preserve key/value pairs | confidence: High

3) GSC Generative AI Bagan.csv (source: seo_data/gsc/raw/https___converigo.com_-Performance-on-Search-Generative-AI-Features-2026-08-20.zip)

Raw -> Canonical field mappings:
- `Tanggal` -> `Date` | type: date | transformation: Parse date; filter to canonical window | confidence: High | justification: per-row date column.
- `Tayangan` -> `Impressions` (or `GenerativeAIFeatureImpressions`) | type: integer | transformation: parse int | confidence: High | justification: direct metric.

GSC Breakdown Files (Aggregate evidence only)
--------------------------------------------
- Files: `Kueri.csv`, `Halaman.csv`, `Negara.csv`, `Perangkat.csv` in GSC Performance zips.
- Characteristic: file-level top-N aggregations without per-row `Date` column.

Specification for treatment:
- Preserve these files as aggregate evidence tables under Layer 2 mapping metadata; do NOT fabricate or assign per-row dates.
- Recommended canonical representation (spec-only): `AggregateTopN_{source}_{file}.csv` containing original columns plus `FileDateRangeStart`, `FileDateRangeEnd` (sourced from `Bagan.csv` or from `Filter.csv` human-readable range) — these FileDateRange fields are metadata and must NOT be used to synthesize per-row dates.
- Raw Field -> Canonical Candidate examples:
  - `Kueri teratas` -> `Query` | type: string | transform: trim | confidence: High (field present)
  - `Halaman teratas` -> `Page` | type: string (URL) | transform: trim; URL normalization NO-GO until Supervisor allows | confidence: Medium
  - `Negara` -> `Country` | type: string | transform: trim | confidence: High
  - `Perangkat` -> `Device` | type: string | transform: normalize device labels | confidence: High

GA4 Summary Export (Evidence-only)
----------------------------------
- File: `seo_data/ga4/raw/Ringkasan_memahami_traffic_web_dan_atau_aplikasi.csv`
- Treatment: Evidence-only summary; do NOT create `canonical_ga4_traffic.csv` from this file alone.
- Sections present (examples): Country counts, City counts, Day-offset series, Event counts, Page title views, DAU/MAU series, Language counts.

For each GA4 section:
- Record SectionName, HeaderColumns, RowCount, SectionDateRange (from section header tokens `Tanggal mulai` / `Tanggal akhir`).
- Mapping rules (spec-only):
  - If a section provides direct `Date` and `PagePath` per row, it may be mapped; otherwise, mark as `UNMAPPABLE` for page-level canonicalization.
  - `Nama peristiwa, Jumlah peristiwa` MUST NOT be mapped to `KeyEvents` unless the event is verified as a Key Event in GA4 property settings (Key Event status not inferable from this export) — record KeyEvents as `UNVERIFIED` / `NOT AVAILABLE`.

Field mapping template (for inclusion in canonicalization spec)
------------------------------------------------------------
Each mapping row must include:
- RAW FIELD
- RAW FILE (location)
- CANONICAL FIELD
- TYPE
- TRANSFORMATION (text description)
- CONFIDENCE (High/Medium/Low)
- JUSTIFICATION

NO-GO RULES (enforced)
----------------------
- No fabricated or synthesized per-row dates for files that lack a native date column.
- No fabricated `KeyEvents` — only events explicitly marked Key Events in the GA4 property may populate `KeyEvents`.
- No page-path inference from page titles or other heuristics.
- No conversion mapping or renaming Key Events to Conversions.
- No inclusion of data outside the canonical baseline window into canonical datasets.
- No modification of Layer 1 raw files.

Validation & Confidence
-----------------------
- Confidence levels are assigned based on presence of native per-row dates, standard GSC column names, and direct metric alignment.
- Any mapping requiring URL normalization, per-row date synthesis, or GA4 KeyEvent verification is assigned `Low` confidence until a supervised transformation rule is approved.

Deliverables (read-only)
------------------------
- This document (spec) under `docs/` — defines canonicalization candidates and NO-GO rules.
- A follow-up actionable transformation plan will be drafted after Supervisor review; implementation requires explicit Supervisor GO.

Signed-off-by: Supervisor (spec draft)
