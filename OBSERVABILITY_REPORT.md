# Observability Report

## Architecture

- Request-scoped observability is implemented at the FastAPI boundary in `app/main.py` with a dedicated ASGI middleware.
- Structured JSON logging, correlation helpers, and an in-memory Prometheus-compatible metrics registry live in `app/core/observability.py`.
- The middleware generates a `request_id` for every HTTP request, attaches it to logs and responses, and correlates unhandled exceptions.
- Conversion correlation stays outside converter implementations: `app/routers/convert.py` creates a `conversion_id` per conversion request and tracks upload, validation, conversion, download-preparation, queue, and cleanup stages.
- Upload-only requests are instrumented in `app/routers/upload.py` without changing converter behavior.

## Metrics

Exposed at `GET /metrics` in Prometheus text format.

- `converigo_requests_total`
- `converigo_request_duration_seconds`
- `converigo_upload_duration_seconds`
- `converigo_conversion_duration_seconds`
- `converigo_download_duration_seconds`
- `converigo_queue_duration_seconds`
- `converigo_success_total`
- `converigo_failure_total`
- `converigo_success_rate`
- `converigo_failure_rate`

Additional stage summaries are also emitted for validation and cleanup to support deeper conversion tracing.

## Sample Logs

```json
{"timestamp":"2026-07-22T14:03:11.842Z","level":"INFO","logger":"app.observability.request","message":"Request completed","request_id":"f4f6f4f77e72457ba16e3a9284f2f42e","conversion_id":"9d3a9f5db6e24e56a9ef5f1db10f44d8","user_agent":"curl/8.9.1","ip_hash":"6cc3fd77c7c6de1b","converter":"pdf-to-docx","duration_ms":482.337,"status":"success","error_code":null,"method":"POST","path":"/convert","status_code":201}
```

```json
{"timestamp":"2026-07-22T14:03:11.401Z","level":"INFO","logger":"app.observability.conversion","message":"Conversion stage completed","request_id":"f4f6f4f77e72457ba16e3a9284f2f42e","conversion_id":"9d3a9f5db6e24e56a9ef5f1db10f44d8","user_agent":"curl/8.9.1","ip_hash":"6cc3fd77c7c6de1b","converter":"pdf-to-docx","duration_ms":317.224,"status":"success","error_code":null,"stage":"conversion"}
```

```json
{"timestamp":"2026-07-22T14:03:13.102Z","level":"WARNING","logger":"app.observability.request","message":"Slow request detected","request_id":"de8f25cbfd2b46b2b42c5086f66bbce7","conversion_id":null,"user_agent":"kube-probe/1.30","ip_hash":"20b6f47408cf72e9","converter":null,"duration_ms":1504.912,"status":"success","error_code":null,"method":"GET","path":"/health","status_code":200}
```

## Health Endpoints

- `GET /health`
  - Lightweight liveness probe.
  - Response: `{"status": "ok", "service": "converigo"}`
- `GET /ready`
  - Readiness probe covering upload/output directories, static assets, and plugin registry availability.
  - Returns `200` when all checks pass, otherwise `503`.
- `GET /metrics`
  - Prometheus-compatible metrics output for request, queue, upload, conversion, and download timing.

All endpoints include `X-Request-ID`. Conversion-related responses also include `X-Conversion-ID`.

## Future Improvements

- Replace in-memory metrics with a process-safe backend for multi-worker deployments.
- Add histogram buckets for latency SLOs instead of summary count/sum pairs only.
- Propagate `conversion_id` through the browser download flow automatically so `/download` requests correlate to the originating conversion without client-side cooperation.
- Emit traces to OpenTelemetry for cross-service correlation if Converigo adds queues or external worker pools.
- Add dashboard alerts for slow requests, elevated failure rate, and converter-specific error spikes.