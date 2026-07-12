# Landing Page Audit

## 1. Daftar seluruh landing page

Landing page khusus yang ditemukan dalam kode:

- `/mp4-to-mp3` -> `app/templates/pages/mp4_to_mp3_landing.html`
- `/jpg-to-png` -> `app/templates/pages/jpg_to_png_landing.html`
- `/png-to-jpg` -> `app/templates/pages/png_to_jpg_landing.html`
- `/png-to-webp` -> `app/templates/pages/png_to_webp_landing.html`
- `/webp-to-jpg` -> `app/templates/pages/webp_to_jpg_landing.html`
- `/webp-to-png` -> `app/templates/pages/webp_to_png_landing.html`
- `/pdf-to-jpg` -> `app/templates/pages/pdf_to_jpg_landing.html`
- `/word-to-pdf` -> `app/templates/pages/word_to_pdf_landing.html`
- `/jpg-to-pdf` -> `app/templates/pages/jpg_to_pdf_landing.html`

Selain itu, ada landing page generik untuk tool detail:

- `/tools/{slug}` -> `app/templates/tool_page.html`

## 2. Komponen yang sama

Banyak landing page khusus menggunakan pola halaman yang sama:

- Hero section dengan:
  - `eyebrow` label statis `SEO Converter Landing Page`
  - judul halaman (contoh: `X to Y Converter Online Free`)
  - paragraf subjudul yang menjelaskan fungsi konversi
  - CTA button `Convert now`
  - CTA link ke FAQ
- Panel upload di hero:
  - panel label `Ready to convert`
  - deskripsi singkat status upload
  - form upload file dengan `accept`, `method`, `action`, dan tombol
- Section benefit / why choose Converigo
  - judul `Why choose Converigo`
  - subjudul produk spesifik
  - daftar `benefits` yang di-render dengan loop
- Section FAQ
  - judul `FAQ`
  - daftar pertanyaan dan jawaban
- Struktur halaman umum
  - `layouts/base.html`
  - `components/header.html`
  - `components/footer.html`
  - `partials/structured_data.html`

## 3. Komponen yang unik

Beberapa landing page memiliki bagian dan struktur khusus:

- `png_to_webp` dan `webp_to_png`
  - section `What is This` / `About the formats`
  - section `Use Cases`
  - section `How it Works` ditampilkan sebagai ordered list atau grid
  - `related_tools` ditampilkan dalam gaya link sederhana
- `mp4_to_mp3`, `png_to_jpg`, `pdf_to_jpg`, `jpg_to_pdf`
  - memiliki `supported_formats`
  - memiliki `how_to_use`
  - memiliki section `related-tools`
- `jpg_to_png`
  - tidak memiliki section `related-tools`
  - tidak memiliki `use_cases` atau `what_is_*`
- `webp_to_jpg` dan `word_to_pdf`
  - halaman relatif lebih sederhana
  - hanya menampilkan hero + benefits + faq
  - tidak selalu menampilkan `supported_formats` atau `how_to_use`

Perbedaan dalam kode Python route:

- Beberapa route menggunakan `seo_service.build_tool_meta(request, tool_data)`
- Beberapa route membangun `meta` manual dengan properti SEO sendiri
- Beberapa page membangun `structured_data` manual daripada menggunakan helper SEO umum
- Konten FAQ, benefits, supported formats, dan how to use disediakan secara inline di masing-masing route

## 4. Peluang refactoring

### 4.1. Satu template landing page universal

`app/templates/tool_page.html` sudah ada sebagai template generik untuk `/tools/{slug}`. Ini bisa dijadikan basis template landing page universal dengan parameter opsional:

- `tool.title`, `tool.description`
- `upload_form`
- `faq`
- `benefits`
- `supported_formats`
- `how_to_use`
- `related_tools`
- tambahan section opsional seperti `what_is_*`, `use_cases`, atau `about_formats`

### 4.2. Konsolidasi metadata dan SEO

