import argparse
import os
import requests
import subprocess
import time
from pathlib import Path

BASE = os.environ.get('CONVERIGO_BASE_URL', 'http://127.0.0.1:8000')


def generate_dummy_mp4(path: Path, size_mb: int):
    # simple fallback when ffmpeg isn't available: create a file of approximate size
    path.write_bytes(b'0' * (size_mb * 1024 * 1024))
    return path


def generate_with_ffmpeg_target_bytes(path: Path, target_bytes: int):
    # try to use ffmpeg to create a file near `target_bytes` using -fs
    cmd = [
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:d=10',
        '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-b:v', '4M',
        '-c:a', 'aac', '-b:a', '128k', '-shortest', '-fs', str(target_bytes), str(path)
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def generate_with_ffmpeg_duration(path: Path, duration_sec: int, bitrate='1M'):
    cmd = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', str(duration_sec), '-c:a', 'aac', '-b:a', bitrate, str(path)]
    return subprocess.run(cmd, capture_output=True, text=True)


def run_tests(sizes_mb, mode='dummy'):
    out_dir = Path('tmp_large_upload_tests')
    out_dir.mkdir(exist_ok=True)
    for size in sizes_mb:
        print(f'\n=== TEST {size} MB ===')
        out_path = out_dir / f'{size}mb.mp4'
        if mode == 'dummy':
            generate_dummy_mp4(out_path, size)
            generated = True
        elif mode == 'ffmpeg_bytes':
            target_bytes = size * 1024 * 1024
            result = generate_with_ffmpeg_target_bytes(out_path, target_bytes)
            print('generate_exit', result.returncode)
            if result.returncode != 0:
                print('generate_stderr', result.stderr[-2000:])
                generated = False
            else:
                generated = True
        else:  # ffmpeg_duration
            duration = max(5, int(size * 10))
            result = generate_with_ffmpeg_duration(out_path, duration, bitrate='8M')
            print('generate_exit', result.returncode)
            if result.returncode != 0:
                print('generate_stderr', result.stderr[-2000:])
                generated = False
            else:
                generated = True

        if not generated:
            print('skipping upload due to generation failure')
            continue

        print('generated', out_path, 'size_bytes', out_path.stat().st_size)
        start = time.time()
        with open(out_path, 'rb') as fh:
            resp = requests.post(f'{BASE}/convert', files={'file': (out_path.name, fh, 'video/mp4')}, data={'target_format': 'mp3'}, timeout=1800)
        elapsed = time.time() - start
        print('http_status', resp.status_code)
        print('elapsed_sec', round(elapsed, 2))
        print('body', resp.text[:1000])
        if resp.status_code == 201:
            try:
                data = resp.json(); download_path = data.get('download_path'); print('download_path', download_path); dl = requests.get(f'{BASE}{download_path}', timeout=600); print('download_status', dl.status_code); print('download_bytes', len(dl.content))
            except Exception as e:
                print('download_error', repr(e))


def cli():
    p = argparse.ArgumentParser()
    p.add_argument('--sizes', nargs='+', type=int, default=[5, 10, 25, 50, 64, 100])
    p.add_argument('--mode', choices=['dummy', 'ffmpeg_bytes', 'ffmpeg_duration'], default='dummy')
    args = p.parse_args()
    run_tests(args.sizes, mode=args.mode)


if __name__ == '__main__':
    cli()
