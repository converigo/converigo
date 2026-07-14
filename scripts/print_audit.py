from pathlib import Path
import sys
import json

# ensure workspace root is on sys.path for imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.production_audit_service import ProductionAuditService

pa = ProductionAuditService(contracts_dir=Path('app/data/converters'))
report = pa.audit_all()
print(json.dumps(report['summary'], indent=2))

for res in report['results']:
    fails = [k for k, v in res['checks'].items() if not v]
    if fails:
        print('\n' + res['slug'] + ': ' + ', '.join(fails))
