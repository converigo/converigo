# JSON Standardization Audit

## 1. Scope

Audit ini mencakup seluruh converter JSON yang tersimpan di [app/data/converters](app/data/converters) dan mengacu pada service pembaca di [app/services/converter_data_service.py](app/services/converter_data_service.py), SEO di [app/services/seo_service.py](app/services/seo_service.py), serta routing landing/tool di [app/routers/tools.py](app/routers/tools.py) dan [app/routers/home.py](app/routers/home.py).

Tujuan dokumen ini adalah memberi standar konsisten untuk metadata converter tanpa mengubah kode aplikasi.

## 2. Inventaris Converter JSON

Terdapat 13 file converter JSON:

- bmp-to-jpg.json
- jpg-to-pdf.json
- jpg-to-png.json
- jpg-to-webp.json
- mp4-to-mp3.json
- pdf-to-jpg.json
- pdf-to-word.json
- png-to-ico.json
- png-to-jpg.json
- png-to-webp.json
- webp-to-jpg.json
- webp-to-png.json
- word-to-pdf.json

## 3. Field Inventory

Field yang muncul dari data saat ini:

| Field | Jumlah file | Keterangan |
|---|---:|---|
| slug | 13 | Identitas unik converter |
| title | 13 | Judul tampilan dan judul halaman |
| description | 13 | Ringkasan singkat converter |
| category | 10 | Kategori konten untuk grouping |
| popular | 10 | Sinyal untuk daftar populer |
| featured | 10 | Sinyal untuk highlight |
| upload_form | 11 | Konfigurasi form upload |
| faq | 11 | Daftar FAQ |
| seo | 11 | Metadata SEO |
| related_tools | 8 | Link ke converter terkait |
| source | 2 | Format input eksplisit |
| target | 2 | Format output eksplisit |
| engine | 2 | Nama engine teknis |
| icon | 2 | Simbol UI |
| keywords | 2 | Kata kunci tambahan |
| benefits | 2 | Keunggulan produk |
| use_cases | 2 | Kasus pemakaian |

## 4. Pengelompokan Field

### Mandatory

Field berikut disarankan wajib ada di setiap file converter JSON V1:

- slug: identitas URL yang stabil.
- title: nama converter yang terlihat di UI.
- description: deskripsi singkat untuk halaman dan meta.
- category: klasifikasi untuk landing/hub/rekomendasi.
- source: format input.
- target: format output.
- active: status enable/disable.
- seo: blok SEO lengkap.
- upload_form: konfigurasi upload.
- faq: daftar pertanyaan yang umum.

### Optional

Field berikut disarankan opsional, tetapi sangat direkomendasikan untuk halaman yang lebih kaya:

- popular
- featured
- related_tools
- benefits
- use_cases
- tags
- created_at
- updated_at
- canonical
- image
- twitter_card
- type

### Deprecated / Legacy

Field berikut sebaiknya tidak dipakai lagi di schema V1 dan hanya dipertahankan untuk backward compatibility:

- engine: sekarang seharusnya ditempelkan di plugin/engine registry, bukan di JSON konten.
- icon: sebaiknya disimpan di layer presentasi, bukan metadata utama.
- keywords: duplikat dengan seo.keywords dan tags.

## 5. Inkonsistensi yang Ditemukan

Beberapa inkonsistensi yang menonjol:

1. Tidak semua file memiliki field yang sama.
   - Beberapa file tidak punya category, source, target, populer, atau featured.
   - Service pembaca mengisi default secara otomatis saat data kurang lengkap.

2. Field teknis bercampur dengan field konten.
   - `engine` dan `icon` lebih cocok sebagai metadata plugin/UI, bukan konten converter utama.

3. SEO masih tidak sepenuhnya JSON-driven.
   - Router landing tertentu masih menulis meta dan FAQ secara hardcoded, misalnya untuk mp4-to-mp3, jpg-to-png, dan png-to-jpg.

4. Sitemap masih memiliki override hardcoded.
   - [app/services/converter_data_service.py](app/services/converter_data_service.py) memetakan beberapa slug ke path khusus secara manual.

5. Related tools tidak konsisten.
   - Beberapa converter punya `related_tools`, beberapa tidak, sehingga fallback ke popular converter dipakai.

6. Field marketing seperti `benefits` dan `use_cases` hanya ada di beberapa file.
   - Ini menghambat konsistensi landing page.

## 6. Proposed JSON Schema V1

Schema V1 menekankan empat prinsip:

