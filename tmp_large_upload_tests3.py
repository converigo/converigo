import subprocess, time, os
from pathlib import Path
import requests
BASE='http://127.0.0.1:8000'
LOG_PATH=Path('app/logs/app.log')
TMP=Path('tmp_large_upload_tests')
TMP.mkdir(exist_ok=True)
sizes_mb=[5,10,25,50,64,100]

for size_mb in sizes_mb:
    out_path = TMP / f'{size_mb}mb_real.mp4'
    duration_sec = max(5, int(size_mb * 10))  # 1 MB ~ 10s at 8Mbps-ish
    bitrate = '8M'
    print(f'\n=== TEST {size_mb} MB ===')
    cmd=['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-t',str(duration_sec),'-c:a','aac','-b:a',bitrate,str(out_path)]
    t0=time.time()
    result=subprocess.run(cmd, capture_output=True, text=True)
    dt=time.time()-t0
    print('generate_exit', result.returncode)
    print('generate_seconds', round(dt,2))
    if result.returncode != 0:
        print('generate_stderr', result.stderr[-2000:])
        continue
    print('generated', out_path, 'size_bytes', out_path.stat().st_size)
    start=time.time()
    with open(out_path,'rb') as fh:
        resp=requests.post(f'{BASE}/convert', files={'file': (out_path.name, fh, 'video/mp4')}, data={'target_format': 'mp3'}, timeout=1800)
    elapsed=time.time()-start
    print('http_status', resp.status_code)
    print('elapsed_sec', round(elapsed,2))
    print('body', resp.text[:1000])
    if resp.status_code == 201:
        try:
            data=resp.json(); download_path=data.get('download_path'); print('download_path', download_path); dl=requests.get(f'{BASE}{download_path}', timeout=600); print('download_status', dl.status_code); print('download_bytes', len(dl.content))
        except Exception as e:
            print('download_error', repr(e))
    if LOG_PATH.exists():
        lines=LOG_PATH.read_text(encoding='utf-8', errors='ignore').splitlines(); relevant=[ln for ln in lines if 'Convert request received' in ln or 'Conversion failed' in ln or 'Upload failed' in ln or 'Unexpected error during conversion' in ln or 'Upload failed during conversion' in ln]
        print('log_tail:')
        for ln in relevant[-8:]:
            print(ln)
    time.sleep(1)
