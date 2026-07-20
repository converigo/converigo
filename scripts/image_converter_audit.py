import asyncio
import json
from pathlib import Path
from PIL import Image
from app.plugins.registry import registry as plugin_registry

ROOT = Path('tests/assets/regression')
OUT = Path('build')
OUT.mkdir(exist_ok=True)

cases = [
    {"name":"JPG -> PNG","source":ROOT / 'sample.jpg',"target":"png","expected_format":"PNG"},
    {"name":"PNG -> JPG","source":ROOT / 'sample.png',"target":"jpg","expected_format":"JPEG"},
    {"name":"WEBP -> JPG","source":ROOT / 'sample.webp',"target":"jpg","expected_format":"JPEG"},
]

results = []

async def run_case(case):
    src = case['source']
    tgt = case['target']
    name = case['name']
    entry = {"converter":name, "input":str(src), "input_ok":False, "input_format":None, "input_size":None, "output":None, "status":None, "error":None}

    if not src.exists():
        entry['status']='FAIL'
        entry['error']='Input missing'
        return entry

    try:
        entry['input_size']=src.stat().st_size
        with Image.open(src) as im:
            entry['input_format']=im.format
        entry['input_ok']=True
    except Exception as e:
        entry['status']='FAIL'
        entry['error']=f'Input open failed: {e}'
        return entry

    try:
        plugin = plugin_registry.get_plugin(src.suffix.lstrip('.'), tgt)
    except Exception as e:
        entry['status']='FAIL'
        entry['error']=f'Plugin resolution failed: {e}'
        return entry

    try:
        out_path = await plugin.convert(src, tgt)
        entry['output']=str(out_path)
        if not out_path.exists() or out_path.stat().st_size==0:
            entry['status']='FAIL'
            entry['error']='Output missing or empty'
            return entry
        # validate with Pillow
        try:
            with Image.open(out_path) as im:
                im.verify()
                out_format = im.format
            if out_format and out_format.upper()==case['expected_format']:
                entry['status']='PASS'
            else:
                entry['status']='FAIL'
                entry['error']=f'Unexpected output format: {out_format} != {case["expected_format"]}'
        except Exception as e:
            entry['status']='FAIL'
            entry['error']=f'Pillow verify failed: {e}'
    except Exception as e:
        entry['status']='FAIL'
        entry['error']=str(e)

    return entry

async def main():
    for c in cases:
        print('Running',c['name'])
        r = await run_case(c)
        results.append(r)
        print('Result', r['status'])

    # write report
    report_lines = ['# IMAGE CONVERTER AUDIT REPORT', '']
    for r in results:
        report_lines.append('Converter: ' + r['converter'])
        report_lines.append('Input: ' + r['input'])
        report_lines.append('Input OK: ' + str(r.get('input_ok')))
        report_lines.append('Input format: ' + str(r.get('input_format')))
        report_lines.append('Input size: ' + str(r.get('input_size')))
        report_lines.append('Output: ' + str(r.get('output')))
        report_lines.append('Result: ' + str(r.get('status')))
        report_lines.append('Error: ' + str(r.get('error')))
        report_lines.append('')

    with open(OUT/'image_converter_audit_report.md','w',encoding='utf8') as fh:
        fh.write('\n'.join(report_lines))

    with open(OUT/'image_converter_audit_results.json','w',encoding='utf8') as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    print('Wrote build/image_converter_audit_report.md and results.json')

if __name__=='__main__':
    asyncio.run(main())
