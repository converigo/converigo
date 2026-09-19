# ANALYTICS ISOLATION — IMPLEMENTATION PLAN

**Project:** Converigo
**Document type:** DESIGN-ONLY / READ-ONLY implementation plan (no implementation performed)
**Supervisor decision being implemented:** **Option C — separate test analytics source** (primary structural remediation)
**Companion document:** `ANALYTICS_DATA_QUALITY_ROOT_CAUSE_REPORT` (root-cause audit; 83.28% TestClient contamination)

---

## 1. Executive Summary

Production analytics events and test analytics events currently share one sink: the file at
`app/logs/analytics.jsonl`. Every `AnalyticsService()` in the application is constructed with the
**default** storage path (`settings.ANALYTICS_LOG_FILE`), and nothing on the write path distinguishes
production traffic from pytest `TestClient`, browser E2E (HeadlessChrome), or internal probe traffic.

This plan designs the structural separation:

```
TEST / E2E TRAFFIC   →   tmp/test_analytics.jsonl      (test sink, gitignored)
REAL PRODUCTION      →   app/logs/analytics.jsonl      (production sink, untouched)
```

**Recommended design: Option C1 — set `ANALYTICS_LOG_FILE` in `tests/conftest.py` at module level,
before any application module is imported.**

C1 is recommended because the codebase has three verified properties that make it uniquely safe:

1. **`settings` is pure `os.getenv`** — there is no `python-dotenv`, no `.env` loading, no config
   file, no vault. The process environment is the *only* configuration source, so setting the
   variable in-process is *guaranteed* to take effect.
2. **`AnalyticsService` resolves its sink at construction time** from `settings.ANALYTICS_LOG_FILE`
   (`analytics_service.py:32`), and all five instantiation sites are **module-level**. Because
   `tests/conftest.py` imports **zero** application modules, its module-level code runs *before* any
   `from app.main import app` — so every `AnalyticsService()` in the process binds to the test sink.
3. **The E2E uvicorn subprocess inherits the parent environment verbatim** — `conftest.py:75` does
   `env = os.environ.copy()` and `conftest.py:98` passes it to `Popen`. The subprocess performs a
   **fresh** `import app.main` in a fresh Python process, re-reads the inherited
   `ANALYTICS_LOG_FILE`, and binds to the test sink **automatically — with no extra plumbing**.

**The entire change is one file: `tests/conftest.py`.** No application source changes. No reader /
dashboard changes (that was Option B, not selected). No `analytics.jsonl` changes. Historical data
is preserved verbatim. Production behavior is provably unchanged, because `tests/conftest.py` is
never imported by the production runtime.

**Files expected to change:** `tests/conftest.py` (required), `tests/test_analytics_isolation.py`
(new test module), and *optionally* two CI workflow files for in-image consistency only.

---

## 2. Confirmed Current Architecture

### 2.1 Configuration layer — `app/core/settings.py`

- Plain `class Settings` with an `__init__` full of `os.getenv(...)` calls. **Not** pydantic.
- `ANALYTICS_LOG_FILE` is read at `settings.py:36`:
  `Path(os.getenv("ANALYTICS_LOG_FILE", str(self.LOG_DIR / "analytics.jsonl")))`.
- `DISABLE_ANALYTICS` at `settings.py:40` — consumed **only** by `app/core/template_context.py`
  (GA4 gating). It is **not** read anywhere on the write path (verified by search).
- Module-level singleton: `settings = Settings()` at `settings.py:74`.
- **No `python-dotenv`, no `load_dotenv`, no `.env` parsing exists anywhere in `app/`** (verified by
  repository-wide search; only false positives in `templates.py` for `env.globals`).
  ⇒ **the process environment is the sole config source.**

### 2.2 Writer layer — `app/services/analytics_service.py`

- `AnalyticsService.__init__(storage_path=None)` (lines 31–34):
  `self.storage_path = Path(storage_path or settings.ANALYTICS_LOG_FILE)`, then
  `self.storage_path.parent.mkdir(parents=True, exist_ok=True)`, then a per-instance
  `threading.Lock`. **No file handle is held** — only a `Path` object; the sink is re-opened per write.
- Single write choke point `_write_event` (lines 173–182): serialize → `mkdir(parents=True,
  exist_ok=True)` → `open("a")` → write line. **No `try/except`** — a genuinely unavailable sink
  **raises and fails the request**. This is **fail-loud by existing architecture**; the design does
  not add (and does not need) any fail-open fallback.
- Single read choke point `_load_events` (lines 184–200): returns `[]` if the file is missing,
  skips blank/unparseable lines. **Read-tolerant.**
- All eight typed trackers funnel through `track_event` (line 36) → `_build_event` → `_write_event`.
- Event marker fields relevant to test design: `conversion_id` (line 157, sourced from the
  `x-conversion-id` request header via `main.py:84` → `state["conversion_id"]`), `page_path`
  (line 136/140), `user_agent` / `ip_hash` / `visitor_id` (lines 158–160), `request_id` (line 156).

### 2.3 Instantiation sites (all module-level, all default sink)

| File | Line | Form |
|---|---|---|
| `app/main.py` | 51 | `analyticsService()` — middleware `page_view`/`error`; `track_download` at 513 |
| `app/routers/convert.py` | 56 | `AnalyticsService()` — funnel events |
| `app/routers/upload.py` | 11 | `AnalyticsService()` — upload events |
| `app/routers/dashboard.py` | 27 | `AnalyticsService()` — reader |
| `app/services/analytics_intelligence_service.py` | 36 | `analytics_service or AnalyticsService()` (**injectable**) |

### 2.4 Test harness

- `tests/conftest.py` imports **only** stdlib (`os`, `socket`, `subprocess`, `sys`, `threading`,
  `time`, `urllib.request`, `pathlib`) and `pytest`. **It does not import `app`.**
- Session-scoped `app_server` fixture (lines 43–136) starts a real uvicorn subprocess:
  `[sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port),
  "--log-level", "info"]`, `cwd=repo_root`, **`env=os.environ.copy()`** (line 75 → passed at line 98).
- `app_base_url` (lines 139–147) waits on `/health`; `ensure_app_server` (lines 152–154) is a
  function-scoped alias. The fixture is **not autouse**.
- 60+ test modules do `from app.main import app` **at module level** (import-time `TestClient`).
- Browser E2E modules use `pytestmark = pytest.mark.usefixtures("app_base_url")` and/or a `page`
  fixture: `test_convert_button_state.py`, `test_final_ui_validation.py`, `test_ui_target_mapping.py`,
  `test_phase_c_mixed_batch.py`, `test_globalfmt_intersection.py`,
  `test_phase25_rc1_globalfmt_consensus.py`, `test_wav_ui_default_target.py`.
- `pytest.ini`: `pythonpath = .`, `testpaths = tests`, one marker (`certified`). **No `addopts`,
  no `env`, no `plugins`, no env-setting mechanism.**
