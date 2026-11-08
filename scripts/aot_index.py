"""Index Blutter's static disassembly and app-to-app calls (not recovered source)."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
methods, calls = [], []
for path in sorted((ROOT / 'analysis/blutter/asm/sky_radar').rglob('*.dart')):
    current = None
    lines = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if re.match(r'^  \S.*\{\s*$', line) and i + 1 < len(lines) and '** addr:' in lines[i + 1]:
            match = re.search(r'addr: (0x[0-9a-f]+), size: (0x[0-9a-f]+)', lines[i + 1])
            if match:
                current = {'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'line': i + 1,
                           'declaration': line.strip(), 'address': match[1], 'size': match[2]}
                methods.append(current)
        match = re.search(r'//\s+(0x[0-9a-f]+): bl\s+#(0x[0-9a-f]+)\s+; \[package:sky_radar/([^]]+)\] (.+)', line)
        if match:
            calls.append({'caller': current, 'instruction': match[1], 'target_address': match[2],
                          'target_library': match[3], 'target_symbol': match[4]})
for name, obj in [('aot_methods.json', methods), ('aot_calls.json', calls)]:
    (ROOT / 'analysis' / name).write_text(json.dumps(obj, indent=2), encoding='utf-8')
print(f'{len(methods)} app methods; {len(calls)} direct app-to-app calls indexed')
