from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from app.engines.archive_engine import ArchiveEngine


@pytest.mark.certified
def test_archive_limits_reject_zip_bomb_like_ratio(tmp_path: Path) -> None:
    zip_path = tmp_path / "bomb.zip"
    # Small compressed bytes can explode in some cases; we simulate via many large members.
    # Engine should reject based on limits even if compression ratio is high.
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i in range(300):
            zf.writestr(f"file_{i}.txt", "A" * 1024)  # 1KB each

    zip_path.write_bytes(bio.getvalue())

    engine = ArchiveEngine()
    with pytest.raises(RuntimeError, match=r"limits|MAX_FILES|MAX_TOTAL_SIZE|bomb|security|Archive extraction failed"):
        import asyncio

        asyncio.run(engine.convert(source_path=zip_path, target_format="zip"))

