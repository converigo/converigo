# Converigo Production Standard (CPS v1.0)

## 1. Converigo Production Standard (CPS v1.0)

Converigo uses a lightweight production standard that reuses the existing service layer rather than introducing a parallel framework. Every converter is expected to pass through the same contract-driven validation path before it is considered production ready.

## 2. Definition of Done

A converter is COMPLETE only if it has:

- ✓ Contract
- ✓ Plugin
- ✓ Landing
- ✓ Knowledge
- ✓ FAQ
- ✓ Related Converter
- ✓ Hub
- ✓ Sitemap
- ✓ Production Audit
- ✓ Regression Tests

## 3. Production Audit Flow

Converter
↓
Contract
↓
Landing
↓
Knowledge
↓
Related
↓
Hub
↓
Sitemap
↓
Quality Score
↓
READY / WARNING / NOT READY

## 4. Quality Score Formula

The production audit uses a simple weighted score based on the presence of key quality signals.

Example:

- Contract: 10
- Landing: 15
- Knowledge: 15
- FAQ: 10
- Related: 10
- Hub: 10
- Sitemap: 10
- Regression: 10
- Internal Links: 5
- Documentation: 5

Total: 100

Status:

- 90–100: READY
- 70–89: WARNING
- 0–69: NOT READY

## 5. Growth Dashboard Integration

The growth dashboard now exposes production readiness metrics through the production_audit section of the dashboard payload. This includes:

- Platform Health
- Production Ready
- Landing Coverage
- Knowledge Coverage
- Contract Coverage
- Hub Coverage
- Sitemap Coverage
- Regression Coverage
- Average Quality Score
