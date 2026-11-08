"""Prepare pinned Dart sources from an archive when WSL Git transport is unavailable.

Only writes tool sources, never APK evidence. Uses Python's standard library.
"""
import hashlib
import json
import pathlib
import tarfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = '3.12.2'
SNAPSHOT = 'ace654289f5abc240509fc941453ebc5'
archive = ROOT / f'tools/dart-sdk-{VERSION}.tar.gz'
url = f'https://codeload.github.com/dart-lang/sdk/tar.gz/refs/tags/{VERSION}'
if not archive.exists():
    with urllib.request.urlopen(url, timeout=180) as response:
        archive.write_bytes(response.read())
expected = 'e84861c0a725990b6efbec1ec3be7cbf38352983871f8e74c3d42bc259a0a0d8'
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise ValueError('Dart SDK archive checksum mismatch')
dest = ROOT / f'tools/blutter/dartsdk/v{VERSION}'
dest.mkdir(parents=True, exist_ok=True)
with tarfile.open(archive) as source:
    for entry in source:
        parts = pathlib.PurePosixPath(entry.name).parts[1:]
        if not parts or parts[0] not in ('runtime', 'tools', 'third_party') or not entry.isfile():
            continue
        target = dest.joinpath(*parts).resolve()
        if not target.is_relative_to(dest.resolve()):
            raise ValueError(entry.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.extractfile(entry).read())
values = {}
for line in (dest / 'tools/VERSION').read_text().splitlines():
    if line and not line.startswith('#'):
        key, value = line.split(' ', 1)
        values[key] = value
values.update(SNAPSHOT_HASH=SNAPSHOT, GIT_HASH='archive', COMMIT_TIME='archive', VERSION_STR=VERSION)
code = (dest / 'runtime/vm/version_in.cc').read_text()
for key, value in values.items():
    code = code.replace('{{' + key + '}}', value)
(dest / 'runtime/vm/version.cc').write_text(code)
record = {'url': url, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
          'version': VERSION, 'snapshot_hash': SNAPSHOT,
          'note': 'version.cc generated from version_in.cc; display-only git fields set to archive'}
(ROOT / 'analysis/dart_sdk_source.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
