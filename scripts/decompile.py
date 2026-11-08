"""Run JADX and record partial-decompilation status without hiding failures."""
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
with (ROOT / 'analysis/jadx.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(['java', '-Xmx4g', '-jar', str(ROOT / 'tools/jadx-1.5.6/lib/jadx-1.5.6-all.jar'),
                             '-d', str(ROOT / 'analysis/jadx'), '--show-bad-code', '--log-level', 'ERROR',
                             str(ROOT / 'analysis/splits/base.apk')], stdout=log, stderr=subprocess.STDOUT)
status = {'exit_code': result.returncode, 'log': 'analysis/jadx.log', 'version': '1.5.6'}
(ROOT / 'analysis/jadx_status.json').write_text(json.dumps(status, indent=2))
markers = []
for path in sorted((ROOT / 'analysis/jadx/sources').rglob('*.java')):
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if re.search(r'JADX ERROR|Method not decompiled', line):
            markers.append(f'{path.relative_to(ROOT)}:{number}:{line.strip()}')
(ROOT / 'analysis/jadx_incomplete_methods.txt').write_text('\n'.join(markers), encoding='utf-8')
print(json.dumps(status))
if result.returncode:
    print('JADX output is partial. Review the log and DEX instructions for affected methods.')
print(f'{len(markers)} incomplete-method/error markers remain in generated Java; inspect the marker inventory.')
