# Certification Process (Product & UI)

This document explains the steps and acceptance criteria for product certification (Mobile, Multilingual, Logo Consistency) used by Converigo.

## Purpose
Certification verifies that visual, interaction, and internationalization requirements meet product standards before a release.

## Scope
- Mobile responsiveness and touch targets
- Multilingual rendering (supported locales)
- Logo and brand asset parity across templates

## Steps
1. Identify target pages and templates to certify.
2. Capture baseline screenshots (desktop + mobile breakpoints) using `qa_tools/hero_capture.py` and `qa_tools/workspace_inspector.py`.
3. Run localization checks across supported locales (see `app/locales/*`).
4. Log issues with reproducible steps, screenshots, and suggested fixes.
5. Propose template/CSS fixes (do not change converter logic).
6. After fixes, capture after-screenshots and produce a before/after comparison.

## Acceptance criteria
- No horizontal overflow at mobile breakpoints listed in the task.
- All interactive touch targets >= 44px where applicable.
- No truncated or clipped localized strings in supported locales.
- Logo assets render consistently (same dimensions, alt text, and file format guidance).

## Reporting
Produce a certification report containing:
- Checklist of pages and breakpoints tested
- Before and after screenshots (linked or embedded)
- PASS/FAIL per page/locale with remediation notes

## Automation
Leverage `qa_tools` for capture, image-diff, and route checks. See `docs/QA_TOOLKIT.md` for commands and examples.
