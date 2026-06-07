# Copy ffmpeg to standard Windows location + project folder, add to user PATH
$ErrorActionPreference = "Stop"

$Source = "D:\CodeApp\Txt2Audio\ffmpeg"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectFfmpeg = Join-Path $Root "ffmpeg"
$SystemFfmpeg = "C:\ffmpeg"
$BinPath = Join-Path $SystemFfmpeg "bin"

if (-not (Test-Path (Join-Path $Source "bin\ffmpeg.exe"))) {
    Write-Host "[ERROR] Source not found: $Source\bin\ffmpeg.exe" -ForegroundColor Red
    exit 1
}

Write-Host "Copying ffmpeg to $SystemFfmpeg ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $SystemFfmpeg | Out-Null
Copy-Item -Path $Source\* -Destination $SystemFfmpeg -Recurse -Force

Write-Host "Copying ffmpeg to $ProjectFfmpeg ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $ProjectFfmpeg | Out-Null
Copy-Item -Path $Source\* -Destination $ProjectFfmpeg -Recurse -Force

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinPath*") {
    $newPath = if ($userPath) { "$userPath;$BinPath" } else { $BinPath }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added $BinPath to user PATH (restart terminal/apps to pick up globally)." -ForegroundColor Green
} else {
    Write-Host "User PATH already contains $BinPath" -ForegroundColor Green
}

$env:Path = "$BinPath;" + $env:Path
& "$BinPath\ffmpeg.exe" -version | Select-Object -First 1
Write-Host "ffmpeg ready." -ForegroundColor Green
