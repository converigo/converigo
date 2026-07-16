"""
Project : Converigo
Author  : Pico Lala & ChatGPT

Convert Router

Version : 2.2.1
"""

import logging

from pathlib import Path

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

    file: UploadFile = File(...),

    target_format: str = Form(...)

):


    logger.info("Convert request received: file=%s target=%s", file.filename, target_format)

    saved_path: Path | None = None


    try:


        upload_service = UploadService()


        saved_path = await upload_service.process_upload(
            file
        )



        target_format = (
            target_format
            .lower()
            .strip()
        )



        source_format = (

            Path(saved_path)
            .suffix
            .replace(".", "")
            .lower()

        )



        try:


            registry.get_plugin(
                source_format,
                target_format
            )


        except ValueError as exc:


            raise UnsupportedConversionError(source_format, target_format) from exc



        conversion_service = ConversionService()



        output_path = await conversion_service.convert_file(

            saved_path,

            target_format

        )



        return {


            "status": "success",


            "filename": output_path.name,


            "download_path":
                "/outputs/" + output_path.parent.name + "/" + output_path.name,


            "message":
                "Conversion completed successfully.",


            "target_format":
                target_format

        }



    except UploadError as exc:
        logger.warning("Upload failed during conversion: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


    except UnsupportedConversionError:
        raise


    except ConversionError as exc:
        logger.warning("Conversion failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )



    except HTTPException:


        raise



    except Exception:
        logger.exception("Unexpected error during conversion")
        raise HTTPException(
            status_code=500,
            detail="Conversion failed.",
        )



    finally:
        try:
            if saved_path and saved_path.exists():
                saved_path.unlink()
        except Exception:
            logger.exception("Failed to remove temporary upload after conversion")