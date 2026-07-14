# Brain v2 Migration Plan

**Status:** AUDIT & PLANNING (No code changes, no files modified)  
**Last Updated:** 2026-07-13  
**Sprint:** D1 — Brain v2 Planning & Migration Audit

---

## Executive Summary

Brain v2 adalah reorganisasi sistematis dari dokumentasi proyek Converigo untuk menciptakan "otak" yang dapat dipahami AI baru tanpa membaca riwayat chat. Rencana ini mendefinisikan pemetaan file lama ke struktur baru, strategi migrasi, dan rollback plan.

---

## Section 1: Current Brain Structure (v1)

### File Inventory

| File | Current Function | Information Stored | Still Needed | Status |
|------|-----------------|--------------------|--------------|----|
| **PROJECT_STATE.md** | Project status & milestone tracking | Vision, phase, current checkpoint, packages, roadmap, workflow | ✓ YES | Keep & Enhance |
| **CHECKPOINTS.md** | Release gate & checkpoint history | Checkpoint definitions, deliverables, status, test results | ✓ YES | Keep & Enhance |
| **DECISIONS.md** | Architecture & product decisions | Decision record (D001-D011), rationale, outcomes | ✓ YES | Keep & Enhance |
| **NEXT.md** | Sprint roadmap & next steps | Completed checkpoints, current work, next focus | ✓ YES | Keep & Enhance |
| **START_HERE.md** | Entry point guide | Usage instructions, checkpoint reference, notes | ✓ YES | Replace with AI_BOOTSTRAP.md |

**Total Files:** 5  
**Current Status:** Functional but dispersed

---

## Section 2: Brain v2 Target Structure

```
brain/
│
├── AI_BOOTSTRAP.md           [NEW] → AI entry point, quick facts
├── PROJECT_CHARTER.md         [NEW] → Mission, vision, non-negotiables
├── PROJECT_STATE.md          [KEEP] → Current phase, checkpoint, metrics
├── ARCHITECTURE.md           [NEW] → Tech decisions, system design
├── DEVELOPMENT_GUIDE.md      [NEW] → Workflows, rules, standards
├── PROJECT_MEMORY.md         [NEW] → Permanent principles & decisions
├── CHANGELOG.md              [KEEP] → Version history
├── NEXT.md                   [KEEP] → Upcoming work
│
└── archive/                  [NEW] → Old documentation (optional, for reference)
    ├── CHECKPOINTS.md        [ARCHIVED] → Historical checkpoint data
    └── DECISIONS.md          [ARCHIVED] → Historical decision log
```

**Total Files (v2):** 8 active files + 2 archived

---

## Section 3: File Mapping (Old → New)

### Migration Strategy

| v1 File | v2 Destination | Content Disposition | Rationale |
|---------|-----------------|----------------------|-----------|
| **START_HERE.md** | **AI_BOOTSTRAP.md** | Rewrite as AI entry point | AI needs quick orientation; content updates |
| **PROJECT_STATE.md** | **PROJECT_STATE.md** | Keep & enhance with metrics | Single source of truth for current state |
| **DECISIONS.md** | **PROJECT_MEMORY.md** (Part A) | Merge permanent decisions into project memory | Permanent principles, legacy decisions archived |
| **DECISIONS.md** (Archive) | **archive/DECISIONS.md** | Archive historical records | Reference for decision history |
| **CHECKPOINTS.md** | **archive/CHECKPOINTS.md** | Archive completed checkpoints | Historical release data, not needed in active brain |
| **CHECKPOINTS.md** (Current) | **PROJECT_STATE.md** (Section) | Current checkpoint moves to project state | Active milestone tracked in state, not history |
| **NEXT.md** | **NEXT.md** | Keep (minimal change) | Already focused on roadmap |
| — | **PROJECT_CHARTER.md** | New file | Define mission, vision, non-negotiables |
| — | **ARCHITECTURE.md** | New file | Consolidate technical decisions |
| — | **DEVELOPMENT_GUIDE.md** | New file | Codify workflows, standards, rules |
| — | **CHANGELOG.md** | Keep & maintain | Version tracking |

---

## Section 4: Information Migration Matrix

### What Gets Moved Where

