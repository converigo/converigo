import asyncio
from pathlib import Path


def test_txt_to_pdf(tmp_path):
    # Create sample TXT input
    src = tmp_path / "sample.txt"
    src.write_text("This is a small test\nLine two\n", encoding="utf-8")

    # Import plugin and run conversion
    from app.plugins.document.txt_to_pdf import TXTToPDFPlugin

    plugin = TXTToPDFPlugin()

    out_path = asyncio.run(plugin.convert(src, "pdf"))

    assert out_path.exists(), "Output PDF was not created"
    assert out_path.suffix.lower() == ".pdf"
    data = out_path.read_bytes()
    assert len(data) > 0
    assert data[:4] == b"%PDF"
