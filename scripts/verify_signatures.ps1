$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$jar = Join-Path $root 'tools/android-build-tools/android-16/lib/apksigner.jar'
$out = Join-Path $root 'analysis/signatures'
New-Item -ItemType Directory -Force -Path $out | Out-Null
foreach ($apk in Get-ChildItem -LiteralPath (Join-Path $root 'analysis/splits') -Filter '*.apk') {
    $result = & java -jar $jar verify --verbose --print-certs $apk.FullName 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Signature verification failed: $($apk.Name): $result" }
    $result | Set-Content -Encoding utf8 -LiteralPath (Join-Path $out ($apk.BaseName + '.txt'))
    Write-Output "Verified $($apk.Name)"
}
