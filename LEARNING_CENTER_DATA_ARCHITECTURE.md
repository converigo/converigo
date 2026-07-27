# Learning Center Data Architecture

**Date:** 2026-07-21  
**Scope:** Data-driven Learning Center using JSON files in `app/data/articles/`  
**Design Phase:** Architecture only (no implementation)

---

## 1. Data Model

### 1.1 Article Schema

Each learning article is a JSON file with the following structure:

```json
{
  "slug": "getting-started-with-file-conversion",
  "title": "Getting Started with File Conversion: A Beginner's Guide",
  "description": "Learn the fundamentals of file conversion, why you might need it, and how to use Converigo to convert your first file.",
  "category": "Fundamentals",
  "topics": ["basics", "conversion-101", "beginner-guide"],
  "author": "Converigo",
  "date_published": "2026-07-01",
  "date_modified": "2026-07-15",
  "read_time_minutes": 8,
  "keywords": ["file conversion basics", "beginner guide", "how to convert files"],
  "seo_keywords": ["file conversion", "convert files online", "file formats"],
  "og_image": "/static/images/og-getting-started.png",
  "og_image_alt": "Getting started with file conversion",
  "canonical": "/learning/getting-started-with-file-conversion",
  "featured": true,
  "order": 1,
  "related_formats": ["pdf", "jpg", "mp3"],
  "related_converters": ["pdf-to-jpg", "jpg-to-png"],
  "related_articles": ["what-are-file-formats", "why-convert-files"],
  "sections": [
    {
      "id": "what-is-file-conversion",
      "title": "What Is File Conversion?",
      "content": "File conversion is the process of transforming a file from one format to another..."
    },
    {
      "id": "why-convert-files",
      "title": "Why Would You Convert a File?",
      "content": "There are many practical reasons to convert files..."
    },
    {
      "id": "how-converigo-works",
      "title": "How Does Converigo Work?",
      "content": "Converigo makes file conversion simple and fast..."
    }
  ],
  "faq": [
    {
      "question": "Is file conversion safe?",
      "answer": "Yes, Converigo uses secure encryption to protect your files during conversion."
    },
    {
      "question": "How long does conversion take?",
      "answer": "Most conversions complete within seconds, depending on file size and type."
    }
  ],
  "call_to_action": {
    "text": "Ready to convert a file?",
    "url": "/tools/pdf-to-jpg",
    "button_text": "Try Converigo Now"
  },
  "related_tools": [
    {
      "slug": "pdf-to-jpg",
      "title": "PDF to JPG Converter",
      "description": "Convert PDF files to JPG images",
      "href": "/pdf-to-jpg"
    }
  ],
  "breadcrumb_override": [
    {"name": "Home", "url": "/"},
    {"name": "Learning", "url": "/learning"},
    {"name": "Fundamentals", "url": "/learning/categories/fundamentals"},
    {"name": "Getting Started with File Conversion", "url": "/learning/getting-started-with-file-conversion"}
  ]
}
```

### 1.2 Schema Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slug` | string | Yes | URL-safe identifier (lowercase, hyphens, no spaces) |
| `title` | string | Yes | Article headline (60-70 chars for SEO) |
| `description` | string | Yes | Meta description for SEO (155-160 chars) |
| `category` | string | Yes | Top-level topic (Fundamentals, Guides, Comparisons, Troubleshooting) |
| `topics` | array[string] | Yes | Subcategories for filtering/discovery |
| `author` | string | Yes | Content creator name |
| `date_published` | string (ISO 8601) | Yes | Publication date for sorting |
| `date_modified` | string (ISO 8601) | No | Last update date |
| `read_time_minutes` | integer | Yes | Estimated reading time |
| `keywords` | array[string] | Yes | Meta keywords (3-5 terms) |
| `seo_keywords` | array[string] | Yes | Primary SEO targets (3-5 high-volume terms) |
| `og_image` | string | No | Open Graph image URL |
| `og_image_alt` | string | No | Alt text for OG image |
| `canonical` | string | No | Canonical URL (defaults to `/learning/{slug}`) |
| `featured` | boolean | No | Featured on homepage/category (defaults to false) |
| `order` | integer | No | Sort order within category (ascending) |
| `related_formats` | array[string] | No | Format slugs (jpg, mp3, pdf, etc.) |
| `related_converters` | array[string] | No | Converter slugs (jpg-to-png, mp3-to-wav, etc.) |
| `related_articles` | array[string] | No | Article slugs (cross-linking) |
| `sections` | array[object] | Yes | Content sections with id, title, content |
| `faq` | array[object] | Yes | FAQ items (question, answer) |
| `call_to_action` | object | No | CTA for conversion (text, url, button_text) |
| `related_tools` | array[object] | No | Converter tools to link (slug, title, description, href) |
| `breadcrumb_override` | array[object] | No | Custom breadcrumb (overrides auto-generated) |

