# Converigo Converter Architecture - Complete Exploration

## Executive Summary

Converigo is a modular file conversion platform built on **FastAPI** with a plugin-based architecture. Converters are defined through:
1. **Contract files** (`.contract.json`) - Define converter metadata and requirements
2. **Data files** (`.json`) - Rich content for landing pages, FAQs, SEO, and features
3. **Plugin classes** (`.py`) - Actual conversion logic inheriting from `ConverterPlugin`
4. **Services** - Registry, landing page building, knowledge generation, recommendation, and audit

---

## Part 1: Converter Contracts & Structure

### Contract File Format
**Location:** `app/data/converters/*.contract.json`

**Example: PNG to JPG Contract**
```json
{
  "id": "png-to-jpg",
  "slug": "png-to-jpg",
  "name": "PNG to JPG",
  "category": "image",
  "description": "Convert PNG images into JPG format.",
  "input_formats": ["png"],
  "output_formats": ["jpg", "jpeg"],
  "accepted_mime_types": ["image/png"],
  "max_upload_size": 104857600,
  "conversion_engine": "image",
  "landing_path": "/png-to-jpg",
  "canonical_url": "https://converigo.com/png-to-jpg",
  "seo_status": "ready",
  "schema_status": "ready",
  "faq_status": "ready",
  "regression_sample": "tests/sample.png",
  "supported_platforms": ["web"],
  "lifecycle_status": "active"
}
```

### Contract Required Fields

```python
REQUIRED_FIELDS = [
    "id",                    # Unique identifier
    "slug",                  # URL-friendly identifier
    "name",                  # Display name
    "category",              # Category (image, document, audio, video, pdf)
    "description",           # Short description
    "input_formats",         # List of input formats (e.g., ["png"])
    "output_formats",        # List of output formats (e.g., ["jpg", "jpeg"])
    "accepted_mime_types",   # MIME types (e.g., ["image/png"])
    "max_upload_size",       # Max file size in bytes
    "conversion_engine",     # Engine type (image, document, audio, video)
    "landing_path",          # URL path (e.g., "/png-to-jpg")
    "canonical_url",         # Full canonical URL
    "seo_status",            # Status: "ready"
    "schema_status",         # Status: "ready"
    "faq_status",            # Status: "ready"
    "regression_sample",     # Path to test file
    "supported_platforms",   # Platforms: ["web"]
    "lifecycle_status"       # Status: "active", "beta", or "deprecated"
]
```

### Contract Validation Rules

- **String fields**: Must be non-empty and trimmed
- **lifecycle_status**: Must be one of: `"active"`, `"beta"`, `"deprecated"`
- **List fields**: Must be non-empty lists
- **max_upload_size**: Must be positive integer
- **Slug/ID uniqueness**: No duplicates allowed

---

## Part 2: Converter Data Files

### Data File Format
**Location:** `app/data/converters/{slug}.json`

**Example: PNG to JPG Data File**
```json
{
  "slug": "png-to-jpg",
  "title": "PNG to JPG Converter",
  "description": "Convert PNG images into JPG format with browser-friendly optimization.",
  "upload_form": {
    "action": "/upload",
    "method": "post",
    "accept": ".png",
    "button_text": "Upload PNG"
  },
  "faq": [
    {
      "question": "Can I convert transparent PNGs?",
      "answer": "Yes, transparent PNGs are supported, but transparency becomes a white background in JPG format."
    },
    {
      "question": "How do I get the converted image?",
      "answer": "You will receive a downloadable JPG file after conversion."
    }
  ],
  "related_tools": [
    {
      "slug": "jpg-to-png",
      "title": "JPG to PNG"
    },
    {
      "slug": "png-to-webp",
      "title": "PNG to WebP"
    }
  ],
  "seo": {
    "title": "PNG to JPG | Converigo",
    "description": "Convert PNG images to JPG format.",
    "keywords": "png to jpg, image converter, photo converter"
  },
  "source": "png",
  "target": "jpg",
  "category": "image",
  "active": true,
  "popular": true,
  "featured": false,
  "hero": {
    "eyebrow": "Converter tool",
    "title": "Convert PNG to JPG Online Free",
    "description": "Convert PNG images into JPG format with browser-friendly optimization.",
    "panel_label": "Ready to convert",
    "panel_title": "Upload a PNG file and receive a JPG result in seconds."
  },
  "features": [
    {
      "title": "High-quality output",
      "text": "Preserve the visual quality of your files while converting between common image formats."
    },
    {
      "title": "Fast workflow",
      "text": "Upload, convert, and download in a few quick steps without installing software."
    },
    {
      "title": "Secure processing",
      "text": "Your files are handled securely and the result is ready to use immediately."
    }
  ],
  "supported_formats": {
    "input": ["PNG"],
    "output": ["JPG"],
    "description": "PNG input, JPG output"
  },
  "how_to_use": [
    {
      "title": "Upload your file",
      "description": "Select a PNG file from your device to start the conversion."
    },
    {
      "title": "Choose the output format",
      "description": "Pick JPG as the result format and review the conversion options."
    },
    {
      "title": "Download the converted file",
      "description": "Get your converted file immediately without installing extra software."
    }
  ],
  "about_formats": [
    {
      "title": "What is PNG?",
      "text": "PNG is the source file format used for this conversion workflow."
    },
    {
      "title": "What is JPG?",
      "text": "JPG is the output format generated by this converter."
    }
  ],
  "cta": {
    "eyebrow": "Ready to convert",
    "title": "Convert PNG files to JPG in seconds",
    "text": "Upload your file and receive a ready-to-use result instantly.",
    "primary_text": "Convert now",
    "secondary_text": "Read FAQs",
    "primary_href": "#converter",
    "secondary_href": "#faq"
  }
}
```

