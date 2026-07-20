#!/usr/bin/env python
"""Update converter contract lifecycle_status fields"""
import json
from pathlib import Path

contracts_dir = Path('app/data/converters')

# Define target states
to_certify = {
    'jpg-to-png', 'png-to-jpg', 'png-to-webp', 'webp-to-png', 'bmp-to-jpg', 
    'tiff-to-jpg', 'pdf-to-docx', 'pdf-to-xlsx', 'pdf-to-ppt', 'pdf-to-odt',
    'docx-to-pdf', 'xlsx-to-pdf', 'ppt-to-pdf', 'mp4-to-mp3', 'mp4-to-m4a',
    'mp4-to-wav', 'mp4-to-aac', 'mp4-to-flac', 'mp4-to-ogg', 'avif-to-jpg',
    'heic-to-jpg', 'svg-to-png'
}

to_disable = {
    'xlsx-to-ods', 'docx-to-xlsx', 'docx-to-ppt', 
    'ppt-to-docx', 'ppt-to-jpg', 'ppt-to-xlsx'
}

updated_certified = []
updated_disabled = []

for contract_file in sorted(contracts_dir.glob('*.contract.json')):
    slug = contract_file.stem.replace('.contract', '')
    
    with open(contract_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    old_status = data.get('lifecycle_status')
    
    if slug in to_certify:
        if old_status != 'certified':
            data['lifecycle_status'] = 'certified'
            updated_certified.append(slug)
    elif slug in to_disable:
        if old_status != 'deprecated':
            data['lifecycle_status'] = 'deprecated'
            updated_disabled.append(slug)
    
    with open(contract_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

print("=== LIFECYCLE STATUS UPDATE ===")
print(f"\nUpdated to CERTIFIED ({len(updated_certified)}):")
for s in sorted(updated_certified):
    print(f"  ✓ {s}")

print(f"\nUpdated to DISABLED/DEPRECATED ({len(updated_disabled)}):")
for s in sorted(updated_disabled):
    print(f"  ✓ {s}")

print(f"\nTotal updated: {len(updated_certified) + len(updated_disabled)}")
