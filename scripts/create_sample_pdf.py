from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

base = Path(__file__).resolve().parent.parent / "test_files"
base.mkdir(parents=True, exist_ok=True)
path = base / "sample.pdf"
canvas_obj = canvas.Canvas(str(path), pagesize=letter)
canvas_obj.drawString(100, 700, "Hello PDF")
canvas_obj.showPage()
canvas_obj.save()
print(f"Created PDF sample: {path}")