- No `pyproject.toml`, no `setup.cfg`, no `tox.ini` (verified absent).
- Installed tooling: `pytest 9.1.1`, `pytest-asyncio 1.4.0`, `pytest-timeout 2.4.0`,
  `playwright 1.62.0`, `httpx 0.28.1`. **`pytest-env` is NOT installed. `pytest-xdist` is NOT
  installed** (the `PYTEST_XDIST_WORKER` read at `conftest.py:56` is defensive only).

### 2.5 Persistence and git status of the sink

- `app/logs/analytics.jsonl` is **NOT git-tracked** (verified: `git ls-files --error-unmatch` fails).
  It is ignored via `.gitignore:27` (`app/logs/`).
- ⇒ The 90,686-line file is a **local working-tree artifact** — not in CI checkouts, not in the
  production image.
- `tmp/` exists, is writable, and is gitignored via `.gitignore:55` (`tmp*/`) — verified:
  `git check-ignore tmp/test_analytics.jsonl` → matched by `.gitignore:55`.

### 2.6 Production runtime

- `Dockerfile`: `WORKDIR /app`, `COPY . ./`, `CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0
  --port ${PORT:-8000} ..."]`. **`ANALYTICS_LOG_FILE` is never set** ⇒ default
  `app/logs/analytics.jsonl`, self-created at first write.
- `railway.toml` `startCommand` mirrors the Dockerfile CMD and likewise sets no analytics env.
- The image contains `tests/` (via `COPY . ./`), but **`conftest.py` is never imported at production
  runtime** — uvicorn imports only `app.main:app`.

---

## 3. Import/Initialization Order

The correctness of Option C1 rests entirely on ordering. Traced precisely:

```
pytest starts
  └─ reads pytest.ini (pythonpath=., testpaths=tests)          ← no app import, no env vars
  └─ collects tests/ → imports tests/conftest.py FIRST         ← conftest for the test dir
       ├─ module-level code executes HERE                      ← ★ the env override goes HERE
       └─ imports only stdlib + pytest                          ← app NOT yet imported
  └─ imports test modules (collection)
       └─ e.g. tests/test_analytics_smoke.py:4  "from app.main import app"
            ├─ import app.core.settings → settings = Settings()
            │    └─ reads os.environ["ANALYTICS_LOG_FILE"]      ← ★ sees the override
            ├─ import app.services.analytics_service
            ├─ import app.main → analytics_service = AnalyticsService()
            │    └─ storage_path = settings.ANALYTICS_LOG_FILE  ← ★ binds TEST sink
            ├─ import app.routers.convert  → AnalyticsService()  ← binds TEST sink
            ├─ import app.routers.upload   → AnalyticsService()  ← binds TEST sink
            └─ import app.routers.dashboard → AnalyticsService() ← binds TEST sink
  └─ test session runs (TestClient + browser E2E)
  └─ app_server fixture (lazy, session-scoped)
       └─ env = os.environ.copy()                               ← ★ includes the override
       └─ Popen([python, -m, uvicorn, app.main:app, ...], env=env)
            └─ fresh process → fresh import app.main → fresh Settings()
                 └─ binds TEST sink                             ← ★ E2E covered automatically
```

**Answer to the Step 1 questions:**

1. **When is `AnalyticsService() → settings.ANALYTICS_LOG_FILE` evaluated?** At the *import time of
   whichever module constructs it* (all five sites are module-level), and again at the *spawn time*
   of the uvicorn E2E subprocess (fresh process, fresh import).
2. **Can `ANALYTICS_LOG_FILE` be safely overridden before application imports?** **Yes — and only via
   the process environment.** Three guarantees make it safe:
   - `os.getenv` is the sole config source (no dotenv / file / vault can override or shadow it);
   - `tests/conftest.py` imports no `app` module, so its module-level code provably precedes every
     `from app.main import app`;
   - pytest provably imports a directory's `conftest.py` before the test modules in that directory
     (it must, in order to resolve fixtures during collection).
3. **Why not `pytest.ini`?** Native `pytest.ini` has no `env` capability; `pytest-env` (which adds
   `[pytest] env =`) is **not installed** and would be a new dependency (see Option C2).

**One ordering hazard, verified as non-existent:** if any `-p` plugin or rootdir `conftest.py`
imported `app` before `tests/conftest.py`, the override would arrive too late. Verified: `pytest.ini`
declares no `plugins`/`addopts`; there is **no root-level `conftest.py`** (only `tests/conftest.py`;
unrelated copies under `.tmp/`, `wt_*`, `tmp_pr69_wt*` are not collected). The guarantee holds.

---

## 4. Isolation Options

Four candidate mechanisms evaluated against the required criteria.

### OPTION C1 — Set `ANALYTICS_LOG_FILE` in `tests/conftest.py` before application import

Set the environment variable at **module level** in `tests/conftest.py` (module-level code runs at
conftest import, which precedes every `from app.main import app`).

| Criterion | Assessment |
|---|---|
| **Affected files** | `tests/conftest.py` (1 file). Zero application source. |
| **Import-order requirements** | Must be module-level (not inside a fixture). Module-level conftest code provably precedes test-module collection imports (Section 3). |
| **TestClient coverage** | ✅ Full. All five module-level `AnalyticsService()` instances bind the test sink at import. |
| **E2E coverage** | ✅ Full, **automatic**. `app_server` does `env = os.environ.copy()` → the uvicorn subprocess inherits the override → fresh `import app.main` re-reads it. No extra plumbing. |
| **CI coverage** | ✅ Local pytest: full. In-image pytest (Docker): needs `-e ANALYTICS_LOG_FILE=…` passthrough to be consistent — but CI containers are ephemeral and `app/logs/` is gitignored, so CI has *never* contaminated the persistent file (Section 8). CI change is optional. |
| **Production safety** | ✅ `conftest.py` is never imported by the production runtime (uvicorn imports only `app.main:app`). Railway/Docker set no `ANALYTICS_LOG_FILE` ⇒ production default is untouched. |
| **Regression risk** | **Very low.** No test reads the live `app/logs/analytics.jsonl` (verified by search); analytics unit tests construct `AnalyticsService(tmp_path/…)` and are unaffected (their events carry an empty UA and an explicit `storage_path`). |
| **Complexity** | ~10 lines in one file. |
| **Rollback** | Delete the added lines. No state to restore (the test sink is a gitignored scratch file). |
| **Future maintainability** | High. Any *new* test channel that runs through pytest or spawns the `app_server` subprocess inherits the isolation for free. |

### OPTION C2 — pytest configuration / environment mechanism

Use `[pytest] env = ANALYTICS_LOG_FILE=…` in `pytest.ini`.

