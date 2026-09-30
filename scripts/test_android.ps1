param([string]$Serial, [switch]$Disconnect)
$ErrorActionPreference = 'Stop'
$adbCommand = Get-Command adb -ErrorAction SilentlyContinue
$adb = if ($adbCommand) { $adbCommand.Source } else { Join-Path $env:LOCALAPPDATA 'Android/Sdk/platform-tools/adb.exe' }
if (-not (Test-Path -LiteralPath $adb)) { throw 'Install Android SDK Platform Tools or add adb to PATH.' }
$rows = & $adb devices
if ($LASTEXITCODE -ne 0) { throw 'Could not list Android devices.' }
$devices = @($rows | Where-Object { $_ -match '^\S+\s+device$' } | ForEach-Object { ($_ -split '\s+')[0] })
if (-not $Serial) {
    if ($devices.Count -eq 0) { throw 'Connect your phone by USB, enable USB debugging, and approve the debugging prompt on the phone.' }
    if ($devices.Count -gt 1) { throw 'Several devices are connected. Run this script with -Serial <device-id>.' }
    $Serial = $devices[0]
}
if ($Serial -notin $devices) { throw 'The selected device is not connected or has not authorized USB debugging.' }
if ($Disconnect) {
    & $adb -s $Serial reverse --remove tcp:8000
    if ($LASTEXITCODE -ne 0) { throw 'Could not remove the USB connection.' }
    Write-Host 'USB app connection removed.'
    exit 0
}
try { $null = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000' -TimeoutSec 10 }
catch { throw 'Start the PC app first: .\scripts\start.ps1 -WithModel' }
& $adb -s $Serial reverse tcp:8000 tcp:8000
if ($LASTEXITCODE -ne 0) { throw 'Could not connect the phone to the PC app.' }
& $adb -s $Serial shell am start -a android.intent.action.VIEW -d http://127.0.0.1:8000/
if ($LASTEXITCODE -ne 0) { throw 'Connection is ready. Open http://127.0.0.1:8000/ in the phone browser.' }
Write-Host 'Ready: http://127.0.0.1:8000/ on your phone. Keep the USB cable connected and the PC app running.'
Write-Host 'AI processing, chats, and saved memories remain on the PC. This tests the phone interface, not on-phone AI performance.'
