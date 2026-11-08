"""Record the final static review checks, including original evidence integrity."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
report = {'scope': 'Phase 1 static only; no device/emulator execution or backend calls', 'checks': {}}
for script in ('verify_integrity.py', 'verify_native_sites.py'):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)], capture_output=True, text=True)
    report['checks'][script] = {'exit_code': result.returncode, 'stdout': result.stdout.strip(),
                                'stderr': result.stderr.strip()}
    if result.returncode:
        raise RuntimeError(f'{script}: {result.stderr}')
asset = json.loads((ROOT / 'analysis/asset_inventory.json').read_text())
assert all(x['matches'] for x in asset['engine_checksums'])
report['checks']['engine_checksums'] = '3/3 match'
signatures = list((ROOT / 'analysis/signatures').glob('*.txt'))
assert len(signatures) == 6
for signature in signatures:
    content = signature.read_text(encoding='utf-8-sig')
    assert 'Verifies' in content and 'v3): true' in content
    assert '6648201f62392c24a7896d6fcc2804573c985c64f7ea144e11bed717272542f4' in content
report['checks']['signature_reports'] = '6/6 verify v3 with expected shared signer'
assert 'Verification successful' in (ROOT / 'analysis/zipalign-arm64.txt').read_text(encoding='utf-8-sig')
report['checks']['native_zip_alignment'] = '16 KiB check passed'
report['checks']['aot_methods'] = len(json.loads((ROOT / 'analysis/aot_methods.json').read_text()))
report['checks']['aot_direct_calls'] = len(json.loads((ROOT / 'analysis/aot_calls.json').read_text()))
markers = (ROOT / 'analysis/jadx_incomplete_methods.txt').read_text(encoding='utf-8-sig').splitlines()
report['checks']['jadx_marker_files'] = len({line.split('.java:', 1)[0] for line in markers})
report['checks']['jadx_exit_status'] = json.loads((ROOT / 'analysis/jadx_status.json').read_text(encoding='utf-8-sig'))
report['deliverables'] = {}
for name in ('architecture.md', 'entitlement_analysis.md', 'findings.md', 'rebuild_plan.md'):
    path = ROOT / 'docs' / name
    data = path.read_bytes()
    assert len(data) > 100
    report['deliverables'][str(path.relative_to(ROOT))] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
(ROOT / 'analysis/validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report['checks'], indent=2))