---

## Part 3: Plugin Structure

### Plugin Class Structure
**Location:** `app/plugins/{category}/{slug}.py`

**Example: PNG to JPG Plugin**
```python
from pathlib import Path
from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin

class PNGToJPGPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "png-to-jpg"
    name = "PNG to JPG"
    description = "Convert PNG images to JPG format with wide compatibility."
    category = "image"
    engine = "image"
    icon = "🖼️"


    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True
    featured = True


    # ==========================================
    # Formats
    # ==========================================

    source_formats = ["png"]
    target_formats = ["jpg", "jpeg"]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "compatibility"
    use_case = "Best when users need JPG support on almost all devices."
    priority = 85
    quality = 90
    compatibility = 100
    estimated_saving = 40
    badge = "Most Compatible"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = "PNG to JPG Converter | Converigo"
    seo_description = "Convert PNG images to JPG with excellent compatibility."


    # ==========================================
    # Conversion
    # ==========================================

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PNGToJPGPlugin only supports PNG -> JPG.")

        engine = ImageEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )
```

### Base Plugin Class
**Location:** `app/plugins/base.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path

class ConverterPlugin(ABC):
    """Base class for every converter plugin."""

    # Identity
    slug = ""
    name = ""
    description = ""
    category = ""
    engine = ""

    # Formats
    source_formats = []
    target_formats = []

    # Recommendation Metadata
    goal = ""
    use_case = ""
    priority = 50              # 1-100
    quality = 50               # 1-100
    compatibility = 50         # 1-100
    estimated_saving = 0       # Percentage
    badge = ""
    icon = "📄"
    color = "blue"

    # SEO
    seo_title = ""
    seo_description = ""

    def supports(self, source_format: str, target_format: str) -> bool:
        """Check if conversion is supported."""
        source = source_format.lower().replace(".", "")
        target = target_format.lower().replace(".", "")
        return (source in self.source_formats and target in self.target_formats)

    def metadata(self) -> dict:
        """Return plugin metadata."""
        return {...}

    @abstractmethod
    async def convert(self, source_path: Path, target_format: str) -> Path:
        """Convert file and return converted file path."""
        raise NotImplementedError
```

### Plugin Categories
Plugins are organized by category in `app/plugins/`:
- `image/` - Image converters (PNG, JPG, WEBP, etc.)
- `document/` - Document converters (PDF, Word, Excel, etc.)
- `audio/` - Audio converters (MP3, WAV, etc.)
- `video/` - Video converters (MP4, etc.)
- `pdf/` - PDF-specific converters

---

## Part 4: Services - Registration & Management

### 1. ConverterRegistryService
**Location:** `app/services/converter_registry_service.py`

**Purpose:** Load, validate, and provide access to converter contracts

