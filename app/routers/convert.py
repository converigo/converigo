"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.1.0
"""

import traceback

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.services.conversion_service import (
    ConversionError,
    ConversionService,
)
from app.services.upload_service import (
    UploadError,
    UploadService,
)

router = APIRouter(
    prefix="/convert",
    tags=["convert"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def convert_file(

    file: UploadFile = File(...),

    target_format: str = Form(...),

):

    try:

        saved_path = await UploadService().process_upload(
            file
        )

        output_path = await ConversionService().convert_file(
            saved_path,
            target_format,
        )

        # menghasilkan path relatif dari folder outputs
        relative_path = output_path.relative_to("outputs")

        return {

            "status": "success",

            "filename": output_path.name,

            "download_path": f"/outputs/{relative_path.as_posix()}",

            "message": "Conversion completed successfully.",

            "target_format": target_format,

        }

    except UploadError as exc:

        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except ConversionError as exc:

        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    except Exception as exc:

        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )