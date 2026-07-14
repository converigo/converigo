import subprocess, time, requests
from pathlib import Path

BASE = 'https://converigo.com'
OUT_DIR = Path('tmp_prod_tests_real')
OUT_DIR.mkdir(exist_ok=True)

for size_mb in [5, 25, 50, 64]:
    out_path = OUT_DIR / f'{size_mb}mb.mp4'
    duration = max(5, size_mb)
    print(f'\n=== TEST {size_mb} MB ===')
    cmd = [
        'ffmpeg','-y','-f','lavfi','-i',f'testsrc=size=1280x720:rate=30:duration={duration}',
        '-f','lavfi','-i',f'sine=frequency=1000:duration={duration}',
        '-shortest','-c:v','libx264','-preset','ultrafast','-b:v','8M','-c:a','aac','-b:a','128k','-movflags','+faststart',str(out_path)
    ]
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.time() - t0
    print('generate_exit', result.returncode)
    print('generate_seconds', round(dt,2))
    if result.returncode != 0:
        print('generate_stderr', result.stderr[-2000:])
        continue
    print('generated', out_path.name, 'size_bytes', out_path.stat().st_size)
    t1 = time.time()
    with open(out_path, 'rb') as fh:
        response = requests.post(
            f'{BASE}/convert',
            files={'file': (out_path.name, fh, 'video/mp4')},
            data={'target_format': 'mp3'},
            timeout=1800,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
    dt2 = time.time() - t1
    print('http_status', response.status_code)
    print('response_time_sec', round(dt2,3))
    print('response_body', response.text[:2000])
