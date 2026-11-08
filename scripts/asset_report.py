"""Inventory bundled web resources and archives; validate packaged engine checksums."""
import hashlib
import json
import pathlib
import re
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'
ASSETS = OUT / 'unpacked/base/assets/flutter_assets/assets'
atlas = ASSETS / 'sky_atlas'
report = {'files': [], 'archives': {}, 'engine_checksums': []}
for path in sorted(ASSETS.rglob('*')):
    if not path.is_file():
        continue
    data = path.read_bytes()
    report['files'].append({'path': str(path.relative_to(ROOT)), 'size': len(data),
                            'sha256': hashlib.sha256(data).hexdigest()})
    if path.suffix == '.zip':
        with zipfile.ZipFile(path) as archive:
            report['archives'][str(path.relative_to(ROOT))] = [
                {'name': e.filename, 'size': e.file_size} for e in archive.infolist()]
    if path.suffix == '.wasm':
        report['wasm_header'] = data[:8].hex()
manifest = json.loads((atlas / 'engine-manifest.json').read_text())
for name, expected in manifest['sha256'].items():
    actual = hashlib.sha256((atlas / name).read_bytes()).hexdigest()
    report['engine_checksums'].append({'file': name, 'expected': expected, 'actual': actual, 'matches': expected == actual})
libapp = OUT / 'unpacked/split_config.arm64_v8a/lib/arm64-v8a/libapp.so'
data = libapp.read_bytes()
match = re.search(rb'\{"schema": 1, "features": .*?"scan_radius_km": 500\}\}\}', data)
if match:
    report['embedded_feature_policy'] = {'file_offset': hex(match.start()), 'policy': json.loads(match.group())}
    (OUT / 'embedded_feature_policy.json').write_bytes(match.group())
(OUT / 'asset_inventory.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'engine_checksums': report['engine_checksums'], 'asset_count': len(report['files']),
                  'policy_offset': report.get('embedded_feature_policy', {}).get('file_offset')}, indent=2))