```python
class ConverterRegistryService:
    REQUIRED_FIELDS = [...]  # See contract section
    VALID_LIFECYCLE_STATUSES = {"active", "deprecated", "beta"}

    def __init__(self, contracts_dir: Path | str) -> None:
        self.contracts_dir = Path(contracts_dir)
        self._load_contracts()

    def list_all(self) -> list[dict]:
        """Get all contracts."""
        return list(self._contracts)

    def get_by_slug(self, slug: str) -> dict | None:
        """Get contract by slug."""

    def get_by_id(self, id_: str) -> dict | None:
        """Get contract by ID."""

    def get_by_category(self, category: str) -> list[dict]:
        """Get contracts by category."""

    def get_active(self) -> list[dict]:
        """Get only active contracts."""

    def get_beta(self) -> list[dict]:
        """Get only beta contracts."""
```

**Contract Validation:**
- Loads all `.contract.json` files
- Validates all required fields present
- Checks for duplicate IDs and slugs
- Raises `ConverterRegistryError` on validation failure

---

### 2. ConverterDataService
**Location:** `app/services/converter_data_service.py`

**Purpose:** Load and manage converter data files

```python
class ConverterDataService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def list_all_converters(self) -> List[dict]:
        """Get all converters sorted by title."""

    def list_active_converters(self) -> List[dict]:
        """Get only active converters."""

    def list_popular_converters(self, limit: int = 6) -> List[dict]:
        """Get popular converters."""

    def load_converter_by_slug(self, slug: str) -> dict:
        """Load specific converter data."""

    def resolve_related_tools(self, converter: dict, limit: int = 4) -> list[dict]:
        """Get related converters."""
```

**Data Loading Rules:**
- Loads `.json` files (excluding `.contract.json` and `.metadata.json`)
- Auto-infers `source` and `target` from slug if missing
- Sets default category as "general"
- Normalizes popularity flags
- Infers cluster and output_category

---

### 3. LandingPageBuilder
**Location:** `app/services/landing_service.py`

**Purpose:** Generate complete landing page context

```python
class LandingPageBuilder:
    REQUIRED_SECTIONS = {
        "h1",
        "seo_title",
        "meta_description",
        "intro",
        "steps",
        "benefits",
        "supported_formats",
        "tips",
        "common_problems",
        "faq",
        "json_ld",
        "breadcrumb",
        "cta",
        "download",
        "related_converter",
        "related_converters",
        "internal_links",
    }

    def __init__(self, seo_service, converter_data_service):
        self.seo_service = seo_service
        self.converter_data_service = converter_data_service

    def build_context(
        self,
        request,
        tool_data: dict,
        faq_items: list | None = None,
        canonical_path: str | None = None,
        meta_overrides: dict | None = None,
    ) -> dict:
        """Build complete landing page context."""
        return {
            "h1": str,                         # Main heading
            "seo_title": str,                  # Page title for SEO
            "meta_description": str,           # Meta description
            "intro": {"title": str, "text": str},
            "steps": [{...}],                  # Conversion steps
            "benefits": [{...}],               # Benefits
            "supported_formats": {...},        # Input/output formats
            "tips": [{...}],                   # Usage tips
            "common_problems": [{...}],        # Problem/solution pairs
            "faq": [{...}],                    # FAQ (min 8, max 12)
            "json_ld": dict,                   # Structured data
            "breadcrumb": [{...}],             # Breadcrumb trail
            "cta": {...},                      # Call-to-action
            "download": {...},                 # Download section
            "related_converter": dict,         # Primary related converter
            "related_converters": [dict],      # 4 related converters
            "internal_links": {...},           # Internal navigation
            "meta": dict,                      # SEO metadata
        }

    def validate_contract(self, landing: dict) -> None:
        """Validate landing page has all required sections."""
```

**Landing Page Construction Rules:**
- Uses tool_data (from `.json` file) to build sections
- Generates default content if not provided
- FAQ ensures min 8, max 12 items
- Resolves related converters based on:
  - Same source format (score +4)
  - Same output category (score +3)
  - Same cluster (score +2)
  - Same target format (score +1)
- Builds structured data for schema.org

---

### 4. KnowledgeService
**Location:** `app/services/knowledge_service.py`

**Purpose:** Generate educational content payloads