#### AI_BOOTSTRAP.md (New)
- **Source:** START_HERE.md + PROJECT_STATE.md (intro section)
- **Content:**
  - What is Converigo? (1 sentence)
  - Current mission (this checkpoint)
  - Architecture overview (1 paragraph)
  - File read sequence
  - Quick links
- **Audience:** AI systems on first read

#### PROJECT_CHARTER.md (New)
- **Source:** PROJECT_STATE.md (vision) + DECISIONS.md (strategic decisions)
- **Content:**
  - Vision statement
  - Core values
  - Non-negotiable principles (D001, D003, D004)
  - Product scope boundaries
  - Governance principles
- **Audience:** Anyone making product decisions

#### PROJECT_STATE.md (Keep & Enhance)
- **Keep from v1:**
  - Vision
  - Current Phase
  - Current Milestone
  - Packages in Scope
  - Development Workflow
- **Add:**
  - Current checkpoint metrics (test count, pass rate, etc)
  - Repository health indicators
  - Active branch
  - Known issues
- **Remove:** Generic roadmap summary (move to NEXT.md)

#### ARCHITECTURE.md (New)
- **Source:** DECISIONS.md (D006-D011, technical) + Project understanding
- **Content:**
  - Data model (JSON-driven converters)
  - Integration points (ConverterDataService, HubService, etc)
  - Technology stack summary
  - Key technical decisions
  - System boundaries
- **Audience:** Developers making code changes

#### DEVELOPMENT_GUIDE.md (New)
- **Source:** PROJECT_STATE.md (workflow) + Implicit standards
- **Content:**
  - Sprint workflow
  - Coding standards
  - Testing requirements (min 95% pass rate)
  - Review process
  - Commit & push rules (checkpoint-based)
  - Branching strategy
- **Audience:** Team members on daily work

#### PROJECT_MEMORY.md (New)
- **Source:** DECISIONS.md (D001-D005, D008, permanent principles) + Archive decisions
- **Content:**
  - Coding philosophy
  - Release workflow (checkpoint-first process)
  - Non-breaking change principle
  - JSON-driven architecture principle
  - Documentation-as-code principle
  - Decision log (all decisions indexed)
- **Audience:** Long-term project memory

#### NEXT.md (Keep)
- **Keep:** Current focus, upcoming work
- **Enhance:** Link to PROJECT_STATE.md for metrics

#### CHANGELOG.md (Keep)
- **Keep:** Version history
- **Status:** No changes

---

## Section 5: Information Consolidation

### What Gets Merged

**DECISIONS.md → PROJECT_MEMORY.md + ARCHITECTURE.md**

Decision classifications:

| Decision | Type | Destination |
|----------|------|-------------|
| D001 — Checkpoint-first release | Permanent Process | PROJECT_MEMORY.md |
| D002 — Image Foundation | Milestone | PROJECT_STATE.md (archive) |
| D003 — No code change in docs | Permanent Principle | PROJECT_MEMORY.md |
| D004 — Release blockers only | Process | PROJECT_MEMORY.md |
| D005 — Git readiness validation | Process | PROJECT_MEMORY.md |
| D006 — Universal route compat | Technical | ARCHITECTURE.md |
| D007 — JSON-driven tool pages | Technical | ARCHITECTURE.md |
| D008 — Legacy template containment | Technical | ARCHITECTURE.md |
| D009 — JSON enrichment | Technical | ARCHITECTURE.md |
| D010 — Data-driven hub automation | Technical | ARCHITECTURE.md |
| D011 — Plugin validation framework | Technical | ARCHITECTURE.md |

**CHECKPOINTS.md → archive/CHECKPOINTS.md**

- Current checkpoint moves to PROJECT_STATE.md
- Historical checkpoints archived for reference
- No data loss

---

## Section 6: Migration Steps

### Phase 1: Create New Files (v2 Structure)

```
Step 1: Create AI_BOOTSTRAP.md
        └─ Content: Quick orientation for AI systems
        
Step 2: Create PROJECT_CHARTER.md
        └─ Content: Vision, values, non-negotiables
        
Step 3: Create ARCHITECTURE.md
        └─ Content: Tech decisions, system design
        
Step 4: Create DEVELOPMENT_GUIDE.md
        └─ Content: Workflows, standards, rules
        
Step 5: Create PROJECT_MEMORY.md
        └─ Content: Permanent principles, decisions
        
Step 6: Enhance PROJECT_STATE.md
        └─ Add: Metrics, health indicators
        
Step 7: Create archive/ folder
        └─ Reference: CHECKPOINTS.md, DECISIONS.md (optional)
```

