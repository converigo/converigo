import urllib.request, hashlib
from pathlib import Path

def check_asset(local: Path, remote_url: str):
    with open(local, 'rb') as f:
        local_hash = hashlib.sha256(f.read()).hexdigest()
    req = urllib.request.Request(remote_url)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        remote_hash = hashlib.sha256(data).hexdigest()
    print(local, 'local_sha256', local_hash)
    print(remote_url, 'remote_sha256', remote_hash)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('usage: asset_parity.py local_path remote_url')
    else:
        check_asset(Path(sys.argv[1]), sys.argv[2])
