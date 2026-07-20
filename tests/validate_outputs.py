from PIL import Image
from pathlib import Path

paths=[
 'outputs/image/475a1ed1a2a740e8a9cbd778f227c711.png',
 'outputs/image/605922a00b3444d4a208491bf51224a8.jpg',
 'outputs/document/914d0dbf00564feda5f9e47e399fdb2d_page_01.jpg',
]

for p in paths:
    pth=Path(p)
    ok=False
    err=None
    if not pth.exists():
        print('MISSING', p)
        continue
    try:
        with Image.open(pth) as im:
            im.verify()
        ok=True
    except Exception as e:
        err=str(e)
    print('CHECK', p, 'exists=', pth.exists(), 'size=', pth.stat().st_size, 'openable=', ok, 'error=', err)