- konsisten untuk semua converter,
- cukup kaya untuk landing/SEO/FAQ/hub/rekomendasi/sitemap,
- tidak bergantung pada hardcoded router,
- tetap bisa hidup berdampingan dengan plugin/engine registry.

Rancangan V1 yang disarankan:

- gunakan `slug`, `title`, `description`, `category`, `source`, `target`, `active` sebagai inti utama,
- simpan konten halaman di `seo`, `upload_form`, `faq`, `benefits`, `use_cases`, `related_tools`,
- gunakan `tags` sebagai klasifikasi pelengkap,
- gunakan `created_at` dan `updated_at` untuk sitemap dan ordering.

## 7. Alasan Setiap Field

| Field | Alasan |
|---|---|
| slug | Menjadi identitas URL stabil dan kunci lookup. |
| title | Digunakan untuk H1, judul halaman, dan label UI. |
| description | Menyediakan ringkasan singkat untuk halaman dan meta description. |
| category | Membantu grouping hub, navigasi, dan rekomendasi. |
| source | Memastikan format input eksplisit dan bisa dipakai oleh halaman dan rekomendasi. |
| target | Memastikan format output eksplisit dan bisa dipakai oleh halaman dan rekomendasi. |
| active | Mengontrol apakah converter muncul di daftar aktif dan sitemap. |
| popular | Menandai converter yang layak tampil di daftar populer. |
| featured | Menandai converter yang diprioritaskan di home atau landing. |
| tags | Memberi kemampuan grouping yang lebih fleksibel daripada category saja. |
| upload_form | Mengatur UI upload dan validasi input. |
| faq | Menyediakan FAQ yang bisa dipakai oleh landing page dan FAQPage schema. |
| seo | Menjadi sumber utama konten SEO, meta tags, canonical, og image, dan keyword. |
| related_tools | Menyediakan tautan silang yang relevan. |
| benefits | Menguatkan value proposition di landing page. |
| use_cases | Memberi konteks penggunaan yang membantu konversi. |
| created_at | Menjadi dasar ordering dan penentuan freshness. |
| updated_at | Menjadi dasar lastmod untuk sitemap. |

## 8. Pemakaian Field oleh Surface

| Field | Landing | SEO | FAQ | Hub | Recommendation | Sitemap | Structured Data |
|---|---|---|---|---|---|---|---|
| slug | ✓ | ✓ |  | ✓ | ✓ | ✓ | ✓ |
| title | ✓ | ✓ |  | ✓ | ✓ |  | ✓ |
| description | ✓ | ✓ |  | ✓ | ✓ |  | ✓ |
| category | ✓ |  |  | ✓ | ✓ | ✓ | ✓ |
| source | ✓ |  |  |  | ✓ |  | ✓ |
| target | ✓ |  |  |  | ✓ |  | ✓ |
| active | ✓ |  |  | ✓ |  | ✓ |  |
| popular | ✓ |  |  | ✓ | ✓ |  |  |
| featured | ✓ |  |  | ✓ |  |  |  |
| tags |  |  |  | ✓ | ✓ |  |  |
| upload_form | ✓ |  |  |  |  |  |  |
| faq | ✓ |  | ✓ |  |  |  | ✓ |
| seo | ✓ | ✓ |  |  |  |  | ✓ |
| related_tools | ✓ |  |  |  | ✓ |  |  |
| benefits | ✓ |  |  |  |  |  |  |
| use_cases | ✓ |  |  |  |  |  |  |
| updated_at |  |  |  |  |  | ✓ |  |

## 9. Rekomendasi Standar V1

1. Semua converter wajib punya field inti: slug, title, description, category, source, target, active, seo, upload_form, faq.
2. `seo` harus selalu berisi minimal `title`, `description`, `keywords`.
3. `faq` harus berupa array objek dengan `question` dan `answer`.
4. `related_tools` harus berupa array slug yang valid.
5. `benefits` dan `use_cases` boleh kosong, tetapi jika ada harus konsisten.
6. Field `engine`, `icon`, dan `keywords` di level atas harus dihapus dari schema konten utama.
7. `updated_at` harus dipakai untuk sitemap dan freshness.

## 10. Ringkasan

Standar JSON V1 yang disarankan adalah model yang berfokus pada konten halaman, SEO, FAQ, rekomendasi, dan navigasi, dengan plugin/engine tetap berada di layer teknis terpisah. Ini akan mengurangi hardcoded logic dan membuat landing, hub, sitemap, serta structured data lebih mudah dihasilkan dari JSON saja.
