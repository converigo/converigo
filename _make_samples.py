from pathlib import Path
from PIL import Image

out_dir = Path('test_files')
out_dir.mkdir(parents=True, exist_ok=True)

# BMP
bmp_path = out_dir / 'sample.bmp'
if not bmp_path.exists():
    img = Image.new('RGB', (200, 120), 'white')
    img.save(bmp_path)

# TIFF
tiff_path = out_dir / 'sample.tiff'
if not tiff_path.exists():
    img = Image.new('RGB', (200, 120), 'white')
    img.save(tiff_path)

# SVG
svg_path = out_dir / 'sample.svg'
if not svg_path.exists():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120">'
        '<rect width="200" height="120" fill="white"/>'
        '<text x="20" y="65" font-size="20" fill="black">Test</text>'
        '</svg>'
    )
    svg_path.write_text(svg, encoding='utf-8')

# Placeholder binary samples for HEIC/AVIF
# These are only to allow the conversion pipeline to attempt conversion; validation will show dependency gaps.
for name in ['sample.heic', 'sample.avif']:
    p = out_dir / name
    if not p.exists():
        p.write_bytes(b'')

print('samples ensured')

