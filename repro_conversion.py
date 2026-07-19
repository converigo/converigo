import asyncio
import io
from pathlib import Path

from fastapi import UploadFile

from app.services.upload_service import UploadService
from app.services.conversion_service import ConversionService


async def main() -> None:
    p = Path('tests/assets/real-test.jpg')
    data = p.read_bytes()
    file = UploadFile(
        filename=p.name,
        file=io.BytesIO(data),
        headers={'content-type': 'image/jpeg'},
    )
    saved_path = await UploadService().process_upload(file)
    print('saved', saved_path, 'exists', saved_path.exists(), 'size', saved_path.stat().st_size)
    try:
        result = await ConversionService().convert_file(saved_path, 'png')
        print('result', result, 'exists', result.exists(), 'size', result.stat().st_size)
    except Exception as exc:
        import traceback
        traceback.print_exc()


asyncio.run(main())
