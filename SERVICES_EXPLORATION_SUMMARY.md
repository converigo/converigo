# Services Directory Exploration

## 1. Complete List of Services

```
authority_service.py              - Format authority & metadata
cleanup_service.py                - Cleanup operations
comparison_service.py             - Format comparison pages
conversion_manager.py             - Plugin registry & conversion orchestration
conversion_service.py             - Conversion orchestration
converter_data_service.py         - Converter data loading & caching
converter_registry_service.py     - Contract loading & validation ⭐
growth_dashboard_service.py       - Growth metrics dashboard
hub_page_service.py               - Hub page generation
hub_service.py                    - Hub content aggregation
knowledge_schema.py               - Knowledge structure definitions
knowledge_service.py              - Educational content generation ⭐
landing_service.py                - Landing page builder
language_manager.py               - Language/locale management
language_service.py               - Localization service
plugin_validation_service.py      - Plugin validation
production_audit_service.py       - Production audit aggregation
programmatic_seo_service.py       - SEO content generation
recommendation_service.py         - Recommendation generation
related_converter_service.py      - Related converter discovery ⭐
seo_service.py                    - SEO metadata & utilities
sitemap_service.py                - Sitemap generation
upload_service.py                 - File upload handling
```

---

## 2. Key Services Deep Dive

### A. ConverterRegistryService ⭐
**File:** [app/services/converter_registry_service.py](app/services/converter_registry_service.py)

**Purpose:** Load, validate, and provide access to converter contracts (JSON files)

#### Class Definition
```python
class ConverterRegistryService:
    REQUIRED_FIELDS = [
        "id", "slug", "name", "category", "description",
        "input_formats", "output_formats", "accepted_mime_types",
        "max_upload_size", "conversion_engine", "landing_path",
        "canonical_url", "seo_status", "schema_status", "faq_status",
        "regression_sample", "supported_platforms", "lifecycle_status",
    ]
    VALID_LIFECYCLE_STATUSES = {"active", "deprecated", "beta"}

    def __init__(self, contracts_dir: Path | str) -> None
```

#### Key Methods
| Method | Purpose | Return Type |
|--------|---------|-------------|
| `list_all()` | Get all contracts | `list[dict[str, Any]]` |
| `get_by_slug(slug)` | Lookup by slug | `dict[str, Any] \| None` |
| `get_by_id(id_)` | Lookup by ID | `dict[str, Any] \| None` |
| `get_by_category(category)` | Get all in category | `list[dict[str, Any]]` |
| `get_active()` | Get active contracts only | `list[dict[str, Any]]` |
| `get_beta()` | Get beta contracts only | `list[dict[str, Any]]` |

#### Instantiation Pattern
```python
from app.services.converter_registry_service import ConverterRegistryService

# Simplest: directory contains .contract.json files
registry = ConverterRegistryService("app/data/converters")

# Access contracts
all_contracts = registry.list_all()
contract = registry.get_by_slug("png-to-jpg")
active = registry.get_active()
```

#### Dependencies
- **Internal:** None
- **External:** `pathlib.Path`, `json`, `typing`

#### Data Structures Returned
```python
contract = {
    "id": "conv-001",
    "slug": "png-to-jpg",
    "name": "PNG to JPG Converter",
    "category": "image",
    "description": "Convert PNG images to JPG format",
    "input_formats": ["PNG"],
    "output_formats": ["JPG"],
    "accepted_mime_types": ["image/png"],
    "max_upload_size": 52428800,  # 50 MB
    "conversion_engine": "PIL",
    "landing_path": "/tools/png-to-jpg",
    "canonical_url": "https://converigo.com/png-to-jpg",
    "seo_status": "complete",
    "schema_status": "complete",
    "faq_status": "complete",
    "regression_sample": "sample.png",
    "supported_platforms": ["web", "api"],
    "lifecycle_status": "active"  # or "deprecated", "beta"
}
```

#### Key Features
- ✅ Loads `.contract.json` files from directory
- ✅ Validates contracts for required fields
- ✅ Prevents duplicate IDs and slugs
- ✅ Error handling: `ConverterRegistryError` on validation failure
- ✅ Thread-safe (data loaded at initialization)

---

### B. RelatedConverterService ⭐
**File:** [app/services/related_converter_service.py](app/services/related_converter_service.py)

**Purpose:** Discover and score related converters based on format matching

#### Class Definition
```python
class RelatedConverterService:
    def __init__(self, converter_data_service: ConverterDataService) -> None:
        self.converter_data_service = converter_data_service
```

