# Learning Center Sitemap Integration Report

Date: 2026-07-21
Scope: Extended the existing sitemap generation to include Learning Center pages without changing the article schema, templates, routers, or the SEO service beyond the required sitemap integration.

## What changed

- Extended the sitemap generation flow in [app/services/seo_service.py](app/services/seo_service.py) to include:
  - the Learning Center index page at /learning
  - every Learning Center article at /learning/{slug}
- Reused the existing article discovery architecture via [app/services/article_service.py](app/services/article_service.py).
- Added a regression assertion in [tests/test_sitemap.py](tests/test_sitemap.py) to ensure Learning Center items appear in the sitemap.

## Validation performed

### Learning Center articles in sitemap
Verified that the sitemap response includes:
- /learning
- /learning/what-is-file-conversion

### Existing sitemap behavior remains unchanged
Verified with the sitemap regression suite that existing expected entries still appear, including:
- /about
- /privacy-policy
- /terms
- /contact
- /cookies
- /mp4-to-mp3
- /jpg-to-pdf
- /png-to-jpg
- /pdf-to-jpg
- /blog
- /blog/how-to-convert-mp4-to-mp3
- /blog/jpg-to-pdf-guide
- /blog/png-to-jpg-guide

## Verification evidence

Command run:
- .\.venv\Scripts\python.exe -m pytest tests/test_sitemap.py tests/test_sitemap_service.py -q

Result:
- 3 passed, 1 warning in 2.43s
