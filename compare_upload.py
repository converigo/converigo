from pathlib import Path
import difflib
app = Path('app/templates/tool_page.html').read_text(encoding='utf-8').splitlines()
proto = Path('design/workspace-prototype/index.html').read_text(encoding='utf-8').splitlines()
startapp = next(i for i,l in enumerate(app) if 'class="upload-card"' in l)
endapp = next(i for i,l in enumerate(app[startapp:], startapp) if 'id="uploadToast"' in l)
startproto = next(i for i,l in enumerate(proto) if 'class="upload-card"' in l)
endproto = next(i for i,l in enumerate(proto[startproto:], startproto) if 'id="uploadToast"' in l)
section_app = app[startapp:endapp+1]
section_proto = proto[startproto:endproto+1]
print('APP SECTION LINES', startapp+1, endapp+1)
print('PROTO SECTION LINES', startproto+1, endproto+1)
print('=== APP ===')
print('\n'.join(section_app))
print('=== PROTO ===')
print('\n'.join(section_proto))
print('=== DIFF ===')
for line in difflib.unified_diff(section_proto, section_app, fromfile='proto', tofile='app', lineterm=''):
    print(line)