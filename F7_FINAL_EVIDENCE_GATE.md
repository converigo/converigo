# F7 — Final Evidence Gate Report (2-Gap Closure)

**Branch:** `feat/factory-f7` · **HEAD:** `41bd798` (chain: `e6c256b` → `137a8e2` → `41bd798`) · **Baseline canonical:** `578f246` (= origin/main)
**Tanggal:** 2026-09-06 · **Mode:** evidence-only — tanpa PR, tanpa scope baru, tanpa perubahan arsitektur, tanpa operasi git destruktif.

---

## Gap 1 — Full regression pasca `137a8e2` vs baseline `578f246`

### Metode (non-destruktif)
- Worktree baseline terpisah: `git worktree add C:\converigo\wt_f7_base 578f246 --detach` (pola identik `wt_f4_base`/`wt_f5_base`; tidak memindah branch mana pun).
- Full suite dijalankan fresh di KEDUA state, command identik:
  `python -m pytest -q --tb=no -rf --junitxml=...` (rootdir = worktree masing-masing, venv yang sama).
- Perbandingan failure dilakukan **per nama test** dari JUnit XML (bukan dari ringkasan angka).

### Angka lengkap (explicit, bukan klaim "identik")

| State | Total | PASS | FAIL | SKIP | XFAIL | Durasi |
|---|---|---|---|---|---|---|
| Baseline `578f246` (fresh, wt_f7_base) | 925 | 899 | 20 | 5 | 1 | 40m23s |
| Post-change `41bd798` (wt_f7, mencakup `137a8e2`) | 937 | 911 | 20 | 5 | 1 | 25m02s |

- Delta total node: **+12** (925 → 937) — persis 12 test certified document F7 yang ditambah `137a8e2`.
- PASS delta: 899 → 911 = **+12**, FAIL/SKIP/XFAIL **tidak berubah** (20/5/1 di kedua state).

### Failure-set baseline vs post-change — identitas satu-per-satu (20 nama, verbatim)

```
tests/certified/archive/test_rar_extract_certified.py::test_rar4_extract_e2e_members_byte_identical
tests/certified/archive/test_rar_extract_certified.py::test_rar5_extract_e2e_members_byte_identical
tests/certified/archive/test_rar_extract_certified.py::test_rar5_single_member_returns_file_directly
tests/certified/archive/test_rar_extract_certified.py::test_rar_corrupt_body_honest_error
tests/certified/archive/test_rar_extract_certified.py::test_rar_extract_plugin_level_round_trip
tests/certified/archive/test_rar_extract_certified.py::test_rar_extract_single_output_file
tests/test_globalfmt_intersection.py::test_globalfmt_no_common_target_for_jpg_png
tests/test_i18n.py::test_homepage_hero_has_no_extra_ctas_and_visible_drop_zone
tests/test_i18n.py::test_japanese_homepage_uses_translated_trust_and_support_copy
tests/test_i18n.py::test_jpg_to_pdf_landing_page_renders_localized_text_and_frontend_locale
tests/test_i18n.py::test_navbar_and_hero_subtitle_are_localized_for_spanish_and_french
tests/test_jpg_to_png_landing.py::test_jpg_to_png_landing_page_renders_with_seo_and_faq
tests/test_office_converter_cluster.py::test_hub_and_sitemap_and_audit
tests/test_production_audit_service.py::test_audit_passes_for_valid_converters
tests/test_seo_crawlability.py::test_converter_page_renders_visible_breadcrumb
tests/test_seo_crawlability.py::test_missing_page_returns_404_status_and_custom_content
tests/test_seo_urls.py::test_seo_service_uses_production_absolute_urls
tests/test_sitemap_service.py::test_sitemap_service_generates_category_sitemaps_and_validates_entries
tests/test_webp_to_jpg_landing.py::test_webp_to_jpg_landing_page_renders_with_seo_and_faq
tests/test_webp_to_png_landing.py::test_webp_to_png_landing_page_renders_with_seo_and_faq
```

Bukti mesin (set-diff, bukan manual):
1. `baseline_failures.txt` vs `post_failures.txt` → **0 diff** ("VERDICT: FAILURE-SET IDENTICAL 20/20, one-by-one by name").
2. Fresh baseline (run saya) vs baseline tercatat executor (`wt_f7\tmp\f7_baseline_failed.txt`) → **0 diff (20/20)** — baseline reproduction sempurna.
3. Fresh post (run saya) vs post tercatat executor (`wt_f7\tmp\f7_post_failed.txt`) → **0 diff (20/20)**.
4. Node-diff JUnit baseline vs post: `added=12 removed=0`, dan 12 node itu seluruhnya `tests/certified/document/test_document_factory_certified.py::...` (9 test parametrized factory + test_static_target_map_f7_rows + test_contract_artifacts_shipped + test_requirements_pin_mammoth_floor).

**Catatan koreksi kecil atas prompt:** "baseline awal sudah tercatat: 20 fail/908 pass/5 skip/1 xfail" — angka 908 berasal dari `wt_f7\tmp\f7_post_pytest.out` (post-change, 934 total), bukan baseline. Baseline canonical tercatat di `wt_f7\tmp\f7_baseline_pytest.out` = **20 fail/899 pass/5 skip/1 xfail (925 total)** — dan baseline fresh saya mereproduksi angka itu persis, termasuk 20 nama failure-nya.

