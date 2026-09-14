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
    CONVERSION_TIMEOUT_FAILURE_MESSAGE,
    GENERIC_CONVERSION_FAILURE_MESSAGE,
    ConversionError,
    ConversionService,
    ConversionTimeoutError,
    UnsupportedConversionError,
)

from app.services.upload_service import (
    UploadError,
    UploadRejectedError,
    UploadService,
)


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/convert",
    tags=["convert"],
)
analytics_service = AnalyticsService()

# ---------------------------------------------------------------------------
# D4 (F1): client-facing failure contract
#
# Plugin and engine exceptions are internal: their text can name classes,
# engines, module paths or on-disk locations. A failing response therefore only
# ever carries one of the stable codes and safe literals below, plus the
# request_id / conversion_id that correlate it with the server-side log record.
# Nothing here is derived from a Python exception class name.
# ---------------------------------------------------------------------------
CONVERSION_FAILED_CODE = "CONVERSION_FAILED"
CONVERSION_TIMEOUT_CODE = "CONVERSION_TIMEOUT"
UPLOAD_FAILED_CODE = "UPLOAD_FAILED"
UNSUPPORTED_FILE_TYPE_CODE = "UNSUPPORTED_FILE_TYPE"
GENERIC_UPLOAD_FAILURE_MESSAGE = "The file could not be uploaded. Please try again."


