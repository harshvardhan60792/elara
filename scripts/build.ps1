# Builds the onedir PyInstaller bundle. TEMP/TMP are redirected to D:\tmp\build
# first - PyInstaller unpacks a lot of intermediate state, and C: does not
# have room for it (ADR-003). Output lands in dist\elara\.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

New-Item -ItemType Directory -Force -Path "D:\tmp\build" | Out-Null
$env:TEMP = "D:\tmp\build"
$env:TMP = "D:\tmp\build"

$python = ".\.venv\Scripts\python.exe"

if (-not (Test-Path "assets\icon_armed.ico")) {
    & $python scripts\make_icons.py
}

Write-Host "Building elara.spec (this can take several minutes)..."
& $python -m PyInstaller elara.spec --noconfirm --clean --distpath dist --workpath "D:\tmp\build\pyinstaller"

Write-Host "Build complete: dist\elara\elara.exe"