| Criterion | Assessment |
|---|---|
| **Affected files** | `pytest.ini` + `requirements.txt` (new dev dep). |
| **Import-order requirements** | The plugin sets env during pytest startup — before conftest/test import. Ordering is fine. |
| **TestClient / E2E coverage** | Same as C1 (env is set before collection; subprocess inherits it). |
| **CI coverage** | Same as C1; still needs Docker `-e` passthrough for in-image runs. |
| **Production safety** | ✅ Same as C1 — `pytest.ini` is not read at production runtime. |
| **Regression risk** | Low, **but adds a new dependency** (`pytest-env`) to a project that currently has none, plus a version-pinning decision. |
| **Complexity** | Higher than C1 (dependency + pin + install in the CI image's `pip install` step). |
| **Rollback** | Remove the `env =` line and uninstall the plugin. |
| **Future maintainability** | Medium. The mechanism lives in `pytest.ini`, a natural home; but the extra dependency is a permanent cost, and the CI `pip install` lines would need updating. |

**Verdict:** functionally equivalent to C1 but strictly worse operationally (a new dependency for
something one line of `os.environ` achieves). **Rejected** — unless the team prefers config-over-code.

### OPTION C3 — Repoint `AnalyticsService` instances through fixtures

A session-scoped autouse fixture that, at setup, reassigns `app.main.analytics_service`,
`app.routers.convert.analytics_service`, `app.routers.upload.analytics_service`,
`app.routers.dashboard.analytics_service` (and reconstructs `AnalyticsIntelligenceService`) to a
`tmp_path`-backed instance.

| Criterion | Assessment |
|---|---|
| **Affected files** | `tests/conftest.py` (fixture) — but it must enumerate **every** instantiation site, coupling the test harness to app internals. |
| **Import-order requirements** | None (it mutates already-imported modules). |
| **TestClient coverage** | ⚠️ **Partial.** `ObservabilityMiddleware` captures `analytics_service` from the `app.main` namespace at *import* time; reassigning the module attribute later does **not** change the object the middleware already bound. `page_view`/`error` events would still hit the production sink. A **real** coverage gap, not a theoretical one. |
| **E2E coverage** | ❌ **None.** The uvicorn subprocess is a separate process with its own module-level instances; in-process monkeypatching cannot reach it. E2E would need a separate mechanism — i.e. it would fall back to C1's env approach anyway. |
| **CI / production safety** | ✅ Test-only. |
| **Regression risk** | **High.** Miss one instantiation site (or a future one) and that channel leaks to production silently. Fragile by construction. |
| **Complexity** | Highest. Per-site enumeration plus a middleware-capture workaround. |
| **Rollback** | Remove the fixture. |
| **Future maintainability** | **Poor** — every new `AnalyticsService()` in app code silently breaks isolation. |

**Verdict:** **Rejected.** Strictly dominated by C1: it covers fewer channels, couples the harness to
app internals, and still needs C1's env mechanism for E2E.

### OPTION C4 — Dedicated analytics environment abstraction

Introduce an indirection in application code — e.g. a `get_analytics_sink()` factory, an
`AnalyticsService.from_settings()` classmethod, or a test/prod mode flag that the writer consults.

| Criterion | Assessment |
|---|---|
| **Affected files** | `app/core/settings.py`, `app/services/analytics_service.py`, and all five instantiation sites — **application source changes**, which the supervisor's Option C decision was designed to avoid. |
| **Import-order requirements** | Depends on design; a mode flag read at construction time reintroduces the same ordering constraints as C1. |
| **TestClient / E2E / CI coverage** | Can be complete, but only if the flag propagates to the E2E subprocess — which again happens most naturally via the environment, i.e. C1. |
| **Production safety** | ⚠️ Touches the write path. Any new branch on the hot write path is a new way to accidentally drop real production events — the exact risk class Option C was chosen to avoid. |
| **Regression risk** | **Highest.** Modifies production code and the write path; requires re-validating all analytics unit tests and the certified suites. |
| **Complexity** | Highest. New abstraction, setting, tests, docs. |
| **Rollback** | Revert application source (multiple files) — heavier and riskier than a test-harness revert. |
| **Future maintainability** | Good in the abstract, but it pays a permanent production-code cost for a problem that originates entirely in the test harness. |

**Verdict:** **Rejected** as the vehicle for Option C. (Its write-path-gating idea corresponds to the
*separate* Option A from the root-cause report — a possible future complement, not this task.)

### Comparative matrix

| Criterion | C1 conftest env | C2 pytest-env | C3 fixture repoint | C4 app abstraction |
|---|---|---|---|---|
| TestClient coverage | ✅ | ✅ | ⚠️ partial | ✅ |
| E2E coverage | ✅ automatic | ✅ automatic | ❌ none | ✅ (via env) |
| Application source changed | **none** | none | none | **yes** |
| New dependency | no | **yes** | no | no |
| Channels covered by design | all | all | subset | all |
| Coupling to app internals | none | none | **high** | medium |
| Implementation size | ~10 lines / 1 file | small + dep | medium | large |
| Rollback ease | trivial | trivial | trivial | hard |

---

## 5. Recommended Design

**Option C1**, implemented as a module-level environment override in `tests/conftest.py` plus a
session-scoped clean-slate fixture. Design-level sketch (not implementation):

```python
# tests/conftest.py — TOP OF FILE, above everything else
import os
from pathlib import Path

import pytest   # existing import

# --- Analytics isolation (Option C1) -------------------------------------
# MUST be module-level (not inside a fixture): pytest imports this conftest
# before it imports any test module, so this runs before every
# `from app.main import app`. Settings reads os.getenv only (no dotenv),
# so this variable is authoritative. The uvicorn E2E subprocess inherits it
# via app_server's `env = os.environ.copy()`.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROD_SINK = (_REPO_ROOT / "app" / "logs" / "analytics.jsonl").resolve()
_TEST_SINK = Path(os.environ.get("CONVERIGO_TEST_ANALYTICS_SINK")
                  or (_REPO_ROOT / "tmp" / "test_analytics.jsonl"))
if _TEST_SINK.resolve() == _PROD_SINK:
    raise RuntimeError("Refusing to point the test analytics sink at the production sink")
os.environ["ANALYTICS_LOG_FILE"] = str(_TEST_SINK)


@pytest.fixture(scope="session", autouse=True)
def _clean_test_analytics_sink():
    """Give every session a clean test sink; leave it in place afterwards for
    inspection (it is gitignored). Never touches the production sink."""
    _TEST_SINK.parent.mkdir(parents=True, exist_ok=True)
    if _TEST_SINK.exists():
        _TEST_SINK.unlink()
    yield
# -------------------------------------------------------------------------

# ... existing fixtures (_drain_subprocess_output, app_server, app_base_url, ...)
```

### 5.1 Design decisions and rationale

| Decision | Rationale |
|---|---|
| **Absolute, repo-root-derived path** (`Path(__file__).resolve().parents[1] / "tmp" / …`) | Tests may run from any cwd, and the uvicorn subprocess starts with `cwd=repo_root`. A *relative* path would resolve differently across the two processes and silently break the E2E channel. Absolute ⇒ identical in both. |
| **`tmp/test_analytics.jsonl`** as the sink | `tmp/` already exists, is writable, and is gitignored (`.gitignore:55 tmp*/` — verified), so test events never pollute the repo and never need cleanup in version control. |
| **Unconditional assignment** (`os.environ[...] = …`), not `setdefault` | `setdefault` would silently honor a stale/ambient `ANALYTICS_LOG_FILE` and leak to production. The isolation guarantee must be deterministic. |
| **Escape hatch via `CONVERIGO_TEST_ANALYTICS_SINK`** | Allows an advanced user/CI to redirect the test sink (e.g. a per-worker path). The hard-fail guard makes it impossible to accidentally point it at production — consistent with the existing fail-loud write path. |
| **Hard-fail guard instead of a fallback** | `_write_event` has no `try/except` (fail-loud by architecture). Mirroring that philosophy in conftest keeps behavior predictable: a misconfiguration stops the session rather than corrupting the production sink. **No fail-open logic is introduced anywhere.** |
| **Clean-slate at session *start*, not teardown** | Removes stale events from a previous run so isolation assertions are exact; leaves the file behind afterwards for developer inspection. Deleting at teardown would destroy evidence exactly when someone needs it. |
| **`unlink()` is safe mid-session** | `AnalyticsService` stores a `Path`, not a file handle (verified at `analytics_service.py:31-34`); the file is re-created by the next `open("a")`. Unlinking cannot break an already-bound sink. |
| **No application-source change** | The whole mechanism rides on the existing `settings`/env contract and the existing `os.environ.copy()` in `app_server`. Nothing in `app/` changes. |
| **No reader/dashboard change** | Option B (read-side exclusion) was not selected. Historical dashboards are addressed by Section 10, not by code. |

### 5.2 Coverage by channel

| Channel | Isolation mechanism | Why it works |
|---|---|---|
| pytest `TestClient` | env set before `app.main` import | All five module-level `AnalyticsService()` bind the test sink at import time. |
| Browser E2E (HeadlessChrome) | env inherited by the uvicorn subprocess | `app_server`: `env = os.environ.copy()` → `Popen(env=env)`; fresh process re-imports `app.main` and re-reads the env. |
| Future test agents | same two paths | Anything that imports `app.main` inside the pytest process, or is spawned by a fixture that copies the environment, inherits isolation automatically. |
| Local test execution | same | `pytest` from the repo root is the documented entry point. |
| CI execution | same for the host runner; optional `-e` passthrough for in-image pytest | See Section 8 — CI containers are ephemeral, so this is consistency, not leak prevention. |
| **Production** | **unaffected** | No `ANALYTICS_LOG_FILE` in Dockerfile/Railway; `tests/conftest.py` is never imported at runtime. See Section 9. |

---

## 6. TestClient Isolation

**Trace of a single TestClient request, pre-fix vs post-fix:**

```
TestClient(app).get("/")                       (Starlette/httpx, UA "testclient")
  └─ ASGI call → ObservabilityMiddleware.__call__
       state["user_agent"] = "testclient"      (main.py:82/89)
       state["ip_hash"]     = hash_ip(...)     (main.py:83/90)
       └─ send_wrapper: GET + text/html + <400
            └─ analytics_service.track_page_view(request)   (main.py:180)
                 └─ AnalyticsService.track_event → _write_event
                      └─ self.storage_path.open("a")
                           PRE-FIX : app/logs/analytics.jsonl   ← CONTAMINATION
                           POST-FIX: tmp/test_analytics.jsonl    ← ISOLATED
```

**Why the TestClient channel is fully covered by C1:** `analytics_service` at `main.py:51` is a
module-level object constructed during `import app.main`. C1 sets the env before that import, so
`settings.ANALYTICS_LOG_FILE` (read at `settings.py:36`) resolves to the test sink, and
`AnalyticsService.__init__` (`analytics_service.py:32`) binds it. The same holds for the `convert`,
`upload`, and `dashboard` routers' module-level instances. The middleware holds a direct reference to
that same object — so every `page_view` / `error` / funnel / upload / download event lands in the test
sink. **No TestClient test needs modification**, and 201 existing `TestClient` call sites are covered
without touching them.

**Residual TestClient subtleties (documented, not problematic):**
- `TestClient` events still carry `user_agent: "testclient"` — they remain *self-labeled*, so any
  future read-side analysis can still distinguish them. C1 redirects them; it does not relabel them.
- TestClient events continue to increment `metrics_registry` counters after the write
  (`analytics_service.py:180-181`). That is in-process metric state, unrelated to the sink, and
  harmless.

---

## 7. E2E / HeadlessChrome Isolation

**The critical insight from the brief is correct: TestClient isolation does NOT automatically isolate
the browser E2E channel. It would not, for a generic mechanism — but it does for C1, because of a
specific, verified line of code.**

**Full trace:**

```
tests/conftest.py
  └─ app_server fixture (session-scoped, lazy)          conftest.py:43
       ├─ env = os.environ.copy()                       conftest.py:75  ★ KEY LINE
       ├─ env["CONVERIGO_BASE_URL"] = base_url          conftest.py:80
       └─ subprocess.Popen(                             conftest.py:84
              [sys.executable, "-m", "uvicorn", "app.main:app",
               "--host", host, "--port", str(port), "--log-level", "info"],
              cwd=repo_root,
              env=env,                                  conftest.py:98  ★ env passed here
              ...)
            └─ NEW PYTHON PROCESS
                 └─ import app.main  (fresh)
                      ├─ settings = Settings() → os.getenv("ANALYTICS_LOG_FILE")
                      │    ★ inherits the value C1 set in the parent process
                      └─ analytics_service = AnalyticsService() → binds TEST sink
  └─ browser (page fixture, HeadlessChrome) → app_base_url
       └─ page.goto(base_url) → request hits the subprocess
            └─ ObservabilityMiddleware → track_page_view → TEST sink
```

**Determination:** because `app_server` copies the **entire** parent environment into the subprocess,
**the proposed C1 isolation mechanism applies to the E2E subprocess automatically. No separate
environment-propagation design is required.** The two properties that make this true are both
verified in the current source:

1. `env = os.environ.copy()` at `conftest.py:75` — full inheritance, not a whitelist;
2. `AnalyticsService` sink selection happens at **import** time (`analytics_service.py:32`), and the
   subprocess performs a **fresh import** of `app.main` (separate interpreter, no shared module
   cache).

**One documented edge case — manual server reuse.** `app_server` reuses an already-open port
(`conftest.py:68`: `if _is_port_open(host, port): … return`) instead of starting a subprocess. If a
developer has a *manually started* uvicorn running on the test port (which would bind the
**production** sink, since it was started outside pytest), E2E requests would go to that server and
its events would land in the production sink.

- This is a **local-development-only** edge case; it cannot occur in CI (no manual server exists).
- It is **detectable and self-protecting**: the E2E isolation test (Section 11, test #4) asserts that
  a uniquely-marked event arrives in the test sink. With a foreign server, that assertion **fails
  loudly** — which is exactly the desired behavior.
- Optional hardening (not required for correctness): have `app_server` record whether it *started*
  the process (`"process" in server_info`) and have the isolation test skip/fail when the server was
  reused. Documented here as a design option, not implemented.

**Additional E2E note:** the E2E subprocess is session-scoped and starts lazily. C1's module-level env
assignment runs at conftest import — long before the fixture is ever requested — so the variable is
guaranteed present in `os.environ` at `env = os.environ.copy()` time.

---

## 8. CI Isolation

### 8.1 How CI launches pytest and E2E (all four workflows inspected)

| Workflow | Triggers | Runs pytest? | How |
|---|---|---|---|
| `docker-verify.yml` (`docker-runtime-verify`) | `pull_request`, `push: main`, `workflow_dispatch` | **Yes** — `[5/5]` | `docker run --rm --workdir /app -e VERIFY_SUITE=… converigo-verify:ci sh -c 'pip install -q pytest pytest-asyncio httpx && python -m pytest "${VERIFY_SUITE:-…}" -v --tb=short'` |
| `xls-xlsx-ci-validation.yml` | `push` to two XLS branches, `workflow_dispatch` | **Yes** — `[4/7]` certified, `[6/7]` targeted regression | `docker run --rm --workdir /app -v "$PWD/artifacts:/out" … sh -c 'pip install -q pytest … && python -m pytest tests/certified/office/… -v … --junitxml=/out/…'` |
| `lo-spike-verify.yml` | `workflow_dispatch` only | **No** | LibreOffice spike in a throwaway `spike_kit` image; executes no application code |
| `xls-final-evidence.yml` | `workflow_dispatch` only | **No** | Evidence probe inside the production image; no pytest |

**Findings:**
1. **Every CI pytest invocation runs inside an ephemeral Docker container** (`docker run --rm`).
2. **The only bind mount is `$PWD/artifacts:/out`** — `app/logs/` is never mounted.
3. **`app/logs/analytics.jsonl` is gitignored** (Section 2.5), so the CI checkout contains **no**
   analytics file; the container's `AnalyticsService.__init__` creates a fresh one at
   `/app/app/logs/analytics.jsonl`, which is **destroyed with the container**.
4. **Railway production is not involved in CI.** No workflow references Railway, no Railway secrets
   are used, and no workflow deploys.

⇒ **Conclusion: CI has never contributed a single line to the persistent `app/logs/analytics.jsonl`.**
The 90,686-line file is a **local working-tree artifact** from local `pytest` runs — an important
correction to the intuition that "CI is polluting production analytics."

### 8.2 Environment inheritance in CI

- `docker run` does **not** inherit the GitHub Actions job environment into the container. Only
  explicitly passed `-e` vars (e.g. `-e VERIFY_SUITE`) are present. Therefore, if in-image pytest
  should also use the test sink, the workflow must pass it explicitly:
  `-e ANALYTICS_LOG_FILE=/app/tmp/test_analytics.jsonl`.
- **This is optional and low-value**, because the container is ephemeral: whatever sink is used, the
  file is discarded at container exit. The benefit is *consistency* (the in-image run behaves like
  the local run) rather than leak prevention.

### 8.3 CI design decision

| Item | Decision |
|---|---|
| Host-runner pytest | Not used by any workflow — nothing to do. |
| In-image pytest | **Optional** `-e ANALYTICS_LOG_FILE=/app/tmp/test_analytics.jsonl` passthrough on `docker-verify.yml [5/5]` and `xls-xlsx-ci-validation.yml [4/7]`/`[6/7]`. Recommended for consistency; not required for isolation. |
| E2E in CI | No CI workflow currently runs the browser E2E suites (local-only). If E2E is later added via pytest, C1's conftest override applies automatically; if launched outside pytest, it must export `ANALYTICS_LOG_FILE` explicitly. |
| Railway | **No changes.** Production env is untouched. |

---

## 9. Production Safety

### 9.1 Proof that production never uses the test sink

Three independent guarantees, each verified against source:

1. **The production runtime never imports `tests/conftest.py`.** Railway (`railway.toml`
   `startCommand`) and the `Dockerfile` `CMD` both run `uvicorn app.main:app`. uvicorn imports
   exactly one application object, `app.main:app`; nothing in its import chain imports `tests/`
   (the five `AnalyticsService` sites import `app.core.settings` and `app.services.analytics_service`
   only). The override is **physically unreachable** in production.
2. **Production sets no `ANALYTICS_LOG_FILE`.** Verified in the `Dockerfile` (only
   `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`), `railway.toml`, and all workflow files. With the
   variable unset, `settings.py:36` falls back to `LOG_DIR / "analytics.jsonl"`.
3. **The override is test-only code with a self-check.** Even if it somehow executed, the
   `CONVERIGO_TEST_ANALYTICS_SINK` guard hard-fails rather than point the sink at production.

### 9.2 Proof that the three forbidden paths are blocked

| Path | Blocked how |
|---|---|
| **LOCAL TEST → production analytics** | C1 sets `ANALYTICS_LOG_FILE` before `app.main` import; all five `AnalyticsService()` instances bind `tmp/test_analytics.jsonl`; `__init__` self-provisions `tmp/` (`mkdir(parents=True, exist_ok=True)`). Nothing writes to `app/logs/`. |
| **CI TEST → production analytics** | (a) CI pytest runs in ephemeral containers with an unmounted, gitignored `app/logs/` ⇒ nothing persists; (b) optional `-e` passthrough makes the in-image run use the test sink too. |
| **E2E TEST → production analytics** | The uvicorn subprocess inherits `ANALYTICS_LOG_FILE` via `os.environ.copy()` and re-reads it at its fresh `import app.main`. |

### 9.3 What happens if the test sink path is unavailable

Determined from the existing architecture — **not invented**:

- `AnalyticsService.__init__` (`analytics_service.py:31-34`) calls
  `self.storage_path.parent.mkdir(parents=True, exist_ok=True)`. The parent directory is **created
  if missing** — the sink is **self-provisioning**.
- `_write_event` (`analytics_service.py:173-182`) has **no `try/except`**. If the write genuinely
  cannot happen (parent is a file, read-only filesystem, permission denied), the exception
  **propagates out of `track_event`** and fails the request.
- `_load_events` (`analytics_service.py:184-200`) returns `[]` if the file is missing — the read
  side is tolerant.

⇒ **Existing behavior is fail-loud on write, fail-open on read.** The design introduces **no new
fallback logic**: no added `try/except`, no secondary sink, no silent event dropping. For the chosen
path (`<repo root>/tmp/test_analytics.jsonl`) the realistic failure modes are nil — `tmp/` exists,
is writable, and is auto-created — and if it ever *were* unavailable, the symptom would be an
immediate, visible test failure rather than silent contamination. That is the correct, safe failure
mode.

---

## 10. Historical Data Treatment

**Constraint (binding):** `analytics.jsonl` must not be deleted, rewritten, compacted, anonymized,
rotated, or migrated. This design complies fully.

| Requirement | How this design satisfies it |
|---|---|
| **Historical file remains authoritative raw history** | C1 never reads, writes, truncates, or deletes `app/logs/analytics.jsonl`. The clean-slate fixture touches **only** `tmp/test_analytics.jsonl`. The historical file is byte-identical before and after implementation. |
| **Future tests stop appending to it** | Guaranteed by Section 9.2 — every test channel binds the test sink. |
| **Clean cutover point** | The cutover is the moment the C1 change lands. `AnalyticsService` appends and every event carries a millisecond `timestamp` (`analytics_service.py:138`), so the cutover is precisely identifiable: **the last line in `app/logs/analytics.jsonl` whose timestamp precedes the commit/deploy of the C1 change is the last contaminated line.** No marker is written into the file. |
| **Distinguishing pre-fix synthetic events from post-fix production events** | Three orthogonal signals: (1) `timestamp` — pre-fix events all predate the cutover; (2) `user_agent` — pre-fix synthetic events still carry `testclient` / `HeadlessChrome…` / probe UAs, whereas post-fix *production* events cannot, because test traffic no longer reaches this file; (3) sink identity — post-fix test events exist only in `tmp/test_analytics.jsonl`. |
| **No rotation / deletion / migration** | Explicitly none. The file grows only with genuine production events from the cutover onward. |
| **Dashboard correction for the historical file** | **Out of scope for Option C.** The supervisor selected C (separate sources), not B (read-side exclusion). Historical dashboards continue to read the raw file as-is. Any future decision to exclude historical synthetic events from reporting is a separate, supervisor-gated decision (Section 17). |

**Cutover baseline recorded by this design audit (for future verification):**

| Metric | Value at design time |
|---|---|
| `app/logs/analytics.jsonl` total lines | **90,686** |
| Lines with `user_agent: "testclient"` | **75,523** (83.28%) |
| File last modified (UTC) | **2026-09-19T04:41:59Z** |
| Git-tracked? | **No** (`.gitignore:27 app/logs/`) |

---

## 11. Test Plan

Designed before implementation, per protocol. All tests live in a **new** module
`tests/test_analytics_isolation.py`. No existing test is modified.

**Shared test technique — the `X-Conversion-Id` marker.** The middleware captures the
`x-conversion-id` request header into `state["conversion_id"]` (`main.py:84`), which `_build_event`
persists as the event's `conversion_id` field (`analytics_service.py:157`). Each test sends a unique
`X-Conversion-Id: <uuid>` and then greps the sink for that exact value — an unambiguous, per-test
marker that works identically for `TestClient` and for browser E2E (`page.set_extra_http_headers`).

| # | Test | Purpose | Key assertions |
|---|---|---|---|
| 1 | **TestClient analytics isolation** | A TestClient request must not touch the production sink. | Send `TestClient(app).get("/", headers={"X-Conversion-Id": uid})`; assert the production sink has **zero** events with `conversion_id == uid`; assert `settings.ANALYTICS_LOG_FILE` resolves under `tmp/`. |
| 2 | **Production sink untouched during a test run** | Global invariant across a whole session. | Snapshot the production sink's line count (or note its absence) at session start; after the suite, assert the count is **unchanged** / the file is still absent. Handles the gitignored-not-present-in-CI case. |
| 3 | **Test sink receives the expected event** | Positive proof the event was recorded, not merely diverted. | After test 1's request, assert `tmp/test_analytics.jsonl` contains exactly one event with `conversion_id == uid`, `event_name == "page_view"`, and `user_agent == "testclient"`. |
| 4 | **E2E subprocess receives the test sink** | The browser channel (HeadlessChrome) must write to the test sink, proving env propagated to the subprocess. | Request `app_base_url` + `page` fixture; `page.set_extra_http_headers({"X-Conversion-Id": uid})`; `page.goto(base_url)`; assert `tmp/test_analytics.jsonl` contains an event with `conversion_id == uid`; assert the production sink contains none. (Fails loudly under the Section 7 manual-server edge case — intended.) |
| 5 | **CI environment receives the test sink** | In-image consistency when the optional `-e` passthrough is added. | Assert `os.environ["ANALYTICS_LOG_FILE"]` is set to the test path *and* that `app.main.analytics_service.storage_path` equals it — runs identically locally and in the in-image pytest invocation. |
| 6 | **Production environment still uses the production sink** | Negative proof that prod behavior is unchanged. | In a subprocess with a **clean** environment (`env = os.environ.copy(); del env["ANALYTICS_LOG_FILE"]`), run `python -c "from app.core.settings import settings; …"` and assert `settings.ANALYTICS_LOG_FILE` resolves to `app/logs/analytics.jsonl`. (Uses an explicit subprocess so it cannot disturb the in-session `settings` singleton.) |
| 7 | **Import-order regression test** | Pins the guarantee that made C1 correct. | After conftest has run, assert `app.main.analytics_service.storage_path`, `app.routers.convert.analytics_service.storage_path`, `app.routers.upload.analytics_service.storage_path`, and `app.routers.dashboard.analytics_service.storage_path` **all** resolve to the test sink. If a future instantiation site is added, this test stays true automatically (it too binds the env-driven default); if the env override is accidentally moved into a fixture, this test fails. |

**Test design notes:**
- Tests 1–3 and 5–7 use only `TestClient`/stdlib — fast, no browser, safe for CI.
- Test 4 requires the `page` fixture and is marked so it can be deselected in environments without
  browsers (consistent with the existing E2E modules).
- Test 6 deliberately avoids importing `app` in-process with a mutated env, because `settings` is a
  module-level singleton; an isolated subprocess is the only sound way to observe the default.
- **Test 2's precondition is the clean-slate fixture**, so the assertion is exact rather than
  "approximately unchanged".

---

## 12. Files Expected To Change

| File | Change type | Required? | Notes |
|---|---|---|---|
| `tests/conftest.py` | **Modify** — add the module-level `ANALYTICS_LOG_FILE` override + guard, and the session-scoped clean-slate fixture | **REQUIRED** | The entire fix. ~15 lines. Zero application-source impact. |
| `tests/test_analytics_isolation.py` | **New** — the 7 tests from Section 11 | **REQUIRED** | New file only; modifies no existing test. |
| `.github/workflows/docker-verify.yml` | **Modify** — add `-e ANALYTICS_LOG_FILE=/app/tmp/test_analytics.jsonl` to the `[5/5]` `docker run` | **Optional** | Consistency for in-image pytest only; the container is ephemeral so this prevents no persistent leak. |
| `.github/workflows/xls-xlsx-ci-validation.yml` | **Modify** — same `-e` passthrough on `[4/7]` and `[6/7]` | **Optional** | Same rationale. |
| `pytest.ini` | **Optional** — register an `analytics_isolation` marker if test #4 needs deselecting in browser-less environments | **Optional** | `markers =` already exists; adding one line is low-risk. |

**Explicitly NOT changed:**
- `app/services/analytics_service.py`, `app/core/settings.py`, `app/main.py`, any router, any service
  (no application source).
- Any reader / dashboard / aggregation code (Option B not selected).
- `app/logs/analytics.jsonl` (forbidden — preserved verbatim).
- GA4 / GSC / sitemap / crawler / XLS-branch surfaces (out of scope).
- Railway configuration / production environment.

---

## 13. Exact Implementation Sequence

Ordered so that each step is independently verifiable, and so the historical file is never at risk.

**Step 0 — Baseline capture (before any change).**
Record the current state of the production sink so the cutover is provable:
`app/logs/analytics.jsonl` = 90,686 lines; 75,523 `testclient` (83.28%); last modified
2026-09-19T04:41:59Z; gitignored (not tracked). Commit these numbers to the implementation ticket.
*(Already captured in Section 10 — this is the cutover datum.)*

**Step 1 — `tests/conftest.py` override (the fix).**
Add, at the very top of the module (above existing imports, keeping the existing `import pytest`),
the `_REPO_ROOT` / `_PROD_SINK` / `_TEST_SINK` computation, the production-collision guard, and the
unconditional `os.environ["ANALYTICS_LOG_FILE"] = str(_TEST_SINK)` — exactly as sketched in Section 5.

**Step 2 — Clean-slate fixture.**
Add the session-scoped autouse `_clean_test_analytics_sink` fixture (Section 5) that unlinks
`tmp/test_analytics.jsonl` at session start. Verify `AnalyticsService` stores a `Path` (not a
handle), so unlinking is safe — already verified at `analytics_service.py:31-34`.

**Step 3 — Smoke check (no new tests yet).**
Run a small existing suite, e.g. `python -m pytest tests/test_analytics_smoke.py tests/test_health.py -q`.
Then confirm:
- `tmp/test_analytics.jsonl` was created and contains events;
- `app/logs/analytics.jsonl` line count is **unchanged** from Step 0.

**Step 4 — Add `tests/test_analytics_isolation.py`.**
Implement tests 1, 2, 3, 5, 6, 7 (no browser), then test 4 (browser, marked for deselection).

**Step 5 — Run the isolation suite.**
`python -m pytest tests/test_analytics_isolation.py -v`. All 7 must pass.

**Step 6 — Full regression run.**
Run the full suite (or a representative large slice) and confirm no existing test broke. Expected
failure count: zero — no test reads the live `app/logs/analytics.jsonl` (verified by search), and
analytics unit tests use `tmp_path`-backed services with explicit `storage_path`.

**Step 7 — Verify the historical file.**
Re-count `app/logs/analytics.jsonl`. It must still be exactly 90,686 lines (or +0 from Step 0) and
byte-identical. If it grew, the isolation is incomplete — stop and re-audit.

**Step 8 — Optional CI consistency.**
Add the `-e ANALYTICS_LOG_FILE=/app/tmp/test_analytics.jsonl` passthrough to the two workflows'
in-image `docker run` commands (Section 12). Re-run `docker-runtime-verify` to confirm it stays green.

**Step 9 — Supervisor verification.**
Re-run the full suite; confirm the acceptance criteria in Section 18, including the unchanged
historical file and the presence of test events exclusively under `tmp/`.

---

## 14. Rollback Plan

The change is small, test-only, and stateless, so rollback is trivial and fully reversible.

| Step | Action |
|---|---|
| 1 | Revert the `tests/conftest.py` additions (the module-level override, the guard, and the `_clean_test_analytics_sink` fixture). |
| 2 | Delete `tests/test_analytics_isolation.py` (new file; no dependents). |
| 3 | Revert the optional `-e` passthrough in the two workflow files if it was added. |
| 4 | Optionally remove `tmp/test_analytics.jsonl` (a gitignored scratch file — safe to delete; it holds no production data). |

**Why rollback is safe:**
- **No production state to restore.** No application source, settings, deployment config, or Railway
  variable changed. Production never used the test sink.
- **No historical data to restore.** `app/logs/analytics.jsonl` is never written, truncated, or
  deleted by this design — verified by the code paths in Section 9.2. After rollback it simply
  resumes receiving events from all channels as before (including test traffic — which is the
  pre-fix behavior being rolled back to).
- **No schema/migration/contract change.** The event format, the sink filename, and the reader API
  are all untouched.
- **No partial-apply hazard.** The override is a handful of lines in one file; there is no multi-file
  invariant to keep in sync. Reverting `conftest.py` alone fully restores prior behavior.

---

## 15. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **The override is accidentally placed inside a fixture** instead of at module level, so it runs *after* `app.main` is imported and never takes effect. | Medium (easy mistake) | High — silent re-contamination | Test #7 (import-order regression) fails loudly in this case; the design sketch and Step 1 both specify module-level placement; code review check. |
| R2 | **A future contributor adds an `AnalyticsService()` that is constructed before conftest runs** (e.g. a pytest plugin imported via `addopts`, or a rootdir `conftest.py` that imports `app`). | Low | High — one channel leaks | Test #7 covers the known sites; additionally, the *mechanism* is env-based, so even a new site binds the test sink as long as it is imported after conftest — which is the normal case. Document the ordering rule in this plan and near the conftest code. |
| R3 | **Manual-server reuse in `app_server`** (Section 7): a developer's manually-started uvicorn on the test port binds the production sink and E2E requests go there. | Low (local only) | Medium — local contamination only | Test #4 fails loudly in this situation. Optional hardening: record whether `app_server` started the process and skip/fail accordingly. Cannot occur in CI. |
| R4 | **A stale `ANALYTICS_LOG_FILE` in the developer's shell** pointing at `app/logs/analytics.jsonl` would be honored if `setdefault` were used. | Eliminated by design | — | The design assigns unconditionally (`os.environ[...] = …`) and hard-fails if the resolved sink equals the production sink. |
| R5 | **Test sink unwritable** (read-only FS, `tmp/` replaced by a file). | Very low | Medium — tests fail | `_write_event` fails loudly (no `try/except`), so the symptom is an immediate visible test failure, never silent production contamination. `mkdir(parents=True, exist_ok=True)` self-provisions; `tmp/` verified writable. |
| R6 | **Existing tests break** because they read the live `app/logs/analytics.jsonl`. | Very low | Medium | Verified by repository-wide search: **no test reads the live log**; analytics unit tests construct `AnalyticsService(tmp_path/…)` with an explicit `storage_path`. Step 6 is the empirical confirmation. |
| R7 | **Concurrent xdist workers share one sink file** (interleaved appends) if `pytest-xdist` is ever adopted. | Not applicable today | Medium if adopted | `pytest-xdist` is **not installed**. If adopted later, use `CONVERIGO_TEST_ANALYTICS_SINK` with a `PYTEST_XDIST_WORKER` suffix per worker (the env var is already read defensively at `conftest.py:56`). Documented as a future note — no change needed now. |
| R8 | **The in-image CI pytest behaves differently from local pytest** (no `-e` passthrough) and someone assumes CI is isolated when it is merely ephemeral. | Low | Low | Section 8 states this explicitly; the optional `-e` passthrough makes them identical. |
| R9 | **Team assumes historical data is now clean.** It is not — only *future* writes are isolated. | Medium (expectation) | Medium (analysis error) | Section 10 states the boundary precisely: the 83.28% synthetic share remains in history and must be excluded by any future analysis; that is the separate Option B decision, supervisor-gated. |

---

## 16. Evidence Gaps

Honest statement of what this design could **not** verify at design time, and how each gap is closed:

| Gap | Why it matters | Resolution |
|---|---|---|
| **The exact mechanism behind the `page` fixture.** Browser E2E tests use `page.goto(...)` and `page.set_extra_http_headers(...)`, but `pytest-playwright` was not visible in the `pip list` output as a distinct package (only `playwright 1.62.0`). | Test #4's implementation depends on the fixture name and header API. | Resolved at implementation time by inspecting the installed plugins. The *design* does not depend on it — the `X-Conversion-Id` marker is a plain request header, settable by any HTTP client or browser automation. If the `page` fixture is unavailable, test #4 uses `httpx` against `app_base_url` instead, exercising the identical subprocess path. |
| **Whether `app/logs/` is a mounted persistent volume on Railway.** The repo's Railway config (`railway.toml`) defines no volume, but volumes can be configured in the Railway dashboard outside the repo. | Affects whether production events persist across deploys — but **not** this design: whatever the mount, it is the production sink, and this design never writes to it. | Out of scope; noted because the root-cause report's historical-data discussion assumed persistence. Does not affect correctness or safety of Option C. |
| **Live Railway state.** No Railway API was queried (read-only protocol; no secrets used). | Cannot confirm the deployed `ANALYTICS_LOG_FILE` from the dashboard. | Not required: Section 9.1 proves production cannot use the test sink from the *deployed configuration* (`railway.toml` + `Dockerfile`), which is the source of truth for a deploy. |

No other claims in this document are unverified: every line number, fixture behavior, git-ignore rule,
CI command, and fail-mode statement was read directly from the repository at design time.

---

## 17. Supervisor Approval Required

**Approval requested:** implementation of **Option C1** as specified — a module-level
`ANALYTICS_LOG_FILE` override and session clean-slate fixture in `tests/conftest.py`, plus the new
`tests/test_analytics_isolation.py` (Section 11), with the **optional** CI `-e` passthrough held
until separately approved.

**Decisions explicitly deferred to the supervisor (not taken by this design):**
1. **Option B / read-side exclusion** — whether and how to exclude the 83.28% historical synthetic
   share from dashboards. This design isolates *future* writes only (Section 10).
2. **Option A / write-side guard** (`testclient`/HeadlessChrome/probe UA filtering in `track_event`)
   — a possible complementary stopgap; intentionally out of scope for Option C.
3. **The SEO/performance dashboard finding** — `landing_page_view`, `performance_metric`, and related
   event names exist only in unit tests, so those dashboard sections are structurally zero in
   production. Whether to remove/hide them is a product decision.
4. **The optional CI workflow edits** — whether to add `-e ANALYTICS_LOG_FILE` to the two in-image
   pytest invocations (consistency only; Section 8).
5. **Historical file disposition** — per the binding constraint, no deletion/rewrite/compaction is
   proposed; if leadership later wants the synthetic share addressed, that is a separate,
   supervisor-gated change.

**Constraints honored during this design phase:** read-only/design-only firewall maintained — no
source, test, CI, or environment modifications; no commits or PRs; `analytics.jsonl` untouched
(verified still 90,686 lines at the end of this phase).

---

## 18. Implementation Acceptance Criteria

The implementation is complete when **all** of the following hold:

1. **Isolation:** after a full local `pytest` run, `app/logs/analytics.jsonl` has the **same line
   count** as the Step-0 baseline (90,686) and is byte-identical — zero new lines.
2. **Diversion:** `tmp/test_analytics.jsonl` exists and contains the test-run events (including
   `testclient` and HeadlessChrome UAs). It is gitignored and must not appear in `git status`.
3. **All 7 tests** in `tests/test_analytics_isolation.py` pass.
4. **No regression:** the full existing suite passes with the same pass/fail counts as before the
   change (expected added-failure count: 0).
5. **Production equivalence:** with `ANALYTICS_LOG_FILE` unset, `settings.ANALYTICS_LOG_FILE`
   resolves to `app/logs/analytics.jsonl` (test #6).
6. **No application source changed:** `git diff --stat` touches only `tests/conftest.py`,
   `tests/test_analytics_isolation.py`, and (if approved) the two workflow files.
7. **Guard works:** setting `CONVERIGO_TEST_ANALYTICS_SINK` to the production path aborts the session
   with the `RuntimeError` from Section 5.

---

## SUMMARY

- **Recommended design:** **Option C1** — module-level `ANALYTICS_LOG_FILE` environment override in
  `tests/conftest.py` (test sink `<repo_root>/tmp/test_analytics.jsonl`), with a production-collision
  guard and a session-scoped clean-slate fixture. Chosen over C2 (needs a new `pytest-env`
  dependency), C3 (cannot cover the middleware-captured instance or the E2E subprocess), and C4
  (modifies production source and the write path).
- **Files expected to change:** `tests/conftest.py` (required, ~15 lines); new
  `tests/test_analytics_isolation.py` (7 tests); **optionally** `-e ANALYTICS_LOG_FILE` passthrough in
  `.github/workflows/docker-verify.yml` and `.github/workflows/xls-xlsx-ci-validation.yml`. **No
  application source, no reader/dashboard code, no Railway config, and no change to
  `analytics.jsonl`.**
- **Risks:** the main ones are placement-of-override (mitigated by test #7), the local-only
  manual-server reuse edge case (fails loudly), and the expectation risk that historical data is
  still contaminated (only future writes are isolated). Full register in Section 15.
- **Validation plan:** 7 dedicated isolation tests using the `X-Conversion-Id` marker across
  TestClient, browser E2E, CI, and production-default channels; a full regression run; and a
  before/after line-count check of the historical file proving zero growth (Section 13, Steps 0–9).

**STATUS: DESIGN COMPLETE — WAITING SUPERVISOR APPROVAL**













