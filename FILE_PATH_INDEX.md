# Converigo - Complete File Path Index & Directory Map

## Directory Structure with Full Paths

```
c:\converigo\
├── app\                                    # Main application directory
│   │
│   ├── main.py                            # FastAPI app entry point
│   │   └── Initializes all routers, middleware, services
│   │
│   ├── bootstrap.py                       # Application bootstrap
│   │
│   ├── core\                              # Core application logic
│   │   ├── registry.py                   # ConverterRegistry class
│   │   │  └── Stores ConverterInfo objects
│   │   │  └── Methods: register(), get(), get_all(), get_by_category()
│   │   │
│   │   ├── register_default.py           # Default converter registration
│   │   │  └── register_default_converters()
│   │   │  └── Populates core registry with built-in converters
│   │   │
│   │   ├── engine_registry.py            # Engine registry for converters
│   │   ├── logging_config.py             # Logging configuration
│   │   ├── settings.py                   # Application settings
│   │   ├── templates.py                  # Jinja2 template config
│   │   ├── template_context.py           # Template context builders
│   │   └── __pycache__\
│   │
│   ├── plugins\                           # Plugin directory
│   │   ├── base.py                       # ConverterPlugin abstract base class
│   │   │  ├── Defines interface for all plugins
│   │   │  ├── Abstract method: convert()
│   │   │  ├── Helper: supports(), metadata()
│   │   │  ├── Properties: slug, name, description, category, engine
│   │   │  ├── Scoring: priority, quality, compatibility, estimated_saving
│   │   │  └── SEO: seo_title, seo_description
│   │   │
│   │   ├── base_plugin.py                # (Currently empty)
│   │   ├── registry.py                   # Plugin registry
│   │   ├── __init__.py
│   │   │
│   │   ├── image\                        # Image converter plugins
│   │   │   ├── avif_to_jpg.py
│   │   │   ├── bmp_to_jpg.py
│   │   │   ├── bmp_to_png.py
│   │   │   ├── bmp_to_webp.py
│   │   │   ├── heic_to_jpg.py
│   │   │   ├── jpg_to_ico.py
│   │   │   ├── jpg_to_png.py
│   │   │   ├── jpg_to_tiff.py
│   │   │   ├── jpg_to_webp.py
│   │   │   ├── png_to_bmp.py
│   │   │   ├── png_to_ico.py
│   │   │   ├── png_to_jpg.py             # Example: See below for full code
│   │   │   ├── png_to_tiff.py
│   │   │   ├── png_to_webp.py
│   │   │   ├── svg_to_png.py
│   │   │   ├── tiff_to_jpg.py
│   │   │   ├── tiff_to_png.py
│   │   │   ├── webp_to_ico.py
│   │   │   ├── webp_to_jpg.py
│   │   │   ├── webp_to_png.py
│   │   │   ├── webp_to_tiff.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__\
│   │   │
│   │   ├── document\                     # Document converter plugins
│   │   │   ├── excel_to_pdf.py
│   │   │   ├── jpg_to_pdf.py
│   │   │   ├── pdf_compress.py
│   │   │   ├── pdf_merge.py
│   │   │   ├── pdf_split.py
│   │   │   ├── pdf_to_excel.py
│   │   │   ├── pdf_to_jpg.py
│   │   │   ├── pdf_to_ppt.py
│   │   │   ├── pdf_to_word.py            # Example: See below for full code
│   │   │   ├── ppt_to_pdf.py
│   │   │   ├── word_to_pdf.py
│   │   │   ├── __init__.py
│   │   │   └── __pycache__\
│   │   │
│   │   ├── audio\                        # Audio converter plugins
│   │   │   ├── {audio converters}
│   │   │   ├── __init__.py
│   │   │   └── __pycache__\
│   │   │
│   │   ├── video\                        # Video converter plugins
│   │   │   ├── {video converters}
│   │   │   ├── __init__.py
│   │   │   └── __pycache__\
│   │   │
│   │   ├── pdf\                          # PDF-specific plugins
│   │   │   ├── __init__.py
│   │   │   └── __pycache__\
│   │   │
│   │   └── __pycache__\
│   │
│   ├── data\                              # Converter data directory
│   │   └── converters\                   # Converter definitions
│   │       ├── avif-to-jpg.contract.json
│   │       ├── avif-to-jpg.json
│   │       │
│   │       ├── bmp-to-jpg.contract.json
│   │       ├── bmp-to-jpg.json
│   │       ├── bmp-to-jpg.metadata.json
│   │       │
│   │       ├── excel-to-pdf.contract.json
│   │       ├── excel-to-pdf.metadata.json
│   │       │
│   │       ├── heic-to-jpg.contract.json
│   │       ├── heic-to-jpg.metadata.json
│   │       │
│   │       ├── jpg-to-png.contract.json
│   │       ├── jpg-to-png.json
│   │       │
│   │       ├── mp4-to-aac.contract.json
│   │       ├── mp4-to-aac.json
│   │       │
│   │       ├── mp4-to-flac.contract.json
│   │       ├── mp4-to-flac.json
│   │       │
│   │       ├── mp4-to-m4a.contract.json
│   │       ├── mp4-to-m4a.json
│   │       │
│   │       ├── mp4-to-mp3.contract.json
│   │       ├── mp4-to-mp3.json
│   │       │
│   │       ├── mp4-to-ogg.contract.json
│   │       ├── mp4-to-ogg.json
│   │       │
│   │       ├── mp4-to-wav.contract.json
│   │       ├── mp4-to-wav.json
│   │       │
│   │       ├── pdf-compress.contract.json
│   │       ├── pdf-compress.json
│   │       │
│   │       ├── pdf-merge.contract.json
│   │       ├── pdf-merge.json
│   │       │
│   │       ├── pdf-split.contract.json
│   │       ├── pdf-split.json
│   │       │
│   │       ├── pdf-to-excel.contract.json
│   │       ├── pdf-to-excel.metadata.json
│   │       │
│   │       ├── pdf-to-ppt.contract.json
│   │       ├── pdf-to-ppt.metadata.json
│   │       │
│   │       ├── pdf-to-word.contract.json
│   │       ├── pdf-to-word.json
│   │       ├── pdf-to-word.metadata.json
│   │       │
│   │       ├── png-to-jpg.contract.json
│   │       ├── png-to-jpg.json
│   │       │
│   │       ├── png-to-webp.contract.json
│   │       ├── png-to-webp.json
│   │       │
│   │       ├── ppt-to-pdf.contract.json
│   │       ├── ppt-to-pdf.metadata.json
│   │       │
│   │       ├── svg-to-png.contract.json
│   │       ├── svg-to-png.metadata.json
│   │       │
│   │       ├── tiff-to-jpg.contract.json
│   │       ├── tiff-to-jpg.json
│   │       │
│   │       ├── webp-to-png.contract.json
│   │       ├── webp-to-png.json
│   │       │
│   │       └── word-to-pdf.json          # Note: No .contract.json (error?)
│   │           └── word-to-pdf.metadata.json
│   │
│   ├── services\                         # Business logic services
│   │   ├── converter_registry_service.py
│   │   │  ├── Class: ConverterRegistryService
│   │   │  ├── Constructor: __init__(contracts_dir)
│   │   │  ├── Methods: list_all(), get_by_slug(), get_by_id(), get_by_category(), get_active(), get_beta()
│   │   │  ├── Validation: REQUIRED_FIELDS, VALID_LIFECYCLE_STATUSES
│   │   │  └── Error: ConverterRegistryError
│   │   │
│   │   ├── converter_data_service.py
│   │   │  ├── Class: ConverterDataService
│   │   │  ├── Constructor: __init__(data_dir)
│   │   │  ├── Methods: list_all_converters(), list_active_converters(), list_popular_converters()
│   │   │  ├── Methods: load_converter_by_slug(), resolve_related_tools()
│   │   │  ├── Inference: _infer_cluster(), _infer_output_category()
│   │   │  └── Data Loading: _load_converter(), _iter_converter_files()
│   │   │
│   │   ├── landing_service.py            # CRITICAL SERVICE
│   │   │  ├── Class: LandingPageBuilder
│   │   │  ├── Constructor: __init__(seo_service, converter_data_service)
│   │   │  ├── Main method: build_context(request, tool_data, faq_items, canonical_path, meta_overrides)
│   │   │  ├── Validation: validate_contract(landing) - checks all REQUIRED_SECTIONS
│   │   │  ├── Builders: _build_intro(), _build_steps(), _build_benefits()
│   │   │  ├── Builders: _build_supported_formats(), _build_tips(), _build_common_problems()
│   │   │  ├── Builders: _build_faq(), _build_breadcrumb(), _build_download_section()
│   │   │  ├── Builders: _build_related_converters(), _build_related_converter()
│   │   │  ├── FAQ auto-generation with fallback content
│   │   │  ├── REQUIRED_SECTIONS: h1, seo_title, meta_description, intro, steps, benefits, etc.
│   │   │  └── Error: LandingContractError
│   │   │
│   │   ├── knowledge_service.py          # EDUCATIONAL CONTENT SERVICE
│   │   │  ├── Class: KnowledgeService
│   │   │  ├── Constructor: __init__(contracts_dir)
│   │   │  ├── Method: generate_payload(contract) -> dict
│   │   │  ├── Method: generate_all() -> dict[slug: payload]
│   │   │  ├── Validation: _validate_payload() - checks all REQUIRED_SECTIONS
│   │   │  ├── REQUIRED_SECTIONS: slug, source_format, target_format, what_is_source, what_is_target
│   │   │  ├── REQUIRED_SECTIONS: differences, advantages, limitations, best_practices, etc.
│   │   │  ├── Output: Educational content (glossary, tips, FAQ enrichment)
│   │   │  └── Deterministic generation from contract data
│   │   │
│   │   ├── related_converter_service.py  # RECOMMENDATION ENGINE
│   │   │  ├── Class: RelatedConverterService
│   │   │  ├── Constructor: __init__(converter_data_service)
│   │   │  ├── Method: get_related_converters(converter, limit=4)
│   │   │  ├── Scoring: same_input(+4), same_category(+3), same_cluster(+2), same_target(+1)
│   │   │  ├── Fallback strategy for insufficient matches
│   │   │  ├── Returns sorted by score, deduplicated
│   │   │  └── Includes match_reasons metadata
│   │   │
│   │   ├── production_audit_service.py   # QUALITY AUDIT SERVICE
│   │   │  ├── Class: ProductionAuditService
│   │   │  ├── Constructor: __init__(contracts_dir, converter_data_dir, registry_instance)
│   │   │  ├── Method: audit_all() -> results with summary and per-converter metrics
│   │   │  ├── Method: audit_converter(contract) -> detailed audit results
│   │   │  ├── Checks: converter_contract, landing_contract, knowledge_payload
│   │   │  ├── Checks: faq_coverage, internal_links, related_converters, sitemap, hub_inclusion
│   │   │  ├── Quality score calculation: (passed_checks / total_checks) * 100
│   │   │  ├── Status determination: READY, WARNING, NOT READY
│   │   │  ├── Services used: ConverterRegistryService, ConverterDataService, LandingPageBuilder, etc.
│   │   │  └── Aggregates validation signals from all layers
│   │   │
│   │   ├── seo_service.py
│   │   │  ├── Class: SeoService
│   │   │  ├── Methods: build_tool_meta(), build_structured_data()
│   │   │  ├── Generates: Meta titles, descriptions, JSON-LD structured data
│   │   │  ├── Handles: Canonical URLs, breadcrumbs, Open Graph tags
│   │   │  └── Constant: PRODUCTION_BASE_URL = "https://converigo.com"
│   │   │
│   │   ├── conversion_manager.py         # Conversion orchestration
│   │   ├── conversion_service.py
│   │   ├── upload_service.py             # File upload handling
│   │   ├── plugin_validation_service.py  # Plugin validation
│   │   ├── recommendation_service.py     # Recommendations
│   │   ├── sitemap_service.py           # Sitemap generation
│   │   ├── hub_page_service.py          # Hub page service
│   │   ├── language_service.py          # Localization
│   │   ├── language_manager.py          # Language management
│   │   ├── seo_service.py               # SEO
│   │   ├── growth_dashboard_service.py  # Growth metrics
│   │   ├── hub_service.py               # Hub management
│   │   ├── programmatic_seo_service.py  # Programmatic SEO
│   │   ├── cleanup_service.py           # Cleanup operations
│   │   └── __pycache__\
│   │
│   ├── routers\                          # HTTP route handlers
│   │   ├── upload.py
│   │   │  ├── Route: POST /upload
│   │   │  ├── Handler: upload_file(file: UploadFile)
│   │   │  ├── Service: UploadService
│   │   │  ├── Returns: {"status", "filename", "message"}
│   │   │  └── Errors: 400 Bad Request, 500 Internal Server Error
│   │   │
│   │   ├── tools.py                     # Tool/converter landing pages
│   │   │  ├── Route: GET /tools/{slug}
│   │   │  ├── Handler: get_tool_page(request, slug)
│   │   │  ├── Services: ConverterDataService, LandingPageBuilder, SeoService
│   │   │  ├── Helper: _build_tool_page_sections()
│   │   │  ├── Returns: HTMLResponse with rendered landing page
│   │   │  └── Template: tools.html
│   │   │
│   │   ├── convert.py                   # Conversion endpoint
│   │   │  ├── Route: POST /convert/{converter_id}
│   │   │  ├── Handler: convert_file(converter_id, file)
│   │   │  ├── Service: ConversionManager
│   │   │  └── Returns: File download
│   │   │
│   │   ├── home.py                      # Home page
│   │   │  ├── Route: GET /
│   │   │  ├── Handler: home_page(request)
│   │   │  ├── Services: Popular converters, recommendations
│   │   │  └── Template: index.html
│   │   │
│   │   ├── plugins.py                   # Plugin listing
│   │   │  ├── Route: GET /plugins
│   │   │  ├── Handler: list_plugins()
│   │   │  └── Returns: JSON with plugin info
│   │   │
│   │   ├── recommend.py                 # Recommendations
│   │   │  ├── Route: GET /recommend
│   │   │  ├── Handler: get_recommendations()
│   │   │  └── Service: RecommendationService
│   │   │
│   │   ├── seo.py                       # SEO routes
│   │   │  ├── Sitemap generation
│   │   │  ├── Robots.txt
│   │   │  └── SEO metadata endpoints
│   │   │
│   │   └── __pycache__\
│   │
│   ├── engines\                          # Conversion engines
│   │   ├── image_engine.py              # Image processing
│   │   ├── document_engine.py           # Document processing
│   │   ├── audio_engine.py              # Audio processing
│   │   ├── video_engine.py              # Video processing
│   │   └── ...
│   │
│   ├── utils\                            # Utility functions
│   ├── pipeline\                         # Conversion pipeline
│   ├── recommendation\                   # Recommendation logic
│   ├── locales\                          # Localization files
│   ├── logs\                             # Log files
│   ├── outputs\                          # Output files
│   ├── static\                           # Static files (CSS, JS, images)
│   ├── templates\                        # HTML templates (Jinja2)
│   ├── uploads\                          # Temporary uploads
│   └── __pycache__\
│
├── brain\                                # Project documentation
│   ├── ARCHITECTURE.md
│   ├── AI_BOOT_SEQUENCE.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── ...
│
├── design\                               # Design files
├── docs\                                 # Documentation
├── scripts\                              # Utility scripts
├── tests\                                # Test files
│   └── sample.png, sample.pdf, etc.
│
├── ARCHITECTURE_EXPLORATION.md           # THIS DOCUMENT
├── QUICK_REFERENCE.md                    # QUICK REFERENCE
├── README.md
├── CHANGELOG.md
├── DEPLOYMENT.md
├── requirements.txt                      # Python dependencies
├── pytest.ini                            # pytest configuration
├── Dockerfile                            # Docker configuration
├── railway.toml                          # Railway.app config
├── nixpacks.toml                         # Nix configuration
├── runtime.txt                           # Python version
└── ...
```

