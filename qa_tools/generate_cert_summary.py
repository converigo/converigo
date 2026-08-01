import json, pathlib
p = pathlib.Path('qa_reports/summary/issues.md')
out = pathlib.Path('qa_reports/summary/certification_result.md')
fixes = pathlib.Path('qa_reports/summary/fixes.md')
if not p.exists():
    print('no issues file')
    raise SystemExit(1)
allr = json.loads(p.read_text())
lines = ['# Certification Results\n']
fix_lines = ['# Fixes\n']
for k,v in allr.items():
    res = v['results']
    passed = True
    reasons = []
    if res.get('hasHorizontalScroll'):
        passed = False; reasons.append('horizontal_scroll')
    if res.get('overflowCandidates') and len(res.get('overflowCandidates'))>0:
        passed = False; reasons.append('overflow_candidates')
    if res.get('overlappingButtons') and len(res.get('overlappingButtons'))>0:
        passed = False; reasons.append('overlapping_buttons')
    if v.get('console_count',0)>0:
        passed = False; reasons.append('console_errors')
    pres = res.get('presence',{})
    missing = [k2 for k2,ex in pres.items() if not ex]
    if missing:
        passed = False; reasons.append('missing_sections:'+','.join(missing))
    lines.append(f'- {k}: {"PASS" if passed else "FAIL"}')
    if not passed:
        lines.append(f'  - reasons: {",".join(reasons)}')
        # add a placeholder fix note
        fix_lines.append(f'- {k}: Investigate {",".join(reasons)}')

out.write_text('\n'.join(lines))
fixes.write_text('\n'.join(fix_lines))
print('written certification_result and fixes')
