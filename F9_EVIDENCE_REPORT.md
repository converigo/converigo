# F-9 IMPLEMENTATION EVIDENCE REPORT — Opsi 1: Restore 5 Registry Pages
**Repo:** converigo · **Tanggal:** 2026-09-07 · **Mode:** IMPLEMENTASI (Supervisor AUTHORIZE, STOP-mandate diterapkan)
**Scope:** restore 5 registry page + contract (`app/data/converters/`) untuk slug yang sudah certified di ledger. **Bukan** manipulasi ledger; **bukan** menyentuh converter/routing/sitemap/SEO lain.

## (0) Ringkasan
- **Yang diubah:** tepat **10 file baru** (5 × `<slug>.json` page + 5 × `<slug>.contract.json`), +715 baris, −0 baris. Tidak ada file lain.
- **Yang TIDAK diubah:** `app/data/certified_converters.json` (ledger, certified=100 tetap), plugin, routing, sitemap manual, template, test, dependency, WIP/stash, worktree lain.
- **Verdict implementasi:** ALL GATES PASS — PR siap; merge/deploy menunggu approval Supervisor (pola F7/F8/Bridge).

## (1) Gate A — Provenance basis (LANGKAH WAJIB #1–#4)
- `git ls-remote origin refs/heads/main` dijalankan **tepat sebelum** worktree dibuat → **`004e6074d7d4a925715d57c289b2520ab3459d91`** (identik baseline Gate 1; remote main tidak bergerak antar sesi pada titik ini).
- Worktree baru terpisah: `C:\converigo-wt_f9`, branch baru `feat/f9-restore-registry-pages` (bukan kelanjutan branch F8/bridge).
- `git rev-parse HEAD` di worktree = persis SHA LANGKAH 1; `git status --porcelain` awal = **kosong**.
- Guard: `git merge-base --is-ancestor fd6e42a1 HEAD` → exit 1 (**fd6e42a1 BUKAN ancestor**); branch `backup-before-homepage-rollback` tidak pernah dirujuk. `C:\converigo` (WIP 50 porcelain + 4 stash) tidak disentuh; origin tidak di-fetch (hanya ls-remote).

## (2) Gate B — Generasi artefak (LANGKAH #5)
- Metode: `scripts/factory_contract_gen.py --spec-file tmp/f9_specs.json --out-dir app/data/converters` (generator Factory yang SUDAH ADA di main `004e6074` — pola F-batch; validasi via `ConverterRegistryService` produksi).
- 5 spec → 10 file (`WROTE` × 10). Field kunci hasil (semua dari plugin/ledger, diverifikasi probe):
  - csv-to-xlsx: engine=spreadsheet, in=csv(text/csv)→out=xlsx, max=524288000, sample=tests/sample.csv, lifecycle=certified
  - xlsx-to-csv: engine=spreadsheet, in=xlsx(xlsxml-mime)→out=csv, max=524288000, sample=tests/sample.xlsx, lifecycle=certified
  - csv-to-json: engine=spreadsheet, in=csv(text/csv)→out=json, max=524288000, sample=tests/sample.csv, lifecycle=certified
  - json-to-csv: engine=spreadsheet, in=json(application/json)→out=csv, max=524288000, sample=tests/sample.csv, lifecycle=certified
  - mp4-to-gif: engine=ffmpeg, in=mp4(video/mp4)→out=gif, max=104857600, sample=tests/sample.mp4, lifecycle=certified
- Keputusan konvensi: category mengikuti plugin (spreadsheet×4, video×1); `max_upload` default generator 500MB untuk spreadsheet = preseden `xlsx-to-json.contract.json` di main; mp4-to-gif 100MB = preseden cluster ffmpeg (`mp4-to-aac`/`mp4-to-mp3`); page JSON = skema generator persis (canonical `https://converigo.com/tools/<slug>`, `lifecycle_status: certified` = preseden `xlsx-to-json.json`).
- **Deviasi terdokumentasi (1):** `regression_sample` untuk json-to-csv = `tests/sample.csv` (default generator `tests/sample.json` **tidak ada** di tree main; file sample.csv ada dan klaster spreadsheet konsisten).

