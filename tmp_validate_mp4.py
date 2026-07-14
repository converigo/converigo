from pathlib import Path
from io import BytesIO
from fastapi import UploadFile
import app.utils.file_validator as fv

p = Path('tmp_prod_5mb.mp4')
data = p.read_bytes()
buf = BytesIO(data)
file = UploadFile(filename=p.name, file=buf, headers={'content-type': 'video/mp4'})

print('file', p.name)
print('size', len(data))
print('first256hex', data[:256].hex())
print('detected_extension', Path(p.name).suffix.lower().replace('.', ''))
print('detected_mime', file.content_type)
print('ftyp_offset', data.find(b'ftyp'))
print('moov_offset', data.find(b'moov'))
print('mdat_offset', data.find(b'mdat'))

try:
    fv.validate_signature(file, 'mp4')
    print('validation_result', 'accepted')
except Exception as exc:
    print('validation_result', 'rejected', str(exc))
