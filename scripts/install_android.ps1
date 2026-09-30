param([string]$Serial)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$apk = Join-Path $root 'dist/android/Mnemos-Android.apk'
$command = Get-Command adb -ErrorAction SilentlyContinue
$adb = if ($command) { $command.Source } else { Join-Path $env:LOCALAPPDATA 'Android/Sdk/platform-tools/adb.exe' }
if (-not (Test-Path -LiteralPath $apk)) { throw 'Build the APK first: .\.venv\Scripts\python.exe scripts/build_android.py' }
if (-not (Test-Path -LiteralPath $adb)) { throw 'Install Android SDK Platform Tools or add adb to PATH.' }
$rows = & $adb devices
if ($LASTEXITCODE -ne 0) { throw 'Could not list devices.' }
$devices = @($rows | Where-Object { $_ -match '^\S+\s+device$' } | ForEach-Object { ($_ -split '\s+')[0] })
if (-not $Serial) {
    if ($devices.Count -ne 1) { throw 'Connect and authorize one Android phone using USB debugging, or use -Serial <device-id>.' }
    $Serial = $devices[0]
}
if ($Serial -notin $devices) { throw 'The selected phone is not connected or authorized.' }
& $adb -s $Serial install -r $apk
if ($LASTEXITCODE -ne 0) { throw 'APK installation failed.' }
& $adb -s $Serial shell am start -n com.mnemos.mobile/.MainActivity
if ($LASTEXITCODE -ne 0) { throw 'Installed. Open Mnemos from your phone launcher.' }
Write-Host 'Mnemos installed. Start chatting with the connection already provisioned on this phone. USB and the PC are not needed for chatting.'
