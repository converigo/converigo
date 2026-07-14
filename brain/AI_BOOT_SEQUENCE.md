# AI Boot Sequence — Brain v2 Reading Order

**Status:** PLANNING PHASE  
**Last Updated:** 2026-07-13  
**Sprint:** D1 — Brain v2 Planning & Migration Audit

---

## Purpose

Dokumen ini mendefinisikan urutan optimal bagi AI untuk membaca file Brain v2 agar memahami proyek Converigo tanpa membaca riwayat chat. Setiap tahap dirancang untuk membangun konteks secara progresif.

---

## Boot Sequence

### ⏱ Estimated Total Read Time: 20-30 minutes

```
┌─────────────────────────────────────────────────────┐
│           AI BOOT SEQUENCE — Brain v2               │
│        (Complete Project Understanding)             │
└─────────────────────────────────────────────────────┘

    STAGE 1 — RAPID ORIENTATION (5 min)
    ═════════════════════════════════════════════════
    1. AI_BOOTSTRAP.md
       └─ What is Converigo?
       └─ Current mission
       └─ Boot sequence (this document)

    STAGE 2 — GOVERNANCE & CONTEXT (5 min)
    ═════════════════════════════════════════════════
    2. PROJECT_CHARTER.md
       └─ Vision & core values
       └─ Non-negotiable principles
       └─ Product scope boundaries

    STAGE 3 — CURRENT STATE (5 min)
    ═════════════════════════════════════════════════
    3. PROJECT_STATE.md
       └─ Where are we now?
       └─ Current checkpoint metrics
       └─ Repository health

    STAGE 4 — TECHNICAL FOUNDATION (5 min)
    ═════════════════════════════════════════════════
    4. ARCHITECTURE.md
       └─ System design overview
       └─ Technology stack
       └─ Integration points

    STAGE 5 — OPERATIONAL STANDARDS (5 min)
    ═════════════════════════════════════════════════
    5. DEVELOPMENT_GUIDE.md
       └─ How we work day-to-day
       └─ Coding standards
       └─ Testing requirements

    STAGE 6 — INSTITUTIONAL MEMORY (3 min)
    ═════════════════════════════════════════════════
    6. PROJECT_MEMORY.md
       └─ Permanent principles
       └─ Decision history
       └─ Why decisions were made

    STAGE 7 — FUTURE ROADMAP (2 min)
    ═════════════════════════════════════════════════
    7. NEXT.md
       └─ What's next?
       └─ Current progress
       └─ Upcoming milestones

    ═════════════════════════════════════════════════
    TOTAL: ~30 minutes for complete context
```

---

## Detailed Boot Sequence

### STAGE 1: Rapid Orientation (5 min)

**File:** [AI_BOOTSTRAP.md](AI_BOOTSTRAP.md)

**What This Stage Does:**
- Introduces Converigo in one sentence
- Shows current mission
- Explains why this boot sequence exists
- Provides file directory map
- Sets expectations

**Key Questions Answered:**
- What is Converigo?
- What are we doing right now?
- Where should I start reading?

**Success Criteria:**
After this stage, AI should understand: "Converigo is a file conversion platform, currently working on [current checkpoint], and here's how to learn more."

**Next:** → Proceed to Stage 2

---

### STAGE 2: Governance & Context (5 min)

**File:** [PROJECT_CHARTER.md](PROJECT_CHARTER.md)

**What This Stage Does:**
- Defines what Converigo IS (not what we build)
- Establishes non-negotiable principles
- Sets scope boundaries
- Explains decision governance

**Key Questions Answered:**
- What is Converigo's mission?
- What are core non-negotiables?
- What's in/out of scope?
- How do we make decisions?

**Success Criteria:**
After this stage, AI should understand: "Converigo's mission is X, we never change Y, and we only do Z."

**Next:** → Proceed to Stage 3

---

### STAGE 3: Current State (5 min)

**File:** [PROJECT_STATE.md](PROJECT_STATE.md)

