import subprocess, time, os, requests
from pathlib import Path

BASE = 'https://converigo.com'
OUT_DIR = Path('tmp_prod_tests')
OUT_DIR.mkdir(exist_ok=True)

configs = [
    (5, 20, '2M', '64k'),
    (25, 60, '5M', '128k'),
    (50, 90, '7M', '128k'),
    (64, 120, '8M', '128k'),
]

for size_mb, duration, video_bitrate, audio_bitrate in configs:
    out_path = OUT_DIR / f'{size_mb}mb.mp4'
    print(f'\n=== TEST {size_mb} MB ===')
    cmd = [
        'ffmpeg','-y','-f','lavfi','-i','color=c=black:s=1280x720:d='+str(duration),
        '-f','lavfi','-i','anullsrc=r=44100:cl=stereo',
        '-shortest','-c:v','libx264','-preset','ultrafast','-b:v',video_bitrate,'-c:a','aac','-b:a',audio_bitrate,'-movflags','+faststart',str(out_path)
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
            headers={'User-Agent':'Mozilla/5.0'}
        )
    dt2 = time.time() - t1
    print('http_status', response.status_code)
    print('response_time_sec', round(dt2,3))
    print('response_body', response.text[:4000])