### Tidak ada failure baru
Zero failure baru, zero error, zero flaky-migration antar state. Semua 20 failure pre-existing (klaster RAR-certified lokal + landing/i18n/SEO — tidak tersentuh F7). **→ Gap 1: PASS (bersih).**

### Insiden transparansi (tidak mempengaruhi verdict)
- Percobaan pertama post-suite terhenti di ~46% karena proses background dimatikan environment (tanpa crash event OS, tanpa traceback, tanpa JUnit); di-restart via wrapper `run_post.bat` dan selesai bersih 25m02s. Bukan hasil test.
- Side-effect test yang diketahui: `RC1_2_CONVERTER_JSON_REPORT.md` tereggenerasi di working tree kedua worktree oleh suite (pola yang sama dengan artefak pre-existing `wt_f7` milik executor). File committed tidak tersentuh; tidak saya "perbaiki" manual.

**Artifacts:** `C:\converigo\f7_evidence\` → `baseline.junit.xml`, `post.junit.xml`, `baseline_failures.txt`, `post_failures.txt`, `baseline.stdout`, `post.stdout`, `post_attempt1_stdout.txt`, `extract_failures.py`, `diff_nodes.py`, `run_post.bat`.

---

## Gap 2 — In-image CI (GitHub Actions production-image) untuk commit terbaru

Workflow resmi satu-satunya di repo: **`docker-runtime-verify`** (`.github/workflows/docker-verify.yml`) — build production image dari branch Dockerfile + verifikasi in-container 5 poin.

### Run untuk state post-FIX

| Run ID | Commit | Trigger | Hasil | Waktu (UTC) |
|---|---|---|---|---|
| **34038671839** | `41bd798b17bfaeb19a0a5055b548b679c0d52604` (HEAD, mencakup `137a8e2`) | workflow_dispatch (dispatched by executor for this gate) | **success** | 2026-09-06 14:16:59Z |
| 34029872536 | `137a8e29488c605661342b11552a26d6bf3b23c3` (FIX commit) | workflow_dispatch (pre-existing, head_sha verbatim) | success | 2026-09-06 11:18:43Z |

URL: https://github.com/converigo/converigo/actions/runs/34038671839

Catatan klarifikasi: run `34022594418` yang dikutip laporan F7 awal ternyata head_branch **main @ 578f246** (run CI baseline, bukan branch F7) — diluruskan di sini dengan run ID di atas.

### Hasil per-komponen run 34038671839 (@ 41bd798) — dipisah tegas

**[A] Probe in-image (step [4/5], script `scripts/ci_in_document_factory_probe.py`):**
```
F7 PROBE OK: docx-to-html (.docx -> html)
F7 PROBE OK: pptx-to-png (.pptx -> png)
F7 PROBE OK: pptx-to-jpg (.pptx -> jpg)
F7 PROBE OK: honest error for non-DOCX input
F7 PROBE OK: artifact docx-to-html.contract.json / docx-to-html.json
F7 PROBE OK: artifact pptx-to-png.contract.json / pptx-to-png.json
F7 PROBE OK: artifact pptx-to-jpg.contract.json / pptx-to-jpg.json
F7 PROBE: PASS (3/3 document converters verified in-image)
```
→ **Probe: PASS 3/3** (+ honest-error + 6 contract artifacts terverifikasi in-image).

**[B] Certified suite in-image (step [5/5], `tests/certified/document/test_document_factory_certified.py`):**
```
12 passed, 13 warnings in 1.87s
(9 parametrized factory tests [docx-to-html|pptx-to-png|pptx-to-jpg x happy_path/unsupported/corrupt]
 + test_static_target_map_f7_rows + test_contract_artifacts_shipped + test_requirements_pin_mammoth_floor)
