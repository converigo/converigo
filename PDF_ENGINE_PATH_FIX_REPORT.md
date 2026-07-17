# PDF_ENGINE_PATH_FIX_REPORT

## Changed:
- `app/engines/document_engine.py`
  - Mengubah base `output_dir` dari hardcoded relatif:
    - `Path("outputs") / "document"`
  - menjadi konfigurasi terarah:
    - `settings.OUTPUT_DIR / "document"`

## Root Cause:
- Pada production, penulisan output `DocumentEngine` menggunakan path relatif `./outputs/document` (bergantung CWD), sementara konfigurasi production mengarahkan output ke direktori absolut `/app/outputs` via `settings.OUTPUT_DIR`.
- Ketidakkonsistenan ini dapat menyebabkan kegagalan saat menulis/validasi output atau output tidak tersimpan di direktori yang diharapkan.

## Solution:
- Gunakan konfigurasi yang sudah ada (`settings.OUTPUT_DIR`) untuk menentukan direktori output dokument.
- Tidak mengubah plugin contract dan tidak melakukan redesign.

## Tests:
- `pytest -q` dijalankan namun gagal dieksekusi di environment lokal.
- Error:
  - `Fatal error in launcher: Unable to create process ... The system cannot find the file specified.`

## Risk:
- Rendah–sedang.
  - Dampak fungsional: output doc kini selalu berada di bawah `settings.OUTPUT_DIR`, sehingga konsisten antara local/production.
  - Risiko kecil: perubahan path dapat memengaruhi test yang mengasumsikan lokasi relatif `./outputs/document`.
- Jika `settings.OUTPUT_DIR` tidak ada/permission bermasalah di production, kegagalan akan bergeser dari path mismatch menjadi permission/IO errors.

STOP

