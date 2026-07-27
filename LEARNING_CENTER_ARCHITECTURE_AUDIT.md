# Learning Center Architecture Audit

**Date:** 2026-07-21  
**Scope:** Existing project components for blog, articles, SEO, breadcrumbs, structured data, and internal linking  
**Goal:** Design a Learning Center that reuses current architecture without modification

---

## 1. Existing Blog & Article Routes

### Current Implementation
- **Route:** `@router.get("/blog")` → [app/routers/home.py](app/routers/home.py#L264)
  - Returns blog index with hardcoded articles list
  - Uses template: `pages/blog_index.html`
  - Includes metadata (title, description, canonical)
  - Generates structured data for blog collection

- **Route:** `@router.get("/blog/{slug}")` → [app/routers/home.py](app/routers/home.py#L324)
  - Returns individual blog articles by slug
  - Uses article-specific templates (e.g., `pages/blog_mp4_to_mp3.html`)
  - Includes breadcrumb data in context
  - Generates structured data for individual blog posts

### Architecture Patterns
| Component | Pattern |
|-----------|---------|
| **Data Source** | Hardcoded article map with slug keys |
| **Template Selection** | Dynamic (`template` field in article map) |
| **Metadata** | Per-article `title`, `description`, `canonical` |
| **Breadcrumbs** | Hardcoded in article map (`breadcrumb` list) |
| **Structured Data** | Generated via `seo_service.build_structured_data()` |

### Reusable Elements
- Article map structure (slug → {title, description, canonical, template, breadcrumb})
- Metadata construction pattern
- Structured data generation integration
- Locale context retrieval via `_get_locale_context(request)`
- Year context for footer

---

## 2. Reusable Templates

### Template Hierarchy
```
layouts/base.html (master layout)
├── includes/header.html
├── includes/footer.html
├── partials/seo_meta.html (meta tags)
└── partials/structured_data.html (JSON-LD)

pages/
├── blog_index.html (blog collection)
├── blog_*.html (individual articles)
├── format_index.html (format encyclopedia)
├── format_page.html (single format)
├── comparison_page.html (comparison tool)
├── home.html (homepage)
├── tools_directory.html
└── [others]

components/
├── breadcrumbs.html (reusable breadcrumb component)
├── hub_page.html (hub page template with breadcrumb support)
├── landing_sections.html (reusable section components)
├── converter_card.html (card component)
└── [others]
```

### SEO Template Partials
- **[partials/seo_meta.html](app/templates/partials/seo_meta.html)** – Renders `<meta>` tags from `meta` context dict
  - Fields: title, description, canonical, keywords, og_url, og_image, og_image_alt, etc.
  
- **[partials/structured_data.html](app/templates/partials/structured_data.html)** – Renders JSON-LD `<script>` from `structured_data` context dict
  - Supports FAQPage, BreadcrumbList, BlogPosting, Blog, Organization, WebSite

### Blog-Specific Templates
- **[pages/blog_index.html](app/templates/pages/blog_index.html)** – Blog collection page
  - Extends `layouts/base.html`
  - Renders article cards with category, title, description, link
  - Context: `articles` list
  
- **[pages/blog_*.html](app/templates/pages/)** – Individual article pages
  - Extends `layouts/base.html`
  - Custom content per article (hero, sections, calls-to-action)
  - Context: `article` dict, `breadcrumb` list, `structured_data` dict

### Breadcrumb Components
- **[components/hub_page.html](app/templates/components/hub_page.html)** (lines 7-15)
  ```html
  <nav aria-label="Breadcrumb">
    <ol class="breadcrumb">
      {% for item in breadcrumb %}
        <li><a href="{{ item.url }}">{{ item.name }}</a></li>
      {% endfor %}
    </ol>
  </nav>
  ```
  - Expects `breadcrumb` list in context (each item: `{name, url}`)
  - Semantically correct navigation element with `aria-label` and `ol/li`

- **[components/hub_page_service_template.html](app/templates/components/hub_page_service_template.html)** (lines 7-13)
  - Alternative breadcrumb pattern (same structure)

### Reusable Base Layout
- **[layouts/base.html](app/templates/layouts/base.html)**
  - Includes analytics (Google Tag Manager)
  - Renders `seo_meta.html` (meta tags)
  - Renders `structured_data.html` (JSON-LD)
  - Blocks: `title`, `content`
  - Globals: `request`, `get_template_globals()`

---

## 3. SEO Utilities

### SeoService [app/services/seo_service.py](app/services/seo_service.py)

#### Core Methods
| Method | Purpose | Returns |
|--------|---------|---------|
| `build_home_meta(request)` | Build homepage metadata dict | `{title, description, canonical, og_url, og_site_name, og_image, og_image_alt, og_type, twitter_*}` |
| `build_tool_meta(request, tool_data, canonical_path)` | Build converter landing page metadata | Same metadata dict |
| `build_structured_data(request, tool_data, page_type, page_data, canonical_path)` | Generate JSON-LD schema | `{@context, @graph or direct schema}` |
| `build_sitemap_xml(request)` | Generate sitemap.xml | XML string |
| `_build_breadcrumb_list(base_url, items)` | Generate BreadcrumbList schema | `{@type: "BreadcrumbList", itemListElement: []}` |

#### Key Features
- **Production URL:** `PRODUCTION_BASE_URL = "https://converigo.com"` (used for canonical URLs and sitemap)
- **Metadata standardization:** Consistent field names and structure across all pages
- **Structured data generation:** Supports multiple page types (blog_index, blog_article, tool_page, trust_page, etc.)
- **Breadcrumb schema:** Automatic BreadcrumbList generation from item list
- **Blog entries:** Dedicated `_build_blog_entries()` for blog path discovery and sitemap inclusion

#### Structured Data Page Types
- **blog_index** – Blog collection with BlogPosting array
- **blog_article** – Individual post with headline, description, breadcrumb
- **tool_page** – Converter landing page (detailed schema)
- **trust_page** – Format encyclopedia, comparison pages
- **None/Default** – Homepage with FAQPage, Organization, WebSite

#### Example Usage
```python
metadata = {
    "title": "...",
    "description": "...",
    "canonical": "...",
    "og_url": "...",
    "og_image": "...",
    # ... more fields
}

structured_data = seo_service.build_structured_data(
    request,
    page_type="blog_article",
    page_data={
        "headline": article["title"],
        "description": article["description"],
        "url": article["canonical"].replace(PRODUCTION_BASE_URL, ""),
        "breadcrumb": article["breadcrumb"],
    },
)
```

---

## 4. Breadcrumb Support

### Breadcrumb Architecture

#### Data Structure
```python
breadcrumb = [
    {"name": "Home", "url": "/"},
    {"name": "Category", "url": "/category"},
    {"name": "Article Title", "url": "/category/article-slug"},
]
```

#### Template Rendering
- Component: [components/hub_page.html](app/templates/components/hub_page.html#L7-L15)
- Semantically correct `<nav><ol><li>` structure
- Safe HTML rendering with click tracking via `href`

#### Schema.org Integration
- **Method:** `SeoService._build_breadcrumb_list(base_url, items)`
- **Output:** BreadcrumbList JSON-LD schema
- **Position:** Auto-indexed starting from 1
- **URL Normalization:** Converts relative paths to absolute URLs

#### Current Implementation
- Blog breadcrumbs: Hardcoded in article map (`article["breadcrumb"]`)
- Hub breadcrumbs: Generated from hub definition
- Comparison breadcrumbs: Built from slug parsing

### Reusable Pattern
1. Define breadcrumb items in page context (list of dicts with `name` and `url`)
2. Include [components/hub_page.html](app/templates/components/hub_page.html) or create similar
3. Call `seo_service._build_breadcrumb_list()` for schema generation
4. Pass to template via `structured_data` context

---

## 5. Structured Data Support

### JSON-LD Implementation

#### Schema Types Generated
| Page Type | Schema | Location |
|-----------|--------|----------|
| Homepage | Organization, WebSite, FAQPage | `SeoService.build_structured_data()` (default) |
| Blog Index | Blog, BlogPosting[], BreadcrumbList | `build_structured_data(page_type="blog_index", page_data=...)` |
| Blog Article | BlogPosting, BreadcrumbList | `build_structured_data(page_type="blog_article", page_data=...)` |
| Converter Landing | Product, Thing, or custom | `build_structured_data(tool_data=..., page_type="tool_page")` |
| Format Page | Thing, BreadcrumbList | `build_structured_data(page_type="trust_page")` |

#### Generation Process
1. **Service method** creates nested schema dict with `@context` and `@graph`
2. **Template partial** ([partials/structured_data.html](app/templates/partials/structured_data.html)) renders as `<script type="application/ld+json">`
3. **Context passing** in route handler: `"structured_data": seo_service.build_structured_data(...)`

#### Core Fields Supported
- Organization: name, url, logo, description
- WebSite: url, name, publisher, potentialAction (search)
- Blog/BlogPosting: headline, description, url, datePublished, dateModified, author
- BreadcrumbList: itemListElement (position, name, item)
- FAQPage: mainEntity (Question/Answer pairs)

#### Template Integration
- **Partial:** `{% include "partials/structured_data.html" %}`
- **Conditional rendering:** `{% if structured_data %}`
- **JSON escaping:** Automatic via Jinja2 filter

### Benefits for Learning Center
- **SEO:** Google understands article content, hierarchy, and organization
- **Rich snippets:** Breadcrumbs appear in search results
- **Schema validation:** Passes Google Rich Result Test
- **Consistency:** Centralized generation in SeoService

---

## 6. Internal Linking Utilities

### InternalLinkService [app/services/internal_link_service.py](app/services/internal_link_service.py)

#### Core Methods
| Method | Purpose | Returns |
|--------|---------|---------|
| `get_links_for_landing(slug, contract)` | Generate links for converter landing page | `{related_converters, related_formats, related_comparisons, related_knowledge, related_hubs, related_articles}` |
| `get_links_for_comparison(slug)` | Generate links for comparison page | Same dict structure |
| `get_links_for_format(format_name)` | Generate links for format encyclopedia | Same dict structure |
| `get_links_for_hub(hub_slug)` | Generate links for hub page | Same dict structure |
| `get_links_for_knowledge(format_name)` | Generate links for knowledge/education page | Same dict structure |

#### Link Categories
Each method returns a dict with up to 6 link groups:
- `related_converters` – Other converter tools
- `related_formats` – Format encyclopedia entries
- `related_comparisons` – Format comparison pages
- `related_knowledge` – Format knowledge pages
- `related_hubs` – Hub pages (image, audio, video, etc.)
- `related_articles` – Blog articles

#### Link Structure
```python
{
    "slug": "png-to-jpg",
    "title": "PNG to JPG Converter",
    "description": "Convert PNG images to JPG format",
    "href": "/tools/png-to-jpg",  # or full path
    "score": 0.95,  # relevance score for sorting
}
```

#### Deduplication
- Method: `_deduplicate_links(links)` removes duplicate slugs across categories
- Preserves highest-scoring link if duplicates exist

#### Dependency Graph
- Uses **ConverterRegistryService** for active converters
- Uses **ConverterDataService** for tool metadata
- Uses **ComparisonService** for format pairs
- Uses **KnowledgeService** for format knowledge pages
- Uses **HubPageService** for hub definitions

#### Relevance Scoring
- Converters matching input/output formats: higher score
- Related formats from master records: medium score
- Hub membership: indexed by category

### Example Usage
```python
from app.services.internal_link_service import InternalLinkService

link_service = InternalLinkService("app/data/converters")
links = link_service.get_links_for_landing("mp3-to-wav")

# Returns:
# {
#     "related_converters": [{"slug": "mp3-to-flac", "title": "...", "href": "...", "score": 0.9}],
#     "related_formats": [{"slug": "mp3", "title": "MP3 Format", "href": "/formats/mp3", "score": 0.8}],
#     "related_comparisons": [...],
#     "related_knowledge": [...],
#     "related_hubs": [...],
#     "related_articles": [...]
# }
```

### Use Cases
- **Landing pages:** Auto-populate "related tools" sections
- **Blog posts:** Link to relevant converters and comparisons
- **Format pages:** Link to relevant knowledge articles and comparisons
- **Comparison pages:** Link to related converters and hub pages

---

## 7. Related Services & Dependencies

### Knowledge Services
- **[FormatKnowledgeService](app/services/format_knowledge_service.py)** – Load format knowledge payloads (FAQ, advantages, comparisons, etc.)
- **[KnowledgeService](app/services/knowledge_service.py)** – Build knowledge pages from format master records
- **[TopicClusterService](app/services/topic_cluster_service.py)** – Generate comprehensive topic clusters (SEO content strategy)

### Content Generation
- **[FormatKnowledgeGenerator](app/services/format_knowledge_generator.py)** – Generate JSON knowledge files from master records
- **[LandingPageBuilder](app/services/landing_service.py)** – Build landing page context and content
- **[HubPageService](app/services/hub_page_service.py)** – Generate hub page definitions and converter grouping

### Data Access
- **[ConverterRegistryService](app/services/converter_registry_service.py)** – Active converter contracts and metadata
- **[ConverterDataService](app/services/converter_data_service.py)** – Tool definitions and properties
- **[AuthorityService](app/services/authority_service.py)** – Format definitions and relationships

### Localization
- **[LanguageService](app/services/language_service.py)** – Locale detection and translation

---

## 8. Current Blog Article Workflow

### Route Handler Flow
```
GET /blog/{slug}
  ↓
1. article_map.get(slug)
  ↓
2. If not found → HTTPException(404)
  ↓
3. Load locale context: _get_locale_context(request)
  ↓
4. Build metadata dict from article map
  ↓
5. Generate structured_data:
   seo_service.build_structured_data(
     request,
     page_type="blog_article",
     page_data={breadcrumb, headline, description, url}
   )
  ↓
6. Render template with context:
   - request, locale, translations (t)
   - meta, article, structured_data
   - year (for footer)
  ↓
7. Return HTMLResponse
```

### Context Structure
```python
context = {
    "request": request,
    "locale": locale_data,
    "t": t,  # translation function
    "supported_locales": supported_locales,
    "meta": {
        "title": "...",
        "description": "...",
        "canonical": "...",
        "keywords": "...",
        "author": "Converigo",
        "robots": "index,follow",
    },
    "article": {
        "title": "...",
        "description": "...",
        "canonical": "...",
        "og_url": "...",
        "template": "pages/blog_mp4_to_mp3.html",
        "breadcrumb": [
            {"name": "Home", "url": "/"},
            {"name": "Blog", "url": "/blog"},
            {"name": "Article Title", "url": "/blog/article-slug"},
        ],
    },
    "structured_data": {...},  # JSON-LD schema
    "year": datetime.utcnow().year,
}
```

---

## 9. Learning Center Architecture Design

### Reuse Strategy: Minimal New Code

The Learning Center can be built by **reusing existing components without modification**:

#### 1. Route Layer
**Proposed:** Create [app/routers/learning.py](app/routers/learning.py)
- Reuse: Route structure from `home.py` `/blog` routes
- Reuse: `_get_locale_context(request)` helper
- Reuse: `seo_service` instance
- Reuse: Template rendering pattern

**Endpoints:**
- `GET /learning` → Collection/hub page
- `GET /learning/{slug}` → Individual learning article
- `GET /learning/topics/{topic}` → Topic-grouped articles
- `GET /learning/search?q=...` → Search results

#### 2. Data Structure
**Proposed:** Use same article map pattern
```python
learning_article_map = {
    "getting-started-with-file-conversion": {
        "title": "Getting Started with File Conversion",
        "description": "Learn the basics of file conversion...",
        "category": "Fundamentals",
        "canonical": "{PRODUCTION_BASE_URL}/learning/getting-started-with-file-conversion",
        "og_url": "{PRODUCTION_BASE_URL}/learning/getting-started-with-file-conversion",
        "template": "pages/learning_fundamentals.html",
        "breadcrumb": [
            {"name": "Home", "url": "/"},
            {"name": "Learning", "url": "/learning"},
            {"name": "Fundamentals", "url": "/learning/topics/fundamentals"},
            {"name": "Getting Started with File Conversion", "url": "/learning/getting-started-with-file-conversion"},
        ],
        "related_formats": ["pdf", "jpg", "png"],  # For internal linking
        "topics": ["fundamentals", "conversion-basics"],  # For categorization
    },
    # ... more articles
}
```

#### 3. Template Layer
**Proposed:** Create new page templates
- `pages/learning_index.html` – Reuses: `blog_index.html` structure
- `pages/learning_article.html` – Reuses: `blog_*.html` structure with breadcrumb
- `pages/learning_topic.html` – Reuses: hub page layout
- `components/learning_article_card.html` – Reuses: `converter_card.html` pattern

**Inherited:** All existing partials
- `partials/seo_meta.html` – No changes
- `partials/structured_data.html` – No changes
- `layouts/base.html` – No changes

#### 4. SEO Integration
**Reuse:** `SeoService.build_structured_data()`
```python
# In learning route handler:
structured_data = seo_service.build_structured_data(
    request,
    page_type="blog_article",  # Same page type
    page_data={
        "headline": article["title"],
        "description": article["description"],
        "url": article["canonical"].replace(PRODUCTION_BASE_URL, ""),
        "breadcrumb": article["breadcrumb"],
    },
)
```
**Result:** Automatic JSON-LD schema, breadcrumb list, all SEO metadata

#### 5. Internal Linking
**Reuse:** `InternalLinkService.get_links_for_knowledge()`
```python
# In learning article context:
internal_links = link_service.get_links_for_knowledge(format_name)

# Returns: related_converters, related_formats, related_comparisons, etc.
# Template renders as "Related Tools", "See Also", "Learn More" sections
```

#### 6. Breadcrumb Support
**Reuse:** `components/hub_page.html` breadcrumb template
**Reuse:** `SeoService._build_breadcrumb_list()` for schema

#### 7. Metadata & Analytics
**Reuse:** Same metadata dict pattern as blog
- `title`, `description`, `canonical`, `keywords`, `og_image`, etc.
- Rendered by existing `partials/seo_meta.html`

#### 8. Localization
**Reuse:** `LanguageService` and `_get_locale_context(request)`
- Same locale detection logic
- Same translation function pattern

---

### Data Source Options

#### Option A: Hardcoded Article Map (Simplest)
- **Pros:** Zero dependencies, matches current blog implementation, fast
- **Cons:** Requires manual article addition in route file
- **Fit:** Good for up to 30-50 articles

#### Option B: Markdown Files + Service
- **Pros:** Separate content from code, easier editing, scalable
- **Requires:** New lightweight service to parse markdown files
- **Fit:** Good for 50-200 articles with versioning

#### Option C: Format Knowledge + Topic Cluster Integration
- **Pros:** Leverage existing knowledge generation pipeline
- **Requires:** Map learning topics to format clusters
- **Fit:** Good for structured, format-focused learning content

#### Recommendation for MVP
**Start with Option A** (hardcoded map in route file):
- Reuses blog pattern exactly
- Zero new service code needed
- Proven reliability
- Can migrate to Option B later without breaking URLs

---

### Proposed File Structure
```
app/routers/learning.py                      (NEW - route handlers)
app/templates/pages/learning_index.html      (NEW - collection page)
app/templates/pages/learning_article.html    (NEW - article page)
app/templates/pages/learning_topic.html      (NEW - topic hub page)
app/templates/components/learning_card.html  (NEW - card component, optional)

# No changes to:
app/services/seo_service.py
app/services/internal_link_service.py
app/templates/partials/seo_meta.html
app/templates/partials/structured_data.html
app/templates/layouts/base.html
```

---

### Content Structure Example

#### Learning Center Topics
- **Fundamentals** – What is file conversion? Why different formats?
- **Guide by Format** – Format-specific best practices (PDF, JPG, MP3, MP4, ZIP)
- **Use Case Guides** – Common workflows (batch conversion, image optimization, audio editing prep)
- **Troubleshooting** – Common issues and solutions
- **Format Comparisons** – Explained (WAV vs MP3, PNG vs JPG, DOCX vs PDF)

#### Learning Article Metadata Example
```python
{
    "slug": "understanding-image-formats",
    "title": "Understanding Image Formats: When to Use JPG, PNG, or WebP",
    "description": "Learn the differences between image formats...",
    "category": "Formats",
    "author": "Converigo",
    "date_published": "2026-07-21",
    "read_time": "8 min",
    "related_formats": ["jpg", "png", "webp"],
    "related_comparisons": ["png-vs-jpg", "webp-vs-png"],
    "breadcrumb": [
        {"name": "Home", "url": "/"},
        {"name": "Learning", "url": "/learning"},
        {"name": "Formats", "url": "/learning/formats"},
        {"name": "Understanding Image Formats...", "url": "/learning/understanding-image-formats"},
    ],
}
```

---

### URL Structure
```
/learning                           (collection)
/learning/{slug}                   (individual article)
/learning/formats                  (formats topic)
/learning/formats/{format_name}    (format-specific guide)
/learning/guides                   (use case guides)
/learning/guides/{guide_slug}      (individual guide)
/learning/comparisons              (comparison hub)
/learning/comparisons/{comparison} (specific comparison)
/learning/search?q=...             (search)
```

---

### Reuse Matrix

| Component | Current Use | Learning Center Reuse | Modification |
|-----------|------------|----------------------|--------------|
| **Route Structure** | `home.py` | Learning routes | None |
| **Article Map Pattern** | Blog | Learning map | None |
| **SeoService** | All pages | Learning articles | None |
| **build_structured_data()** | All pages | Learning articles | None |
| **Breadcrumb Component** | Hubs, Blog | Learning articles | None |
| **InternalLinkService** | Tools, Comparisons | Learning articles | None |
| **Template Layout** | All | Learning pages | None |
| **seo_meta.html** | All | Learning pages | None |
| **structured_data.html** | All | Learning pages | None |
| **LanguageService** | All | Learning pages | None |
| **Metadata Pattern** | All | Learning pages | None |

---

### Minimal Implementation Checklist
- [ ] Create `app/routers/learning.py` (route handlers only)
- [ ] Create `app/templates/pages/learning_index.html` (based on `blog_index.html`)
- [ ] Create `app/templates/pages/learning_article.html` (based on `blog_*.html`)
- [ ] Add learning routes to `app/main.py` router registration
- [ ] Define learning article map in route file
- [ ] (Optional) Create topic hub template based on `hub_page.html`
- [ ] Test route, breadcrumbs, SEO meta, structured data rendering
- [ ] Verify internal linking via InternalLinkService

**No changes needed:**
- SeoService
- InternalLinkService
- Templates (use existing partials and layout)
- Services layer

---

## 10. Advantages of This Architecture

### Consistency
- Same URL pattern as `/blog`
- Same metadata structure
- Same breadcrumb pattern
- Same structured data generation

### Maintainability
- Single article map source
- Reuses proven blog route handlers
- No new service code
- Same template patterns

### SEO Performance
- JSON-LD schema for all articles (Google understands hierarchy)
- Breadcrumb navigation (appears in search results)
- Canonical URLs (prevents duplicate content)
- Internal linking via InternalLinkService (crawlability)

### Scalability
- Route handler pattern scales to thousands of articles
- Can migrate to markdown/database later (same template interface)
- InternalLinkService deduplication prevents link overload
- Topic grouping built into data structure

### User Experience
- Breadcrumb navigation (wayfinding)
- Related content links (discovery)
- Consistent styling with rest of site
- Locale support (translations)

---

## Summary

**The Learning Center requires minimal new code** by reusing:
1. **Route patterns** from `/blog` handlers
2. **Article map structure** (hardcoded or from service)
3. **SeoService** for metadata and structured data
4. **InternalLinkService** for related content
5. **Existing templates** (partials, layout, breadcrumb component)
6. **LanguageService** for localization

**New files needed:** 1 route file + 2-3 template files  
**Services modified:** 0  
**Backward compatibility:** Guaranteed (no existing code changes)

**Learning Center homepage:** `/learning`  
**Learning article:** `/learning/getting-started-with-file-conversion`  
**Topic hub:** `/learning/formats`, `/learning/use-cases`  
**Related content:** Auto-generated from InternalLinkService  
**SEO:** Automatic via existing SeoService + structured data  

---

## Appendix: File References

### Key Routes
- [app/routers/home.py](app/routers/home.py) – Blog implementation (reference)
- [app/routers/formats.py](app/routers/formats.py) – Format encyclopedia (reference)
- [app/routers/comparison.py](app/routers/comparison.py) – Comparison pages (reference)

### Key Services
- [app/services/seo_service.py](app/services/seo_service.py) – SEO metadata & structured data
- [app/services/internal_link_service.py](app/services/internal_link_service.py) – Internal linking
- [app/services/format_knowledge_service.py](app/services/format_knowledge_service.py) – Format content
- [app/services/hub_service.py](app/services/hub_service.py) – Hub definitions (reference)
- [app/services/language_service.py](app/services/language_service.py) – Localization

### Key Templates
- [app/templates/layouts/base.html](app/templates/layouts/base.html) – Master layout (reuse)
- [app/templates/pages/blog_index.html](app/templates/pages/blog_index.html) – Blog index (reference)
- [app/templates/pages/blog_mp4_to_mp3.html](app/templates/pages/blog_mp4_to_mp3.html) – Blog article (reference)
- [app/templates/components/hub_page.html](app/templates/components/hub_page.html) – Breadcrumb component (reuse)
- [app/templates/partials/seo_meta.html](app/templates/partials/seo_meta.html) – Meta tag rendering (reuse)
- [app/templates/partials/structured_data.html](app/templates/partials/structured_data.html) – JSON-LD rendering (reuse)

### Related Configs
- [app/main.py](app/main.py) – Route registration
- [app/core/templates.py](app/core/templates.py) – Template configuration
