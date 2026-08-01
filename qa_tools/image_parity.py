from pathlib import Path
from PIL import Image, ImageChops

def compare_images(a: Path, b: Path, out: Path):
    ia = Image.open(a).convert('RGB')
    ib = Image.open(b).convert('RGB')
    if ia.size != ib.size:
        ib = ib.resize(ia.size)
    diff = ImageChops.difference(ia, ib)
    diff.save(out)
    print('wrote', out)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print('usage: image_parity.py reference.png before.png out.png')
    else:
        compare_images(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