---

## Key Service Interaction Diagram

```
HTTP Request
    ↓
Router (e.g., tools.py)
    ↓
ConverterDataService.load_converter_by_slug()
    ├─ Reads: app/data/converters/{slug}.json
    ├─ Auto-infers: source, target, cluster, output_category
    └─ Returns: tool_data dict
    ↓
LandingPageBuilder.build_context()
    ├─ Uses: SeoService (for SEO metadata)
    ├─ Builds: All required landing sections
    ├─ Gets: Related converters via RelatedConverterService
    ├─ Prepares: FAQ (auto-generated if missing)
    ├─ Validates: All REQUIRED_SECTIONS present
    └─ Returns: Complete landing context
    ↓
Template Rendering (Jinja2)
    ├─ Uses: landing context data
    └─ Returns: HTML response
    ↓
HTTP Response (200 OK)
```

---

## Service Layering

```
Layer 1: Data Access
├─ ConverterRegistryService      (Contracts: .contract.json)
├─ ConverterDataService          (Data: .json files)
└─ SeoService                    (SEO metadata)

Layer 2: Business Logic
├─ LandingPageBuilder            (Page generation)
├─ KnowledgeService              (Educational content)
├─ RelatedConverterService       (Recommendations)
├─ ConversionManager             (Conversion orchestration)
└─ RecommendationService         (Recommendations)

Layer 3: Quality & Validation
├─ ProductionAuditService        (Quality audit)
├─ PluginValidationService       (Plugin validation)
└─ SitemapService                (Sitemap validation)

Layer 4: HTTP Handlers
├─ upload.py                     (POST /upload)
├─ tools.py                      (GET /tools/{slug})
├─ convert.py                    (POST /convert/{id})
├─ home.py                       (GET /)
├─ plugins.py                    (GET /plugins)
├─ recommend.py                  (GET /recommend)
└─ seo.py                        (GET /sitemap.xml, etc.)
```

