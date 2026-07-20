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

from app.services.conversion_service import (
    ConversionError,
    ConversionService,
    UnsupportedConversionError,
)

from app.services.upload_service import (
    UploadError,
    UploadService,
)

from app.plugins.registry import registry


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/convert",
    tags=["convert"],
)


async def unsupported_conversion_exception_handler(
    request: Request,
    exc: UnsupportedConversionError,
) -> JSONResponse:
    return JSONResponse(
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

    file: List[UploadFile] = File(...),

    target_format: str = Form(...)

):


    logger.info("Convert request received: files=%d target=%s", len(file), target_format)

    if not file or len(file) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    target_format = target_format.lower().strip()
    
    upload_service = UploadService()
    conversion_service = ConversionService()
    
    results = []
    saved_paths = []

    try:
        # Process each file
        for uploaded_file in file:
            saved_path: Path | None = None
            try:
                saved_path = await upload_service.process_upload(uploaded_file)
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
                    raise UnsupportedConversionError(source_format, target_format) from exc

                output_path = await conversion_service.convert_file(
                    saved_path,
                    target_format
                )

                # Build download_path relative to configured OUTPUT_DIR when possible.
                try:
                    rel = output_path.relative_to(settings.OUTPUT_DIR)
                    download_path = "/outputs/" + str(rel).replace('\\\\', '/')
                except Exception:
                    # Fallback: preserve previous behavior (use parent folder name)
                    download_path = "/outputs/" + output_path.parent.name + "/" + output_path.name

                results.append({
                    "filename": output_path.name,
                    "download_path": download_path,
                    "status": "success",
                })

            except UnsupportedConversionError:
                raise
            except (UploadError, ConversionError) as exc:
                logger.warning("Conversion failed for %s: %s", uploaded_file.filename, exc)
                results.append({
                    "filename": uploaded_file.filename,
                    "status": "failed",
                    "error": str(exc),
                })

        # Return single-file format for 1 file (backward compatibility)
        # or batch format for multiple files
        if len(file) == 1 and len(results) == 1:
            result = results[0]
            result["status"] = "success" if result["status"] == "success" else "failed"
            result["target_format"] = target_format
            if result["status"] == "failed":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"],
                )
            return result
        
        # Batch response for multiple files
        return {
            "status": "completed",
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
        logger.exception("Unexpected error during batch conversion")
        raise HTTPException(
            status_code=500,
            detail="Batch conversion failed.",
        )

    finally:
        # Clean up all saved paths
        for saved_path in saved_paths:
            try:
                if saved_path and saved_path.exists():
                    saved_path.unlink()
            except Exception:
                logger.exception("Failed to remove temporary upload %s", saved_path)