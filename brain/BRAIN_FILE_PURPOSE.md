# Brain v2 File Purpose Guide

**Status:** PLANNING PHASE  
**Last Updated:** 2026-07-13  
**Sprint:** D1 — Brain v2 Planning & Migration Audit

---

## Purpose

Dokumen ini menjelaskan fungsi masing-masing file dalam struktur Brain v2 dan bagaimana file-file tersebut bekerja bersama untuk menciptakan "otak" proyek yang kohesif.

---

## File Directory

### 1. AI_BOOTSTRAP.md [NEW]

**Function:** AI Entry Point & Quick Orientation  
**Audience:** New AI systems, automated agents  
**Update Frequency:** Rarely (only when project fundamentals change)

**Purpose:**
- First file AI should read
- Provides 5-minute project understanding
- Clear file read sequence
- Quick reference to key concepts
- Links to detailed documentation

**Contains:**
```
□ Project tagline (1 sentence: "What is Converigo?")
□ Current mission & phase
□ Architecture overview (1 paragraph)
□ Core non-negotiables (3-5 bullets)
□ Boot sequence & file read order
□ Quick links to other brain files
□ Key contacts & resources
```

**Why Needed:**
AI systems need rapid context without requiring full chat history review. This file serves as the "new AI checklist" to get up to speed in minutes.

**Related Files:**
- Links to PROJECT_CHARTER.md for mission details
- Links to PROJECT_STATE.md for current metrics
- Links to AI_BOOT_SEQUENCE.md for read order

---

### 2. PROJECT_CHARTER.md [NEW]

**Function:** Project Governance & Non-Negotiables  
**Audience:** Product leads, decision makers, architects  
**Update Frequency:** When product scope changes (rare)

**Purpose:**
- Define what Converigo IS (not what we build)
- Establish permanent principles
- Document non-negotiable constraints
- Provide decision governance framework
- Prevent scope creep & mission drift

**Contains:**
```
□ Vision statement (clear, concise)
□ Core values (3-5 core principles)
□ Non-negotiable rules (what we never change)
□ Product boundaries (what's in/out of scope)
□ Governance principles (how decisions are made)
□ Success metrics (what "good" looks like)
□ Constraints (technical, business, legal)
```

**Why Needed:**
Teams need to understand the "why" behind decisions. PROJECT_CHARTER.md answers: "What is this project fundamentally about?" This prevents decisions that violate core values.

**Related Files:**
- References ARCHITECTURE.md (tech boundaries)
- References PROJECT_MEMORY.md (permanent decisions)
- References DEVELOPMENT_GUIDE.md (decision process)

---

### 3. PROJECT_STATE.md [KEEP & ENHANCE]

**Function:** Current Phase & Metrics Dashboard  
**Audience:** Everyone (daily reference)  
**Update Frequency:** Each sprint (checkpoint completion)

**Purpose:**
- Single source of truth for current project state
- Milestone tracking
- Repository health indicators
- Active development focus
- Quick status check

**Contains:**
```
□ Vision (project context)
□ Current phase & checkpoint
□ Current milestone & deliverables
□ Packages in scope (features)
□ Development workflow
□ Repository health (tests, coverage, branch)
□ Known issues & blockers
□ Next immediate goal
□ Checkpoint metrics (test count, pass rate)
```

**Why Needed:**
Teams need to know: "Where are we right now?" This is the living document updated every sprint. More frequent updates than other files (often, at checkpoint completion).

**Related Files:**
- Updated by NEXT.md (when moving to next checkpoint)
- References DEVELOPMENT_GUIDE.md (workflow)
- References CHECKPOINTS.md (historical data)

---

### 4. ARCHITECTURE.md [NEW]

**Function:** Technical System Design & Tech Stack  
**Audience:** Developers, architects  
**Update Frequency:** When architecture changes (rarely)

**Purpose:**
- Document system design decisions
- Explain technology choices
- Define integration points
- Show data flow
- Record technical constraints

**Contains:**
```
□ Data model overview (JSON-driven converters)
□ System components (services, plugins, routes)
□ Integration points (ConverterDataService, HubService, etc.)
□ Technology stack (Python, FastAPI, PostgreSQL, etc.)
□ Technical decisions (from DECISIONS.md D006-D011)
□ Data flow diagram (text-based)
□ System boundaries & constraints
□ Performance characteristics
□ Scalability notes
```

