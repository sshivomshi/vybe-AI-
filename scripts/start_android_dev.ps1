param([string]$Serial, [switch]$ConnectOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$command = Get-Command adb -ErrorAction SilentlyContinue
$adb = if ($command) { $command.Source } else { Join-Path $env:LOCALAPPDATA 'Android/Sdk/platform-tools/adb.exe' }
if (-not (Test-Path -LiteralPath $adb)) { throw 'Install Android SDK Platform Tools or add adb to PATH.' }
$rows = & $adb devices
if ($LASTEXITCODE -ne 0) { throw 'Could not list Android devices.' }
$devices = @($rows | Where-Object { $_ -match '^\S+\s+device$' } | ForEach-Object { ($_ -split '\s+')[0] })
if ($Serial -and $Serial -notin $devices) { throw 'Selected device is not connected or authorized.' }
if (-not $Serial -and $devices.Count -eq 1) { $Serial = $devices[0] }
if (-not $Serial -and $devices.Count -gt 1) { throw 'Use -Serial <device-id> when multiple devices are connected.' }
if ($Serial) {
    foreach ($port in @(8000,5173)) {
        & $adb -s $Serial reverse "tcp:$port" "tcp:$port"
        if ($LASTEXITCODE -ne 0) { throw "Could not forward port $port." }
    }
    Write-Host "Development ports connected for $Serial."
} else { Write-Warning 'No phone/emulator connected. Once connected, run this script in another terminal with -ConnectOnly.' }
if ($ConnectOnly) { return }
try { $null = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/status' -TimeoutSec 5 }
catch { throw 'Start the backend in another terminal first: .\scripts\start.ps1 -WithModel. Then run this script again.' }
Write-Host 'Run the android debug variant in Android Studio. Save frontend/src files for live UI updates.'
Write-Host 'Keep this terminal, the backend, and USB connection active. Ctrl+C stops Vite.'
Push-Location (Join-Path $root 'frontend')
try { & npm.cmd run dev -- --port 5173 --strictPort; if ($LASTEXITCODE -ne 0) { throw 'Vite stopped with an error. Check whether port 5173 is already in use.' } }
finally { Pop-Location }
