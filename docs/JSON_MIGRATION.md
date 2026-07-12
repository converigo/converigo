# JSON Migration Plan

## 1. Tujuan Migrasi

Migrasi ini bertujuan membawa semua converter JSON ke format standar V1 sehingga landing page, SEO, FAQ, hub, rekomendasi, sitemap, dan structured data bisa dipenuhi sepenuhnya dari JSON tanpa bergantung pada hardcoded logic.

## 2. Prinsip Migrasi

- Tidak mengubah kode aplikasi saat fase awal.
- Fokus pada konsistensi data.
- Lakukan migrasi bertahap agar rollback aman.
- Prioritaskan file converter yang paling sering dipakai.

## 3. Fase 1 — Inventory dan Normalisasi

Langkah:

1. Audit semua file di [app/data/converters](app/data/converters).
2. Tentukan field inti yang wajib ada.
3. Standarkan penamaan field: `slug`, `title`, `description`, `category`, `source`, `target`, `active`, `seo`, `upload_form`, `faq`.
4. Isi field yang hilang dengan nilai default yang aman.

Output:

- semua file punya field inti,
- tidak ada converter yang kosong atau tidak valid.

## 4. Fase 2 — Pemetaan Field Lama ke Field Baru

Mapping yang disarankan:

| Field lama | Field baru |
|---|---|
| `source` / `target` tidak ada | tambahkan eksplisit |
| `engine` | hapus dari metadata konten dan pindah ke plugin registry |
| `icon` | pindah ke layer presentasi / UI |
| `keywords` level atas | pindah ke `seo.keywords` |
| `benefits` / `use_cases` kosong | isi sesuai masing-masing converter |

## 5. Fase 3 — Migrasi Konten Halaman

Target:

- FAQ dipindahkan dari router hardcoded ke `faq` di JSON.
- SEO meta dipindahkan ke `seo` di JSON.
- Value proposition landing dipindahkan ke `benefits` dan `use_cases` di JSON.
- Related tools ditempatkan di `related_tools`.

## 6. Fase 4 — Migrasi Hub, Rekomendasi, dan Sitemap

Target:

- `category` dan `tags` dipakai untuk halaman hub.
- `featured` dan `popular` dipakai untuk rank dan blok rekomendasi.
- `updated_at` dipakai sebagai lastmod sitemap.
- `active` dipakai untuk menampilkan atau menyembunyikan entry sitemap.

## 7. Fase 5 — Deprecation dan Cleanup

Setelah semua file baru kompatibel:

1. hentikan penggunaan field lama yang tidak lagi diperlukan,
2. pastikan fallback di service tidak lagi bergantung pada hardcoded overrides,
3. tetap pertahankan backward compatibility untuk satu siklus release.

## 8. Prioritas Implementasi

Prioritas 1:
- slug, title, description, category, source, target, active, seo, upload_form, faq.

Prioritas 2:
- benefits, use_cases, related_tools, tags.

Prioritas 3:
- created_at, updated_at, canonical, image, og metadata tambahan.

## 9. Risiko yang Harus Diwaspadai

- Data lama bisa tidak lengkap.
- Beberapa converter mungkin memerlukan konten landing yang lebih panjang dari yang saat ini tersedia.
- Penataan SEO harus konsisten sehingga tidak ada page yang kehilangan metadata.

## 10. Exit Criteria

Migrasi dianggap selesai ketika:

- semua converter memiliki JSON V1 yang valid,
- landing page dapat dibangun dari JSON tanpa hardcoded FAQ/meta yang redundan,
- sitemap, hub, dan recommendation dapat dihasilkan dari metadata JSON,
- tidak ada lagi field inti yang hilang secara sistematis.