---

## Full File Path Reference - Alphabetical

**Contracts:**
```
c:\converigo\app\data\converters\avif-to-jpg.contract.json
c:\converigo\app\data\converters\bmp-to-jpg.contract.json
c:\converigo\app\data\converters\excel-to-pdf.contract.json
c:\converigo\app\data\converters\heic-to-jpg.contract.json
c:\converigo\app\data\converters\jpg-to-png.contract.json
c:\converigo\app\data\converters\mp4-to-aac.contract.json
c:\converigo\app\data\converters\mp4-to-flac.contract.json
c:\converigo\app\data\converters\mp4-to-m4a.contract.json
c:\converigo\app\data\converters\mp4-to-mp3.contract.json
c:\converigo\app\data\converters\mp4-to-ogg.contract.json
c:\converigo\app\data\converters\mp4-to-wav.contract.json
c:\converigo\app\data\converters\pdf-compress.contract.json
c:\converigo\app\data\converters\pdf-merge.contract.json
c:\converigo\app\data\converters\pdf-split.contract.json
c:\converigo\app\data\converters\pdf-to-excel.contract.json
c:\converigo\app\data\converters\pdf-to-ppt.contract.json
c:\converigo\app\data\converters\pdf-to-word.contract.json
c:\converigo\app\data\converters\png-to-jpg.contract.json
c:\converigo\app\data\converters\png-to-webp.contract.json
c:\converigo\app\data\converters\ppt-to-pdf.contract.json
c:\converigo\app\data\converters\svg-to-png.contract.json
c:\converigo\app\data\converters\tiff-to-jpg.contract.json
c:\converigo\app\data\converters\webp-to-png.contract.json
```

