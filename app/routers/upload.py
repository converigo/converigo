import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.core.observability import elapsed_ms, metrics_registry, normalize_error_code, start_timer
from app.services.analytics_service import AnalyticsService
from app.services.upload_service import UploadError, UploadService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])
analytics_service = AnalyticsService()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request, file: UploadFile = File(...)):
    started = start_timer()
    try:
        analytics_service.track_upload_start(
            request,
            page_path=request.url.path,
            category="upload",
            input_format=(file.content_type or "file"),
            event_status="started",
        )
        saved_path = await UploadService().process_upload(file)
        duration_ms = elapsed_ms(started)
        analytics_service.track_upload_success(
            request,
            page_path=request.url.path,
            category="upload",
            input_format=(file.content_type or saved_path.suffix.lstrip(".") or "file"),
            event_status="success",
            processing_ms=duration_ms,
        )
        metrics_registry.observe(
            "converigo_upload_duration_seconds",
            duration_ms / 1000,
            converter="upload-only",
            status="success",
        )
        logger.info(
            "Upload completed",
            extra={
                "duration_ms": duration_ms,
                "status": "success",
                "converter": "upload-only",
            },
        )
        return {
            "status": "success",
            "filename": saved_path.name,
            "message": "File uploaded successfully.",
        }
    except UploadError as exc:
        request.state.error_code = "UPLOAD_ERROR"
        duration_ms = elapsed_ms(started)
        analytics_service.track_error(
            request,
            page_path=request.url.path,
            error_type="UPLOAD_ERROR",
            event_status="failure",
            processing_ms=duration_ms,
        )
        metrics_registry.observe(
            "converigo_upload_duration_seconds",
            duration_ms / 1000,
            converter="upload-only",
            status="failure",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        request.state.error_code = normalize_error_code("UPLOAD_ERROR", fallback="UPLOAD_ERROR")
        duration_ms = elapsed_ms(started)
        analytics_service.track_error(
            request,
            page_path=request.url.path,
            error_type="UNKNOWN_ERROR",
            event_status="failure",
            processing_ms=duration_ms,
        )
        metrics_registry.observe(
            "converigo_upload_duration_seconds",
            duration_ms / 1000,
            converter="upload-only",
            status="failure",
        )
        logger.exception("Unexpected upload error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the upload.",
        )