```python
class KnowledgeService:
    REQUIRED_SECTIONS = {
        "slug",
        "source_format",
        "target_format",
        "what_is_source",
        "what_is_target",
        "differences",
        "advantages",
        "limitations",
        "best_practices",
        "common_mistakes",
        "tips",
        "faq_enrichment",
        "glossary",
    }

    def generate_payload(self, contract: dict) -> dict:
        """Generate knowledge payload for a converter."""
        return {
            "slug": str,
            "source_format": str,              # e.g., "PNG"
            "target_format": str,              # e.g., "JPG"
            "what_is_source": {"title": str, "text": str},
            "what_is_target": {"title": str, "text": str},
            "differences": [{"title": str, "text": str}],
            "advantages": [{"title": str, "text": str}],
            "limitations": [{"title": str, "text": str}],
            "best_practices": [{"title": str, "text": str}],
            "common_mistakes": [{"title": str, "text": str}],
            "tips": [{"title": str, "text": str}],
            "faq_enrichment": [{"question": str, "answer": str}],
            "glossary": [{"term": str, "definition": str}],
        }

    def generate_all(self) -> dict[str, dict]:
        """Generate knowledge payloads for all active converters."""
        return {slug: payload, ...}
```

---

### 5. RelatedConverterService
**Location:** `app/services/related_converter_service.py`

**Purpose:** Discover and score related converters

```python
class RelatedConverterService:
    def get_related_converters(self, converter: dict, limit: int = 4) -> list[dict]:
        """Get related converters with scoring."""
        # Matching criteria:
        # 1. Same input format (highest weight)
        # 2. Same output category
        # 3. Same cluster (format family)
        # 4. Same target format (bonus)
        
        # Returns sorted by score, then by title
        # Falls back to any converter if not enough matches
        
        return [
            {
                "slug": str,
                "title": str,
                "description": str,
                "source": str,
                "target": str,
                "category": str,
                "cluster": str,
                "match_reasons": {
                    "same_input": bool,
                    "same_output_category": bool,
                    "same_cluster": bool,
                },
            }
        ]
```

---

### 6. ProductionAuditService
**Location:** `app/services/production_audit_service.py`

**Purpose:** Audit converter quality and readiness

```python
class ProductionAuditService:
    def audit_all(self) -> dict:
        """Audit all active converters."""
        return {
            "summary": {
                "total_converters": int,
                "ready_count": int,
                "warning_count": int,
                "not_ready_count": int,
                "quality_score_average": float,
            },
            "results": [
                {
                    "slug": str,
                    "status": "READY" | "WARNING" | "NOT READY",
                    "quality_score": float,
                    "checks": {
                        "converter_contract": bool,
                        "landing_contract": bool,
                        "knowledge_payload": bool,
                        "faq_coverage": bool,
                        "internal_links": bool,
                        "related_converters": bool,
                        "sitemap_inclusion": bool,
                        "hub_inclusion": bool,
                    },
                }
            ],
        }

    def audit_converter(self, contract: dict) -> dict:
        """Audit individual converter."""
```

**Audit Checks:**
1. Converter contract exists and valid
2. Landing page contract has all sections
3. Knowledge payload generated successfully
4. FAQ coverage (min 8 items)
5. Internal links present
6. Related converters identified
7. Sitemap inclusion validated
8. Hub page inclusion validated

---

## Part 5: Request Flow & HTTP Routes

### Routers
**Location:** `app/routers/`

#### Upload Router (`upload.py`)
```python
@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process file."""
    saved_path = await UploadService().process_upload(file)
    return {
        "status": "success",
        "filename": saved_path.name,
        "message": "File uploaded successfully.",
    }
```

#### Tools Router (`tools.py`)
```python
@router.get("/tools/{slug}", response_class=HTMLResponse)
async def get_tool_page(request: Request, slug: str):
    """Render landing page for converter."""
    tool_data = converter_data_service.load_converter_by_slug(slug)
    landing = landing_page_builder.build_context(request, tool_data)
    return templates.TemplateResponse("tool.html", {"request": request, "page": landing})
```

#### Convert Router (`convert.py`)
```python
@router.post("/convert/{converter_id}")
async def convert_file(converter_id: str, file: UploadFile):
    """Perform conversion."""
    converted_path = await conversion_manager.convert(converter_id, file)
    return FileResponse(converted_path)
```

#### Home Router (`home.py`)
```python
@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page with popular converters."""
    converters = converter_data_service.list_popular_converters()
    recommendations = recommendation_service.get_recommendations()
    return templates.TemplateResponse("index.html", {...})
```

---

## Part 6: Complete Converter Inventory

### All Active Converters (23 Total)

**Image Converters:**
- avif-to-jpg
- bmp-to-jpg
- heic-to-jpg
- jpg-to-png
- png-to-jpg
- png-to-webp
- svg-to-png
- tiff-to-jpg
- webp-to-png