**Data Files:**
```
c:\converigo\app\data\converters\avif-to-jpg.json
c:\converigo\app\data\converters\bmp-to-jpg.json
c:\converigo\app\data\converters\bmp-to-jpg.metadata.json
c:\converigo\app\data\converters\bmp-to-png.json
c:\converigo\app\data\converters\bmp-to-webp.json
c:\converigo\app\data\converters\jpg-to-ico.json
c:\converigo\app\data\converters\jpg-to-pdf.json
c:\converigo\app\data\converters\jpg-to-png.json
c:\converigo\app\data\converters\jpg-to-tiff.json
c:\converigo\app\data\converters\jpg-to-webp.json
c:\converigo\app\data\converters\mp4-to-aac.json
c:\converigo\app\data\converters\mp4-to-flac.json
c:\converigo\app\data\converters\mp4-to-m4a.json
c:\converigo\app\data\converters\mp4-to-mp3.json
c:\converigo\app\data\converters\mp4-to-ogg.json
c:\converigo\app\data\converters\mp4-to-wav.json
c:\converigo\app\data\converters\pdf-compress.json
c:\converigo\app\data\converters\pdf-merge.json
c:\converigo\app\data\converters\pdf-split.json
c:\converigo\app\data\converters\pdf-to-excel.metadata.json
c:\converigo\app\data\converters\pdf-to-jpg.json
c:\converigo\app\data\converters\pdf-to-ppt.metadata.json
c:\converigo\app\data\converters\pdf-to-word.json
c:\converigo\app\data\converters\pdf-to-word.metadata.json
c:\converigo\app\data\converters\png-to-bmp.json
c:\converigo\app\data\converters\png-to-ico.json
c:\converigo\app\data\converters\png-to-jpg.json
c:\converigo\app\data\converters\png-to-tiff.json
c:\converigo\app\data\converters\png-to-webp.json
c:\converigo\app\data\converters\ppt-to-pdf.metadata.json
c:\converigo\app\data\converters\svg-to-png.metadata.json
c:\converigo\app\data\converters\tiff-to-jpg.json
c:\converigo\app\data\converters\tiff-to-png.json
c:\converigo\app\data\converters\webp-to-ico.json
c:\converigo\app\data\converters\webp-to-jpg.json
c:\converigo\app\data\converters\webp-to-png.json
c:\converigo\app\data\converters\webp-to-tiff.json
c:\converigo\app\data\converters\word-to-pdf.json
c:\converigo\app\data\converters\word-to-pdf.metadata.json
```