#### Key Methods
| Method | Purpose | Return Type |
|--------|---------|-------------|
| `get_related_converters(converter, limit=4)` | Get scored related converters | `list[dict[str, Any]]` |
| `_infer_cluster(converter)` | Infer format family | `str` |
| `_infer_output_category(converter)` | Infer output category | `str` |

#### Instantiation Pattern
```python
from app.services.related_converter_service import RelatedConverterService
from app.services.converter_data_service import ConverterDataService

# Requires a ConverterDataService instance
data_service = ConverterDataService("app/data/converters")
related_service = RelatedConverterService(data_service)

# Get related converters
converter = data_service.load_converter_by_slug("png-to-jpg")
related = related_service.get_related_converters(converter, limit=4)
```

#### Dependencies
- **Internal:** `ConverterDataService` (injected)
- **External:** `typing`

#### Data Structures Returned
```python
related_converters = [
    {
        "slug": "jpg-to-png",
        "title": "JPG to PNG",
        "description": "Convert JPG images to PNG format",
        "source": "jpg",
        "target": "png",
        "category": "image",
        "cluster": "image",
        "match_reasons": {
            "same_input": False,
            "same_output_category": True,
            "same_cluster": True,
        },
        "_score": 5  # internal scoring (higher = better match)
    },
    # ... up to `limit` items, sorted by score then title
]
```

#### Scoring Algorithm
| Match Type | Score | Weight |
|------------|-------|--------|
| Same input format | +4 | Highest |
| Same output category | +3 | High |
| Same cluster (format family) | +2 | Medium |
| Same target format | +1 | Bonus |

#### Helper Methods
```python
def _infer_cluster(converter) -> str:
    # Returns: "video-audio", "image", "audio", "video", "document", or category

def _infer_output_category(converter) -> str:
    # Analyzes target format: "audio", "image", "video", "document", or category

def _is_audio(value) -> bool:      # mp3, wav, flac, ogg, m4a, aac, opus
def _is_image(value) -> bool:      # jpg, jpeg, png, webp, bmp, gif, ico, svg
def _is_video(value) -> bool:      # mp4, mov, avi, mkv, webm, mpeg, mpg, wmv
def _is_document(value) -> bool:   # pdf, doc, docx, ppt, pptx, xls, xlsx, txt, odt, rtf
```

#### Key Features
- ✅ Scores matches by relevance
- ✅ Falls back to any converter if insufficient matches
- ✅ Deduplicates results by slug
- ✅ Infers format families automatically
- ✅ Returns match reasons for transparency

---

### C. KnowledgeService ⭐
**File:** [app/services/knowledge_service.py](app/services/knowledge_service.py)

**Purpose:** Generate deterministic educational content payloads from converter contracts

#### Class Definition
```python
class KnowledgeService:
    """Generate deterministic educational Knowledge Objects from converter contracts."""
    
    REQUIRED_SECTIONS = {
        "slug", "overview", "source_format", "target_format",
        "advantages", "limitations", "use_cases", "faq",
        "related_converters", "internal_links", "hub_reference",
        "what_is_source", "what_is_target", "differences",
        "best_practices", "common_mistakes", "tips", "faq_enrichment",
        "glossary"
    }

    def __init__(self, contracts_dir: str | Any) -> None:
        self.registry = ConverterRegistryService(contracts_dir)
```

#### Key Methods
| Method | Purpose | Return Type |
|--------|---------|-------------|
| `generate_payload(contract)` | Build complete knowledge payload | `dict[str, Any]` |
| `generate_all()` | Build payloads for all active converters | `dict[str, dict[str, Any]]` |
| `validate_payload(payload)` | Validate required sections | `None` (raises ValueError if invalid) |

#### Instantiation Pattern
```python
from app.services.knowledge_service import KnowledgeService

# Initialize with contracts directory
knowledge = KnowledgeService("app/data/converters")

# Generate payload for single converter
contract = {...}  # from registry
payload = knowledge.generate_payload(contract)

# Validate it
knowledge.validate_payload(payload)

# Or generate all at once
all_payloads = knowledge.generate_all()  # Returns {slug: payload}
```

#### Dependencies
- **Internal:** `ConverterRegistryService`
- **External:** `typing`

