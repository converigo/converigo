# PROJECT_CHARTER — Vision & Non-Negotiables

**Converigo** is the easiest, fastest, cleanest way to convert files.

---

## Vision

Convert anything in seconds. Simple. Trustworthy. Done.

### Core Values
- **User First** — Simplicity over features
- **Quality Over Speed** — Tests before release
- **Trust & Safety** — Files are sacred
- **Reliability** — When it works, it works

---

## Non-Negotiable Principles

| Principle | Rule |
|-----------|------|
| **Checkpoint-First** | All work in named checkpoints, no ad-hoc pushes |
| **Plugin-Based** | Converters are plugins, not hardcoded |
| **JSON-First** | Config in JSON, not code |
| **Non-Breaking** | Old URLs never break, always backwards compatible |
| **Data-Driven** | UI from data, not hardcoded |
| **Quality Gate** | 95%+ tests required to release |
| **Universal Route** | /converters/{slug} for all converters |
| **Repository=Truth** | Source code + JSON = authority |

---

## Product Scope

### In Scope ✓
- File conversion (image, document, audio, video, archive)
- Plugin-based architecture
- Recommendation engine
- Quality assurance framework

### Out of Scope ✗
- Cloud storage
- Batch conversion
- API (future phase)
- Custom user plugins
- Account system (future)

---

## Success Criteria

- Conversion time: <5s average
- Page load: <2s
- Tests: 95%+ pass rate
- Quality: 100% converter validation
- Uptime: 99.9%

---

## Release Gate

All tests passing + zero critical bugs + docs updated = **READY TO RELEASE**

Source: See docs/ for detailed product specification.
