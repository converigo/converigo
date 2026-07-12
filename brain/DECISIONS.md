# Converigo Decision Log

## Decision Record

### D001 — Checkpoint-first release process
- **Decision:** Use named checkpoints to manage release scope and audit readiness.
- **Rationale:** Checkpoints keep the project focused and prevent unrelated changes from leaking into release candidate builds.
- **Outcome:** Checkpoint C1 is the official release gate for Image Foundation.

### D002 — Image Foundation milestone
- **Decision:** Treat the image category as the first formal milestone after project initialization.
- **Rationale:** Image conversions are a core product offering and provide clear value for release.
- **Outcome:** C1 delivers `IMG-001` PNG→WEBP and `IMG-002` WEBP→PNG as the first production packages.

### D003 — No code change in documentation
- **Decision:** Brain and release docs are separate from application code.
- **Rationale:** Documentation files should not alter runtime behavior or feature scope.
- **Outcome:** All `brain/` and `docs/` files are content-only and do not modify application code.

### D004 — Release blockers only
- **Decision:** For C1 final push, only unresolved release blockers may be addressed.
- **Rationale:** Avoid scope creep and preserve checkpoint integrity.
- **Outcome:** The final audit and fix cycle was limited to accessibility and repository cleanliness.

### D005 — Git readiness validation
- **Decision:** Only checkpoint-related files are staged for the C1 commit.
- **Rationale:** Ensures a clean release commit with no accidental changes.
- **Outcome:** C1 readiness was verified for the intended files only.
