# ARCHITECTURE — System Design

**Core Principle:** JSON-driven, plugin-based converters.

---

## Data Model

`
Converter JSON (app/data/converters/*.json)
    ↓
ConverterDataService (load, cache, validate)
    ↓
Services (HubService, RecommendationService, SeoService)
    ↓
Routes (render UI)
    ↓
User
`

---

## Key Components

| Component | Purpose |
|-----------|---------|
| **ConverterDataService** | Loads converter JSON, single source of truth |
| **PluginRegistry** | Maps source→target to Python plugins |
| **PluginValidationService** | Validates converters across 8 integration points |
| **HubService** | Generates category hubs from JSON |
| **RecommendationService** | Suggests related converters |
| **SeoService** | Generates metadata & structured data |

---

## Data Flow

1. User visits /converters/{slug}
2. Route calls ConverterDataService.get_converter()
3. Service loads JSON, returns metadata
4. Template renders using data
5. User uploads file
6. Plugin executes conversion
7. User downloads result

---

## Technology Stack

- **Backend:** Python 3.10+, FastAPI
- **Database:** PostgreSQL (future)
- **Storage:** JSON files (current)
- **Testing:** Pytest

---

## Key Decisions

- **Universal Route:** Single /converters/{slug} + category routes coexist (P006)
- **Data-Driven Pages:** All landing content from JSON (P004)
- **Plugin Validation:** 8 validators, non-breaking framework (P007)

---

## Integration Points

All services query ConverterDataService (single source of truth):
- HubService → by category
- RecommendationService → by metadata
- SeoService → for metadata generation
- PluginValidationService → for consistency checks

Details: See docs/ARCHITECTURE.md
