param([switch]$Decompile)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $python = Join-Path $root '.venv/Scripts/python.exe'
    & $python scripts/extract_inventory.py
    if ($LASTEXITCODE -ne 0) { throw 'Extraction failed' }
    & $python scripts/static_report.py
    if ($LASTEXITCODE -ne 0) { throw 'Static report failed' }
    & $python scripts/asset_report.py
    if ($LASTEXITCODE -ne 0) { throw 'Asset report failed' }
    & "$PSScriptRoot/verify_signatures.ps1"
    $zipalign = Join-Path $root 'tools/android-build-tools/android-16/zipalign.exe'
    & $zipalign -c -P 16 -v 4 analysis/splits/split_config.arm64_v8a.apk |
        Set-Content -Encoding utf8 analysis/zipalign-arm64.txt
    if ($LASTEXITCODE -ne 0) { throw 'Native split alignment verification failed' }
    if ($Decompile) {
        & $python scripts/decompile.py
        if ($LASTEXITCODE -ne 0) { throw 'Decompiler orchestration failed' }
    }
} finally { Pop-Location }
