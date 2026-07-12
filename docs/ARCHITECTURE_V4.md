# Converigo Architecture V4 Blueprint

## 1. Current Architecture

### Overview
Converigo saat ini berjalan sebagai aplikasi FastAPI yang menggabungkan: rute landing khusus, rute tool generik, metadata JSON, layanan SEO, registry plugin, pipeline konversi, rekomendasi, dan engine konversi.

### Komponen Utama
- `app/main.py`: bootstrap aplikasi, lifecycle startup, routing, static file mounting.
- `app/routers/home.py`: home page, trust pages, landing khusus (`/mp4-to-mp3`, `/jpg-to-png`, `/pdf-to-jpg`, dll.), dan image hub.
- `app/routers/tools.py`: route generik `/tools/{slug}` dengan `tool_page.html`.
- `app/routers/seo.py`: `sitemap.xml` dan `robots.txt`.
- `app/routers/recommend.py`: API rekomendasi berdasarkan format input.
- `app/routers/plugins.py`: API discovery plugin.
- `app/services/converter_data_service.py`: pembaca JSON converter, pencarian slug, related tools, sitemap entries.
- `app/services/seo_service.py`: builder SEO dan structured data.
- `app/plugins/registry.py`: discovery plugin lintas format.
- `app/services/conversion_manager.py`: registry engine/plugin dan pembuatan converter.
- `app/pipeline/pipeline_manager.py`: registrasi dan pembuatan pipeline konversi.
- `app/data/converters/*.json`: metadata converter, upload_form, faq, seo.
- `app/templates/tool_page.html`: template tool generik.
- `app/templates/pages/*.html`: template landing page khusus yang sebagian besar duplikat.

### 1.1 Current Request Flow
1. Browser request masuk ke FastAPI.
2. Middleware locale meresolusi bahasa dan meneruskan `request.state.t`.
3. Router yang sesuai memanggil handler.
4. Handler memuat `ConverterDataService` (jika tool), menyiapkan `seo_service`, dan membangun context template.
5. Handler merender HTML template.
6. Jika request ke `/convert`, `UploadService` menyimpan file sementara, `ConversionService` menjalankan konversi melalui plugin, lalu hasil dioutputkan.

### 1.2 Current Landing Flow
- Aplikasi masih menggunakan landing page hybrid:
  - landing khusus root seperti `/mp4-to-mp3`, `/jpg-to-png`, `/png-to-webp`, dll.
  - generic tool page di `/tools/{slug}`.
- Landing khusus memuat banyak logika inline di router: FAQ, benefits, supported formats, how-to, structured data.
- `tool_page.html` sudah ada sebagai template generik, tetapi penggunaannya terbatas pada route `/tools/{slug}` saja.

### 1.3 Current Plugin Flow
- Plugin ditemukan dengan `discover_plugin_classes()`.
- `PluginRegistry` menyimpan plugin berdasarkan pair `(source, target)`.
- Registry dapat mengembalikan plugin, metadata plugin, dan plugin terbaik untuk sumber tertentu.
- API `/api/plugins` mengekspos metadata plugin yang sudah terdaftar.

### 1.4 Current Pipeline Flow
- Pipeline terdaftar di `app/pipeline/pipeline_manager.py` dengan nama `conversion_pipeline`.
- Langkah default: `ValidateStep`, `MetadataStep`, `PrepareStep`, `ConvertStep`, `OptimizeStep`, `SaveStep`, `CleanupStep`.
- Pipeline bersifat modular,
  tetapi pipeline data dan kondisi eksekusi belum dipetakan ke JSON tool data.

### 1.5 Current Engine Flow
- Engine terdaftar via `EngineRegistry`.
- Engine tersedia untuk `audio`, `document`, `image`, `video`, dan `ffmpeg`.
- Konverter plugin memanggil engine yang sesuai dalam metode `convert()`.

### 1.6 Current ConverterDataService Flow
- Membaca `app/data/converters/*.json`.
- Memberi fallback metadata dasar (`slug`, `title`, `source`, `target`, `category`, `popular`, `featured`).
- Menyediakan: daftar semua converter, daftar aktif, converter populer, converter terbaru, lookup slug, related tool resolver.
- `sitemap_entries()` menghasilkan entri sitemap untuk homepage, trust pages, dan converter, dengan override rute beberapa slug.

