from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from app.engines.archive_engine import ArchiveEngine


def _make_tar(path: Path, members: list[tuple[str, bytes]]) -> None:
    with tarfile.open(path, "w") as tf:
        for name, data in members:
            # TarInfo expects a relative name; we inject absolute/traversal strings.
            ti = tarfile.TarInfo(name=name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))


@pytest.mark.certified
def test_tar_rejects_path_traversal(tmp_path: Path) -> None:
    tar_path = tmp_path / "malicious.tar"
    _make_tar(tar_path, [("../evil.txt", b"EVIL"), ("safe/ok.txt", b"OK")])

    engine = ArchiveEngine()
    with pytest.raises(RuntimeError, match=r"unsafe|traversal|security|Archive extraction failed"):
        import asyncio

        asyncio.run(engine.convert(source_path=tar_path, target_format="tar"))


@pytest.mark.certified
def test_tar_rejects_absolute_paths(tmp_path: Path) -> None:
    tar_path = tmp_path / "absolute.tar"
    _make_tar(tar_path, [("/abs/evil.txt", b"EVIL")])

    engine = ArchiveEngine()
    with pytest.raises(RuntimeError, match=r"unsafe|absolute|traversal|security|Archive extraction failed"):
        import asyncio

        asyncio.run(engine.convert(source_path=tar_path, target_format="tar"))

