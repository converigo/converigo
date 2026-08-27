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

):


    tracker = ConversionTracker(request)
    tracker.observe_queue()

    tracker.start("validation")

    if not file or len(file) == 0:
        request.state.error_code = "NO_FILES_PROVIDED"
        tracker.fail("validation", request.state.error_code)
        raise HTTPException(status_code=400, detail="No files provided")

    tracker.finish("validation")

    # Read form fields manually to support multipart uploads with arbitrary fields
    form = await request.form()
    # Debug: log form keys and simple summaries to diagnose malformed multipart bodies
    try:
        form_summary = {k: ("<file>" if hasattr(v, "filename") else str(v)[:200]) for k, v in form.items()}
        logger.debug("Convert form fields: %s", form_summary)
    except Exception:
        logger.debug("Convert form fields: <unserializable>")
    target_format = (form.get('target_format') or '')
    target_format = target_format.lower().strip() if target_format else ''
    parsed_targets = None
    # Strict validation: if `targets` present it MUST be a JSON array
    if 'targets' in form:
        try:
            import json

            parsed_targets = json.loads(form.get('targets'))
        except Exception:
            request.state.error_code = "INVALID_TARGETS"
            tracker.fail("validation", request.state.error_code)
            raise HTTPException(status_code=400, detail="targets must be a valid JSON array")

        if not isinstance(parsed_targets, list):
            request.state.error_code = "INVALID_TARGETS"
            tracker.fail("validation", request.state.error_code)
            raise HTTPException(status_code=400, detail="targets must be a valid JSON array")

        # Ensure list length matches number of uploaded files
        if len(parsed_targets) != len(file):
            request.state.error_code = "INVALID_TARGETS_LENGTH"
            tracker.fail("validation", request.state.error_code)
            raise HTTPException(status_code=400, detail="targets length must match number of files")

    # If no `targets` array was provided, ensure there's at least a legacy `target_format` value
    if 'targets' not in form and not target_format:
        request.state.error_code = "NO_TARGET_SPECIFIED"
        tracker.fail("validation", request.state.error_code)
        raise HTTPException(status_code=400, detail="no target format specified")

    analytics_service.track_conversion_start(
        request,
        page_path=request.url.path,
        target_format=(target_format or ""),
        event_status="started",
    )
    
    upload_service = UploadService()
    conversion_service = ConversionService()
    
    results = []
    saved_paths = []

    # Log high-level request info after we've parsed form fields
    logger.info("Convert request received: files=%d target=%s targets=%s", len(file), target_format, '[masked]' if parsed_targets else None)

    try:
        # Process each file independently; determine per-file target from `parsed_targets` or fallback to `target_format`
        for idx, uploaded_file in enumerate(file):
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

                # Determine this file's target format
                this_target = None
                if parsed_targets and idx < len(parsed_targets):
                    this_target = (str(parsed_targets[idx]) or '').lower().strip()
                elif target_format:
                    this_target = target_format
                else:
                    this_target = ''

                if not this_target:
                    # No target provided for this file; mark as failed
                    results.append({
                        "filename": uploaded_file.filename,
                        "status": "failed",
                        "error": "NO_TARGET_SPECIFIED",
                        "conversion_id": tracker.conversion_id,
                    })
                    continue

                # Resolve plugin for this specific pair. If unsupported, record failed result and continue.
                try:
                    plugin = registry.get_plugin(source_format, this_target)
                    slug = getattr(plugin, "slug", None)
                except ValueError as exc:
                    analytics_service.track_conversion_failed(
                        request,
                        page_path=request.url.path,
                        converter_name=f"{source_format}-to-{this_target}",
                        output_format=this_target,
                        error_type="UNSUPPORTED_CONVERSION",
                        event_status="failure",
                    )
                    results.append({
                        "filename": uploaded_file.filename,
                        "status": "failed",
                        "error": "UNSUPPORTED_CONVERSION",
                        "message": str(exc) or "Conversion not supported",
                        "target_format": this_target,
                        "conversion_id": tracker.conversion_id,
                    })
                    continue

                tracker.set_converter(slug or f"{source_format}-to-{this_target}")

                tracker.start("conversion")
                output_path = await conversion_service.convert_file(
                    saved_path,
                    this_target,
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
                    converter_name=tracker.converter or f"{source_format}-to-{this_target}",
                    category=str(getattr(request.state, "converter", "converter") or "converter"),
                    output_format=this_target,
                    event_status="success",
                    processing_ms=processing_ms,
                )

                results.append({
                    "filename": output_path.name,
                    "download_path": download_path,
                    "status": "success",
                    "target_format": this_target,
                    "conversion_id": tracker.conversion_id,
                })

            except UnsupportedConversionError as exc:
                tracker.fail("conversion", "UNSUPPORTED_CONVERSION")
                analytics_service.track_conversion_failed(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{Path(uploaded_file.filename or 'file').suffix.lstrip('.') or 'file'}-to-{target_format}",
                    output_format=(target_format or ""),
                    error_type="UNSUPPORTED_CONVERSION",
                    event_status="failure",
                )
                results.append({
                    "filename": uploaded_file.filename,
                    "status": "failed",
                    "error": "UNSUPPORTED_CONVERSION",
                    "message": str(exc) or "Conversion not supported",
                    "conversion_id": tracker.conversion_id,
                })
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
                    output_format=(this_target if 'this_target' in locals() else (target_format or '')),
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
            # Keep compatibility: report the explicit target for single-file responses
            result_target = result.get("target_format") or target_format
            result["target_format"] = result_target
            if result["status"] == "failed":
                request.state.error_code = normalize_error_code(result.get("error"), fallback="CONVERSION_FAILED")
                analytics_service.track_conversion_failed(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{Path(file[0].filename or 'file').suffix.lstrip('.') or 'file'}-to-{target_format}",
                    output_format=result.get("target_format") or (target_format or ''),
                    error_type=request.state.error_code,
                    event_status="failure",
                )
                if result.get("error") == "UNSUPPORTED_CONVERSION":
                    error_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                    error_detail = {
                        "success": False,
                        "code": "UNSUPPORTED_CONVERSION",
                        "message": result.get("message") or "Conversion not supported",
                    }
                else:
                    error_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    error_detail = result["error"]
                raise HTTPException(
                    status_code=error_status_code,
                    detail=error_detail,
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
            "target_formats": [r.get("target_format") for r in results],
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