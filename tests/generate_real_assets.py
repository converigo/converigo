from pathlib import Path
from PIL import Image

out = Path("tests") / "assets"
out.mkdir(parents=True, exist_ok=True)

img = Image.new("RGB", (800, 600), (200, 100, 50))

jpg_path = out / "real-test.jpg"
png_path = out / "real-test.png"
pdf_path = out / "real-test.pdf"

img.save(jpg_path, "JPEG", quality=90)
img.save(png_path, "PNG")
# Save a simple one-page PDF
img.save(pdf_path, "PDF", resolution=100.0)

for p in (jpg_path, png_path, pdf_path):
    print(f"WROTE: {p} ({p.stat().st_size} bytes)")
