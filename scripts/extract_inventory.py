"""Read-only SAI/APK inventory. Usage: python scripts/extract_inventory.py [backup.apks]."""
import hashlib
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract_checked(archive, target):
    target.mkdir(parents=True, exist_ok=True)
    for entry in archive.infolist():
        dest = (target / entry.filename).resolve()
        if not dest.is_relative_to(target.resolve()):
            raise ValueError(f'Unsafe archive entry: {entry.filename}')
        if entry.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        data = archive.read(entry)  # also validates CRC
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if dest.read_bytes() != data:
                raise ValueError(f'Refusing to overwrite different evidence: {dest}')
        else:
            dest.write_bytes(data)


def main():
    source = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else next(ROOT.glob('*.apks'))
    OUT.mkdir(exist_ok=True)
    digest = sha256(source)
    with zipfile.ZipFile(source) as archive:
        extract_checked(archive, OUT / 'splits')
    results = {'source': str(source), 'source_size': source.stat().st_size,
               'source_sha256': digest, 'apks': []}
    for apk in sorted((OUT / 'splits').glob('*.apk')):
        with zipfile.ZipFile(apk) as archive:
            extract_checked(archive, OUT / 'unpacked' / apk.stem)
            entries = [{'path': e.filename, 'size': e.file_size, 'compressed_size': e.compress_size,
                        'crc32': f'{e.CRC:08x}'} for e in archive.infolist()]
        results['apks'].append({'path': str(apk.relative_to(ROOT)), 'size': apk.stat().st_size,
                                'sha256': sha256(apk), 'entries': entries})
    assert sha256(source) == digest, 'Source changed during extraction'
    (OUT / 'inventory.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in results.items() if k != 'apks'}, indent=2))
    print(f"Extracted and inventoried {len(results['apks'])} APKs")


if __name__ == '__main__':
    main()
