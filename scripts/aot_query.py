"""Read indexed static AOT methods: python scripts/aot_query.py <path regex> [method regex].

With no method regex, list declarations. With one, print symbolic disassembly
comments; use the indexed source file for complete ARM64 instructions.
"""
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[1]
methods = json.loads((ROOT / 'analysis/aot_methods.json').read_text(encoding='utf-8'))
for method in methods:
    if not re.search(sys.argv[1], method['path'], re.I):
        continue
    if len(sys.argv) < 3:
        print(f"{method['address']} {method['declaration']} ({method['path']}:{method['line']})")
        continue
    if not re.search(sys.argv[2], method['declaration'], re.I):
        continue
    print(f"\n{method['path']}:{method['line']} {method['declaration']} @ {method['address']}")
    lines = (ROOT / method['path']).read_text(encoding='utf-8').splitlines()
    for line in lines[method['line']:]:
        if line == '  }':
            break
        if re.match(r'    // 0x', line):
            print(line.strip())