**Why Needed:**
Developers making code changes need to understand: "How is the system designed?" ARCHITECTURE.md is the technical reference for why code is organized the way it is.

**Related Files:**
- Implements decisions from PROJECT_MEMORY.md
- Referenced by DEVELOPMENT_GUIDE.md (for coding patterns)
- Supports PROJECT_CHARTER.md (technical boundaries)

---

### 5. DEVELOPMENT_GUIDE.md [NEW]

**Function:** Daily Workflows & Coding Standards  
**Audience:** Developers, contributors  
**Update Frequency:** When standards change (occasionally)

**Purpose:**
- Define how we work day-to-day
- Establish coding standards & practices
- Document testing requirements
- Clarify review & approval process
- Record commit & push rules

**Contains:**
```
□ Sprint workflow (how sprints run)
□ Coding standards (Python style, naming, patterns)
□ Testing requirements (coverage, test count, pass rate)
□ Code review process (who reviews, what to check)
□ Commit rules (message format, scope, linking)
□ Push rules (branch strategy, tags, releases)
□ Tools & setup (environment, dependencies)
□ Branching strategy (main, feature, hotfix)
□ Release process (checkpoint-based releases)
□ Common tasks (how to add converter, run tests, etc.)
```

**Why Needed:**
New developers need: "What are the rules?" DEVELOPMENT_GUIDE.md is the operations manual that ensures consistency across the team.

**Related Files:**
- Implements principles from PROJECT_MEMORY.md
- References ARCHITECTURE.md (for code patterns)
- Updated by NEXT.md (when processes change)

---

### 6. PROJECT_MEMORY.md [NEW]

**Function:** Permanent Principles & Long-term Memory  
**Audience:** All stakeholders  
**Update Frequency:** Rarely (only permanent decisions)

**Purpose:**
- Record permanent principles
- Preserve decision history
- Document "why" behind decisions
- Prevent re-litigating old debates
- Create institutional memory

**Contains:**
```
□ Coding philosophy (why we code the way we do)
□ Release workflow (checkpoint-first process)
□ Non-breaking change principle
□ JSON-driven architecture principle
□ Documentation-as-code principle
□ Data-driven rendering principle
□ Quality-first release principle
□ Decision log (all decisions D001-D011+)
  - Decision name & ID
  - Rationale
  - Outcome
  - Status (active, archived, superseded)
□ Lessons learned
□ Avoided pitfalls
```

**Why Needed:**
6 months from now, team members will ask: "Why did we make that decision?" PROJECT_MEMORY.md prevents repeating mistakes and preserves institutional knowledge.

**Related Files:**
- Feeds principles to PROJECT_CHARTER.md
- Referenced by all other files (for decision context)
- Archived decisions stored here for reference

---

### 7. CHANGELOG.md [KEEP]

**Function:** Version & Release History  
**Audience:** All stakeholders (reference)  
**Update Frequency:** Each release / checkpoint completion

**Purpose:**
- Track version history
- Document what changed in each release
- Provide release notes
- Enable rollback traceability
- Track feature delivery timeline

**Contains:**
```
□ Version entries (v1.0.0, v1.1.0, etc.)
□ Release date
□ Features added
□ Bugs fixed
□ Breaking changes (if any)
□ Migration guide (if applicable)
□ Contributors
```

**Why Needed:**
Standard practice. Allows stakeholders to understand what has shipped and when.

**Related Files:**
- Updated from PROJECT_STATE.md (current version)
- References NEXT.md (upcoming releases)

---

### 8. NEXT.md [KEEP]

**Function:** Roadmap & Upcoming Work  
**Audience:** All stakeholders, especially product team  
**Update Frequency:** Each sprint (completion + planning)

**Purpose:**
- Roadmap for next checkpoints
- What's in progress
- What's blocked
- What's coming next
- Long-term vision execution

**Contains:**
```
□ Current sprint status (completed tasks)
□ Current sprint work (in-progress)
□ Next sprint preview (upcoming)
□ Blocked items & why
□ Dependencies & timeline
□ Risk flags
□ Metrics tracking
```

**Why Needed:**
Teams need: "What's next?" This file provides visibility into near-term roadmap and helps with planning.

**Related Files:**
- Feeds into PROJECT_STATE.md (updates current phase)
- References DEVELOPMENT_GUIDE.md (sprint workflow)