## (3) Gate C — Validasi kontrak & governance (LANGKAH #6, #9)
- `factory_contract_gen.py --check`: **PASS — 97 contract valid** per ConverterRegistryService produksi (92 sebelum + 5 baru).
- Governance probe (`tmp/f9_governance_check.py`, evidence): **PASS 5/5** — plugin terdaftar & metadata (name/description/engine/format) == contract == page; `lifecycle_status=certified` di contract & page; kelima slug ada di section `certified` ledger; **ledger certified=100, untouched** (LANGKAH #6 terpenuhi).

## (4) Gate D — Test targeted + perbandingan baseline (LANGKAH #9)
Suite (identik pre/post): `tests/certified/spreadsheet/test_spreadsheet_certified.py`, `tests/certified/video/test_mp4_to_gif.py`, `tests/test_converter_registry_service.py`, `tests/test_related_converter_service.py`, `tests/test_sitemap.py`, `tests/test_search_console_readiness.py`, `tests/test_ui_target_mapping.py`.
| Run | Hasil | Log |
|---|---|---|
| Baseline (worktree bersih @004e6074, sebelum file ditulis) | **42 passed**, 0 failed (26.09s) | `tmp/f9_baseline_pytest.txt` |
| Post-change (setelah 10 file) | **42 passed**, 0 failed (17.74s) | `tmp/f9_post_pytest.txt` |
- **Failure-set diff = 0.** Tidak ada regresi pada test terkait (registry, related-4-unique, sitemap, search-console, UI-target-map).

## (5) Gate E — Route verification lokal (pre-deploy proxy)
`tmp/f9_route_check.py` (TestClient, mirror `g1_f9_probe.py`): **PASS**
- `/tools/csv-to-xlsx`, `/tools/xlsx-to-csv`, `/tools/csv-to-json`, `/tools/json-to-csv`, `/tools/mp4-to-gif` → **HTTP 200 + konten nyata** (title ter-render: "CSV to XLSX Converter" dst., 63.7–64.0 KB per halaman, markup FAQ ada) — 404 → 200.
- Kontrol positif `/tools/mp4-to-mp3` → 200. Kontrol negatif `/tools/does-not-exist` → 404 (404 tetap generik untuk slug tanpa registry).
- `/sitemap.xml` → 200, **207 URL**, kelima URL `/tools/<slug>` baru **hadir otomatis** (202 + 5, aditif; tidak ada edit sitemap manual).

## (6) Gate F — Audit diff (LANGKAH #10)
- `git status --porcelain` (pre-stage): **tepat 10 `??`**, semua di `app/data/converters/`.
- `git diff --stat`: **10 files changed, 715 insertions(+), 0 deletions(-)** — murni aditif.
- Diff penuh disimpan: `tmp/f9_full_diff.txt` (775 baris; daftar file = 10 yang diharapkan, tidak ada lainnya). **Tidak ada temuan out-of-scope → tidak ada STOP.**

## (7) Gate G — PR
- Branch: `feat/f9-restore-registry-pages` (baru, dari `004e6074`), push ke origin, PR terpisah (bukan lanjutan F8/bridge).
- Isi PR: 10 file registry + report ini (pola BATCH3/BATCH5_EVIDENCE_REPORT.md yang committed di root).

## (8) Production verification checklist — POST-MERGE/DEPLOY (menunggu approval Supervisor)
1. 5 route `/tools/{csv-to-xlsx,xlsx-to-csv,csv-to-json,json-to-csv,mp4-to-gif}` → HTTP 200 + verifikasi konten level (real file/page render, pola F7/F8/Bridge).
2. `/tools/pdf-metadata` → HTTP 200 (kontrol positif, area sama, tidak regress).
3. Regression smoke: cluster spreadsheet (4 slug CSV/XLSX) + cluster ffmpeg (mp4-to-gif) → PASS; failure-set dibandingkan baseline pre-change.
4. Konfirmasi ledger↔produk: accessible Y 95 → **100** (ledger tetap X=100, tanpa perubahan).
5. Evidence production verification → **STOP untuk final sign-off Supervisor.** SEO Gate 1 tetap HOLD.

## (9) Attestation
Dilarang-dilarang dipenuhi: ledger tidak disentuh; stash & WIP tidak disentuh; `fd6e42a1`/`backup-before-homepage-rollback` tidak dipakai dalam bentuk apapun; tidak ada perubahan converter lain/routing/sitemap manual/SEO; tidak ada perubahan di luar 10 file registry. Remote main tidak di-fetch/mutasi (ls-remote read-only).

## TERMINATION (sesi implementasi)
F-9 Opsi 1: IMPLEMENTED (10 file) — TESTS PASS — PR READY
MERGE: NOT PERFORMED (menunggu approval Supervisor)
DEPLOY: NOT PERFORMED
PRODUCTION VERIFICATION: PENDING (post-merge)
SEO GATE 1: STILL HOLD

