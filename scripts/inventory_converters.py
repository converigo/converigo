import json
from pathlib import Path
p = Path('app/data/converters')
files = sorted([f for f in p.iterdir() if f.suffix=='.json'])
slugs = set()
entries = {}
for f in files:
    name = f.name
    base = name
    if base.endswith('.contract.json'):
        base = base[:-len('.contract.json')]
    elif base.endswith('.metadata.json'):
        base = base[:-len('.metadata.json')]
    elif base.endswith('.json'):
        base = base[:-len('.json')]
    slugs.add(base)
    try:
        j = json.loads(f.read_text())
    except Exception:
        j = None
    entries.setdefault(base, {})
    key = 'contract' if f.name.endswith('.contract.json') else ('metadata' if f.name.endswith('.metadata.json') else 'primary')
    entries[base][key] = {
        'file': str(f),
        'json_present': isinstance(j, dict)
    }
    if isinstance(j, dict):
        # capture source/target/active/engine
        entries[base].setdefault('meta', {})
        entries[base]['meta']['source'] = j.get('source')
        entries[base]['meta']['target'] = j.get('target')
        entries[base]['meta']['active'] = j.get('active')
        # lifecycle_status in contract files
        entries[base]['meta']['lifecycle_status'] = j.get('lifecycle_status')
        entries[base]['meta']['title'] = j.get('title')

out = {
    'all_files': len(files),
    'unique_slugs': len(slugs),
    'slugs': sorted(list(slugs)),
    'entries': entries
}
Path('build').mkdir(exist_ok=True)
with open('build/converter_inventory.json','w',encoding='utf8') as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)
print('Wrote build/converter_inventory.json')
