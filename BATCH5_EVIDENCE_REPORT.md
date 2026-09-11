# BATCH 5 EVIDENCE REPORT — Opsi D (5 converter)

- **STATUS**: SELESAI DI GATE L — menunggu keputusan PC (tidak push / tidak PR / tidak merge / tidak deploy)
- **GATE**: L (evidence report delivered; STOP sebelum staging push)
- **Base**: `origin/main` @ `0257ea7` (worktree `C:\converigo\wt_batch5`, branch lokal `feat/certify-batch5-doc-image-archive`)
- **Metode**: FAST BATCH A–L penuh
- **Dikeluarkan**: rar-extract (VAR-34) — TIDAK disentuh sama sekali (plugin, engine, Dockerfile, requirements)

## A. Audit-ulang pra-implementasi
- Semua 6 kandidat di-audit ulang langsung dari worktree bersih `0257ea7` sebelum edit apa pun.
- `wt_batch5` dibuat via `git worktree add` dari `0257ea7`; verifikasi `git rev-parse HEAD` = `0257ea76c65312f3fc6cfc65af3129c1e2a59165`, status bersih sebelum baseline.

## B. Dependency
- **TIDAK ADA dependency baru.** `pypdf>=6.16.2` (BSD-3) sudah ada di `requirements.txt` dan venv (versi terpasang 6.16.2 — diverifikasi).
- zip-extract fix memakai `shutil.make_archive` (stdlib). RAR tidak disentuh (tetap butuh `unrar` binary — ditunda ke Batch 6).

## C. Implementasi (13 file disentuh: 9 modified + 5 baru)
| # | File | Aksi |
|---|------|------|
| 1 | `app/plugins/archive/zip_extract.py` | FIX VAR-33: plugin kini mengemas hasil ekstraksi menjadi **file ZIP** via `shutil.make_archive` dan mengembalikan Path file (bukan directory). Engine bersama (`app/engines/archive_engine.py`) TIDAK diubah → rar-extract/7z-extract 100% utuh |
| 2 | `app/plugins/document/pdf_compress.py` | REWRITE asli: `PdfReader` → `PdfWriter.append` → `page.compress_content_streams()` (deflate lossless per halaman) → `writer.compress_identical_objects()` (dedup objek). Guard: output tidak pernah lebih besar dari input (fallback byte asli bila rekompresi tidak mengecilkan) |
| 3 | `app/routers/tools.py` | `DISABLED_TOOL_SLUGS` → kosong (pdf-compress un-disable; halaman publik aktif) |
| 4 | `app/services/converter_data_service.py` | `PUBLIC_UI_DISABLED_SLUGS` → hanya `pdf-merge` (pdf-compress dikeluarkan; pdf-merge tidak disentuh) |
| 5 | `app/data/converters/txt-to-pdf.contract.json` | BARU — `/tools/txt-to-pdf`, `lifecycle_status: certified` |
| 6 | `app/data/converters/jpg-to-pdf.contract.json` | BARU — `/tools/jpg-to-pdf`, `certified` |
| 7 | `app/data/converters/webp-to-jpg.contract.json` | BARU — `/tools/webp-to-jpg`, `certified` |
| 8 | `app/data/converters/zip-extract.contract.json` | UPDATE — `landing_path/canonical_url` → `/tools/zip-extract`, `active`→`certified` |
| 9 | `app/data/converters/pdf-compress.contract.json` | UPDATE (sesuai instruksi PC) — `landing_path/canonical_url` → `/tools/pdf-compress`, `active`→`certified` |
| 10 | `app/data/converters/txt-to-pdf.json` | BARU — landing JSON lengkap (20 key, pola jpg-to-pdf.json), `canonical /tools/txt-to-pdf` |
| 11 | `app/data/certified_converters.json` | +5 entry `certified+locked` dengan `test_files` (52→57 slug; 0 duplikat; 0 tabrakan) |
| 12–16 | `tests/certified/document/test_{txt_to_pdf,jpg_to_pdf,pdf_compress}_certified.py`, `tests/certified/image/test_webp_to_jpg_certified.py`, `tests/certified/archive/test_zip_extract_certified.py` | BARU — certified test real-file parametrized (33 test) |

## D–E. Certified test + E2E real-file (server uvicorn nyata, port 8123)

