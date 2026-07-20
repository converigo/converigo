import asyncio
import json
from pathlib import Path
from app.services.conversion_manager import ConversionManager
from app.plugins.registry import registry as plugin_registry

from PIL import Image
import shutil
import subprocess

ROOT = Path('tests/assets/regression')
OUT = Path('build')
OUT.mkdir(exist_ok=True)

conv = ConversionManager()

cases = [
    # Images
    {"name":"JPG -> PNG","source":ROOT / 'sample.jpg',"target":"png","type":"image"},
    {"name":"PNG -> JPG","source":ROOT / 'sample.png',"target":"jpg","type":"image"},
    {"name":"WEBP -> JPG","source":ROOT / 'sample.webp',"target":"jpg","type":"image"},
    {"name":"JPG -> PDF","source":ROOT / 'sample.jpg',"target":"pdf","type":"image"},
    # Audio
    {"name":"MP4 -> MP3","source":ROOT / 'sample_with_audio.mp4',"target":"mp3","type":"audio"},
    {"name":"MP4 -> WAV","source":ROOT / 'sample_with_audio.mp4',"target":"wav","type":"audio"},
    # Document
    {"name":"DOCX -> PDF","source":ROOT / 'sample.docx',"target":"pdf","type":"document"},
    {"name":"PDF -> DOCX","source":ROOT / 'sample.pdf',"target":"docx","type":"document"},
    {"name":"PDF -> XLSX","source":ROOT / 'sample.pdf',"target":"xlsx","type":"document"},
    {"name":"PDF -> PPT","source":ROOT / 'sample.pdf',"target":"ppt","type":"document"},
]

# Fix small typo in last case target key
cases[-1]['target'] = 'ppt'

results = []

async def run_case(case):
    name = case['name']
    src = case['source']
    tgt = case['target']
    typ = case['type']
    entry = {"converter":name, "input":str(src), "output":None, "status":None, "error":None, "validation":None}
    if not src.exists():
        entry['status']='BLOCKED'
        entry['error']='Source file missing'
        return entry
    try:
        # prefer plugin registry which holds instances
        plugin = plugin_registry.get_plugin(src.suffix.lstrip('.'), tgt)
    except Exception as e:
        entry['status']='FAIL'
        entry['error']=f'Plugin resolution failed: {e}'
        return entry
    try:
        out_path = await plugin.convert(src, tgt)
        entry['output']=str(out_path)
        if not out_path.exists():
            entry['status']='FAIL'
            entry['error']='Output not produced'
            return entry
        # validation: choose by target format where appropriate
        # If target is pdf, run PDF validation (prefer PyMuPDF if available)
        if tgt.lower() == 'pdf':
            try:
                import fitz
                try:
                    doc = fitz.open(str(out_path))
                    page_count = doc.page_count
                    if page_count > 0:
                        entry['status'] = 'PASS'
                        entry['validation'] = f'PyMuPDF open OK pages={page_count}'
                    else:
                        entry['status'] = 'FAIL'
                        entry['error'] = 'PDF opened but contains zero pages'
                except Exception as e:
                    entry['status'] = 'FAIL'
                    entry['error'] = f'PyMuPDF failed to open PDF: {e}'
            except ImportError:
                # PyMuPDF not available; fallback to basic checks
                if out_path.exists() and out_path.stat().st_size > 0:
                    entry['status'] = 'PASS'
                    entry['validation'] = 'file exists and non-empty (PyMuPDF not installed)'
                else:
                    entry['status'] = 'FAIL'
                    entry['error'] = 'Output missing or empty and PyMuPDF not available'
        elif typ == 'image':
            try:
                with Image.open(out_path) as im:
                    im.verify()
                entry['status']='PASS'
                entry['validation']='PIL open OK'
            except Exception as e:
                entry['status']='FAIL'
                entry['error']=f'PIL open failed: {e}'
        elif typ=='audio':
            # try ffprobe
            ffprobe=shutil.which('ffprobe')
            if ffprobe:
                cmd=[ffprobe,'-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(out_path)]
                try:
                    r=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
                    dur=r.stdout.strip()
                    if dur:
                        entry['status']='PASS'
                        entry['validation']=f'duration={dur}'
                    else:
                        entry['status']='FAIL'
                        entry['error']='ffprobe returned no duration'
                except Exception as e:
                    entry['status']='FAIL'
                    entry['error']=f'ffprobe failed: {e}'
            else:
                entry['status']='WARNING'
                entry['validation']='ffprobe not available — output exists'
        elif typ=='document':
            # simple checks: output exists and non-zero
            if out_path.stat().st_size>0:
                entry['status']='PASS'
                entry['validation']='file exists and non-empty'
            else:
                entry['status']='FAIL'
                entry['error']='Empty output file'
        else:
            entry['status']='PASS'
    except Exception as e:
        entry['status']='FAIL'
        entry['error']=str(e)
    return entry

async def main():
    for c in cases:
        print('Running',c['name'])
        r=await run_case(c)
        results.append(r)
        print('Result',r['status'])
    with open(OUT/'real_conversion_results.json','w',encoding='utf8') as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print('Wrote build/real_conversion_results.json')

if __name__=='__main__':
    asyncio.run(main())