```
→ **Certified suite: PASS 12/12.**

Point [1/5]–[5/5] semua PASS (job tunggal "Build image + in-container verification" = success; run keseluruhan = success). Run `34029872536` (@ `137a8e2`) menunjukkan pola hasil identik (probe PASS 3/3, certified 12 passed in 1.35s).

### Pembedaan sumber evidence (tidak dicampur)

| Bukti | Sumber | Nilai |
|---|---|---|
| Build image + probe 3/3 + certified 12/12 **in production image** | GitHub Actions run **34038671839** @ `41bd798` (dan 34029872536 @ `137a8e2`) | CI production-image |
| Full regression 937 test + set-diff vs baseline | Lokal `wt_f7` @ `41bd798` vs `wt_f7_base` @ `578f246` (JUnit XML) | Re-validasi lokal wt_f7 |

CI production-image hanya mensertifikasi converter F7 di dalam container (12 test); full-suite regression adalah bukti lokal terpisah. Keduanya saling melengkapi, tidak saling menggantikan. **→ Gap 2: PASS.**

---

## Verdict gabungan

| Gap | Requirement | Hasil | Verdict |
|---|---|---|---|
| 1 | Full regression pasca 137a8e2 vs 578f246, angka eksplisit, failure-set per nama | 925→937 node (+12 F7), 20F/5S/1XF tak berubah, failure-set identik 20/20 satu-per-satu, 0 failure baru | **PASS** |
| 2 | CI production-image untuk commit terbaru dengan RUN ID eksplisit | Run **34038671839** @ `41bd798` success; probe PASS 3/3; certified suite PASS 12/12 (in-image); diluruskan juga atribusi run 34022594418 (main @ 578f246) | **PASS** |

Tidak ada STOP condition: tidak ada failure baru yang tidak terjelaskan. Git state tidak berubah oleh sesi ini (`wt_f7` tetap `41bd798` = `origin/feat/factory-f7`; `wt_f7_base` = `578f246` detached, evidence-only; tidak ada commit/push baru; tidak ada operasi destruktif). PR tetap ditahan menunggu keputusan reviewer.

---

## Merge Gate (post-review) — PR #85

Dengan Gap 1 + Gap 2 PASS dan otorisasi reviewer, merge gate dijalankan sesuai proses standar proyek:

| Langkah | Bukti | Hasil |
|---|---|---|
| PR dibuka | **PR #85** https://github.com/converigo/converigo/pull/85 — `feat/factory-f7` → `main`, deskripsi lengkap (scope 3 slug, ledger 90→93, range `578f246..41bd798`, disclaimers MVP pptx, ringkasan gate ini + dependency audit) | MERGED (non-squash) 2026-09-06T16:15:39Z |
| CI PR-trigger standar (bukan dispatch) | `docker-runtime-verify` run **34044703120**, event **`pull_request`**, head `41bd798` | **SUCCESS** (~2 min) |
| CI post-merge (push `main`) | `docker-runtime-verify` run **34044870523**, event `push`, commit `0db8f98` | **SUCCESS** |
| Merge method | `gh pr merge 85 --merge` — **merge commit, non-squash**; histori `e6c256b → 137a8e2 → 41bd798` utuh di `main` (diverifikasi `git log --graph`) | ✔ |

### Baseline baru (kanonik)

**`0db8f987765c4ec348b4fac0c9778339dfb2eff3`** — "Merge pull request #85 from converigo/feat/factory-f7" (parents: `578f246` + `41bd798`). Merge-commit tree == branch-head tree (`git diff 41bd798..0db8f98` kosong → tidak ada drift saat merge).

### Production deploy (Railway, auto-deploy main)

| Fakta | Nilai |
|---|---|
| Project / service / environment | `amiable-growth` / `converigo` / `production` |
| Deployment aktif | commit **`0db8f98`**, status **SUCCESS**, instance **RUNNING** (BUILDING → DEPLOYING → SUCCESS ~2,5 menit) |
| Domain | `https://converigo.com` (custom) + `https://converigo-production.up.railway.app` (railway service) |

### Production smoke — real file, bukan cuma 201 (`tmp/f7_prod_smoke.py`, pola `f6_prod_smoke.py`)

Fixture = tracked regression samples nyata (`tests/assets/regression/sample.docx` 36.646 B, `sample.pptx` 28.342 B) via `POST /convert` → **201** → `GET /download` → **200 + attachment** → konten divalidasi (bukan sekadar status):

| Endpoint | Verifikasi konten | converigo.com | railway.app domain |
|---|---|---|---|
| `docx-to-html` | HTML valid (`<!DOCTYPE html>`+`<body>`); **2/2 paragraf DOCX** (ground-truth python-docx) hadir di teks HTML | **PASS** (219 B) | **PASS** (219 B) |
| `pptx-to-png` | PNG valid (PIL), **1224×1584** | **PASS** (12.410 B) | **PASS** (12.410 B) |
| `pptx-to-jpg` | JPEG valid (PIL), **1224×1584** | **PASS** (35.412 B) | **PASS** (35.412 B) |
| honest-error (bonus) | `tests/sample.txt` → docx-to-html → **422 `UNSUPPORTED_CONVERSION`** (tidak fabrikasi output) | **PASS** | **PASS** |

**F7 PRODUCTION SMOKE PASS: 4/4 di kedua domain.** (MVP tetap berlaku: pptx-to-png/jpg = text-extraction render slide pertama, bukan render visual penuh — 1224×1584 adalah halaman A4 teks di atas latar putih, bukan tampilan PowerPoint.)

### Certified count resmi pasca-merge

Ledger resmi `app/data/certified_converters.json` dibaca dari **tree merge-commit** `0db8f98`: **certified = 93** (beta = 0), berisi `docx-to-html`, `pptx-to-png`, `pptx-to-jpg`. Baseline `578f246` = 90 → delta **90 → 93** terkonfirmasi di main pasca-merge.

### Posisi batch berikutnya

Baseline F7 **LIVE di production** (@ `0db8f98`, smoke 4/4). Prasyarat sebelum batch baru terpenuhi — **belum ada batch baru yang dimulai**; langkah berikutnya = audit posisi **93 → 100** untuk menentukan batch F8.