### 1.7 Current SEO Flow
- `SeoService.build_home_meta()` mengembalikan SEO home statis.
- `SeoService.build_tool_meta()` memetakan JSON `tool_data.seo` ke meta tags.
- `SeoService.build_structured_data()` mengembalikan JSON-LD general website, FAQ, blog, trust page, dan tool page berdasarkan `tool_data.faq`.
- Sitemap saat ini dibangun dari `ConverterDataService.sitemap_entries()` plus blog paths statis.

### 1.8 Current Recommendation Flow
- `RecommendationEngine` menggunakan `registry.get_plugins_by_source(source_format)`.
- Semua opsi plugin dari source format diproses oleh `RecommendationScorer`.
- API `/recommend/{source_format}` mengembalikan best choice dan alternatives untuk source input.
- Recommendation masih mengandalkan metadata plugin, bukan JSON converter langsung.

### 1.9 Current Sitemap Flow
- `SeoService.build_sitemap_xml()` membuat XML dengan entri dari `ConverterDataService.sitemap_entries()`.
- Sitemap saat ini menggabungkan homepage, trust pages, landing page overrides, dan plugin converter paths.
- Rute fallback `tools/{slug}` dipakai untuk converter tanpa landing khusus.

## 2. Target Architecture

### High-level Target
Tujuan V4 adalah mengubah Converigo menjadi Platform Converter Framework yang:
- sepenuhnya JSON-driven,
- memiliki satu universal route,
- mendukung landing dinamis,
- mengotomasi SEO, sitemap, hub, dan rekomendasi,
- mengintegrasikan plugin sebagai sumber kebenaran metadata.

### Target Flow
Browser
↓
Universal Route
↓
ConverterDataService
↓
Converter JSON
↓
SEO Builder
↓
Tool Template
↓
Plugin Registry
↓
Pipeline
↓
Engine
↓
Output

### Target Komponen
- Universal routing layer untuk semua converter.
- `ConverterDataService` sebagai reader tunggal dari JSON.
- `tool_data` JSON sebagai Single Source of Truth.
- SEO automation service yang memetakan semua meta, OG, schema, breadcrumbs, dan sitemap dari JSON.
- Plugin registry yang memvalidasi plugin/JSON relationship.
- Hub generator yang menyusun page hub otomatis berdasarkan kategori JSON.
- Recommendation engine data-driven dari metadata JSON/plugin.
- Pipeline yang dibentuk oleh JSON tool definitions dan plugin/engine capabilities.

## 3. Dynamic Platform Vision

### Konsep
Converigo V4 bukan hanya website converter, tapi framework konversi:
- setiap format pairing adalah entitas data.
- setiap entitas memiliki SEO, landing, hub, recommendation, dan pipeline terotomasi.
- setiap plugin adalah kapabilitas eksekusi dan metadata sosial.

### Prinsip Utama
- Dynamic Landing: semua converter dapat menghadirkan landing halaman secara otomatis.
- Dynamic Route: satu route universal menghilangkan duplikasi route manual.
- JSON First: metadata halaman, SEO, FAQ, benefits, related, hub, sitemap, recommendation semua dibaca dari JSON.
- Plugin First: plugin memperkaya JSON dan menjadi sumber metadata teknis, tetapi tidak menyalahi sumber kebenaran konten.
- SEO Automation: setiap converter page dilengkapi metadata tanpa penulisan manual per route.
- Sitemap Automation: semua route, termasuk hub dan tool, dibangun dari JSON dan plugin registry.
- Hub Automation: kategori hub beserta tool-nya dihasilkan dari converter JSON.

## 4. JSON First Strategy

### Tujuan
Menjadikan file JSON converter sebagai satu-satunya sumber kebenaran untuk:
- landing content,
- SEO metadata,
- FAQ,
- benefits,
- how-to,
- related tools,
- structured data,
- OpenGraph,
- sitemap,
- hub data,
- recommendation hints.

### Data Model JSON
Setiap `app/data/converters/{slug}.json` harus mendukung:
- `slug`, `title`, `description`
- `category`, `tags`, `featured`, `popular`, `enabled`
- `source`, `target`
- `upload_form` (action, method, accept, button_text)
- `faq` array
- `benefits` array
- `how_to_use` array
- `supported_formats` optional
- `use_cases` optional
- `related_tools` array
- `seo` object: title, description, keywords, canonical, image, twitter_card, type
- `structured_data` optional overrides
- `hub` object optional: hub_title, hub_section, hub_tags
- `recommendation` object optional: priority, compatibility, quality, goal, badge, icon
- `plugin` object link ke plugin slug, engine name, metadata source

