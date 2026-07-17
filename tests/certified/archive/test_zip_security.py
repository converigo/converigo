from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from app.engines.archive_engine import ArchiveEngine


@pytest.mark.certified
def test_zip_rejects_path_traversal(tmp_path: Path) -> None:
    # Create a malicious zip with ../ traversal
    zip_path = tmp_path / "malicious.zip"
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../evil.txt", "EVIL")
        zf.writestr("safe/ok.txt", "OK")

    zip_path.write_bytes(bio.getvalue())

    engine = ArchiveEngine()
    with pytest.raises(RuntimeError, match=r"unsafe|traversal|security|Archive extraction failed"):
        import asyncio

        asyncio.run(engine.convert(source_path=zip_path, target_format="zip"))


@pytest.mark.certified
def test_zip_members_must_stay_inside_target(tmp_path: Path) -> None:
    zip_path = tmp_path / "escape.zip"
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # absolute path entry
        zf.writestr("/abs/evil.txt", "EVIL")

    zip_path.write_bytes(bio.getvalue())

    engine = ArchiveEngine()
    with pytest.raises(RuntimeError, match=r"unsafe|absolute|traversal|security|Archive extraction failed"):
        import asyncio

        asyncio.run(engine.convert(source_path=zip_path, target_format="zip"))

