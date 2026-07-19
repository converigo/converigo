# PDF Engine Deployment Checklist

## Merge details
- Merge commit: `40c6ed2bf0124fab2d5ab8092447eea19e990371`
- PR: #13
- Title: `fix(pdf): recover PDF office conversion engine`
- Branch merged: `fix/pdf-office-engine-release-clean`

## Changed components
- `app/engines/document_engine.py`
- `app/services/conversion_service.py`
- `tests/certified/pdf/*`
- `CONVERSION_SERVICE_SCOPE_REVIEW.md`
- `FINAL_PDF_RELEASE_APPROVAL_REPORT.md`
- `PDF_OFFICE_REGRESSION_REPORT.md`
- `PDF_OFFICE_VALIDATION_REPORT.md`
- `PDF_TEST_PATH_NORMALIZATION_REPORT.md`

## Test results
- Local build verification: PASS
  - `python -m compileall app` passed
  - `python -c "import app"` passed
- Dependency verification: PASS for runtime dependencies
  - `pip check` reported missing optional packages for non-runtime tools only
- Production health check: PASS
  - `https://converigo.com/health` returned `200 OK`
- Production website check: PASS
  - `https://converigo.com/` returned `200 OK`

## Production conversion verification
- PDF → DOCX: FAILED
  - Production response: `422 UNSUPPORTED_CONVERSION`
- PDF → XLSX: FAILED
  - Production response: `422 UNSUPPORTED_CONVERSION`
- PDF → PPTX: FAILED
  - Production response: `422 UNSUPPORTED_CONVERSION`
- PDF → ODT: FAILED
  - Production response: `422 UNSUPPORTED_CONVERSION`
- PDF → JPG: SUCCESS
  - Production response: `201 CREATED`

## Deployment steps
1. Confirm current `main` includes merge commit `40c6ed2...`.
2. Build container image from `Dockerfile`:
   - `docker build -t converigo:pdf-engine .`
3. Run container locally for smoke test:
   - `docker run --rm -p 8000:8000 converigo:pdf-engine`
4. Deploy to production platform (Railway or equivalent):
   - `railway deploy` or use the project deploy pipeline
5. Verify health endpoint:
   - `curl -I https://converigo.com/health`
6. Verify conversions via production API.

## Rollback plan
- Roll back the production service to the previous main release commit.
- If using Railway, restore the previous deployment release or rollback from the Railway dashboard.
- If using container deployment, redeploy the prior image/tag.
- Notify stakeholders and monitor logs for the rollback event.

## Notes and limitations
- Local environment tools:
  - `docker` CLI is not available in this workspace, so container build/run could not be executed locally here.
  - `railway` CLI is installed but not linked to a project in this workspace.
- Production environment is reachable and healthy, but PDF office conversions are currently unsupported for DOCX, XLSX, PPTX, and ODT on the live site.
- Do not begin Office Engine Migration until PDF release is fully certified and production verified.
