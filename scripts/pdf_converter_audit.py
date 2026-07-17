import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Only audit PDF source flows from the user's specified list.
converters = [
    ("pdf", "docx"),
    ("pdf", "xlsx"),
    ("pdf", "pptx"),
    ("pdf", "odt"),
    ("pdf", "jpg"),
    ("pdf", "png"),
]

report = []

for source, target in converters:
    filename = Path("test_files") / "sample.pdf"
    if not filename.exists():
        raise FileNotFoundError(f"Test PDF not found: {filename}")

    with open(filename, "rb") as fh:
        files = {"file": (filename.name, fh, "application/pdf")}
        data = {"target_format": target}
        response = client.post("/convert", files=files, data=data)
        payload = None
        error = None
        plugin = None
        engine = None
        output_success = False

        try:
            payload = response.json()
        except Exception:
            payload = {"raw_text": response.text}

        # Attempt to glean plugin/engine from the response or logs.
        if response.status_code == 201:
            output_success = True
        else:
            error = payload.get("detail") or payload.get("message") or payload.get("error") or payload

        report.append({
            "converter": f"{source}-{target}",
            "status": response.status_code,
            "plugin": "unknown",
            "engine": "unknown",
            "error": error,
            "output_success": output_success,
            "response": payload,
        })

report_path = Path(__file__).resolve().parent.parent / "converter_audit_report.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Report written to {report_path}")
for item in report:
    print(item)
