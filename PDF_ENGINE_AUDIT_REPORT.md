# PDF ENGINE AUDIT REPORT

## Current Flow

1. UploadService menerima file PDF dan menyimpan sementara ke `uploads/`.
2. `app.services.conversion_service.ConversionService.convert_file()` memanggil plugin registry untuk memilih plugin berdasarkan `source_format` dan `target_format`.
3. Plugin terpilih (`PDFToWordPlugin`, `PDFToExcelPlugin`, `PDFToPPTPlugin`, `PDFToODTPlugin`) memanggil `DocumentEngine.convert()`.
4. `DocumentEngine.convert()` memilih konversi PDF office yang sesuai dan menulis hasil ke `outputs/document/`.
5. Output dikembalikan jika file ada dan berada dalam direktori yang diizinkan.

## Failure Point

- Tidak ditemukan error log production terkait `pdf-to-docx`, `pdf-to-xlsx`, `pdf-to-pptx`, atau `pdf-to-odt` di repositori saat ini.
- Lokal reproduksi langsung terhadap `DocumentEngine` untuk PDF → DOCX/XLSX/PPTX/ODT berhasil.
- Regression tests lokal untuk PDF Office konversi juga lulus.

## Root Cause

- Pada kondisi saat ini, tidak ada bukti bahwa kesalahan berasal dari kode konversi langsung; alur `DocumentEngine` dan plugin registry terlihat valid.
- Kode tidak menggunakan `soffice`/LibreOffice untuk PDF Office conversion, meskipun `Dockerfile` menginstal LibreOffice.
- Kemungkinan penyebab utama:
  - lingkungan produksi berbeda atau log belum tersedia sehingga kesalahan tidak dapat direproduksi dari repo ini,
  - atau PDF input produksi mengandung konten yang tidak didukung oleh library saat ini dan tidak tercakup oleh regression test.

## Files Involved

- `app/engines/document_engine.py`
- `app/plugins/document/pdf_to_word.py`
- `app/plugins/document/pdf_to_excel.py`
- `app/plugins/document/pdf_to_ppt.py`
- `app/plugins/document/pdf_to_odt.py`
- `app/plugins/document/__init__.py`
- `app/plugins/registry.py`
- `app/services/conversion_service.py`
- `app/routers/convert.py`
- `Dockerfile`
- `requirements.txt`
- `tests/test_convert_unsupported.py`
- `tests/test_office_converter_cluster.py`

## Proposed Minimal Fix

- Tambahkan regression test untuk `PDF → DOCX` dan perkuat validasi output pada PDF Office converter tests.
- Tetap gunakan implementasi saat ini karena lokal dan regression tests pass.
- Pastikan produksi mengumpulkan logs lengkap untuk `ConversionError` dan `RuntimeError` saat PDF Office conversion.
- Jika akar masalah adalah input PDF yang tidak didukung, pertimbangkan peningkatan validasi atau fallback khusus di engine tersebut.

## Risk Assessment

- Risiko rendah untuk perubahan yang hanya menambahkan regression tests.
- Tidak ada perubahan arsitektur atau pipeline yang diperlukan.
- Tidak ada dampak pada Image Engine atau Audio/Video Engine jika hanya menambahkan test coverage.

## Test Plan

- `pytest tests/test_convert_unsupported.py -q`
- `pytest tests/test_office_converter_cluster.py -q`
- `pytest -q` (suite penuh setelah konfirmasi perubahan kecil)

## Notes

- `Dockerfile` menginstal LibreOffice, tetapi kode `DocumentEngine` tidak memanggil `soffice`.
- `which soffice` di lingkungan lokal saat ini mengembalikan `None`.
- `discover_plugin_classes()` berjalan dengan benar dan menemukan semua PDF document plugins termasuk `PDFToODTPlugin`.