### Kelebihan
- tidak ada lagi logika landing page lain di Python route.
- konten halaman dapat diperbarui dengan edit JSON.
- SEO dan sitemap dilahirkan dari data yang sama.
- migration path untuk landing pages menjadi data-driven.

## 5. Universal Route

### Rekomendasi
Gunakan satu pola universal seperti `/tools/{slug}` sebagai entry point converter, atau jika ingin SEO lebih pendek, gunakan root `/{slug}`.

**Strategi ideal**:
- `/{slug}` sebagai alias publik untuk pengalaman end user.
- `/tools/{slug}` sebagai route internal canonical dan fallback.
- landing khusus lama tetap dipertahankan sebagai redirect atau alias ke route universal.

### Universal route handling
- route menerima `slug`
- `ConverterDataService.load_converter_by_slug(slug)` mencari JSON
- jika `tool_data` tidak ditemukan, return 404
- `seo_service.build_tool_meta(request, tool_data)` memetakan SEO dari JSON
- template universal dirender dengan context JSON
- internal navigation dan anchor dihasilkan dari `tool_data` yang ada

### Strategi migrasi
- Tahap 1: pertahankan landing khusus sebagai redirect ke universal route.
- Tahap 2: pindahkan semua page-specific content dari router ke JSON.
- Tahap 3: buat fallback `landing_page_overrides` sementara untuk canonical berlaku.
- Tahap 4: deprecate template landing khusus setelah semua route generik berhasil.

## 6. Universal Template

### Rekomendasi struktur
`tool_page.html` harus menjadi template universal yang mendukung:
- Hero section
- Upload panel
- Optional section: benefits
- Optional section: supported formats
- Optional section: how to use
- Optional section: related tools
- Optional section: hub teasers atau category callout
- FAQ section
- Optional section: product-specific details

### Mandatory Section
- Header dan navigation global.
- Hero dengan `title`, `description`, CTA, dan `upload_form`.
- `upload_form` action/method/accept/button_text.
- FAQ section karena structured data dan trust page.
- related tools atau fallback related.
- SEO partial dan structured data partial.

### Optional Section
- `benefits`
- `supported_formats`
- `how_to_use`
- `use_cases`
- `what_is` / `about_format`
- `hub_related` / `workflow` blocks
- `related_tools`
- `extra_sections` untuk halaman khusus seperti image vs document versus audio

### Fallback
- jika `faq` kosong, gunakan default FAQ global.
- jika `related_tools` kosong, pilih popular converter dari `ConverterDataService`.
- jika `upload_form` tidak lengkap, gunakan fallback generik berdasarkan `source`/`target`.
- jika `seo` tidak ada, bangun title/description/canonical dari `tool_data`.

### Reusable Partials
- `partials/landing_hero.html`
- `partials/landing_upload.html`
- `partials/landing_benefits.html`
- `partials/landing_steps.html`
- `partials/landing_formats.html`
- `partials/landing_faq.html`
- `partials/landing_related.html`
- `partials/landing_hub.html`
- `partials/structured_data.html`
- `partials/seo_meta.html`

## 7. Plugin Strategy

### Hubungan Plugin ➝ JSON ➝ Landing ➝ SEO ➝ Hub ➝ Recommendation ➝ Sitemap
- Plugin memberikan metadata teknis: source/target, engine, priority, compatibility, badge, icon.
- JSON converter berisi konten produk dan link ke plugin yang relevan.
- Landing page dibangun dari JSON konten + plugin metadata.
- SEO builder memanfaatkan JSON SEO dan plugin metadata untuk `breadcrumb`, `schema`, `og`, `keywords`.
- Hub otomatis mengelompokkan converter dari `category`/`tags` JSON.
- Recommendation engine menggunakan plugin metadata dan hub context sebagai sinyal.
- Sitemap dihasilkan dari semua JSON converter dan hub halaman.

### Plugin Validator
Usulkan sistem validasi otomatis saat startup atau CI:
- Plugin ada, JSON tidak ada → warning/alert.
- JSON ada, plugin tidak ada → warning/alert.
- Landing belum tersedia untuk JSON/Plugin baru → warning.
- `seo` data kosong atau tidak lengkap → warning.
- `upload_form` invalid → warning.