---

## File Relationships

### Read Sequence (AI Boot Sequence)

```
AI_BOOTSTRAP.md
    ↓ (Read this first for 5-min context)
    │
    ├─→ PROJECT_CHARTER.md (What is this project?)
    │   ↓
    ├─→ PROJECT_STATE.md (Where are we now?)
    │   ↓
    ├─→ ARCHITECTURE.md (How is it built?)
    │   ↓
    ├─→ DEVELOPMENT_GUIDE.md (How do we work?)
    │   ↓
    ├─→ PROJECT_MEMORY.md (Why did we decide this?)
    │   ↓
    └─→ NEXT.md (What's next?)
```

### Update Dependencies

```
PROJECT_CHARTER.md ← Never changes (unless mission changes)
         ↓ (informs)
PROJECT_MEMORY.md ← Rarely changes (decisions are permanent)
         ↓ (implements)
    ┌────┴─────┬──────────────┐
    ↓          ↓              ↓
ARCHITECTURE DEVELOPMENT_GUIDE PROJECT_STATE
    (rarely)  (occasionally)   (frequently)
    ↓          ↓              ↓
    └────┬──────┴──────────────┘
         ↓ (feeds)
    CHANGELOG.md ← Each release
         ↓ (next steps)
     NEXT.md ← Each sprint
```

### Consistency Rules

1. **AI_BOOTSTRAP.md** should reflect PROJECT_CHARTER.md + PROJECT_STATE.md
2. **ARCHITECTURE.md** should implement decisions from PROJECT_MEMORY.md
3. **DEVELOPMENT_GUIDE.md** should follow principles from PROJECT_MEMORY.md
4. **PROJECT_STATE.md** should reference active checkpoint details
5. **CHANGELOG.md** should track PROJECT_STATE.md version changes
6. **NEXT.md** should update PROJECT_STATE.md when checkpoint completes

---

## Content Maintenance Matrix

| File | Owner | Update Trigger | Review Required |
|------|-------|-----------------|-----------------|
| AI_BOOTSTRAP.md | Tech Lead | Mission change | Product Lead |
| PROJECT_CHARTER.md | Product Lead | Scope change | CTO |
| PROJECT_STATE.md | Sprint Lead | Checkpoint done | Tech Lead |
| ARCHITECTURE.md | Tech Lead | Design change | Architect |
| DEVELOPMENT_GUIDE.md | Engineering Manager | Standard change | Tech Lead |
| PROJECT_MEMORY.md | Tech Lead | New decision | All stakeholders |
| CHANGELOG.md | Release Manager | Version release | Tech Lead |
| NEXT.md | Product Manager | Sprint planning | Tech Lead |

---

## File Size & Complexity

| File | Target Size | Complexity | Update Burden |
|------|-------------|-----------|---------------|
| AI_BOOTSTRAP.md | 500-1000 words | Low | Very low |
| PROJECT_CHARTER.md | 1000-2000 words | Low | Very low |
| PROJECT_STATE.md | 1500-3000 words | Medium | Medium |
| ARCHITECTURE.md | 2000-4000 words | Medium-High | Low |
| DEVELOPMENT_GUIDE.md | 2000-3500 words | Medium | Medium |
| PROJECT_MEMORY.md | 2000-5000 words | Medium | Low |
| CHANGELOG.md | Grows over time | Low | Low |
| NEXT.md | 1000-2000 words | Medium | High |

---

## Success Metrics

Brain v2 files are successful when:

✓ **AI can read all 8 files in sequence and understand the project**  
✓ **Developers can find the answer to any process question**  
✓ **Files are updated consistently (no stale information)**  
✓ **No information is duplicated across files**  
✓ **New team members onboard in <1 hour**  
✓ **Files remain maintainable (not too large, clear sections)**  
✓ **Cross-references are accurate (no dead links)**  
✓ **Files grow with the project (scalable structure)**

---

## Next Steps

1. Create draft content for each file (Task 6)
2. Run AI boot sequence test (Task 7)
3. Verify completeness
4. Get stakeholder review
5. Finalize Brain v2 structure

---

## Document Metadata

- **Version:** 1.0-DRAFT
- **Status:** PLANNING PHASE (Ready for Review)
- **Created:** 2026-07-13
- **Sprint:** D1 — Brain v2 Planning & Migration Audit
- **Scope:** Documentation planning only
