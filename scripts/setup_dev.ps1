# Elara dev environment setup.
# Everything stays on D: â€” the C: drive on this machine is nearly full.

$ErrorActionPreference = "Stop"

$root     = Split-Path -Parent $PSScriptRoot
$venv     = Join-Path $root ".venv"
$py       = Join-Path $venv "Scripts\python.exe"
$pipCache = "D:\tmp\pip-cache"

New-Item -ItemType Directory -Force -Path $pipCache, "D:\tmp\elara", "D:\tmp\build" | Out-Null

$free = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
Write-Host "C: free space: $free GB (installs are redirected to D:)"

if (-not (Test-Path $py)) {
    Write-Host "Creating venv with Python 3.12 at $venv"
    py -3.12 -m venv $venv
}

& $py -m pip install --upgrade pip --cache-dir $pipCache
& $py -m pip install -r (Join-Path $root "requirements.txt")     --cache-dir $pipCache
& $py -m pip install -r (Join-Path $root "requirements-dev.txt") --cache-dir $pipCache
& $py -m pip install -e $root --no-deps --cache-dir $pipCache

& $py -c "import mediapipe, cv2, numpy, PySide6; print('core imports ok')"

Write-Host ""
Write-Host "Done. Voice extras are optional:"
Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements-voice.txt --cache-dir $pipCache"
Write-Host "Run:  .\.venv\Scripts\python.exe -m elara"
