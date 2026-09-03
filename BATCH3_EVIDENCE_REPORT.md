# BATCH 3 EVIDENCE REPORT — images-to-pdf (VAR-10) + pdf-to-txt (DOC-05)

Branch: `feat/batch3-images-pdf-txt` (dari `origin/main` = `83a8d08`, memuat PR #70/Batch1+2 live)
Tanggal: 2026-09-03 · Metode: FAST BATCH DEVELOPMENT (A–L) · Status: **STOP di merge/deploy gate (L)** — belum push, belum PR.

## Konteks keputusan
PR #69 (feat/subbatch-c-p1-image-doc) **CLOSED (bukan merged)** pada 2026-09-03T13:18:18Z dengan komentar penjelasan: klaim sertifikasi kedua converter tidak pernah ter-commit di repo manapun (merge 8a80279 bahkan mengecualikan keduanya), sehingga substansinya dilanjutkan sebagai pekerjaan baru dari main terkini. Branch lama dipertahankan untuk referensi.

## A. Audit ulang dari kondisi main saat ini
- `registry.py` main: slug-aware resolution (`by_slug`, `registered_keys`) + registrasi `source_formats × target_formats`; **TIDAK memerlukan** filter `supports()` versi stash (stash dibuat sebelum slug-aware resolution & sebelum PR#68 menyediakan jalur `merge()`).
- `conversion_service.merge_files()` sudah ada (warisan PR#68) tetapi *hardcode* `pdf→pdf` → digeneralisasi minimal (lihat C/F).
- Router main sudah punya pola multi-file (`pdf-merge`) → diikuti untuk `images-to-pdf`.
- `STATIC_TARGET_MAP` di `app/templates/main/converigo_main.html` + permanent regression test `tests/test_ui_target_mapping.py` (Playwright live).

## B. Dependency & lisensi (TIDAK ada dependency baru)
| Lib | Kebutuhan | Lisensi | Status |
|---|---|---|---|
| Pillow>=12.2.0 | images-to-pdf (combine → PDF) | MIT-CMU/HPND (permissive) | sudah di `requirements.txt` + venv |
| pypdf>=6.16.2 | pdf-to-txt (extract_text) | BSD-3-Clause | sudah di `requirements.txt` + venv |

## C. Implementasi plugin (review ulang dari stash@{0} + file untracked, BUKAN commit buta)
- `app/plugins/image/images_to_pdf.py` — Pillow `save_all` multi-image→1 PDF; `merge()` wajib ≥2 file; `convert()` **disempurnakan** dari draft stash (yang me-raise): single-image → genuine 1-page PDF (preseden `pdf_merge.convert()`), sehingga jalur dropdown png/webp/bmp/tiff/gif→PDF tidak menghasilkan error palsu. `source_formats = [png, webp, bmp, tiff, gif]` — jpg/jpeg sengaja dikecualikan (dilayani `jpg-to-pdf` yang sudah certified, hindari tabrakan pasangan).
- `app/plugins/document/pdf_to_txt.py` — pypdf; cek encrypted & pages kosong (honest error); join `\n\n` antar halaman; UTF-8.
- `app/routers/convert.py` — branch multi-file `operation == "images-to-pdf"` (mirror pola `pdf-merge`): upload semua → wajib ≥2 → `merge_files(slug)` → respons single-object.
- `app/services/conversion_service.py` — `merge_files()` derive `source_format` dari suffix file pertama (perilaku pdf-merge `pdf→pdf` tidak berubah — dibuktikan test certified pdf-merge/split tetap PASS).
- `app/utils/file_validator.py` — **PERBAIKAN GAP PRE-EXISTING yang membuktikan diri saat verifikasi real-file (langkah E/I)**: `tiff` tidak ada di `ALLOWED_EXTENSIONS` (png/gif/webp/bmp ada) sehingga upload `.tiff` selalu ditolak. Ditambahkan konsisten: `ALLOWED_EXTENSIONS` + `FILE_SIGNATURES["tiff"] = [II*\0, MM\0*]` + `CONTENT_TYPE_BY_EXTENSION["tiff"] = ["image/tiff"]`.
- Data converter (disinkronkan dengan scope plugin; draft lokal mengklaim jpg/jpeg untuk images-to-pdf — dikoreksi): `app/data/converters/images-to-pdf.json` (+`.contract.json`), `pdf-to-txt.json` (+`.contract.json`).
- `app/data/certified_converters.json` — 2 entry baru `locked: true` + `test_files` (mengikuti preseden pdf-merge/pdf-split dari PR#68). Total slug certified: 40→42, locked: 40→42.

## D. Certified tests — PASS (16/16, 3.9s)
- `tests/certified/image/test_images_to_pdf_certified.py` — 11 test: discovery, resolusi pair kelima source (+ jpg tetap ke jpg-to-pdf), combine 3 real image via `/convert` (201, 3 halaman, bukan byte-copy), download attachment, reject single file (400 "at least 2"), reject garbage (honest error), parametrized **real-file per format PNG/WEBP/BMP/TIFF/GIF** via `plugin.merge()` (file disk nyata, validasi `%PDF-` + jumlah halaman).
- `tests/certified/pdf/test_pdf_to_txt_certified.py` — 5 test: discovery, ekstraksi teks asli 2 halaman (string khusus terverifikasi di output), download, reject fake PDF, resolusi pair tanpa slug.
- Semua test memakai `@pytest.mark.certified`; STATUS header = CERTIFIED (evidence run, pending gate PC).

## E. Real-file verification (mandiri) — ALL PASSED
`tmp/realfile_verify_batch3.py` (output: `tmp/realfile_verify_batch3.out.txt`):
- 5 file real di disk (png 281B, webp 102B, bmp 32.454B, tiff 32.540B, gif 207B; sha256 dicatat) → `/convert` HTTP 201 → `combined.pdf` 6.948B, header `%PDF-`, **5 halaman**, download `/download/...` 200 (6.948B).
- `doc.pdf` real (1.909B) → HTTP 201 → TXT 67B berisi teks kedua halaman (verified).

## F. Registry verification
Registry main TIDAK perlu filter stash; kelima pair (png/webp/bmp/tiff/gif→pdf) terdaftar dan resolve ke plugin baru; `jpg→pdf` tetap ke `jpg-to-pdf` (dibuktikan TEST 002). `merge_files` slug-resolution lolos validasi `registered_keys`.

## G. UI target mapping — MATCH (0 regresi Batch3)
Map di-patch manual (6 baris), lalu diverifikasi `tmp/verify_map_vs_registry.py` (Node-parse HTML vs derivasi registry):
- `png:['BMP','ICO','JPEG','JPG','PDF','TIFF','WEBP']`, `webp:['ICO','JPEG','JPG','PDF','PNG','TIFF']`, `bmp:['JPEG','JPG','PDF','PNG','WEBP']`, `tiff:['JPEG','JPG','PDF','PNG']`, `gif:['PDF']` (sebelumnya kosong), `pdf: +TXT` (urut alfabetis).
- Sisa MISMATCH = pre-existing & bukan sentuhan Batch3: key kosong by-design (html/md/rtf/ogg/mov/avi/webm/mkv/flv → artefak perbandingan script) + `gz/gzip` (aturan alias generator memfilter pasangan arsip; baris tidak disentuh batch ini).
- **Tidak ada key Batch1/2 (xlsx/csv/json/wav/flac/m4a/aac/mp4) yang berubah** — git diff template hanya 6 baris target di atas.

## H/I. Regression targeted — 29 passed, 0 gagal (15.7s)
`test_ui_target_mapping` (Playwright live), certified pdf-merge+split, `test_converter_contract` (JSON baru lolos kontrak), `test_supported_converter_filtering`, `test_convert_unsupported`, `test_jpg_to_pdf`, `test_png_to_jpg_integration`. Warning = deprekasi pre-existing (SwigPy/pymupdf).

## J. Full regression checkpoint (SATU KALI)
Suite penuh (PID 24240, 11m16s): **661 passed / 14 failed / 5 skipped / 1 xfailed**.
- Rerun 15 failure terhadap worktree pristine `origin/main` (83a8d08, `wt_b3_baseline`): **14 dari 15 GAGAL JUGA di baseline** → pre-existing (i18n landing, SEO/sitemap URL produksi, globalfmt jpg+png stale, dll.), bukan sentuhan Batch 3.
- Satu-satunya delta nyata: `test_phase_c_mixed_batch.py::test_partial_success_via_api` (baseline PASS → Batch3 FAIL) — test mengasumsikan `png→pdf` unsupported ("phase A matrix"), kini pasangan itu certified. **Diperbaiki (langkah I)**: leg failing diganti ke `png→mp3` (memang tanpa converter), intent test (partial success) tetap. Re-run: **PASS**.
- Net delta Batch 3 setelah fix = **0 regresi** (14 pre-existing gagal di kedua sisi).


## K. Lampiran
- Commit di branch ini: staging eksplisit per kelompok (tanpa `git add -A`), lihat `git log`.
- Worktree terpisah `C:\converigo\wt_batch3` — main worktree & server produksi tidak tersentuh.
- Converter certified+locked lain: TIDAK disentuh (hanya penambahan entry baru di cc.json).