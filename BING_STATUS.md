# Bing Webmaster — SEO Audit

**Status: NOT CONFIGURED**

---

## 1. Bing Site Verification

| Item | Status | Evidence |
|------|--------|----------|
| `msvalidate.01` meta tag | ❌ **Not Found** | No `<meta name="msvalidate.01"` tag found in any template (base.html, seo_meta.html, any page template) |
| Bing XML verification file | ❌ **Not Found** | No `BingSiteAuth.xml` or similar verification file in `app/static/` directory |
| DNS TXT verification | ❌ **Not Found** | No DNS verification instructions or records referenced in project |

**Impact:** Without verification, Bing Webmaster Tools cannot confirm site ownership, preventing access to Bing's search performance data, crawl stats, and index management.

---

## 2. Bing Sitemap Submission

| Item | Status | Evidence |
|------|--------|----------|
| Sitemap URL for Bing | ✅ **Available** | `https://converigo.com/sitemap.xml` is accessible and can be submitted manually via Bing Webmaster Tools |
| Category sitemaps for Bing | ✅ **Available** | `sitemap-video.xml`, `sitemap-image.xml`, `sitemap-pdf.xml`, `sitemap-audio.xml` — all accessible |
| Automated Bing sitemap ping | ❌ **Not Found** | No code found that pings `https://www.bing.com/ping?sitemap=...` on deploy or sitemap regeneration |
| Bing-specific sitemap index | ❌ **Not Found** | No sitemap index tailored specifically for Bing submission |

---

## 3. Robots.txt Reference for Bing

| Item | Status | Evidence |
|------|--------|----------|
| Bingbot crawl directives | ❌ **Not Found** | Current `robots.txt` has only `User-agent: *` — no specific `User-agent: bingbot` rules |
| Bing-specific allow/disallow | ❌ **Not Found** | No Bing-specific crawl rules, crawl-delay, or indexing preferences |
| Sitemap reference accessible to Bing | ✅ **Available** | `Sitemap: /sitemap.xml` in robots.txt is accessible by all crawlers including bingbot |

---

## 4. Bing Webmaster Tools Integration Code

| Item | Status | Evidence |
|------|--------|----------|
| Programmatic Bing integration | ❌ **Not Found** | No API integration with Bing Webmaster Tools for automated index submission, URL inspection, or performance data retrieval |

---

## Summary

| Category | Status |
|----------|--------|
| Site Verification | ❌ Not configured |
| Meta Tag | ❌ Missing |
| Verification File | ❌ Missing |
| Sitemap Submission | ⚠️ Available manually, no automation |
| Bing-specific robots.txt | ❌ Not configured |
| API Integration | ❌ Not configured |
| **Overall Bing** | **❌ Not Configured** |

### Recommendations
1. **Verify site in Bing Webmaster Tools** — Add `msvalidate.01` meta tag to `app/templates/partials/seo_meta.html` with the verification ID from Bing Webmaster Tools
2. **Submit sitemap** — Manually submit `https://converigo.com/sitemap.xml` via Bing Webmaster Tools dashboard
3. **Add automated ping** — Consider adding a post-deploy step that pings `https://www.bing.com/ping?sitemap=https://converigo.com/sitemap.xml`
4. **Consider Bing-specific rules** in robots.txt if Bingbot behaves differently than Googlebot for this site