#### Data Structures Returned
```python
payload = {
    "slug": "png-to-jpg",
    
    # Basic sections
    "overview": {
        "title": "Overview of PNG to JPG Converter",
        "text": "Use this converter to transform PNG files into JPG output..."
    },
    
    "source_format": {
        "title": "Source format",
        "format": "PNG",
        "text": "PNG is the input format used by this converter."
    },
    
    "target_format": {
        "title": "Target format",
        "format": "JPG",
        "text": "JPG is the output format produced by this converter."
    },
    
    # List sections
    "advantages": [
        {"title": "Fast conversion", "text": "Convert png files to jpg with quick..."},
        {"title": "Wide compatibility", "text": "..."}
    ],
    
    "limitations": [
        {"title": "Compression loss", "text": "..."}
    ],
    
    "use_cases": [
        {"title": "Web optimization", "text": "..."}
    ],
    
    "best_practices": [
        {"title": "Use a clean source file", "text": "..."}
    ],
    
    "common_mistakes": [
        {"title": "Uploading the wrong file", "text": "..."}
    ],
    
    "tips": [
        {"title": "Keep a backup", "text": "..."}
    ],
    
    "faq": [
        {"question": "How long does conversion take?", "answer": "..."}
    ],
    
    "faq_enrichment": [
        # Same as faq
    ],
    
    "glossary": [
        {"term": "PNG", "definition": "Portable Network Graphics format..."},
        {"term": "JPG", "definition": "Joint Photographic Experts Group format..."}
    ],
    
    "differences": [
        {"title": "Format structure", "text": "PNG and JPG differ in how they..."},
        {"title": "Use case", "text": "PNG is usually the starting point..."}
    ],
    
    "what_is_source": {
        "title": "What is PNG?",
        "text": "PNG is the source format used in the PNG to JPG conversion workflow."
    },
    
    "what_is_target": {
        "title": "What is JPG?",
        "text": "JPG is the output format produced by the PNG to JPG process."
    },
    
    # Complex sections
    "related_converters": [
        {
            "slug": "jpg-to-png",
            "title": "JPG to PNG",
            "description": "Convert JPG images to PNG format",
            "href": "/tools/jpg-to-png"
        }
    ],
    
    "internal_links": {
        "title": "Related resources",
        "items": [
            {
                "title": "Open the PNG to JPG converter",
                "href": "/tools/png-to-jpg",
                "description": "Start the conversion process on the converter landing page."
            },
            {
                "title": "Image Conversion Hub",
                "href": "/image-converter",
                "description": "Explore the hub for image conversion tools."
            }
        ]
    },
    
    "hub_reference": {
        "title": "Image Conversion Hub",
        "href": "/image-converter",
        "description": "Convert images for web use, editing, compatibility, and sharing."
    }
}
```

#### Hub Categories
```python
HUB_SLUG_BY_CATEGORY = {
    "video": "video-converter",
    "image": "image-converter",
    "pdf": "pdf-tools",
    "document": "pdf-tools",
    "audio": "audio-tools",
    "archive": "archive-tools",
}
```

#### Key Features
- ✅ Deterministic content generation (same input = same output)
- ✅ Validates all required sections
- ✅ Integrates related converters automatically
- ✅ Builds hub references by category
- ✅ Comprehensive FAQ, glossary, best practices
- ✅ Friendly format: title + text pairs, lists with descriptions

---

### D. ComparisonService ⭐
**File:** [app/services/comparison_service.py](app/services/comparison_service.py)

**Purpose:** Build comparison pages for format-pair pages (e.g., PNG vs JPG)

#### Class Definition
```python
class ComparisonService:
    """Build comparison landing-page content for format-pair pages."""

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self.seo_service = SeoService(self.contracts_dir)
        self.landing_builder = LandingPageBuilder(self.seo_service, self.converter_data_service)
        self.authority_service = AuthorityService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.related_service = RelatedConverterService(self.converter_data_service)
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.programmatic_seo_service = ProgrammaticSEOService(self.contracts_dir)
```

#### Key Methods
| Method | Purpose | Return Type |
|--------|---------|-------------|
| `build_payload(slug)` | Build complete comparison payload | `dict[str, Any]` |
| `render_context(request, slug)` | Build template context | `dict[str, Any]` |

#### Instantiation Pattern
```python
from app.services.comparison_service import ComparisonService

# Initialize (auto-creates dependencies)
comparison = ComparisonService("app/data/converters")

# Build payload for specific comparison
payload = comparison.build_payload("pdf-vs-docx")

# Or render with request context
context = comparison.render_context(request, "png-vs-jpg")
```

#### Dependencies (Auto-Injected)
- `ConverterDataService`
- `SeoService`
- `LandingPageBuilder`
- `AuthorityService`
- `KnowledgeService`
- `RelatedConverterService`
- `ConverterRegistryService`
- `ProgrammaticSEOService`

