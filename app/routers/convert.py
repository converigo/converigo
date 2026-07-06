from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.conversion_service import ConversionError, ConversionService
from app.services.upload_service import UploadError, UploadService

router = APIRouter(prefix="/convert", tags=["convert"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def convert_mp4_to_mp3(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".mp4"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only MP4 files are supported for conversion.",
        )

    try:
        saved_path = await UploadService().process_upload(file)
        output_path = await ConversionService().convert_file(saved_path, "mp3")
        return {
            "status": "success",
            "filename": output_path.name,
            "download_path": f"/outputs/audio/{output_path.name}",
            "message": "Conversion completed successfully.",
        }
    except UploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ConversionError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversion failed due to an unexpected error.",
        )