### Phase 2: Update Existing Files (v1 → v2)

```
Step 8: Update START_HERE.md
        └─ Point to AI_BOOTSTRAP.md
        └─ Keep as legacy reference
        
Step 9: Verify NEXT.md
        └─ Links to PROJECT_STATE.md
        └─ No structural changes needed
        
Step 10: Verify CHANGELOG.md
         └─ No changes needed
```

### Phase 3: Validation

```
Step 11: AI Boot Sequence Test
         └─ Read in order: AI_BOOTSTRAP.md → PROJECT_CHARTER.md → PROJECT_STATE.md
            → ARCHITECTURE.md → DEVELOPMENT_GUIDE.md → PROJECT_MEMORY.md → NEXT.md
         └─ Verify AI understands project without chat history
         
Step 12: Information Completeness Audit
         └─ Verify no information gaps
         └─ Verify no redundancy
         └─ Verify consistency across files
         
Step 13: Link Verification
         └─ Cross-reference check
         └─ Dead link detection
```

---

## Section 7: Rollback Plan

### If Migration Fails

**Decision Point:** If new structure doesn't provide sufficient AI context

**Rollback Steps:**

1. **Immediate Rollback:**
   - Keep original files (v1) as-is
   - Delete new v2 files
   - Revert any updates to existing files
   - No code impact

2. **Partial Rollback:**
   - Keep successful new files (e.g., DEVELOPMENT_GUIDE.md, PROJECT_CHARTER.md)
   - Revert failing files
   - Blend structures (hybrid v1/v2)

3. **Alternative:** Iterative Refinement
   - Keep new structure
   - Incrementally improve content
   - Add missing context as identified

### No Data Loss
- All v1 files remain intact
- v2 is additive (new files, not replacements)
- Migration is non-destructive

---

## Section 8: Risk Assessment

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| AI doesn't understand project after v2 | LOW | HIGH | Create AI_BOOT_SEQUENCE.md, test thoroughly |
| Information gaps in new structure | MEDIUM | MEDIUM | Run completeness audit (Task 7) |
| Files become redundant/contradictory | MEDIUM | MEDIUM | Create consistency checker in NEXT.md |
| Developers can't find information | LOW | MEDIUM | Create index in AI_BOOTSTRAP.md |
| Structure doesn't scale beyond C3.7 | MEDIUM | LOW | Design for extensibility (Task 2) |

### Mitigation Strategy

1. **Completeness Check:** Audit ensures all v1 info captured in v2
2. **AI Testing:** Run AI boot sequence with fresh prompt
3. **Consistency:** Document guidelines for future updates
4. **Scalability:** Design file structure to handle future checkpoints

---

## Section 9: Success Criteria

Brain v2 is successful when:

✓ **AI can understand project state** without reading chat history  
✓ **All v1 information is preserved** (no data loss)  
✓ **New structure is intuitive** (developers quickly find what they need)  
✓ **Files are maintainable** (easy to update during sprints)  
✓ **No code changes required** (documentation only)  
✓ **Extensible** (scales to future checkpoints)  
✓ **Consistent** (no conflicting information)

---

## Section 10: Timeline

- **Task 1:** Inventory brain/ files → COMPLETE ✓
- **Task 2:** Design v2 structure → IN PROGRESS
- **Task 3:** Create migration plan (THIS DOC) → COMPLETE ✓
- **Task 4:** Create file purposes → PENDING
- **Task 5:** Create boot sequence → PENDING
- **Task 6:** Create draft contents → PENDING
- **Task 7:** Audit & recommendations → PENDING

**Total Effort:** Audit & planning phase (no implementation yet)

---

## Next Steps

1. Review this migration plan
2. Create file purpose document (Task 4)
3. Define AI boot sequence (Task 5)
4. Create draft contents for all 8 files (Task 6)
5. Audit completeness (Task 7)
6. Provide recommendations for Brain v2 readiness

---

## Document Metadata

- **Version:** 1.0-DRAFT
- **Status:** AUDIT PHASE (Ready for Review)
- **Created:** 2026-07-13
- **Sprint:** D1 — Brain v2 Planning & Migration Audit
- **Scope:** Documentation & planning only (no code changes)