#### Data Structures Returned
```python
payload = {
    "slug": "pdf-vs-docx",
    "h1": "PDF vs DOCX",
    "seo_title": "PDF vs DOCX | Converigo",
    "meta_description": "Compare PDF and DOCX to choose the best format...",
    
    "introduction": {
        "title": "PDF vs DOCX explained",
        "text": "Choose between PDF and DOCX based on compatibility, quality..."
    },
    
    "winner_summary": {
        "title": "Winner summary",
        "text": "PDF is often better when you need broad compatibility..."
    },
    
    "comparison_table": [
        {"feature": "Best for", "source": "PDF files", "target": "DOCX files"},
        {"feature": "Compression", "source": "Low", "target": "High"},
        {"feature": "Compatibility", "source": "Universal", "target": "Office focused"}
    ],
    
    "advantages": [
        {"title": "PDF strengths", "text": "PDF is strong for broad compatibility..."},
        {"title": "DOCX strengths", "text": "DOCX is strong for editable content..."}
    ],
    
    "disadvantages": [
        {"title": "PDF limitations", "text": "PDF may be less flexible for editing..."},
        {"title": "DOCX limitations", "text": "DOCX may be less ideal for..."}
    ],
    
    "best_use_cases": [
        {"title": "Use PDF when", "text": "You need the original PDF workflow..."},
        {"title": "Use DOCX when", "text": "You need the output DOCX workflow..."}
    ],
    
    "faq": [
        {"question": "Which is better for PDF workflows?", "answer": "Choose PDF..."},
        {"question": "Which is better for DOCX workflows?", "answer": "Choose DOCX..."}
    ],
    
    "related_converters": [
        {
            "slug": "pdf-to-excel",
            "title": "PDF to Excel",
            "description": "Convert PDFs to Excel spreadsheets",
            "href": "/tools/pdf-to-excel"
        }
    ],
    
    "related_formats": [
        {"title": "PDF format info", "description": "...", "href": "/formats/pdf"},
        {"title": "DOCX format info", "description": "...", "href": "/formats/docx"}
    ],
    
    "internal_links": {
        "title": "Related resources",
        "items": [...]
    },
    
    "breadcrumb": [
        {"name": "Home", "url": "/"},
        {"name": "PDF vs DOCX", "url": "/pdf-vs-docx"}
    ],
    
    "json_ld": {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "PDF vs DOCX | Converigo",
        "description": "Compare PDF and DOCX...",
        "url": "https://converigo.com/pdf-vs-docx",
        "breadcrumb": [...]
    },
    
    "meta": {
        "title": "PDF vs DOCX | Converigo",
        "description": "Compare PDF and DOCX to choose the best format...",
        "canonical": "https://converigo.com/pdf-vs-docx",
        "og_url": "https://converigo.com/pdf-vs-docx"
    }
}
```

#### Supported Comparisons
```python
_comparison_specs = {
    "pdf-vs-docx": {"title": "PDF vs DOCX", "source_format": "pdf", "target_format": "docx"},
    "png-vs-jpg": {"title": "PNG vs JPG", "source_format": "png", "target_format": "jpg"},
    "webp-vs-png": {"title": "WEBP vs PNG", "source_format": "webp", "target_format": "png"},
    "mp4-vs-mov": {"title": "MP4 vs MOV", "source_format": "mp4", "target_format": "mov"},
    "mp3-vs-wav": {"title": "MP3 vs WAV", "source_format": "mp3", "target_format": "wav"},
}
```

#### Key Features
- ✅ Orchestrates multiple services (composition pattern)
- ✅ Generates SEO-rich comparison pages
- ✅ Includes JSON-LD structured data
- ✅ Breadcrumb navigation
- ✅ Related converters and formats
- ✅ FAQ and comparison table
- ✅ Authority-based content about each format

---

## 3. Reusable Service Patterns

### Pattern 1: Registry Service (Read-Only Metadata)
**Used by:** ConverterRegistryService

✅ Loads data from files at initialization
✅ Validates structure
✅ Provides query methods (by slug, id, category)
✅ Immutable after init
✅ Throws custom exceptions on validation failure

```python
class RegistryService:
    def __init__(self, dir_path: Path | str):
        self._data = []
        self._load_and_validate()
    
    def get_by_slug(self, slug: str) -> dict | None:
        return self._find_one(lambda x: x["slug"] == slug)
    
    def list_all(self) -> list[dict]:
        return list(self._data)
```

---

### Pattern 2: Dependency-Injected Service (with Helper Service)
**Used by:** RelatedConverterService, ComparisonService

✅ Constructor accepts helper service(s)
✅ Composition over inheritance
✅ Methods consume and transform data from dependencies
✅ Testable (can mock dependencies)

```python
class CompositeService:
    def __init__(self, helper_service: HelperService) -> None:
        self.helper = helper_service
    
    def do_something(self, input_data):
        raw_data = self.helper.fetch(...)
        return self.transform(raw_data)
```