**What This Stage Does:**
- Shows current project phase
- Lists current milestone & checkpoint
- Shows packages in scope
- Reports repository health
- Lists known issues

**Key Questions Answered:**
- What checkpoint are we on?
- What are we building this sprint?
- Is the repository healthy?
- Are there blockers?

**Success Criteria:**
After this stage, AI should understand: "We're at checkpoint C3.8, working on [current milestone], tests passing [X%], and we're focused on [next goal]."

**Cross-References to Review:**
- Link to CHECKPOINTS.md for historical data (optional)
- Link to DEVELOPMENT_GUIDE.md for current workflow

**Next:** → Proceed to Stage 4

---

### STAGE 4: Technical Foundation (5 min)

**File:** [ARCHITECTURE.md](ARCHITECTURE.md)

**What This Stage Does:**
- Explains system design & architecture
- Shows technology stack
- Documents integration points
- Explains technical decisions (Why is code organized this way?)

**Key Questions Answered:**
- How is the system organized?
- What technologies do we use?
- What are the key components?
- How do services integrate?

**Success Criteria:**
After this stage, AI should understand: "The system uses a JSON-driven converter model, integrates X services, uses Y tech stack, and is organized around [data flow]."

**Cross-References to Review:**
- Links to DEVELOPMENT_GUIDE.md for coding patterns
- Links to PROJECT_MEMORY.md for why we chose this architecture

**Next:** → Proceed to Stage 5

---

### STAGE 5: Operational Standards (5 min)

**File:** [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)

**What This Stage Does:**
- Defines daily workflows
- Establishes coding standards
- Documents testing requirements
- Explains review & commit process
- Lists common tasks

**Key Questions Answered:**
- How do we code?
- What tests do we run?
- How do we review code?
- What are the commit rules?
- How do we release?

**Success Criteria:**
After this stage, AI should understand: "We follow these standards, require tests, review via X process, and release using Y mechanism."

**Cross-References to Review:**
- Links to ARCHITECTURE.md for code patterns
- Links to PROJECT_MEMORY.md for principles

**Next:** → Proceed to Stage 6

---

### STAGE 6: Institutional Memory (3 min)

**File:** [PROJECT_MEMORY.md](PROJECT_MEMORY.md)

**What This Stage Does:**
- Records permanent principles
- Documents decision history (D001-D011+)
- Preserves "why" behind decisions
- Prevents re-litigating old debates

**Key Questions Answered:**
- Why did we make decision X?
- What are our permanent principles?
- What mistakes did we learn from?
- What was decided long ago?

**Success Criteria:**
After this stage, AI should understand: "We learned X the hard way, decided Y because Z, and never again do A because B."

**Decision Reference:**
- Link to DECISIONS.md archive for historical records
- Link to CHECKPOINTS.md archive for completed milestones

**Next:** → Proceed to Stage 7

---

### STAGE 7: Future Roadmap (2 min)

**File:** [NEXT.md](NEXT.md)

**What This Stage Does:**
- Shows what's in progress
- Lists what's blocked & why
- Previews next checkpoint
- Tracks progress metrics

**Key Questions Answered:**
- What's in progress?
- What's blocked?
- What comes next?
- What's the timeline?

**Success Criteria:**
After this stage, AI should understand: "We just completed X, currently working on Y, blocked by Z, and next is A."

**Cross-References to Review:**
- Updates PROJECT_STATE.md when checkpoint completes
- References DEVELOPMENT_GUIDE.md for sprint workflow

**Next:** → Boot sequence complete!

---

## Post-Boot Information Access

After completing the boot sequence, AI can:

1. **Answer project questions** by consulting appropriate files
2. **Make decisions consistent with** PROJECT_CHARTER.md + PROJECT_MEMORY.md
3. **Code following standards** from DEVELOPMENT_GUIDE.md
4. **Understand system design** from ARCHITECTURE.md
5. **Check current progress** from PROJECT_STATE.md
6. **Find technical rationale** from ARCHITECTURE.md + PROJECT_MEMORY.md
7. **Learn project history** from CHANGELOG.md

