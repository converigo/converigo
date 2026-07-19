from pathlib import Path
from PIL import Image

p = Path('valid_test_image.jpg')
print('exists', p.exists())
print('size', p.stat().st_size)
print('head', p.read_bytes()[:32])
try:
    with Image.open(p) as img:
        print('format', img.format)
        print('size', img.size)
except Exception as e:
    print(type(e).__name__, e)
