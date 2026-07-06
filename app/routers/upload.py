from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.upload_service import UploadError, UploadService

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    try:
        saved_path = await UploadService().process_upload(file)
        return {
            "status": "success",
            "filename": saved_path.name,
            "message": "File uploaded successfully.",
        }
    except UploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the upload.",
        )
