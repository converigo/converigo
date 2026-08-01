from pathlib import Path
from PIL import Image

img = Image.new('RGB', (120, 80), color=(255, 0, 0))
img.save('sample_image.png')
print('created', Path('sample_image.png').exists(), Path('sample_image.png').stat().st_size)
