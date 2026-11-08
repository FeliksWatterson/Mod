"""Validate original backup and every preserved/extracted ZIP entry, read-only."""
import hashlib
import io
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
source = ROOT / 'SkyRadar by Duy Chris_com.duychris.sky_radar_0.6.14.apks'
EXPECTED = '07671a93371ebaa1e6aa31cf2bd8ab8d64c2ffd27c5087baa92be45abc0d2b84'
with source.open('rb') as stream:
    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
assert actual == EXPECTED, f'Original backup differs: {actual}'
count = 0
with zipfile.ZipFile(source) as backup:
    for entry in backup.infolist():
        if entry.is_dir():
            continue
        payload = backup.read(entry)
        preserved = ROOT / 'analysis/splits' / entry.filename
        assert preserved.read_bytes() == payload, str(preserved)
        if entry.filename.endswith('.apk'):
            with zipfile.ZipFile(io.BytesIO(payload)) as apk:
                for member in apk.infolist():
                    if member.is_dir():
                        continue
                    unpacked = ROOT / 'analysis/unpacked' / pathlib.Path(entry.filename).stem / member.filename
                    assert unpacked.read_bytes() == apk.read(member), str(unpacked)
                    count += 1
print(f'Original SHA-256 unchanged: {actual}; all SAI entries and {count} unpacked APK members byte-identical')
