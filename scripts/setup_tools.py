"""Download pinned analysis tools into tools/. Does not install or run the target app."""
import hashlib
import pathlib
import subprocess
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
TOOLS.mkdir(exist_ok=True)
downloads = [
    ('https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip',
     'jadx-1.5.6.zip', 'jadx-1.5.6', '545ea2be9c242511bc145755cf4bda2485ade42966e096f8b4d3da2a230e8974'),
    ('https://dl.google.com/android/repository/build-tools_r36_windows.zip',
     'build-tools_r36_windows.zip', 'android-build-tools', 'aa1095cb14d83e483818a748a2c06faaeb8e601561b06a356a119a1b2ca280d3'),
]
for url, name, directory, expected in downloads:
    archive = TOOLS / name
    if not archive.exists():
        with urllib.request.urlopen(url, timeout=180) as response:
            archive.write_bytes(response.read())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError(f'Checksum mismatch: {archive}')
    with zipfile.ZipFile(archive) as source:
        target = (TOOLS / directory).resolve()
        for entry in source.infolist():
            if not (target / entry.filename).resolve().is_relative_to(target):
                raise ValueError(entry.filename)
        source.extractall(target)
    print(f'{name}: {digest}')
blutter = TOOLS / 'blutter'
commit = '4a60ac648bf448c5a7596437243bcd0b9376fdf0'
if not blutter.exists():
    subprocess.run(['git', 'clone', 'https://github.com/worawit/blutter.git', str(blutter)], check=True)
    subprocess.run(['git', '-C', str(blutter), 'checkout', commit], check=True)
actual = subprocess.check_output(['git', '-C', str(blutter), 'rev-parse', 'HEAD'], text=True).strip()
if actual != commit:
    raise ValueError(f'Unexpected Blutter commit: {actual}')
for name in ('blutter.py', 'dartvm_fetch_build.py'):
    path = blutter / name
    code = path.read_text()
    path.write_text(code.replace('subprocess.run([NINJA_CMD],', "subprocess.run([NINJA_CMD, '-j', '4'],"))
print(f'Blutter: {commit}; tool compilation limited to four jobs')