### Plugin Metadata vs JSON
- Plugin metadata harus menjadi sumber kebenaran untuk kemampuan eksekusi.
- JSON menjadi sumber utama untuk konten, navigasi, dan halaman.
- Validasi cross-check memastikan:
  - setiap `tool_data.plugin.slug` resolvable oleh plugin registry.
  - setiap plugin yang tersedia memiliki setidaknya satu JSON landing/tool.

## 8. Hub Strategy

### Tujuan
Hub menjadi halaman pilar kategori otomatis: Image, Audio, Video, PDF, Document.

### Otomatisasi Hub
- `ConverterDataService` membaca semua JSON dan menghasilkan grouping berdasarkan `category`/`tags`.
- Hub pages dibangun dari satu template generik dengan data JSON kategori.
- `Image Hub`, `Audio Hub`, `Video Hub`, `PDF Hub`, `Document Hub` bisa menjadi alias atau path dinamis berdasarkan kategori.
- Content hub seperti workflow cards, featured tools, knowledge cards, dan tools grid dibaca dari JSON.

### Struktur Hub
- `hub_title`, `hub_description` dari JSON kategori global.
- `featured_tools` ditentukan oleh `featured` flag.
- `category_tools` dihasilkan dari semua converter dengan `category` yang sama.
- `faq_items` kategori dapat diambil dari FAQ global untuk category hub.
- `hub_sections` optional dapat diisi oleh JSON atau fallback.

### Contoh
- `image-conversion`: semua converter `category: image`.
- `audio-conversion`: semua converter `category: audio`.
- `video-conversion`: semua converter `category: video`.
- `pdf-conversion`: semua converter `category: document` + `tags: pdf`.
- `document-conversion`: semua converter `category: document`.

## 9. SEO Strategy

### Tujuan
Berpindah dari SEO manual ke SEO otomatis semua berasal dari JSON.

### Data otomasi SEO
Untuk setiap converter, JSON harus menyediakan:
- `seo.title`
- `seo.description`
- `seo.canonical`
- `seo.keywords`
- `seo.image`
- `seo.twitter_card`
- `seo.type`
- optional `seo.breadcrumb` dan `seo.og_url`

### Output otomatis
- `seo_meta.html` di-include dari context yang dibangun `SeoService`.
- `Json-LD` schema untuk `WebSite`, `SoftwareApplication`, `FAQPage`, `BreadcrumbList` dihasilkan dari JSON.
- Breadcrumb otomatis berasal dari route dan `category`/`hub`.
- OpenGraph dan Twitter Card dibentuk dari `seo` object.

### Fallback
- Jika JSON tidak berisi `canonical`, gunakan default `/<slug>` atau `/tools/<slug>`.
- Jika `keywords` kosong, gunakan kombinasi `source`, `target`, `category`.
- Jika `seo.image` kosong, gunakan default og image.

## 10. Recommendation Strategy

### Tujuan
Recommendation engine harus bekerja tanpa hardcode dan langsung dari metadata.

### Data-driven recommendation
- Gunakan metadata plugin dan converter JSON sebagai sinyal.
- Recommendation model dapat membaca:
  - `source_format`, `target_format`
  - `category`
  - `priority`, `quality`, `compatibility`, `estimated_saving`
  - `use_case`, `goal`, `badge`
- Jika `tool_data.recommendation` ada, gunakan skor dasar tersebut.
- Jika tidak ada, gunakan plugin-level defaults.

### Mekanisme
- `RecommendationEngine.recommend(source_format)` mencari semua converter/plugin yang mendukung source.
- Build option dari JSON/plugin metadata.
- Urutkan berdasarkan `score` yang dihitung secara otomatis.
- Kembalikan `best_choice` dan `alternatives`.

### Tanpa hardcode
- Hindari `if source == 'jpg'` atau `if slug == 'mp4-to-mp3'`.
- Gunakan JSON `related_tools` dan `category` untuk clue rekomendasi.
- Gunakan plugin registry sebagai sumber konversi aktual, bukan halaman.

## 11. Sitemap Strategy

### Tujuan
Sitemap otomatis dihasilkan dari JSON dan hub definition.

### Sumber data sitemap
- Semua converter JSON aktif.
- Semua hub category page.
- Homepage dan trust pages.
- Semua alias landing lama jika masih dipertahankan.
- Blog atau artikel yang ditentukan di data statis/JSON.

