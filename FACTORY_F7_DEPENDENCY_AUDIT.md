# FACTORY F7 — Gate 0 Dependency Audit (COMPLETED) + Scope Decision Record

Batch   : F7 (docx-to-html, pptx-to-png, pptx-to-jpg)
Branch  : feat/factory-f7
Commits : e6c256b (F7 initial) + 137a8e2 (F7 FIX: pptx-to-jpg + fidelity disclosure)
Baseline: 578f246 (origin/main, Merge PR #84 feat/factory-f6) — worktree wt_f7 was created exactly at this commit (verified via wt_f7 reflog and `git merge-base 578f246 e6c256b = 578f246`).
Written : 2026-09-06 (review FIX round — completes the previously partial Mammoth audit)

---

## 1. Mammoth — completed audit (Gate 0)

Package          : mammoth
Declared floor   : `mammoth>=1.11.0` (requirements.txt:7) — CVE-2025-11849 security floor
Installed        : 1.12.1 (verified: `importlib.metadata.version('mammoth')` under the runtime venv)
Vulnerability scan: PyPI JSON for 1.12.1 reports `"vulnerabilities": []` (no known vulnerabilities against the installed release)

### 1.1 License (explicit, with sources)
- License name: **BSD-2-Clause** ("2-Clause BSD").
- Sources (all three agree):
  - Installed wheel metadata: `.venv/Lib/site-packages/mammoth-1.12.1.dist-info/METADATA` line 8 — `License: BSD-2-Clause` (license file `LICENSE` shipped in the wheel, `license_files: ["LICENSE"]`).
  - PyPI: https://pypi.org/project/mammoth/1.12.1/ — `license: "BSD-2-Clause"`; classifier `License :: OSI Approved :: BSD License`.
  - Upstream repo: https://github.com/mwilliamson/python-mammoth — GitHub displays "BSD-2-Clause license" (LICENSE at repo root).
- BSD-2-Clause is a permissive license approved for commercial/production use; attribution of the upstream copyright notice is retained in the wheel's LICENSE file.

### 1.2 Maintenance status (last release, activity)
- Latest release: **1.12.1**, PyPI upload **2026-08-09T14:11:18Z** (wheel) / **2026-08-09T14:11:20Z** (sdist); GitHub release tag `1.12.1` published 2026-08-09T13:59:19Z.
- Latest upstream commit: "Bump version to 1.12.1", 2026-08-09T13:59:07Z (author mwilliamson).
- Release cadence (GitHub releases.atom): 1.9.1 (2025-05-28) → 1.10.0 (2025-08-02) → 1.11.0 (2025-09-19) → 1.12.0 (2026-03-12) → 1.12.1 (2026-08-09) — steady, roughly quarterly through 2025–2026.
- Repo activity: 706 commits, 22 open issues, 4 open PRs, single owner `michaelwilliamson`; PyPI classifier `Development Status :: 5 - Production/Stable`.
- Verdict: **actively maintained**; last release is 4 weeks old relative to this audit date.

### 1.3 Python 3.11 compatibility (explicit confirmation)
- Metadata classifiers include **`Programming Language :: Python :: 3.11`** (and 3.12); `Requires-Python: >=3.7`.
- Runtime proof on this project: the runtime venv is **Python 3.11.9**; `mammoth 1.12.1` imports and executes under it; the F7 certified suite (12/12 tests) passes under this interpreter (re-validated 2026-09-06, see §4).
- Verdict: **compatible with Python 3.11** — confirmed both by declared metadata and by live execution.

### 1.4 Transitive dependencies (licenses)
mammoth declares exactly **one** dependency: `Requires-Dist: cobble<0.2,>=0.1.3` (installed: **cobble 0.1.4**).
- License: **BSD 2-Clause** — sources: cobble wheel metadata classifier `License :: OSI Approved :: BSD License`; package description "License: `2-Clause BSD`" (cobble-0.1.4.dist-info/METADATA); PyPI https://pypi.org/project/cobble/.
- Same upstream author as mammoth: Michael Williamson (mike@zwobble.org), repo http://github.com/mwilliamson/python-cobble.
- Maintenance: last release 0.1.4 (2024-06-01); no transitive dependencies of its own (`requires_dist: null`); pure-Python, no C extensions; PyPI reports no known vulnerabilities.
- Risk note: cobble's Development Status is "4 - Beta" and its last release predates 2026, but the version is bounded by mammoth's own requirement (`cobble<0.2,>=0.1.3`), its API surface is trivial (data-object helpers used internally by mammoth), and it adds no second-order dependency tree. Accepted risk: low.

Audit verdict: **PASS** — mammoth 1.12.1 (BSD-2-Clause, active, Python 3.11-confirmed, single permissively-licensed transitive dep) satisfies Gate 0.

## 2. PPTX → PNG / JPG fidelity — honest disclosure (D5b MVP scope)

Confirmed limitation (this is exactly what was flagged in review):

- What the converter really does: python-pptx extracts the **text lines of slide 1 only** → reportlab re-renders those lines as plain text (Helvetica 10, white letter page) into a one-page PDF → PyMuPDF rasterizes page 1 at `fitz.Matrix(2, 2), alpha=False` → PNG. JPG reuses this pipeline 1:1, then PIL-encodes the PNG as JPEG (quality 95).
- This is a **text preview, not a visual render of the slide**. Original images, shapes, colors, fonts, backgrounds and layout are **not** reproduced. Slides containing no text render the engine's placeholder line "(slide contains non-text content)".
- Scope is **first slide only, by design**; slides 2+ are not converted at all (single-page, single-file output).

Documentation of the limitation (shipped in commit 137a8e2 so users cannot mistake it for a full visual render):
- Product pages: `app/data/converters/pptx-to-png.json` and `pptx-to-jpg.json` — each carries the FAQ entry "What exactly does the PNG/JPG contain?" ("...It is not a full visual render of the slide - original images, shapes, colors, fonts, backgrounds and layout are not reproduced, and only the first slide is converted (MVP scope)."), an about-formats note ("...not a pixel-perfect copy of the slide design (MVP scope)"), and a description string "(first slide, text preview)".
- Contract artifacts: `pptx-to-png.contract.json` / `pptx-to-jpg.contract.json` description mirrors the same "(first slide, text preview)" wording.
- Code: `app/plugins/document/document_factory.py` module docstring (MVP scope, explicit, D5b) and per-hook docstrings state the text-only, first-slide-only limitation.

---

## 3. PPTX → JPG — scope decision record (no silent narrowing)

Original F7 scope included PPTX→PNG **and** PPTX→JPG. The initial F7 commit (e6c256b) shipped only PNG; the FIX commit (137a8e2) **restores the full scope in-batch** rather than moving or dropping the JPG target.

Official decision (for governance record): **PPTX→JPG is realized inside F7 via commit 137a8e2 — not deferred to another batch, not dropped.**

Explicit rationale:
1. Scope restoration, not expansion: F7's original mandate already listed PPTX→JPG; shipping it closes the gap instead of narrowing the batch.
2. Marginal cost ~zero: `_convert_pptx_to_jpg` reuses the certified png pipeline 1:1 (same text extraction, same reportlab PDF, same PyMuPDF rasterization) with only a final PIL JPEG-encode step (quality 95).
3. Compliance driver: the pre-F7 homepage `STATIC_TARGET_MAP` already advertised `pptx → JPG` with no page behind it (over-claim); shipping the converter makes the public map honest. Map comment updated: "F7: +PNG,+JPG via pptx-to-png / pptx-to-jpg (FIX round)".
4. Ledger integrity: certified ledger append-only 92 → 93 (`certified_converters.json` contains 93 entries incl. `pptx-to-jpg`); contract-path artifacts generated via factory_contract_gen; static-map verifier PASS (52 rows, map == registry derivation).

---

## 4. Live re-validation (2026-09-06, wt_f7 @ 137a8e2)

- Certified suite: `tests/certified/document/test_document_factory_certified.py` — **12 passed** (includes pptx-to-jpg cases) under Python 3.11.9.
- CI probe: `scripts/ci_in_document_factory_probe.py` — **PASS 3/3** (pptx-to-png, pptx-to-jpg, honest-error + all 6 contract/JSON artifacts verified).
- Ledger: 93 certified converters; `pptx-to-png` and `pptx-to-jpg` both present.
- Working-tree note: `RC1_2_CONVERTER_JSON_REPORT.md` shows a local modification from test runs (untracked test artifacts under `temp/`, `tests/results/`); not part of the F7 change set.


