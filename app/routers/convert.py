"""
Project : Converigo
Author  : Pico Lala & ChatGPT

Convert Router

Version : 2.2.1
"""

import logging

from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse

from app.core.observability import (
    ConversionTracker,
    build_error_response,
    elapsed_ms,
    normalize_error_code,
)
from app.core.settings import settings
from app.plugins.registry import registry
from app.services.analytics_service import AnalyticsService
from app.services.conversion_service import (
    ConversionError,
    ConversionService,
    UnsupportedConversionError,
)

from app.services.upload_service import (
    UploadError,
    UploadService,
)


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/convert",
    tags=["convert"],
)
analytics_service = AnalyticsService()


async def unsupported_conversion_exception_handler(
    request: Request,
    exc: UnsupportedConversionError,
) -> JSONResponse:
    request.state.error_code = "UNSUPPORTED_CONVERSION"
    return build_error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "code": "UNSUPPORTED_CONVERSION",
            "message": str(exc),
        },
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
async def convert_file(

    request: Request,

    file: List[UploadFile] = File(...),

    target_format: str = Form(...)

):


    tracker = ConversionTracker(request)
    tracker.observe_queue()

    logger.info("Convert request received: files=%d target=%s", len(file), target_format)

    tracker.start("validation")

    if not file or len(file) == 0:
        request.state.error_code = "NO_FILES_PROVIDED"
        tracker.fail("validation", request.state.error_code)
        raise HTTPException(status_code=400, detail="No files provided")

    tracker.finish("validation")

    target_format = target_format.lower().strip()
    analytics_service.track_conversion_start(
        request,
        page_path=request.url.path,
        target_format=target_format,
        event_status="started",
    )
    
    upload_service = UploadService()
    conversion_service = ConversionService()
    
    results = []
    saved_paths = []

    try:
        # Process each file
        for uploaded_file in file:
            saved_path: Path | None = None
            try:
                tracker.start("upload")
                saved_path = await upload_service.process_upload(uploaded_file)
                tracker.finish("upload")
                saved_paths.append(saved_path)
                
                source_format = (
                    Path(saved_path)
                    .suffix
                    .replace(".", "")
                    .lower()
                )

                # [CONVERTER_DEBUG] — log converter selection and upload path
                try:
                    plugin = registry.get_plugin(source_format, target_format)
                    slug = getattr(plugin, "slug", None)
                except Exception:
                    slug = None

                tracker.set_converter(slug or f"{source_format}-to-{target_format}")

                logger.info(
                    "[CONVERTER_DEBUG] Request: converter_slug=%s source_format=%s target_format=%s upload_path=%s",
                    slug,
                    source_format,
                    target_format,
                    str(saved_path),
                )

                try:
                    registry.get_plugin(
                        source_format,
                        target_format
                    )
                except ValueError as exc:
                    request.state.error_code = "UNSUPPORTED_CONVERSION"
                    raise UnsupportedConversionError(source_format, target_format) from exc

                tracker.start("conversion")
                output_path = await conversion_service.convert_file(
                    saved_path,
                    target_format,
                    conversion_id=tracker.conversion_id,
                )
                tracker.finish("conversion")

                # Build download_path using a dedicated download route so browsers
                # receive an explicit attachment response on mobile devices.
                tracker.start("download")
                try:
                    rel = output_path.relative_to(settings.OUTPUT_DIR)
                    download_path = "/download/" + rel.as_posix()
                except Exception:
                    # Fallback: preserve previous behavior (use parent folder name)
                    download_path = "/download/" + output_path.parent.name + "/" + output_path.name
                tracker.finish("download")

                processing_ms = elapsed_ms(getattr(request.state, "request_started_ns", 0)) if getattr(request.state, "request_started_ns", None) else None
                analytics_service.track_conversion_success(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{source_format}-to-{target_format}",
                    category=str(getattr(request.state, "converter", "converter") or "converter"),
                    output_format=target_format,
                    event_status="success",
                    processing_ms=processing_ms,
                )

                results.append({
                    "filename": output_path.name,
                    "download_path": download_path,
                    "status": "success",
                    "conversion_id": tracker.conversion_id,
                })

            except UnsupportedConversionError:
                tracker.fail("conversion", "UNSUPPORTED_CONVERSION")
                analytics_service.track_conversion_failed(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{Path(uploaded_file.filename or 'file').suffix.lstrip('.') or 'file'}-to-{target_format}",
                    output_format=target_format,
                    error_type="UNSUPPORTED_CONVERSION",
                    event_status="failure",
                )
                raise
            except (UploadError, ConversionError) as exc:
                request.state.error_code = normalize_error_code(type(exc).__name__, fallback="CONVERSION_FAILED")
                if isinstance(exc, UploadError):
                    tracker.fail("upload", request.state.error_code)
                else:
                    tracker.fail("conversion", request.state.error_code)
                analytics_service.track_conversion_failed(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{Path(uploaded_file.filename or 'file').suffix.lstrip('.') or 'file'}-to-{target_format}",
                    output_format=target_format,
                    error_type=request.state.error_code,
                    event_status="failure",
                )
                logger.warning("Conversion failed for %s: %s", uploaded_file.filename, exc)
                results.append({
                    "filename": uploaded_file.filename,
                    "status": "failed",
                    "error": str(exc),
                    "conversion_id": tracker.conversion_id,
                })

        # Return single-file format for 1 file (backward compatibility)
        # or batch format for multiple files
        if len(file) == 1 and len(results) == 1:
            result = results[0]
            result["status"] = "success" if result["status"] == "success" else "failed"
            result["target_format"] = target_format
            if result["status"] == "failed":
                request.state.error_code = normalize_error_code(result.get("error"), fallback="CONVERSION_FAILED")
                analytics_service.track_conversion_failed(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{Path(file[0].filename or 'file').suffix.lstrip('.') or 'file'}-to-{target_format}",
                    output_format=target_format,
                    error_type=request.state.error_code,
                    event_status="failure",
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"],
                )
            result["conversion_id"] = tracker.conversion_id
            return result
        
        # Batch response for multiple files
        return {
            "status": "completed",
            "conversion_id": tracker.conversion_id,
            "results": results,
            "total": len(file),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "target_format": target_format,
        }

    except HTTPException:
        raise

    except UnsupportedConversionError:
        raise

    except Exception:
        request.state.error_code = "BATCH_CONVERSION_FAILED"
        logger.exception("Unexpected error during batch conversion")
        raise HTTPException(
            status_code=500,
            detail="Batch conversion failed.",
        )

    finally:
        # Clean up all saved paths
        tracker.start("cleanup")
        for saved_path in saved_paths:
            try:
                if saved_path and saved_path.exists():
                    saved_path.unlink()
            except Exception:
                logger.exception("Failed to remove temporary upload %s", saved_path)
        tracker.finish("cleanup")