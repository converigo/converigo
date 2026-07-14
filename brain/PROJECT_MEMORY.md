# PROJECT_MEMORY — Permanent Principles

---

## Non-Negotiable Principles

These principles NEVER change without full team agreement:

| Principle | Definition |
|-----------|-----------|
| **Checkpoint-First** | All work in named checkpoints (C1, C2, C3.8, etc.) |
| **Plugin-Based** | Converters are plugins, architecture doesn't change |
| **JSON-First** | All converter config in JSON files, not code |
| **Data-Driven** | UI rendering from data, not hardcoded |
| **Non-Breaking** | Old URLs forever, new features = new routes |
| **Quality-Gate** | 95%+ tests required, no exceptions |
| **Universal Route** | /converters/{slug} as single entry point |
| **Repository=Truth** | Source code + JSON is authority, not chat |

---

## Permanent Decisions

| Decision | Rule |
|----------|------|
| **D001** | Checkpoint-first release process |
| **D003** | No code changes in documentation |
| **D004** | Only release blockers during final push |
| **D005** | Git readiness validation before push |
| **D006** | Universal route compatible with category routes |
| **D007** | JSON-driven tool page sections (hero, features, etc.) |
| **D008** | Legacy templates preserved, not deleted |
| **D009** | JSON enrichment for universal tool pages |
| **D010** | Data-driven hub automation from converter JSON |
| **D011** | Plugin validation as non-breaking framework |

---

## Architecture Principles

- **Single Source of Truth** — ConverterDataService (JSON)
- **No Hardcoded Config** — All in JSON or code, never mixed
- **Services are Read-Only** — No direct DB writes (future DB sync)
- **Plugin Registry Authoritative** — All converters registered

---

## Lessons Learned

✓ Checkpoint-based releases prevent scope creep  
✓ Validation built-in from start (not backfilled)  
✓ Smaller checkpoints better than large ones  
✓ Automation beats manual processes  
✗ Large planning documents don't scale (→ Brain v2)

---

## Coding Philosophy

- **Simplicity over cleverness**
- **Explicit over implicit**
- **Type safety matters** (type hints required)
- **Test-driven** (write tests first)
- **Data-driven logic** (config in data, not code)

---

## Release Workflow

Requirements to release:
✓ All tests passing (97+)  
✓ Zero critical bugs  
✓ Docs updated  
✓ Tech lead approval  

Rollback: Keep previous version available for quick switch.

---

Archive: Full decision log in docs/
