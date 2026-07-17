import sys
from pathlib import Path

# Ensure repo root is on sys.path so `app` imports resolve when running script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

BASE = Path(__file__).resolve().parent.parent
TEST_FILES = BASE / "test_files"

# Preferred image/audio cases present in repo
cases = [
    (TEST_FILES / "sample.jpg", "png"),
    (TEST_FILES / "sample.png", "jpg"),
    (TEST_FILES / "sample.mp3", "mp3"),
    (TEST_FILES / "test.png", "jpg"),
]

# The user asked specifically for mp4->mp3 and pdf->docx as well. If sample files are missing, we'll note that.
extra_cases = [
    (TEST_FILES / "sample.mp4", "mp3"),
    (TEST_FILES / "sample.pdf", "docx"),
]

all_cases = cases + extra_cases

results = []

for path, target in all_cases:
    exists = path.exists()
    logger.info("Testing %s -> %s (exists=%s)", path.name, target, exists)
    if not exists:
        results.append({"file": str(path), "target": target, "status": "missing file"})
        continue

    with open(path, "rb") as fh:
        files = {"file": (path.name, fh, "application/octet-stream")}
        data = {"target_format": target}
        resp = client.post("/convert", files=files, data=data)
        try:
            payload = resp.json()
        except Exception as exc:
            payload = {"error": "invalid json response", "text": resp.text}

        results.append({
            "file": path.name,
            "target": target,
            "status_code": resp.status_code,
            "payload": payload,
        })


from pprint import pprint
pprint(results)

# Exit code 0 if all succeeded
failed = [r for r in results if isinstance(r.get("status_code"), int) and r.get("status_code") >= 400]
if failed:
    logger.error("Some conversions failed")
    for f in failed:
        logger.error(f)
    raise SystemExit(1)

logger.info("All tested conversions completed (or were skipped due to missing files).")