### Mekanisme
- `ConverterDataService.sitemap_entries(base_url)` menjadi standar.
- `SeoService.build_sitemap_xml()` menggabungkan entri converter, hub, trust page, dan artikel.
- Atur `lastmod` dari `updated_at` atau `created_at` JSON.
- Gunakan canonical path dari `seo.canonical` jika ada.

### Migrasi dari manual
- hapus `landing_page_overrides` satu per satu setelah rute universal aktif.
- biarkan routes lama redirect ke canonical universal.
- gunakan `enabled: false` untuk converter non-active.

## 12. Migration Plan

### Fase 1: Audit dan Data Cleanup
- Inventarisasi semua landing page dan JSON yang sudah ada.
- Temukan JSON converter yang belum terpakai oleh route.
- Tandai `landing_page_overrides` yang masih digunakan.
- Kumpulkan FAQ, benefits, how-to, related tools yang tersebar di route.

### Fase 2: Standardisasi JSON
- Perluas data model JSON converter agar mendukung landing penuh.
- Tambahkan field SEO, structured data, hub, recommendation, and page sections.
- Validasi JSON dengan schema simple.

### Fase 3: Universal Route + Template
- Implementasikan route universal `/tools/{slug}` dengan alias root `/{slug}`.
- Render `tool_page.html` dengan semua section opsional.
- Tambahkan partials reusable dan fallback logic.
- Test semua converter path dengan JSON-driven rendering.

### Fase 4: Hub dan SEO Automation
- Buat hub generation dari JSON categories.
- Automatiskan `image-conversion`, `audio-conversion`, `video-conversion`, `pdf-conversion`, `document-conversion`.
- Pindahkan SEO builder ke JSON-driven service.
- Tambahkan structured data JSON-LD otomatis.

### Fase 5: Recommendation & Sitemap
- Integrasikan recommendation engine agar menggunakan converter JSON/plugin metadata.
- Perbarui endpoint `/recommend` dan tambahkan validation.
- Otomatiskan sitemap berdasarkan JSON dan hub pages.
- Verifikasi `robots.txt`.

### Fase 6: Cleanup & Deprecation
- Redirect landing spesifik lama ke universal route.
- Hapus template landing khusus yang sudah tergantikan.
- Tambahkan validator plugin/JSON.
- Finalisasi dokumentasi, tests, dan release notes.

## 13. Risk Analysis

### Risiko Teknologi
- Perubahan besar pada route dan template dapat merusak SEO canonical links.
- Content duplication jika alias lama tidak disatukan dengan redirect.
- JSON schema tidak konsisten dapat menyebabkan halaman gagal render.

### Risiko Produk
- Konten landing yang hilang jika tidak semua section dipindahkan ke JSON.
- Hub page kehilangan konteks jika `category`/`tags` JSON tidak lengkap.
- Recommendation engine kurang relevan jika metadata plugin/JSON tidak cukup detail.

### Risiko Operasional
- Deployment schema validation perlu ketat.
- Developer harus menjaga tooling JSON/Plugin sinkron.
- Tes harus diperluas untuk route universal, SEO, sitemap, dan hub.

## 14. Sprint Roadmap

### Sprint 1: Arsitektur Data & Route
- Definisikan JSON schema converter lengkap.
- Buat versi `ConverterDataService` yang memuat schema baru.
- Implementasikan universal route sementara.
- Tulis partial template generic untuk semua section.

### Sprint 2: SEO & Hub Automation
- Migrasikan semua SEO builder ke JSON-driven service.
- Buat hub generator untuk kategori otomatis.
- Bangun page hub generik dan hub routing.
- Tambahkan structured data JSON-LD otomatis.

### Sprint 3: Recommendation & Sitemap
- Integrasikan recommendation engine dengan converter JSON/plugin metadata.
- Perbarui endpoint `/recommend` dan tambahkan validation.
- Otomatiskan sitemap berdasarkan JSON dan hub pages.
- Verifikasi `robots.txt`.

### Sprint 4: Cleanup & Deprecation
- Redirect landing spesifik lama ke universal route.
- Hapus template landing khusus yang sudah tergantikan.
- Tambahkan validator plugin/JSON.
- Finalisasi dokumentasi, tests, dan release notes.

### Delivery
- Output V4: satu platform converter yang sepenuhnya data-driven, dengan semua halaman, SEO, sitemap, recommendation, dan hub dihasilkan dari JSON dan plugin metadata.
