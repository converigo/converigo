"""Standalone real-file verification for Batch 3 (VAR-10 images-to-pdf, DOC-05 pdf-to-txt).

Generates REAL files on disk, converts via the real HTTP path (TestClient),
verifies outputs, and prints SHA256/size/page-count evidence.
Run: python tmp\\realfile_verify_batch3.py
"""
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"C:\converigo\wt_batch3")

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402
from pypdf import PdfReader  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from app.main import app  # noqa: E402

MIME = {"png": "image/png", "webp": "image/webp", "bmp": "image/bmp", "tiff": "image/tiff", "gif": "image/gif"}


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    client = TestClient(app)
    work = Path(tempfile.mkdtemp(prefix="b3_real_"))
    lines = [f"WORKDIR: {work}"]
    failures = []

    # ---------- VAR-10 images-to-pdf: 5 real image files -> 1 PDF ----------
    srcs = []
    for fmt, color in [
        ("png", (200, 30, 30)),
        ("webp", (30, 200, 30)),
        ("bmp", (30, 30, 200)),
        ("tiff", (120, 120, 20)),
        ("gif", (200, 20, 200)),
    ]:
        p = work / f"img_{fmt}.{fmt}"
        Image.new("RGB", (120, 90), color).save(p, format=fmt.upper())
        srcs.append(p)
        lines.append(f"SRC  {p.name:20s} size={p.stat().st_size:7d} sha256={_sha(p)}")

    payload = [
        ("file", (p.name, p.read_bytes(), MIME[p.suffix.strip(".").lower()]))
        for p in srcs
    ]
    resp = client.post(
        "/convert",
        files=payload,
        data={"target_format": "pdf", "operation": "images-to-pdf"},
    )
    lines.append(f"HTTP /convert images-to-pdf -> {resp.status_code}")
    if resp.status_code != 201:
        failures.append(f"images-to-pdf HTTP {resp.status_code}: {resp.text[:300]}")
    else:
        out_rel = resp.json()["download_path"].removeprefix("/download/")
        out_path = Path("outputs") / out_rel
        lines.append(f"OUT  {out_path.name:20s} size={out_path.stat().st_size:7d} sha256={_sha(out_path)}")
        header = out_path.read_bytes()[:5]
        reader = PdfReader(str(out_path))
        pages = len(reader.pages)
        lines.append(f"PDF header={header!r} pages={pages}")
        if header != b"%PDF-" or pages != 5:
            failures.append(f"images-to-pdf output invalid: header={header!r} pages={pages}")
        dl = client.get(resp.json()["download_path"])
        lines.append(f"HTTP /download -> {dl.status_code} bytes={len(dl.content)}")
        if dl.status_code != 200 or not dl.content:
            failures.append(f"download failed: {dl.status_code}")
        out_path.unlink(missing_ok=True)

    # ---------- DOC-05 pdf-to-txt: real 2-page PDF -> TXT ----------
    pdf_path = work / "doc.pdf"
    cv = canvas.Canvas(str(pdf_path))
    cv.drawString(100, 750, "BATCH3 REALFILE PAGE ONE alpha")
    cv.showPage()
    cv.drawString(100, 750, "BATCH3 REALFILE PAGE TWO beta")
    cv.showPage()
    cv.save()
    lines.append(f"SRC  doc.pdf             size={pdf_path.stat().st_size:7d} sha256={_sha(pdf_path)}")

    resp2 = client.post(
        "/convert",
        files=[("file", ("doc.pdf", pdf_path.read_bytes(), "application/pdf"))],
        data={"target_format": "txt", "operation": "pdf-to-txt"},
    )
    lines.append(f"HTTP /convert pdf-to-txt -> {resp2.status_code}")
    if resp2.status_code != 201:
        failures.append(f"pdf-to-txt HTTP {resp2.status_code}: {resp2.text[:300]}")
    else:
        out_rel2 = resp2.json()["download_path"].removeprefix("/download/")
        txt_path = Path("outputs") / out_rel2
        text = txt_path.read_text(encoding="utf-8")
        lines.append(f"OUT  {txt_path.name:20s} size={txt_path.stat().st_size:7d} sha256={_sha(txt_path)}")
        ok_alpha = "BATCH3 REALFILE PAGE ONE alpha" in text
        ok_beta = "BATCH3 REALFILE PAGE TWO beta" in text
        lines.append(f"TXT contains page-one text={ok_alpha} page-two text={ok_beta}")
        lines.append(f"TXT preview: {text[:120]!r}")
        if not (ok_alpha and ok_beta):
            failures.append("pdf-to-txt text extraction incomplete")
        txt_path.unlink(missing_ok=True)

    lines.append("")
    lines.append(f"RESULT: {'FAIL: ' + '; '.join(failures) if failures else 'ALL REAL-FILE VERIFICATIONS PASSED'}")
    report = "\n".join(lines)
    print(report)
    Path(__file__).parent.joinpath("realfile_verify_batch3.out.txt").write_text(report, encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())