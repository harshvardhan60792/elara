# Zips the built dist\elara\ folder into a portable, no-install zip and
# writes SHA256SUMS.txt next to it. Run scripts\build.ps1 first.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path "dist\elara\elara.exe")) {
    throw "dist\elara\elara.exe not found - run scripts\build.ps1 first"
}

$version = (Get-Content pyproject.toml | Select-String '^version = "(.+)"').Matches[0].Groups[1].Value
$zipName = "elara-$version-portable-win64.zip"
$zipPath = "dist\$zipName"

if (Test-Path $zipPath) { Remove-Item $zipPath }

Write-Host "Zipping dist\elara -> $zipPath"
Compress-Archive -Path "dist\elara\*" -DestinationPath $zipPath

$hash = Get-FileHash $zipPath -Algorithm SHA256
"$($hash.Hash.ToLower())  $zipName" | Out-File -FilePath "dist\SHA256SUMS.txt" -Encoding utf8 -Append

Write-Host "Wrote $zipPath and appended its hash to dist\SHA256SUMS.txt"