---

### Pattern 3: Multi-Dependency Service (Orchestrator)
**Used by:** ComparisonService, ProductionAuditService

✅ Auto-initializes all dependencies in `__init__`
✅ Each dependency is a separate service
✅ Orchestrates calls across services
✅ Combines results into higher-level payload

```python
class OrchestratorService:
    def __init__(self, contracts_dir):
        self.svc1 = ServiceOne(contracts_dir)
        self.svc2 = ServiceTwo(contracts_dir)
        self.svc3 = ServiceThree(self.svc2)  # Can depend on other services
    
    def build_complete_payload(self, input_key):
        data1 = self.svc1.get(input_key)
        data2 = self.svc2.get(input_key)
        data3 = self.svc3.process(data1, data2)
        return self.combine(data1, data2, data3)
```

---

### Pattern 4: Content Generation Service (Templating)
**Used by:** KnowledgeService

✅ Generates complex nested data structures
✅ Uses builder helper methods (\_build_*)
✅ Validates result against schema
✅ Deterministic (same input always = same output)

```python
class GeneratorService:
    REQUIRED_SECTIONS = {"field1", "field2", ...}
    
    def generate_payload(self, contract):
        payload = {
            "field1": self._build_field1(contract),
            "field2": self._build_field2(contract),
            ...
        }
        self.validate_payload(payload)
        return payload
    
    def _build_field1(self, contract):
        # Transform contract data into field1 structure
        pass
    
    def validate_payload(self, payload):
        missing = [f for f in self.REQUIRED_SECTIONS if f not in payload]
        if missing:
            raise ValueError(f"Missing: {missing}")
```

---

## 4. Usage Examples in Tests

### Example 1: Registry + Related Service
```python
def test_related_converter_service():
    data_svc = ConverterDataService(Path("app/data/converters"))
    related_svc = RelatedConverterService(data_svc)
    
    converter = data_svc.load_converter_by_slug("png-to-webp")
    related = related_svc.get_related_converters(converter, limit=4)
    
    assert len(related) >= 4
    assert converter["slug"] not in {item["slug"] for item in related}
```

### Example 2: Knowledge Service
```python
def test_knowledge_generation():
    knowledge = KnowledgeService(Path("app/data/converters"))
    
    for contract in knowledge.registry.get_active():
        payload = knowledge.generate_payload(contract)
        knowledge.validate_payload(payload)  # Raises if invalid
```

### Example 3: Comparison Service
```python
def test_comparison_payload():
    comparison = ComparisonService()
    payload = comparison.build_payload("pdf-vs-docx")
    
    assert payload["slug"] == "pdf-vs-docx"
    assert "comparison_table" in payload
    assert "json_ld" in payload
```

---

## 5. Dependency Injection Map

```
ConverterDataService
├── RelatedConverterService
├── ComparisonService (uses this)
├── LandingPageBuilder
└── HubService

ConverterRegistryService
├── KnowledgeService
├── ComparisonService
├── SeoService
├── AuthorityService
└── ProductionAuditService

SeoService
├── ComparisonService
├── LandingPageBuilder
└── ProgrammaticSEOService

AuthorityService
└── ComparisonService

KnowledgeService
└── ComparisonService

ComparisonService (Orchestrator)
├── ConverterDataService
├── SeoService
├── LandingPageBuilder
├── AuthorityService
├── KnowledgeService
├── RelatedConverterService
├── ConverterRegistryService
└── ProgrammaticSEOService
```

---

## 6. Recommendations for InternalLinkService

Based on these patterns:

1. **Decide: Registry vs Composer**
   - If building internal link metadata → Registry pattern (load from files)
   - If orchestrating link discovery → Composer pattern (inject services)

2. **Inject these services:**
   - `ConverterRegistryService` (to list converters)
   - `ConverterDataService` (to get converter details)
   - Possibly `KnowledgeService` (if linking to knowledge content)

3. **Return structure:**
   ```python
   internal_link = {
       "title": str,           # Display text
       "href": str,            # URL path
       "description": str,     # Brief explanation
       "relevance_score": int, # Optional: 0-100 relevance
       "type": str,            # "converter", "hub", "format", "blog"
   }
   ```

4. **Methods to implement:**
   - `get_links_for_converter(converter)` → list of internal links
   - `get_links_for_format(format_name)` → list of related format links
   - `get_hub_link(category)` → hub page link
   - `discover_contextual_links(content)` → infer links from content

5. **Validation:**
   - Use pattern from KnowledgeService
   - Validate required fields
   - Check href validity
   - Prevent self-links