**Document Converters:**
- excel-to-pdf
- pdf-to-excel
- pdf-to-ppt
- pdf-to-word
- ppt-to-pdf
- word-to-pdf
- jpg-to-pdf

**PDF Utilities:**
- pdf-compress
- pdf-merge
- pdf-split

**Audio Converters:**
- mp4-to-aac
- mp4-to-flac
- mp4-to-m4a
- mp4-to-mp3
- mp4-to-ogg
- mp4-to-wav

---

## Part 7: File Organization Patterns

### Directory Structure Pattern

```
app/
├── plugins/
│   ├── image/
│   │   ├── png_to_jpg.py          # Plugin class
│   │   ├── jpg_to_png.py
│   │   └── ...
│   ├── document/
│   │   ├── pdf_to_word.py
│   │   └── ...
│   ├── audio/
│   ├── video/
│   ├── pdf/
│   ├── base.py                     # Base plugin class
│   └── registry.py                 # Plugin registry
│
├── data/
│   └── converters/
│       ├── png-to-jpg.contract.json     # Contract (required)
│       ├── png-to-jpg.json              # Data (optional)
│       ├── png-to-jpg.metadata.json     # Metadata (optional)
│       ├── pdf-to-word.contract.json
│       ├── pdf-to-word.json
│       ├── pdf-to-word.metadata.json
│       └── ...
│
├── services/
│   ├── converter_registry_service.py    # Contract loading
│   ├── converter_data_service.py        # Data loading
│   ├── landing_service.py               # Landing page building
│   ├── knowledge_service.py             # Knowledge generation
│   ├── related_converter_service.py     # Recommendations
│   ├── production_audit_service.py      # Quality audit
│   ├── seo_service.py                   # SEO metadata
│   └── ...
│
├── routers/
│   ├── upload.py
│   ├── tools.py
│   ├── convert.py
│   ├── home.py
│   └── ...
│
├── core/
│   ├── registry.py                      # Core registry
│   ├── register_default.py              # Default registration
│   └── ...
│
└── main.py                              # FastAPI app
```

---

## Part 8: Registration & Initialization Flow

### Step 1: Core Registry
```python
# app/core/registry.py
@dataclass(slots=True)
class ConverterInfo:
    id: str
    name: str
    category: str
    source_format: str
    target_format: str
    enabled: bool = True

class ConverterRegistry:
    def register(self, converter: ConverterInfo) -> None:
        """Register converter."""
        if converter.id in self._converters:
            raise ValueError(f"Already registered: {converter.id}")
        self._converters[converter.id] = converter
```

### Step 2: Default Registration
```python
# app/core/register_default.py
def register_default_converters() -> None:
    """Register built-in converters."""
    defaults = [
        ConverterInfo(
            id="mp4_to_mp3",
            name="MP4 to MP3",
            category="audio",
            source_format="mp4",
            target_format="mp3",
        ),
        # ...
    ]
    for converter in defaults:
        if registry.get(converter.id) is None:
            registry.register(converter)
```

### Step 3: Contract-Based Registry
```python
# app/services/converter_registry_service.py
registry_service = ConverterRegistryService("app/data/converters")

# Loads all .contract.json files
# Validates each contract
# Throws error on duplicate ID/slug
# Provides methods to access by slug, ID, category, etc.
```

---

## Part 9: Key Patterns & Best Practices

### Pattern 1: Slug Convention
**Format:** `{source-format}-to-{target-format}`

Examples:
- `png-to-jpg`
- `pdf-to-word`
- `mp4-to-mp3`

Used for:
- File naming (`png-to-jpg.contract.json`)
- URL paths (`/png-to-jpg`)
- Plugin class identification
- Related converter discovery

### Pattern 2: Plugin Discovery
Converters are discovered by:
1. Scanning `app/plugins/` for `.py` files
2. Looking for classes inheriting `ConverterPlugin`
3. Using `slug` attribute as unique identifier
4. Matching to contract via slug

### Pattern 3: Content Layering
**Three levels of converter definition:**

1. **Contract** (`.contract.json`) - Metadata & status
   - What is it, required fields, lifecycle status
   - Minimal, machine-generated

2. **Data** (`.json`) - Rich content
   - Landing page sections, FAQ, features
   - Human-curated

3. **Knowledge** (generated) - Educational content
   - Differences, advantages, tips, glossary
   - Auto-generated from contract