- Standarisasi penggunaan `seo_service.build_tool_meta()` untuk semua landing page
- Pastikan `canonical`, `og_url`, `og_image`, dan `keywords` konsisten di setiap route
- Buat fallback SEO di `converter_data_service` atau `tool_data` sehingga route tidak perlu membangun meta manual

### 4.3. Konten page-specific di data, bukan di route

- Pindahkan konten landing page spesifik ke metadata converter atau konfigurasi tool page
- Contoh yang bisa dikeluarkan dari route:
  - `faq_items`
  - `benefits`
  - `supported_formats`
  - `how_to_use`
  - `related_tools`
  - `what_is_png` / `what_is_webp`
  - `use_cases`

### 4.4. Reuse partials untuk blok umum

- `components/upload_card.html` untuk upload form
- Partial untuk `benefits` / `why choose`
- Partial untuk `faq`
- Partial untuk `related_tools`
- Partial untuk `supported_formats`
- Partial untuk `how_to_use`

## 5. Risiko migrasi

- Perbedaan konten halaman: beberapa landing page memiliki section unik yang tidak bisa langsung digeneralisasi tanpa kehilangan pesan spesifik
- SEO / canonical URL: landing page khusus menggunakan rute root (`/jpg-to-pdf`, `/mp4-to-mp3`) yang berbeda dari `/tools/{slug}`
- Structured data: beberapa page membuat `FAQPage` manual sementara lainnya mengandalkan service SEO
- Tes: ada banyak unit test landing page untuk setiap rute; refactor perlu memperbarui test case
- Fall-back data: `tool_data` tidak selalu mengandung semua field yang saat ini dibuat inline di route
- UX: variasi navigasi internal (hero links, section anchor) berbeda antar halaman, jadi migrasi bisa memengaruhi tautan internal

## 6. Rekomendasi struktur `tool_page.html`

Gunakan struktur template yang mendukung blok opsional dan fallback data. Contoh struktur:

1. Hero section
   - `eyebrow`
   - `title`
   - `description`
   - CTA buttons
   - optional internal anchor links jika `nav_links` tersedia
2. Hero upload panel
   - panel label
   - panel title
   - upload form partial
3. Optional section `benefits`
   - render jika `benefits` ada
4. Optional section `supported_formats`
   - render jika `supported_formats` ada
5. Optional section `how_to_use`
   - render jika `how_to_use` ada
6. Optional section `what_is_*` / `about_formats`
   - render block if data present
7. Optional section `use_cases`
   - render list if data present
8. FAQ section
   - render jika `faq` ada atau fallback ke `tool_data.faq`
9. Optional `related_tools`
   - render jika tersedia

### Rekomendasi konkret

- Buat partial `pages/partials/landing_hero.html`
- Buat partial `pages/partials/landing_benefits.html`
- Buat partial `pages/partials/landing_faq.html`
- Buat partial `pages/partials/landing_related.html`
- Buat partial `pages/partials/landing_sections.html` untuk section opsional seperti `use_cases` atau `about_formats`

### Data-driven page config

Agar satu template universal bekerja baik, setiap converter harus dapat menyediakan struktur data seperti:

- `seo` (title, description, canonical, keywords)
- `upload_form`
- `faq`
- `benefits`
- `supported_formats`
- `how_to_use`
- `related_tools`
- `extra_sections` (opsional)

Dengan pendekatan ini, semua landing page khusus dapat dipindahkan menjadi:

- satu route wrapper yang memilih data dan render `tool_page.html`
- rute tetap `/{slug}` untuk SEO dan UX

## 7. Catatan tambahan

- `tool_page.html` saat ini sudah menampilkan blok upload, how it works, FAQ, related tools, dan generic hero. Ini adalah aset yang sangat kuat untuk refactor.
- Namun, landing page khusus saat ini menambahkan duplikasi HTML dan logika route yang berat. Konsolidasi ke template universal akan mengurangi beban pemeliharaan.