**Core Services:**
```
c:\converigo\app\services\converter_registry_service.py
c:\converigo\app\services\converter_data_service.py
c:\converigo\app\services\landing_service.py
c:\converigo\app\services\knowledge_service.py
c:\converigo\app\services\related_converter_service.py
c:\converigo\app\services\production_audit_service.py
```

**Routers:**
```
c:\converigo\app\routers\upload.py
c:\converigo\app\routers\tools.py
c:\converigo\app\routers\convert.py
c:\converigo\app\routers\home.py
c:\converigo\app\routers\plugins.py
c:\converigo\app\routers\recommend.py
c:\converigo\app\routers\seo.py
```

**Plugins (Example Images):**
```
c:\converigo\app\plugins\image\png_to_jpg.py
c:\converigo\app\plugins\image\jpg_to_png.py
c:\converigo\app\plugins\image\png_to_webp.py
c:\converigo\app\plugins\image\webp_to_png.py
c:\converigo\app\plugins\image\svg_to_png.py
```

**Plugins (Example Documents):**
```
c:\converigo\app\plugins\document\pdf_to_word.py
c:\converigo\app\plugins\document\pdf_to_excel.py
c:\converigo\app\plugins\document\pdf_to_ppt.py
c:\converigo\app\plugins\document\word_to_pdf.py
c:\converigo\app\plugins\document\excel_to_pdf.py
c:\converigo\app\plugins\document\ppt_to_pdf.py
```