**Targeted certified run**: `68 passed, 0 failed` (5 file certified baru + test_pdf_cluster + test_archive_converter_cluster + test_converter_contract).
**E2E evidence** (`wt_batch5/tmp/batch5_e2e/evidence.json`, run 2× — hijau konsisten):

| Converter | Input (sha256 awal 8) | in→out (B) | Validasi output |
|---|---|---|---|
| txt-to-pdf | `ee06af3f` (sample.txt 14 B) | 14 → 1.414 | PDF valid, 1 halaman; sha256 output `1cbeeebf…`; `content-disposition: attachment` |
| jpg-to-pdf | `dd07a180` (sample.jpg 634 B) | 634 → 1.720 | PDF valid, 1 halaman; `58159bc0…` |
| webp-to-jpg | `72bd530a` (sample.webp 68 B) | 68 → 635 | PIL format JPEG; `5fcf0859…` |
| zip-extract | `daafb111` (zip buatan 393 B, 3 member + nested dir) | 393 → 665 | **zip valid**; member set & isi byte-identik (`alpha/one.txt`, `beta/two.txt`, `alpha/deep/three.txt`); `c91a4f4f…` |
| pdf-compress | `6e87b608` (PDF reportlab pageCompression=0, 3 halaman, 11.273 B) | 11.273 → **2.443** | **Output benar-benar lebih kecil (ratio 0.2167, −78%)**; teks terjaga (`BATCH5-E2E` terekstrak); 3 halaman; `0cca9c4e…`; nama file download `*_compressed.pdf` |

- Tool pages publik `/tools/{5 slug}` semua **200** — khusus pdf-compress: **tidak lagi 404** ✓
- Download route: semua 5 output terunduh 200 dengan header `attachment`.

## F. Registry
- 5 entry baru `certified + locked` dengan `test_files` tepat; `app/data/certified_converters.json` valid (57 slug, tanpa duplikat, tanpa tabrakan; konfirmasi via parser JSON).

## G. UI STATIC_TARGET_MAP (+ verify_map_vs_registry)
- `converigo_main.html` **TIDAK disentuh** — `git diff` = kosong → **0 perubahan key Batch1/2/3/4** (jpg/pdf/txt/webp/zip semuanya sudah ada di map sebelumnya; zip→zip & pdf→pdf = self-conversion yang memang dikecualikan dari map).
- Verifier derivasi-registry (aturan yang sama dengan test permanen `tests/test_ui_target_mapping.py`): **deployed map == derivasi registry untuk SEMUA 38 source key**; 9 key html-only semuanya placeholder kosong pre-existing.
- `tmp/verify_map_vs_registry.py` (repo, node-based) diadaptasi ke wt_batch5: satu-satunya "mismatch" = `gz/gzip` + placeholder keys — **state pre-existing main** (aturan alias tmp-script lebih ketat daripada map ter-deploy), BUKAN akibat Batch 5 (registrasi plugin tidak berubah; file script tmp masih hardcode `wt_batch3` — pre-existing, tidak disentuh).

## H–I. Targeted regression & fix
- Test yang meng-encode state LAMA di-update **karena keputusan PC** (un-disable + sertifikasi), bukan untuk menyembunyikan regresi:
  1. `tests/test_pdf_cluster.py::test_disabled_pdf_compress_is_404_and_absent_from_homepage` → diganti `test_pdf_compress_tool_page_is_live_after_batch5` (200 + judul tampil; pola test_pdf_merge_is_now_live).
  2. `tests/test_archive_converter_cluster.py::test_archive_contracts_have_valid_schema` — assert `lifecycle_status == "active"` diperluas `in {"active","certified"}` (konsisten klaster Batch 3/4; zip-extract kini certified).
- Seluruh test terdampak hijau (lihat D).

## J. Full regression — baseline vs delta
- **Baseline (0257ea7 bersih, sebelum edit apa pun)**: `681 passed, 14 failed, 5 skipped, 1 xfailed` (18m19s). Catatan PC "665P/14F" terkonfirmasi bentuknya: 14F sama, P naik karena Batch 1–4 sudah tergabung.
- **14F baseline (pre-existing)**: test_globalfmt_intersection (1), test_i18n (4), jpg_to_png_landing (1), office_converter_cluster hub/sitemap/audit (1), production_audit_service (1), seo_crawlability (2), seo_urls (1), sitemap_service (1), webp_to_jpg_landing (1), webp_to_png_landing (1).
- **Delta penuh**: lihat bagian K-Result di bawah (diisi pada run final).

