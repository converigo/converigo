import urllib.request
import urllib.error
from pathlib import Path

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = []
body.append(b'--' + boundary.encode() + b'\r\n')
body.append(b'Content-Disposition: form-data; name="file"; filename="sample_image.png"\r\n')
body.append(b'Content-Type: image/png\r\n\r\n')
body.append(Path('sample_image.png').read_bytes())
body.append(b'\r\n')
body.append(b'--' + boundary.encode() + b'\r\n')
body.append(b'Content-Disposition: form-data; name="target_format"\r\n\r\n')
body.append(b'jpg\r\n')
body.append(b'--' + boundary.encode() + b'--\r\n')
request_body = b''.join(body)

req = urllib.request.Request('http://127.0.0.1:8003/convert', data=request_body, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

try:
    with urllib.request.urlopen(req, timeout=120) as response:
        print('STATUS', response.status)
        print('BODY', response.read().decode('utf-8', 'ignore'))
except urllib.error.HTTPError as e:
    print('HTTPERR', e.code)
    print(e.read().decode('utf-8', 'ignore'))
except Exception as e:
    print('ERR', repr(e))