### Pattern 4: Related Converter Scoring

Scoring algorithm:
```python
score = 0
if same_input_format:
    score += 4   # Highest priority
if same_output_category:
    score += 3
if same_cluster:
    score += 2
if same_target_format:
    score += 1
```

Result sorted by score descending, then title ascending.

### Pattern 5: Landing Page Auto-Generation

If data field missing, LandingPageBuilder:
- Extracts from slug and contract
- Generates deterministic defaults
- Ensures all required sections present
- Validates completeness

### Pattern 6: Metadata Inference

From slug `{source}-to-{target}`:
- `source_format` = source
- `target_format` = target
- `cluster` = format family (image, document, etc.)
- `output_category` = output format type

---

## Part 10: Quality & Validation

### Contract Validation
**ConverterRegistryService** validates:
- All required fields present
- String fields non-empty
- List fields non-empty
- max_upload_size > 0
- lifecycle_status in valid set
- No duplicate IDs or slugs

### Landing Page Validation
**LandingPageBuilder** validates:
- All required sections present
- FAQ has 8-12 items
- Steps, benefits, tips non-empty lists
- Intro, CTA, download have title & text
- Breadcrumb and internal_links present

### Audit Service
**ProductionAuditService** checks:
- Contract exists
- Landing page valid
- Knowledge payload generated
- FAQ coverage (≥8)
- Internal links present
- Related converters found
- Sitemap inclusion
- Hub inclusion

Quality score calculation:
- Score = (passed_checks / total_checks) × 100
- Average across all active converters

---

## Part 11: SEO & Schema.org

### SEO Service
**Location:** `app/services/seo_service.py`

Generates:
- Meta titles and descriptions
- Structured data (JSON-LD)
- Canonical URLs
- Breadcrumb schema
- Open Graph tags

### Structured Data Components
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "PNG to JPG Converter",
  "description": "Convert PNG images to JPG format",
  "url": "https://converigo.com/png-to-jpg",
  "applicationCategory": "UtilitiesApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "breadcrumb": {...},
  "faqPage": {...}
}
```

---

## Summary Table

| Component | Location | Purpose |
|-----------|----------|---------|
| Contract | `app/data/converters/*.contract.json` | Metadata & validation |
| Data | `app/data/converters/*.json` | Landing page content |
| Plugin | `app/plugins/{category}/*.py` | Conversion logic |
| Registry Service | `app/services/converter_registry_service.py` | Contract loading |
| Data Service | `app/services/converter_data_service.py` | Data loading |
| Landing Builder | `app/services/landing_service.py` | Page generation |
| Knowledge Service | `app/services/knowledge_service.py` | Educational content |
| Related Service | `app/services/related_converter_service.py` | Recommendations |
| Audit Service | `app/services/production_audit_service.py` | Quality scoring |
| Upload Router | `app/routers/upload.py` | File upload |
| Tools Router | `app/routers/tools.py` | Landing pages |
| Convert Router | `app/routers/convert.py` | Conversion endpoint |

---

## Important File Paths Reference

**Contracts:**
- `c:\converigo\app\data\converters\png-to-jpg.contract.json`
- `c:\converigo\app\data\converters\pdf-to-word.contract.json`
- `c:\converigo\app\data\converters\{slug}.contract.json`

**Data Files:**
- `c:\converigo\app\data\converters\png-to-jpg.json`
- `c:\converigo\app\data\converters\pdf-to-word.json`

**Plugins:**
- `c:\converigo\app\plugins\image\png_to_jpg.py`
- `c:\converigo\app\plugins\document\pdf_to_word.py`

**Services:**
- `c:\converigo\app\services\converter_registry_service.py`
- `c:\converigo\app\services\converter_data_service.py`
- `c:\converigo\app\services\landing_service.py`
- `c:\converigo\app\services\knowledge_service.py`
- `c:\converigo\app\services\related_converter_service.py`
- `c:\converigo\app\services\production_audit_service.py`

**Routers:**
- `c:\converigo\app\routers\upload.py`
- `c:\converigo\app\routers\tools.py`
- `c:\converigo\app\routers\convert.py`
- `c:\converigo\app\routers\home.py`

**Core:**
- `c:\converigo\app\core\registry.py`
- `c:\converigo\app\core\register_default.py`
- `c:\converigo\app\plugins\base.py`

**Entry Point:**
- `c:\converigo\app\main.py`