### 1.3 Sections Field Structure

```json
"sections": [
  {
    "id": "unique-section-id",
    "title": "Section Title",
    "content": "HTML or markdown content here...",
    "subsections": [
      {
        "id": "subsection-id",
        "title": "Subsection Title",
        "content": "Content here..."
      }
    ]
  }
]
```

**Purpose:**
- Enables table of contents generation
- Supports anchor linking (#what-is-file-conversion)
- Allows section-level schema markup (Article sections)
- Enables progressive disclosure in templates

---

## 2. Data Organization

### 2.1 Directory Structure

```
app/data/articles/
├── _schema.json                    (schema definition & validation rules)
├── _index.json                     (generated index for discovery)
│
├── fundamentals/
│   ├── getting-started.json
│   ├── what-are-formats.json
│   └── why-convert-files.json
│
├── guides/
│   ├── batch-conversion.json
│   ├── image-optimization.json
│   ├── pdf-workflows.json
│   ├── audio-editing-prep.json
│   └── video-preparation.json
│
├── comparisons/
│   ├── png-vs-jpg-explained.json
│   ├── wav-vs-mp3-explained.json
│   ├── docx-vs-pdf-explained.json
│   └── mp4-vs-webm-explained.json
│
├── troubleshooting/
│   ├── conversion-fails.json
│   ├── quality-issues.json
│   ├── file-size-large.json
│   └── format-not-supported.json
│
└── format-specific/
    ├── understanding-pdf.json
    ├── understanding-images.json
    ├── understanding-audio.json
    └── understanding-video.json
```

**Organization Philosophy:**
- Top-level folders by category (pedagogical structure)
- Flat files within folders (easy discovery)
- Underscore-prefixed meta files (_schema.json, _index.json)
- Slugs become filenames for URL-to-file mapping

### 2.2 Category Structure

| Category | Purpose | Example Articles | Topics |
|----------|---------|------------------|--------|
| **Fundamentals** | Core concepts | "What is file conversion?", "Understanding file formats" | basics, concepts, beginner-guide |
| **Guides** | Workflow tutorials | "Batch conversion", "Image optimization", "Audio editing prep" | how-to, workflow, step-by-step |
| **Comparisons** | Format explanations | "PNG vs JPG", "WAV vs MP3", "DOCX vs PDF" | comparison, explained, differences |
| **Troubleshooting** | Problem solving | "Conversion fails", "Quality issues", "File size too large" | troubleshooting, help, problems |
| **Format-Specific** | Deep dives | "Understanding PDF", "Understanding Audio", "Image quality explained" | format-specific, technical, deep-dive |

### 2.3 Index File (_index.json)

```json
{
  "version": "1.0",
  "last_generated": "2026-07-21T10:00:00Z",
  "total_articles": 24,
  "by_category": {
    "Fundamentals": {
      "count": 3,
      "articles": [
        {
          "slug": "getting-started",
          "title": "Getting Started with File Conversion",
          "date_published": "2026-07-01",
          "featured": true
        }
      ]
    },
    "Guides": {
      "count": 5,
      "articles": [...]
    }
  },
  "by_topic": {
    "basics": {
      "articles": ["getting-started", "what-are-formats"]
    },
    "workflow": {
      "articles": ["batch-conversion", "image-optimization"]
    }
  },
  "featured_articles": [
    "getting-started",
    "image-optimization",
    "png-vs-jpg-explained"
  ],
  "related_formats": {
    "pdf": ["understanding-pdf", "pdf-workflows"],
    "jpg": ["png-vs-jpg-explained", "image-optimization"]
  },
  "related_converters": {
    "pdf-to-jpg": ["understanding-pdf", "image-optimization"],
    "png-to-jpg": ["png-vs-jpg-explained", "image-optimization"]
  }
}
```

**Purpose:**
- Fast discovery without loading all files
- SEO sitemaps generation
- Homepage featured articles
- Topic/format-based filtering
- Related content discovery

**Auto-generated by:** New `ArticleIndexService` (reads all article files, validates, builds index)

---

## 3. Service Layer

### 3.1 ArticleService (New)

**File:** `app/services/article_service.py`

```python
class ArticleService:
    """Load, validate, and manage learning center articles."""
    
    def __init__(self, articles_dir: Path | str | None = None) -> None:
        self.articles_dir = Path(articles_dir or "app/data/articles")
    
    def load_article(self, slug: str) -> dict[str, Any] | None:
        """Load single article by slug."""
        # Locate file: articles/{category}/{slug}.json
        # Validate against schema
        # Return article dict or None if not found
    
    def load_articles_by_category(self, category: str) -> list[dict]:
        """Load all articles in a category."""
        # Find all .json files in articles/{category}/
        # Sort by order/date_published
        # Return sorted list
    
    def load_articles_by_topic(self, topic: str) -> list[dict]:
        """Load all articles tagged with a topic."""
        # Search across all categories for articles with topic
        # Return sorted list
    
    def load_articles_by_format(self, format_slug: str) -> list[dict]:
        """Load all articles related to a format."""
        # Search for articles with format_slug in related_formats
        # Return sorted list
    
    def get_index(self) -> dict[str, Any]:
        """Get generated index of all articles."""
        # Load app/data/articles/_index.json
        # Return index dict
    
    def validate_article(self, data: dict) -> list[str]:
        """Validate article against schema."""
        # Check required fields
        # Validate field types and structure
        # Return list of errors (empty if valid)
    
    def get_article_by_slug(self, slug: str) -> dict | None:
        """Load article and populate computed fields."""
        # Load article JSON
        # Add breadcrumbs (auto-generated or override)
        # Add computed_canonical
        # Return enriched article dict
```

**Dependencies:**
- `pathlib.Path` for file operations
- `json` for parsing
- Reuses validation pattern from `FormatKnowledgeService`

### 3.2 ArticleIndexService (New)

**File:** `app/services/article_index_service.py`

```python
class ArticleIndexService:
    """Generate and cache article index for discovery."""
    
    def __init__(self, articles_dir: Path | str | None = None) -> None:
        self.articles_dir = Path(articles_dir or "app/data/articles")
        self.article_service = ArticleService(articles_dir)
    
    def build_index(self) -> dict[str, Any]:
        """Scan all articles and generate index."""
        # Enumerate all .json files
        # Load and validate each
        # Build by_category, by_topic, by_format maps
        # Identify featured articles
        # Write to app/data/articles/_index.json
        # Return index dict
    
    def discover_categories(self) -> list[str]:
        """Get all unique categories."""
        # Scan articles_dir for subdirectories
        # Return sorted list of category names
    
    def discover_topics(self) -> list[str]:
        """Get all unique topics across articles."""
        # Scan all articles for topics field
        # Return sorted, deduplicated list
    
    def discover_related_formats(self) -> dict[str, list[str]]:
        """Get format-to-articles mapping."""
        # Scan all articles for related_formats
        # Return {format_slug: [article_slugs]}
    
    def discover_related_converters(self) -> dict[str, list[str]]:
        """Get converter-to-articles mapping."""
        # Scan all articles for related_converters
        # Return {converter_slug: [article_slugs]}
    
    def regenerate_index(self) -> dict[str, Any]:
        """Rebuild index from scratch."""
        # Call build_index()
        # Log statistics (total articles, by category, etc.)
        # Return index dict
```

**Purpose:**
- Enables fast discovery without loading all files
- Supports sitemaps, search, filtering
- Can be regenerated offline via CLI

---

## 4. Integration with Existing Services

### 4.1 SeoService Integration

**Reuse:** `SeoService.build_structured_data()` unchanged

**Route handler enrichment:**

```python
# In learning route handler:
article = article_service.get_article_by_slug(slug)

metadata = {
    "title": article["title"],
    "description": article["description"],
    "canonical": f"{PRODUCTION_BASE_URL}{article['canonical']}",
    "og_url": f"{PRODUCTION_BASE_URL}{article['canonical']}",
    "og_image": article.get("og_image", f"{PRODUCTION_BASE_URL}/static/images/og-default.png"),
    "og_image_alt": article.get("og_image_alt", article["title"]),
    "keywords": ", ".join(article.get("keywords", [])),
    "author": article.get("author", "Converigo"),
    "robots": "index,follow",
}

structured_data = seo_service.build_structured_data(
    request,
    page_type="blog_article",  # Reuse existing page type
    page_data={
        "headline": article["title"],
        "description": article["description"],
        "url": article["canonical"],
        "breadcrumb": article.get("breadcrumb", []),  # Auto-generated or override
    },
)
```

**Structured data includes:**
- Article schema (title, description, author, date, breadcrumb)
- BreadcrumbList (navigation)
- FAQPage (if article.faq exists)
- Organization + WebSite context

### 4.2 InternalLinkService Integration

**Reuse:** `InternalLinkService.get_links_for_knowledge()` + new methods

**Enhancement:**

```python
# New method: get_links_for_article(article_slug)
# Returns: {related_converters, related_formats, related_comparisons, related_articles}

links = internal_link_service.get_links_for_article("getting-started")

# Returns:
{
    "related_converters": [
        {"slug": "pdf-to-jpg", "title": "...", "href": "...", "score": 0.9}
    ],
    "related_formats": [
        {"slug": "pdf", "title": "...", "href": "...", "score": 0.85}
    ],
    "related_articles": [
        {"slug": "what-are-formats", "title": "...", "href": "...", "score": 0.95}
    ],
    "related_comparisons": [...]
}
```

**Template rendering:**
- "Related Tools" section (related_converters)
- "Learn More" section (related_articles)
- "See Also" section (related_formats)
- Deduplication prevents link overload

### 4.3 Breadcrumb Generation

**Two modes:**

1. **Auto-generated** (default):
   ```python
   breadcrumb = [
       {"name": "Home", "url": "/"},
       {"name": "Learning", "url": "/learning"},
       {"name": article["category"], "url": f"/learning/categories/{category.lower()}"},
       {"name": article["title"], "url": f"/learning/{article['slug']}"},
   ]
   ```

2. **Override** (from article JSON):
   ```python
   # If article["breadcrumb_override"] exists, use that instead
   breadcrumb = article["breadcrumb_override"]
   ```

**Schema generation:**
- Passed to `seo_service._build_breadcrumb_list()`
- Automatic JSON-LD BreadcrumbList schema
- Appears in search results

---

## 5. Route Layer

### 5.1 Learning Routes

**File:** `app/routers/learning.py`

```python
@router.get("/learning", response_class=HTMLResponse)
async def learning_index(request: Request) -> HTMLResponse:
    """Learning center homepage."""
    # Load article index
    # Get featured articles
    # Group by category
    # Render learning_index.html
    # Pass: request, locale, categories, featured, structured_data

@router.get("/learning/categories", response_class=HTMLResponse)
async def learning_categories(request: Request) -> HTMLResponse:
    """All categories."""
    # Load index
    # Get all categories with article counts
    # Render learning_categories.html

@router.get("/learning/categories/{category}", response_class=HTMLResponse)
async def learning_category(request: Request, category: str) -> HTMLResponse:
    """Articles in category."""
    # Load articles_by_category(category)
    # Sort by order/date_published
    # Render learning_category.html
    # Pass: request, category, articles, breadcrumb, structured_data

@router.get("/learning/topics/{topic}", response_class=HTMLResponse)
async def learning_topic(request: Request, topic: str) -> HTMLResponse:
    """Articles by topic."""
    # Load articles_by_topic(topic)
    # Render learning_topic.html
    # Pass: request, topic, articles, breadcrumb, structured_data

@router.get("/learning/{slug}", response_class=HTMLResponse)
async def learning_article(request: Request, slug: str) -> HTMLResponse:
    """Individual article."""
    # Load article_service.get_article_by_slug(slug)
    # If not found → HTTPException(404)
    # Generate metadata + breadcrumb + structured_data
    # Get internal links via link_service
    # Render learning_article.html
    # Pass: request, article, links, breadcrumb, structured_data
```

### 5.2 Context Structure

```python
context = {
    "request": request,
    "locale": locale_data,
    "t": t,  # translation function
    "meta": {
        "title": article["title"],
        "description": article["description"],
        "canonical": f"{PRODUCTION_BASE_URL}{article['canonical']}",
        "og_image": article.get("og_image", "..."),
        "keywords": ", ".join(article.get("keywords", [])),
        "author": article.get("author", "Converigo"),
        "robots": "index,follow",
    },
    "article": {
        "slug": article["slug"],
        "title": article["title"],
        "description": article["description"],
        "category": article["category"],
        "read_time_minutes": article["read_time_minutes"],
        "date_published": article["date_published"],
        "date_modified": article.get("date_modified"),
        "author": article.get("author", "Converigo"),
        "sections": article.get("sections", []),
        "faq": article.get("faq", []),
        "call_to_action": article.get("call_to_action"),
        "related_tools": article.get("related_tools", []),
    },
    "breadcrumb": breadcrumb,
    "structured_data": structured_data,
    "internal_links": internal_links,
    "year": datetime.utcnow().year,
}
```

---

## 6. Template Layer

### 6.1 Template Hierarchy

```
layouts/base.html (existing, reuse)

pages/
├── learning_index.html           (NEW - collection homepage)
├── learning_categories.html      (NEW - category index)
├── learning_category.html        (NEW - articles in category)
├── learning_topic.html           (NEW - articles with topic)
└── learning_article.html         (NEW - individual article)

components/
├── learning_breadcrumb.html      (NEW, optional - reuse hub_page.html pattern)
├── article_card.html             (NEW, optional - reuse converter_card.html pattern)
├── related_content_section.html  (NEW - related tools, articles, etc.)
└── article_toc.html              (NEW, optional - table of contents from sections)

partials/
├── seo_meta.html                 (existing, reuse unchanged)
├── structured_data.html          (existing, reuse unchanged)
└── [others]
```

### 6.2 Article Template (learning_article.html)

```html
{% extends "layouts/base.html" %}

{% block title %}{{ meta.title }}{% endblock %}

{% block content %}
{% include "components/header.html" %}

<main class="main" role="main">
  <!-- Breadcrumb (reuse hub_page.html pattern) -->
  <nav aria-label="Breadcrumb">
    <ol class="breadcrumb">
      {% for item in breadcrumb %}
      <li>
        <a href="{{ item.url }}">{{ item.name }}</a>
      </li>
      {% endfor %}
    </ol>
  </nav>

  <!-- Article Hero -->
  <section class="hero section">
    <div class="container hero-inner">
      <div class="hero-copy">
        <span class="eyebrow">{{ article.category }}</span>
        <h1 class="hero-title">{{ article.title }}</h1>
        <p class="hero-sub">{{ article.description }}</p>
        <div class="article-meta">
          <span class="author">By {{ article.author }}</span>
          <span class="date">{{ article.date_published | format_date }}</span>
          <span class="read-time">{{ article.read_time_minutes }} min read</span>
        </div>
      </div>
    </div>
  </section>

  <!-- Article Content -->
  <section class="article section">
    <div class="container">
      <article class="article-body">
        {% for section in article.sections %}
        <section id="{{ section.id }}" class="article-section">
          <h2>{{ section.title }}</h2>
          {{ section.content | safe }}
          {% for subsection in section.get('subsections', []) %}
          <section id="{{ subsection.id }}" class="article-subsection">
            <h3>{{ subsection.title }}</h3>
            {{ subsection.content | safe }}
          </section>
          {% endfor %}
        </section>
        {% endfor %}
      </article>

      <!-- CTA (if exists) -->
      {% if article.call_to_action %}
      <section class="cta-section">
        <p>{{ article.call_to_action.text }}</p>
        <a href="{{ article.call_to_action.url }}" class="btn btn-primary">
          {{ article.call_to_action.button_text }}
        </a>
      </section>
      {% endif %}

      <!-- FAQ -->
      {% if article.faq %}
      <section class="faq-section">
        <h2>Frequently Asked Questions</h2>
        {% for item in article.faq %}
        <details class="faq-item">
          <summary>{{ item.question }}</summary>
          <p>{{ item.answer }}</p>
        </details>
        {% endfor %}
      </section>
      {% endif %}

      <!-- Related Tools (from InternalLinkService) -->
      {% if internal_links.related_converters %}
      <section class="related-tools-section">
        <h3>Related Tools</h3>
        <div class="cards-grid">
          {% for tool in internal_links.related_converters | slice(3) %}
          <article class="card">
            <h4><a href="{{ tool.href }}">{{ tool.title }}</a></h4>
            <p>{{ tool.description }}</p>
          </article>
          {% endfor %}
        </div>
      </section>
      {% endif %}

      <!-- Related Articles -->
      {% if internal_links.related_articles %}
      <section class="related-articles-section">
        <h3>Learn More</h3>
        <ul>
          {% for article_link in internal_links.related_articles | slice(5) %}
          <li><a href="/learning/{{ article_link.slug }}">{{ article_link.title }}</a></li>
          {% endfor %}
        </ul>
      </section>
      {% endif %}
    </div>
  </section>
</main>

{% include "components/footer.html" %}
{% endblock %}
```

### 6.3 Collection Template (learning_index.html)

```html
{% extends "layouts/base.html" %}

{% block title %}Learning Center | {{ meta.title }}{% endblock %}

{% block content %}
{% include "components/header.html" %}

<main class="main" role="main">
  <section class="hero section">
    <div class="container hero-inner">
      <div class="hero-copy">
        <span class="eyebrow">Learning Center</span>
        <h1 class="hero-title">Learn File Conversion Fundamentals</h1>
        <p class="hero-sub">Guides, tutorials, and best practices for file conversion</p>
      </div>
    </div>
  </section>

  <!-- Featured Articles -->
  {% if featured %}
  <section class="featured section">
    <div class="container">
      <h2>Featured Articles</h2>
      <div class="cards-grid">
        {% for article in featured | slice(3) %}
        <article class="card">
          <p class="eyebrow">{{ article.category }}</p>
          <h3><a href="/learning/{{ article.slug }}">{{ article.title }}</a></h3>
          <p>{{ article.description }}</p>
          <a href="/learning/{{ article.slug }}">Read Article</a>
        </article>
        {% endfor %}
      </div>
    </div>
  </section>
  {% endif %}

  <!-- Categories -->
  {% if categories %}
  <section class="categories section section-white">
    <div class="container">
      <h2>Browse by Category</h2>
      <div class="categories-grid">
        {% for category in categories %}
        <a href="/learning/categories/{{ category.slug }}" class="category-card">
          <h3>{{ category.name }}</h3>
          <p>{{ category.count }} articles</p>
        </a>
        {% endfor %}
      </div>
    </div>
  </section>
  {% endif %}
</main>

{% include "components/footer.html" %}
{% endblock %}
```

---

## 7. URL Structure

### 7.1 Learning Center URLs

```
/learning                                  (Homepage - featured + categories)
/learning/categories                       (All categories)
/learning/categories/{category}            (Articles in category)
/learning/topics/{topic}                   (Articles by topic tag)
/learning/{slug}                           (Individual article)
/learning/search?q={query}                 (Search results - future feature)
/learning/sitemap.xml                      (Sitemap - for SEO crawlers)
```

**URL-to-File Mapping:**
```
/learning/{slug} → app/data/articles/{category}/{slug}.json

Example:
/learning/getting-started-with-file-conversion → 
  app/data/articles/fundamentals/getting-started-with-file-conversion.json
```

**Category URLs:**
```
/learning/categories/fundamentals
/learning/categories/guides
/learning/categories/comparisons
/learning/categories/troubleshooting
/learning/categories/format-specific
```

---

## 8. Sitemap Integration

### 8.1 Learning Center Sitemap

**Extend:** `SeoService._build_blog_entries()` to include learning articles

```python
def _build_learning_entries(self, base_url: str) -> list[dict[str, str]]:
    """Build sitemap entries for learning center articles."""
    today = datetime.utcnow().date().isoformat()
    
    index = article_index_service.get_index()
    entries = []
    
    # Add learning homepage
    entries.append({
        "loc": f"{base_url}/learning",
        "lastmod": today,
    })
    
    # Add category pages
    for category in index["by_category"].keys():
        entries.append({
            "loc": f"{base_url}/learning/categories/{category.lower()}",
            "lastmod": today,
        })
    
    # Add articles (use date_modified or date_published)
    for article in index["all_articles"]:
        date = article.get("date_modified", article.get("date_published", today))
        entries.append({
            "loc": f"{base_url}/learning/{article['slug']}",
            "lastmod": date,
        })
    
    return entries
```

**Result:** `/sitemap.xml` includes:
- `/learning` (homepage)
- `/learning/categories/{category}` (category pages)
- `/learning/{slug}` (all articles)

---

## 9. Discovery & Search

### 9.1 Index-Based Discovery

**Query patterns:**

```python
# Get featured articles for homepage
featured = index["featured_articles"]

# Get all articles by category
fundamentals = index["by_category"]["Fundamentals"]["articles"]

# Get articles by topic
basics = index["by_topic"]["basics"]

# Get articles related to a format
pdf_articles = index["related_formats"]["pdf"]

# Get articles related to a converter
pdf_to_jpg_articles = index["related_converters"]["pdf-to-jpg"]
```

### 9.2 Search Implementation (Future)

**Proposed:** Full-text search via Elasticsearch/Meilisearch

**Interim:** Database search on `title`, `description`, `keywords` fields

---

## 10. CLI Tools

### 10.1 Article Validation CLI

```bash
# Validate all articles
python -m app.services.article_service validate

# Validate specific article
python -m app.services.article_service validate --slug getting-started

# Validate specific category
python -m app.services.article_service validate --category fundamentals
```

### 10.2 Index Generation CLI

```bash
# Generate/regenerate index
python -m app.services.article_index_service regenerate

# Show index statistics
python -m app.services.article_index_service stats
```

### 10.3 Article Creation Template

```bash
# Create new article from template
python -m app.services.article_service create \
  --slug my-article \
  --title "My Article Title" \
  --category fundamentals \
  --template default
```

---

## 11. Data Pipeline

### 11.1 Article Lifecycle

```
1. Create article JSON in app/data/articles/{category}/{slug}.json
   ↓
2. Run validation: python -m app.services.article_service validate
   ↓
3. Regenerate index: python -m app.services.article_index_service regenerate
   ↓
4. URL available: /learning/{slug}
   ↓
5. Appears in sitemap.xml automatically
   ↓
6. Related content auto-linked via InternalLinkService
   ↓
7. Structured data auto-generated via SeoService
```

### 11.2 Update Workflow

```
1. Edit article JSON (update content, date_modified, etc.)
   ↓
2. Run validation
   ↓
3. Regenerate index (updates related_* mappings)
   ↓
4. Changes live at next page load
```

---

## 12. Reuse Summary

| Component | Source | Usage | Modification |
|-----------|--------|-------|--------------|
| **Article loading** | FormatKnowledgeService pattern | ArticleService | New service |
| **Route structure** | /blog routes | /learning routes | New routes |
| **Metadata generation** | SeoService.build_tool_meta() | SeoService (same) | None |
| **Structured data** | SeoService.build_structured_data() | SeoService (same) | None |
| **Breadcrumbs** | hub_page.html component | learning_article.html | Reused, no changes |
| **Layouts** | layouts/base.html | All learning pages | None |
| **SEO partials** | seo_meta.html, structured_data.html | All learning pages | None |
| **Internal links** | InternalLinkService pattern | InternalLinkService + new get_links_for_article() | Enhancement |
| **Localization** | LanguageService | Learning routes | None |
| **Sitemap** | SeoService._build_blog_entries() | SeoService._build_learning_entries() | Extension |

---

## 13. File Count & Storage

### 13.1 Initial Content

**Projected articles:** 20-30 for MVP

```
Fundamentals: 3-4 articles (~50KB)
Guides: 5-6 articles (~100KB)
Comparisons: 5-6 articles (~100KB)
Troubleshooting: 3-4 articles (~60KB)
Format-Specific: 4-5 articles (~80KB)

Total: ~25 articles, ~390KB
```

**Scalability:**
- Format supports unlimited articles
- Index query time O(1) for most operations
- JSON parsing handles thousands of articles
- No database needed for MVP

---

## 14. Schema Validation Example

### 14.1 Required Fields Check

```python
ARTICLE_REQUIRED_FIELDS = [
    "slug",
    "title",
    "description",
    "category",
    "topics",
    "author",
    "date_published",
    "read_time_minutes",
    "keywords",
    "seo_keywords",
    "sections",
    "faq",
]

ARTICLE_OPTIONAL_FIELDS = [
    "date_modified",
    "og_image",
    "og_image_alt",
    "canonical",
    "featured",
    "order",
    "related_formats",
    "related_converters",
    "related_articles",
    "call_to_action",
    "related_tools",
    "breadcrumb_override",
]

ARTICLE_FIELD_TYPES = {
    "slug": str,
    "title": str,
    "description": str,
    "category": str,
    "topics": list,
    "author": str,
    "date_published": str,  # ISO 8601
    "read_time_minutes": int,
    "keywords": list,
    "seo_keywords": list,
    "sections": list,
    "faq": list,
    "featured": bool,
    "order": int,
}
```

---

## 15. Migration Path (Future)

### 15.1 From Hardcoded Map to JSON

**Phase 1 (Current):** Hardcoded article map in route

```python
article_map = {
    "getting-started": {...},
    "what-are-formats": {...},
}
```

**Phase 2 (Proposed):** JSON files + ArticleService

```python
article = article_service.get_article_by_slug("getting-started")
```

**Migration steps:**
1. Create app/data/articles/ directory structure
2. Convert hardcoded map entries to JSON files
3. Deploy ArticleService
4. Update route handlers to use ArticleService
5. Delete old article_map from route file
6. Regenerate index

**Backward compatibility:** URLs remain `/learning/{slug}` (unchanged)

---

## 16. Comparison: Hardcoded vs JSON

| Aspect | Hardcoded Map | JSON Files |
|--------|---------------|----|
| **Scalability** | ~50 articles (file size) | Unlimited |
| **Editing** | Requires code change + deployment | Update JSON + regenerate index |
| **Versioning** | Changes in Git history | Article diffs in Git |
| **Search** | Manual implementation | Index-based queries |
| **Discovery** | Hardcoded categories | Automatic via topics, formats, converters |
| **Maintenance** | Single Python file | Multiple JSON files (organized) |
| **API Integration** | Not suitable | Easy JSON export for API |

**Recommendation for MVP:** Start with JSON architecture. It's more maintainable and aligns with existing data patterns (formats, converters).

---

## 17. Example Article File

**File:** `app/data/articles/fundamentals/getting-started-with-file-conversion.json`

```json
{
  "slug": "getting-started-with-file-conversion",
  "title": "Getting Started with File Conversion: A Beginner's Guide",
  "description": "Learn the fundamentals of file conversion, why you might need it, and how to use Converigo to convert your first file in just a few minutes.",
  "category": "Fundamentals",
  "topics": ["basics", "conversion-101", "beginner-guide", "step-by-step"],
  "author": "Converigo",
  "date_published": "2026-07-01",
  "date_modified": "2026-07-15",
  "read_time_minutes": 8,
  "keywords": ["file conversion basics", "beginner guide", "how to convert files"],
  "seo_keywords": ["file conversion", "convert files online", "file formats"],
  "og_image": "/static/images/og-getting-started.png",
  "og_image_alt": "Getting started with file conversion guide",
  "featured": true,
  "order": 1,
  "related_formats": ["pdf", "jpg", "mp3"],
  "related_converters": ["pdf-to-jpg", "jpg-to-png"],
  "related_articles": ["what-are-file-formats", "why-convert-files"],
  "sections": [
    {
      "id": "what-is-file-conversion",
      "title": "What Is File Conversion?",
      "content": "<p>File conversion is the process of transforming a file from one format to another...</p>"
    },
    {
      "id": "why-convert-files",
      "title": "Why Would You Convert a File?",
      "content": "<p>There are many practical reasons to convert files...</p>"
    },
    {
      "id": "quick-start",
      "title": "Your First Conversion (Quick Start)",
      "content": "<p>Ready to try it? Here's how simple it is...</p>",
      "subsections": [
        {
          "id": "step-1",
          "title": "Step 1: Choose Your File",
          "content": "<p>Click the upload button...</p>"
        },
        {
          "id": "step-2",
          "title": "Step 2: Select Output Format",
          "content": "<p>Choose the format you want...</p>"
        }
      ]
    }
  ],
  "faq": [
    {
      "question": "Is file conversion safe?",
      "answer": "Yes, Converigo uses secure encryption to protect your files during conversion. Files are deleted within hours of conversion."
    },
    {
      "question": "How long does conversion take?",
      "answer": "Most conversions complete within seconds, depending on file size and type."
    }
  ],
  "call_to_action": {
    "text": "Ready to convert your first file?",
    "url": "/tools/pdf-to-jpg",
    "button_text": "Try Converigo Now"
  },
  "related_tools": [
    {
      "slug": "pdf-to-jpg",
      "title": "PDF to JPG Converter",
      "description": "Convert PDF files to JPG images",
      "href": "/pdf-to-jpg"
    },
    {
      "slug": "jpg-to-png",
      "title": "JPG to PNG Converter",
      "description": "Convert JPG images to PNG format",
      "href": "/jpg-to-png"
    }
  ]
}
```

---

## Summary

**Learning Center Data Architecture:** JSON-file-based with automatic discovery and full SEO integration

**Key Design Principles:**
1. **Reuse:** Existing SeoService, InternalLinkService, templates, layouts
2. **Scalability:** JSON files instead of hardcoded maps
3. **Discovery:** Index-based queries for categories, topics, formats, converters
4. **Consistency:** Same metadata structure as blog articles
5. **Maintainability:** Separate concerns (data, service, route, template)

**New Components:**
- `ArticleService` – Load/validate individual articles
- `ArticleIndexService` – Generate searchable index
- Route handlers in `learning.py` – Same pattern as blog
- Templates in `pages/learning_*.html` – Reuse existing layouts
- Index file `_index.json` – Auto-generated, enables fast discovery

**No modifications needed:**
- SeoService
- InternalLinkService
- Existing templates/layouts
- Breadcrumb components
- Structured data generation

**Scaling:** Supports hundreds of articles; can migrate to database/search engine later without URL changes.

---

## Appendix: File References

### New Files to Create (Not Implemented)
- `app/services/article_service.py` – Article loading and validation
- `app/services/article_index_service.py` – Index generation
- `app/routers/learning.py` – Route handlers
- `app/templates/pages/learning_*.html` – Article templates
- `app/data/articles/` – Article storage directory

### Files to Reuse (No Changes)
- `app/services/seo_service.py`
- `app/services/internal_link_service.py`
- `app/templates/layouts/base.html`
- `app/templates/partials/seo_meta.html`
- `app/templates/partials/structured_data.html`

### Example Article Directory
- `app/data/articles/fundamentals/getting-started-with-file-conversion.json`
- `app/data/articles/guides/image-optimization.json`
- `app/data/articles/comparisons/png-vs-jpg-explained.json`
- `app/data/articles/_index.json` (generated)
- `app/data/articles/_schema.json` (schema definition)