def client_failure_fields(exc: Exception) -> tuple[str, str, bool]:
    """Map a per-file failure to (public code, safe message, upload_rejected)."""
    if isinstance(exc, UploadRejectedError):
        # PR-1: this text is the validator's own re-save guidance, built from
        # public policy literals - it is the purpose of the response, not a leak.
        return UNSUPPORTED_FILE_TYPE_CODE, str(exc), True
    if isinstance(exc, UploadError):
        return UPLOAD_FAILED_CODE, GENERIC_UPLOAD_FAILURE_MESSAGE, False
    if isinstance(exc, ConversionTimeoutError):
        return CONVERSION_TIMEOUT_CODE, CONVERSION_TIMEOUT_FAILURE_MESSAGE, False
    return CONVERSION_FAILED_CODE, GENERIC_CONVERSION_FAILURE_MESSAGE, False


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

    # Optional `operation` slug (e.g. "pdf-compress", "pdf-split") sent by the
    # /tools/* frontend to disambiguate converters that share the same pair.
    operation = (form.get('operation') or '')
    operation = operation.lower().strip() if operation else None
    if operation is not None and not registry.has_slug(operation):
        request.state.error_code = "UNSUPPORTED_CONVERSION"
        tracker.fail("validation", request.state.error_code)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "code": "UNSUPPORTED_CONVERSION",
                "message": f"Operation '{operation}' is not registered (slug tidak tersedia).",
            },
        )

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
        # PDF Merge (DOC-27) is a multi-file operation: upload every file
        # first, then merge them into a single PDF output via pypdf.
        if operation == "pdf-merge":
            tracker.set_converter("pdf-merge")
            tracker.start("upload")
            for uploaded_file in file:
                merge_saved = await upload_service.process_upload(uploaded_file)
                saved_paths.append(merge_saved)
            tracker.finish("upload")

            if len(saved_paths) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="pdf-merge requires at least 2 PDF files",
                )

            tracker.start("conversion")
            merge_output = await conversion_service.merge_files(
                saved_paths,
                conversion_id=tracker.conversion_id,
                plugin_slug=operation,
            )
            tracker.finish("conversion")

            tracker.start("download")
            try:
                rel = merge_output.relative_to(settings.OUTPUT_DIR)
                merge_download_path = "/download/" + rel.as_posix()
            except Exception:
                merge_download_path = "/download/" + merge_output.parent.name + "/" + merge_output.name
            tracker.finish("download")

            merge_ms = elapsed_ms(getattr(request.state, "request_started_ns", 0)) if getattr(request.state, "request_started_ns", None) else None
            analytics_service.track_conversion_success(
                request,
                page_path=request.url.path,
                converter_name="pdf-merge",
                category="document",
                output_format="pdf",
                event_status="success",
                processing_ms=merge_ms,
            )

            return {
                "filename": merge_output.name,
                "download_path": merge_download_path,
                "status": "success",
                "target_format": "pdf",
                "conversion_id": tracker.conversion_id,
            }

        # Images to PDF (VAR-10) is a multi-file operation: upload every image
        # first, then combine them into a single PDF via Pillow.
        if operation == "images-to-pdf":
            tracker.set_converter("images-to-pdf")
            tracker.start("upload")
            for uploaded_file in file:
                merge_saved = await upload_service.process_upload(uploaded_file)
                saved_paths.append(merge_saved)
            tracker.finish("upload")

            if len(saved_paths) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="images-to-pdf requires at least 2 image files",
                )

            tracker.start("conversion")
            merge_output = await conversion_service.merge_files(
                saved_paths,
                conversion_id=tracker.conversion_id,
                plugin_slug=operation,
            )
            tracker.finish("conversion")

            tracker.start("download")
            try:
                rel = merge_output.relative_to(settings.OUTPUT_DIR)
                merge_download_path = "/download/" + rel.as_posix()
            except Exception:
                merge_download_path = "/download/" + merge_output.parent.name + "/" + merge_output.name
            tracker.finish("download")

            merge_ms = elapsed_ms(getattr(request.state, "request_started_ns", 0)) if getattr(request.state, "request_started_ns", None) else None
            analytics_service.track_conversion_success(
                request,
                page_path=request.url.path,
                converter_name="images-to-pdf",
                category="image",
                output_format="pdf",
                event_status="success",
                processing_ms=merge_ms,
            )

            return {
                "filename": merge_output.name,
                "download_path": merge_download_path,
                "status": "success",
                "target_format": "pdf",
                "conversion_id": tracker.conversion_id,
            }

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
                    plugin = registry.get_plugin(source_format, this_target, slug=operation)
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
                    plugin_slug=operation,
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
                error_code, error_message, upload_rejected = client_failure_fields(exc)
                request.state.error_code = error_code
                if isinstance(exc, UploadError):
                    tracker.fail("upload", error_code)
                else:
                    tracker.fail("conversion", error_code)
                analytics_service.track_conversion_failed(
                    request,
                    page_path=request.url.path,
                    converter_name=tracker.converter or f"{Path(uploaded_file.filename or 'file').suffix.lstrip('.') or 'file'}-to-{target_format}",
                    output_format=(this_target if 'this_target' in locals() else (target_format or '')),
                    error_type=error_code,
                    event_status="failure",
                )
                # The exception itself - and therefore any plugin/engine detail -
                # stays in this log record only. exc_info keeps the traceback
                # available for correlation with the returned IDs.
                logger.warning(
                    "Conversion failed for %s: %s", uploaded_file.filename, exc, exc_info=True
                )
                results.append({
                    "filename": uploaded_file.filename,
                    "status": "failed",
                    "error": error_message,
                    "error_code": error_code,
                    # PR-1: a validation-policy rejection is a client error. Tag it
                    # so the single-file response can answer 415 instead of
                    # masking a refusal as a server-side 500. Genuine storage/IO
                    # failures keep raising the plain UploadError and stay 500s.
                    "upload_rejected": upload_rejected,
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
                # Prefer the code the failure handler already chose. Normalizing a
                # free-text message is how internal strings reached analytics.
                request.state.error_code = (
                    result.get("error_code")
                    or normalize_error_code(result.get("error"), fallback=CONVERSION_FAILED_CODE)
                )
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
                elif result.get("upload_rejected"):
                    # PR-1: the upload was refused by policy (e.g. a legacy OLE2
                    # .xls/.doc/.ppt, or any disallowed type). Report it honestly
                    # as an unsupported media type with the re-save guidance, never
                    # as a 500 that implies the server broke.
                    error_status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                    error_detail = {
                        "success": False,
                        "code": UNSUPPORTED_FILE_TYPE_CODE,
                        "message": result.get("error") or "Uploaded file was rejected.",
                    }
                else:
                    # D4 (F1): the same structured contract as the 422/415 paths.
                    # The internal exception text (and its traceback) lives in the
                    # log record, correlated through request_id / conversion_id.
                    error_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    error_detail = {
                        "success": False,
                        "code": request.state.error_code,
                        "message": result.get("error") or GENERIC_CONVERSION_FAILURE_MESSAGE,
                    }
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