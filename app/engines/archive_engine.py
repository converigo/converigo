"""
Archive Engine for Converigo

Handles extraction of archive formats: ZIP, RAR, 7Z, TAR, GZ
"""

import zipfile
import tarfile
import gzip
import shutil
from pathlib import Path

from app.engines.base_engine import BaseEngine


class ArchiveEngine(BaseEngine):
    """Engine for extracting archive files."""

    ENGINE_NAME = "archive"

    SUPPORTED_FORMATS = [
        "zip",
        "rar",
        "7z",
        "tar",
        "gz",
        "gzip",
        "tar.gz",
        "tgz",
    ]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        """Extract archive to output directory."""
        
        suffix = source_path.suffix.lower()
        stem = source_path.stem
        
        # Handle double extensions like .tar.gz
        if source_path.name.endswith(".tar.gz") or source_path.name.endswith(".tgz"):
            extract_dir_name = source_path.name.replace(".tar.gz", "").replace(".tgz", "")
        else:
            extract_dir_name = stem
        
        output_dir = Path("outputs") / "archive"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extract_path = output_dir / extract_dir_name
        extract_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if suffix == ".zip":
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            
            elif suffix == ".rar":
                # RAR extraction requires unrar executable
                import subprocess
                try:
                    subprocess.run(
                        ["unrar", "x", str(source_path), str(extract_path)],
                        check=True,
                        capture_output=True
                    )
                except FileNotFoundError:
                    raise RuntimeError(
                        "unrar is not installed. Please install WinRAR or unrar utility."
                    )
            
            elif suffix == ".7z":
                # 7Z extraction requires 7z executable
                import subprocess
                try:
                    subprocess.run(
                        ["7z", "x", str(source_path), f"-o{extract_path}"],
                        check=True,
                        capture_output=True
                    )
                except FileNotFoundError:
                    raise RuntimeError(
                        "7z is not installed. Please install 7-Zip or p7zip utility."
                    )
            
            elif suffix in {".tar", ".tgz", ".gz"}:
                # TAR and TAR.GZ handling
                if source_path.name.endswith(".tar.gz") or source_path.name.endswith(".tgz"):
                    with tarfile.open(source_path, "r:gz") as tar_ref:
                        tar_ref.extractall(extract_path)
                elif suffix == ".tar":
                    with tarfile.open(source_path, "r") as tar_ref:
                        tar_ref.extractall(extract_path)
                elif suffix == ".gz":
                    # For standalone .gz files, decompress to extract_dir/filename
                    output_file = extract_path / stem
                    with gzip.open(source_path, 'rb') as f_in:
                        with open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
            else:
                raise RuntimeError(f"Unsupported archive format: {suffix}")
            
            return extract_path
        
        except Exception as e:
            # Cleanup on failure
            if extract_path.exists():
                shutil.rmtree(extract_path)
            raise RuntimeError(f"Archive extraction failed: {str(e)}")