---

## Common Question → Correct File Mapping

| Question | File | Section |
|----------|------|---------|
| What is Converigo? | AI_BOOTSTRAP.md | Project definition |
| What's the mission? | PROJECT_CHARTER.md | Vision statement |
| Where are we now? | PROJECT_STATE.md | Current phase |
| What's next? | NEXT.md | Next checkpoint |
| How do I code? | DEVELOPMENT_GUIDE.md | Coding standards |
| How do I test? | DEVELOPMENT_GUIDE.md | Testing requirements |
| Why do we do X? | PROJECT_MEMORY.md | Decision history |
| How is the system designed? | ARCHITECTURE.md | System overview |
| What's the history? | CHANGELOG.md | Release history |
| What have we learned? | PROJECT_MEMORY.md | Lessons learned |
| What tech do we use? | ARCHITECTURE.md | Tech stack |
| Are there blockers? | NEXT.md | Current blockers |
| What are non-negotiables? | PROJECT_CHARTER.md | Core principles |
| Is the repo healthy? | PROJECT_STATE.md | Repository health |

---

## Pre-Boot vs Post-Boot Capability

### Pre-Boot (Before reading Brain v2)
- ❌ No understanding of project
- ❌ Can't make informed decisions
- ❌ Can't follow coding standards
- ❌ Can't predict decision consistency
- ❌ Requires human context/prompts

### Post-Boot (After reading Brain v2)
- ✅ Full project understanding
- ✅ Can make decisions aligned with vision
- ✅ Knows coding & testing standards
- ✅ Understands why decisions were made
- ✅ Can work autonomously on tasks
- ✅ Can onboard new team members
- ✅ Can review code for consistency

---

## Boot Sequence Testing

### Test Checklist (for Task 7)

After reading the complete boot sequence, verify AI can:

- [ ] **Identify Converigo** — What is it?
- [ ] **State the mission** — What are we doing?
- [ ] **Describe current checkpoint** — Where are we?
- [ ] **Explain system architecture** — How is it built?
- [ ] **List coding standards** — How do we code?
- [ ] **Identify non-negotiables** — What never changes?
- [ ] **Predict next steps** — What's coming?
- [ ] **Explain key decisions** — Why D001-D011?
- [ ] **Answer "should we..." questions** — Make consistent decisions
- [ ] **Find answers independently** — Use file index

### Success Criteria
All 10 test items should pass. If not, identify missing information and update files.

---

## Boot Sequence Evolution

As the project grows, the boot sequence adapts:

| Checkpoint | New Information | Update Boot Sequence |
|-----------|-----------------|-------------------|
| C1-C3 | New milestone data | Update PROJECT_STATE.md + NEXT.md |
| C5+ | Major architecture | Update ARCHITECTURE.md |
| Any | New decision | Update PROJECT_MEMORY.md |
| Any | New principle | Update PROJECT_CHARTER.md |
| Any | Standard change | Update DEVELOPMENT_GUIDE.md |

The boot sequence structure (7 stages) remains constant; only file contents evolve.

---

## Troubleshooting

### If AI doesn't understand project after boot:
1. Check which file is missing information
2. Update that file with necessary context
3. Re-run boot sequence test
4. Record findings for Task 7 audit

### If boot sequence takes too long (>30 min):
1. Files may be too long
2. Consider splitting into sub-documents
3. Use better structure (headers, summaries)
4. Verify no redundancy between files

### If AI makes decisions inconsistent with project:
1. Check PROJECT_CHARTER.md clarity
2. Check PROJECT_MEMORY.md decision documentation
3. Verify AI read both files
4. Update files with clearer guidance

---

## Document Metadata

- **Version:** 1.0-DRAFT
- **Status:** PLANNING PHASE (Ready for Review)
- **Created:** 2026-07-13
- **Sprint:** D1 — Brain v2 Planning & Migration Audit
- **Scope:** AI boot sequence specification (no implementation)
