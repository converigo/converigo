# DEVELOPMENT_GUIDE — Workflows & Standards

---

## Sprint Workflow

`
Week 1: Plan scope → Week 2: Develop + test → Week 3: Integrate + release
`

**Rule:** All work organized by checkpoint. No mid-checkpoint additions.

---

## Coding Standards

- **Language:** Python 3.10+
- **Style:** PEP 8 + FastAPI conventions
- **Type Hints:** Required on all functions
- **Tests:** 95%+ pass rate minimum
- **Commit:** Descriptive messages, reference issues

Example format:
`
feat(converter-data): Add JSON enrichment for universal pages
`

---

## Testing Requirements

| Type | Target |
|------|--------|
| **Unit Tests** | Tests for each function |
| **Integration** | Tests across services |
| **Regression** | All tests before release |

**Gate:** 95%+ pass rate required for release.

---

## Code Review

- Reviewer checks: tests pass, style good, docs updated
- Approval: 1 (features), 2 (architecture)
- No merge without approval

---

## Adding New Converter

1. Create JSON metadata in pp/data/converters/
2. Implement plugin in pp/plugins/
3. Register in pp/core/plugin_registry.py
4. Write tests
5. Mark ctive: true in JSON

---

## 10 Brain Rules

1. Brain is MEMORY, not Wiki
2. Each file max ±150 lines
3. Long docs go to docs/
4. Brain = info for AI to work
5. Repository is Source of Truth
6. Source code = implementation documentation
7. PROJECT_MEMORY = permanent decisions
8. PROJECT_STATE = updated each sprint
9. NEXT = current sprint only
10. AI_BOOTSTRAP = always first file

---

Details: See docs/DEVELOPMENT_GUIDE.md for full standards.