**Core Files:**
```
c:\converigo\app\main.py
c:\converigo\app\bootstrap.py
c:\converigo\app\core\registry.py
c:\converigo\app\core\register_default.py
c:\converigo\app\plugins\base.py
```

---

## Contract-to-Service-to-Router Flow Example: PNG to JPG

### 1. Define Contract
**File:** `c:\converigo\app\data\converters\png-to-jpg.contract.json`
```json
{
  "id": "png-to-jpg",
  "slug": "png-to-jpg",
  "name": "PNG to JPG",
  "category": "image",
  ...
}
```

### 2. Define Data
**File:** `c:\converigo\app\data\converters\png-to-jpg.json`
```json
{
  "slug": "png-to-jpg",
  "title": "PNG to JPG Converter",
  "hero": {...},
  "faq": [{...}],
  ...
}
```

### 3. Define Plugin
**File:** `c:\converigo\app\plugins\image\png_to_jpg.py`
```python
class PNGToJPGPlugin(ConverterPlugin):
    slug = "png-to-jpg"
    ...
    async def convert(self, source_path, target_format):
        ...
```

### 4. Load Contract
```python
# In tools.py router
from app.services.converter_registry_service import ConverterRegistryService

registry = ConverterRegistryService("app/data/converters")
contract = registry.get_by_slug("png-to-jpg")
```

### 5. Load Data
```python
# In tools.py router
from app.services.converter_data_service import ConverterDataService

data_service = ConverterDataService(Path("app/data/converters"))
tool_data = data_service.load_converter_by_slug("png-to-jpg")
```

### 6. Build Landing
```python
# In tools.py router
from app.services.landing_service import LandingPageBuilder

landing = landing_page_builder.build_context(request, tool_data)
landing_page_builder.validate_contract(landing)  # Verify completeness
```

### 7. Render
```python
# In tools.py router
return templates.TemplateResponse("tool.html", {
    "request": request,
    "page": landing
})
```

### 8. HTTP Response
```
GET /png-to-jpg
→ Rendered HTML landing page with all sections
```

---