## K. Evidence report — this document
- Artefak bukti: `wt_batch5/tmp/batch5_e2e/evidence.json` + `tmp/batch5_e2e/*_input|_output` + log baseline/full regression (`tmp/baseline_stdout.log`, `tmp/batch5_full_stdout.log`) + staging `c:\converigo\tmp\batch5_staging\` (skrip verifikasi, di luar tree).

## Verifikasi tata kelola
- **rar-extract/Dockerfile/requirements.txt TIDAK disentuh** — `git diff --stat` pada `app/plugins/archive/rar_extract.py`, `app/engines/archive_engine.py`, `Dockerfile`, `requirements.txt` = kosong.
- **Tidak ada dependency baru** (pypdf sudah ada; make_archive = stdlib).
- **Staging eksplisit**: tidak ada `git add -A`; hanya file-file pada tabel di atas yang akan di-stage.
- Converter certified+locked lain TIDAK disentuh (perubahan JSON converter hanya pada 5 slug Batch 5 + registry).
- `wt_batch4/` lama dihapus sesuai otorisasi (komit tetap aman di branch `feat/batch4-image-conversions`).

## Catatan teknis (untuk PC)
1. **pypdf 6.16.2 API**: `PageObject.compress_content_streams()` tersedia; `compress_identical_objects()` dipanggil tanpa argumen (default `remove_duplicates/remove_unreferenced=True`) untuk menghindari DeprecationWarning `remove_orphans` (deprecated, dihapus di pypdf 7).
2. **Guard pdf-compress**: PDF yang sudah teroptimasi bisa tidak mengecil → plugin mengembalikan byte asli (output ≤ input, diuji TEST 006). Ini perilaku produk yang disengaja dan terdokumentasi di docstring plugin.
3. **Artefak `temp/` untracked** muncul di worktree karena test memakai `settings.TEMP_DIR` default (`temp/`) yang tidak ada di `.gitignore` — TIDAK di-stage; opsi: tambahkan `temp/` ke `.gitignore` (keputusan PC, di luar scope batch).
4. `tmp/regenerate_static_map.py` & `tmp/verify_map_vs_registry.py` masih hardcode `wt_batch3` (pre-existing, tracked di main) — tidak disentuh; verifikasi Batch 5 memakai salinan adaptif di `c:\converigo\tmp\batch5_staging\`.
5. `tests/results/` adalah artefak pytest — tidak di-stage.
6. `RC1_2_CONVERTER_JSON_REPORT.md` ikut di-commit: itu artefak generated `tests/test_converter_json_validator.py` yang otomatis ter-regenerasi saat suite berjalan ("Checked files: 64→65" karena `txt-to-pdf.json` baru; "Files with issues: 0" tetap).

## K-Result (full regression final)
- PASS/FAIL delta: baseline `681P / 14F / 5S / 1xF` → post-Batch5 `720P / 14F / 5S / 1xF` = **+39 passed** (tepat 39 test-item certified baru: 7+7+7+9+9), **failed tetap 14 dan IDENTIK per test-id dengan baseline** (Compare-Object = kosong; daftar di `c:\converigo\tmp\batch5_staging\fullreg_failed.txt`).
- Kesimpulan: **0 regresi baru**; 14 failure adalah pre-existing main (terdokumentasi di bagian J, di luar scope Batch 5 — sebagian besar klaster i18n/SEO/landing yang sudah merah sebelum batch ini). Tidak ada fix regresi yang diperlukan (I: N/A — bukti pre-existing vs baru disajikan di atas).

## L. STOP
- Tidak push, tidak PR, tidak merge, tidak deploy. Branch lokal `feat/certify-batch5-doc-image-archive` berisi komit Batch 5 (lokal saja).
- **DECISION REQUIRED dari PC**: (1) terima/ Tolak hasil Batch 5 di gate ini; (2) arahan lanjut Batch 6 (rar-extract: libarchive-c vs symlink+RAR≤3 vs defer); (3) opsional: tambah `temp/` ke `.gitignore`; (4) opsional: perbaiki hardcode `wt_batch3` pada 2 script tmp.


