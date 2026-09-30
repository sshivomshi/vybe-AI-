param([string]$Serial)

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv/Scripts/python.exe'
$verifier = Join-Path $root 'scripts/verify_gemini_android.py'
$apk = Join-Path $root 'android/build/outputs/apk/debug/android-debug.apk'
$testApk = Join-Path $root 'android/build/outputs/apk/androidTest/debug/android-debug-androidTest.apk'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Create the project Python environment first: py -m venv .venv'
}
if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) {
    throw 'Missing scripts/verify_gemini_android.py. Restore the project setup verifier first.'
}
if (-not (Test-Path -LiteralPath $apk -PathType Leaf) -or -not (Test-Path -LiteralPath $testApk -PathType Leaf)) {
    throw 'Build both debug APKs first from the project folder: .\gradlew.bat :android:assembleDebug :android:assembleDebugAndroidTest'
}

# Use the same SDK location as the Python verifier so both target the same adb.
if (-not $env:LOCALAPPDATA) {
    throw 'LOCALAPPDATA is not set. Run this setup from your Windows user account.'
}
$adb = Join-Path $env:LOCALAPPDATA 'Android/Sdk/platform-tools/adb.exe'
if (-not (Test-Path -LiteralPath $adb -PathType Leaf)) {
    throw 'Install Android SDK Platform Tools at %LOCALAPPDATA%\Android\Sdk\platform-tools first.'
}

$rows = & $adb devices
if ($LASTEXITCODE -ne 0) { throw 'Could not list Android devices.' }
$devices = @($rows | Where-Object { $_ -match '^\S+\s+device\s*$' } | ForEach-Object { ($_ -split '\s+')[0] })
if ($devices.Count -eq 0) {
    throw 'Connect your phone by USB, enable USB debugging, and approve the debugging prompt on the phone.'
}
if ($devices.Count -ne 1) {
    throw 'The Gemini setup verifier requires exactly one authorized device. Disconnect other phones and stop emulators, then retry. -Serial cannot override this requirement.'
}
if ($Serial -and $Serial -ne $devices[0]) {
    throw 'The selected device is not the connected, authorized phone. Check its ID with adb devices.'
}
$Serial = $devices[0]

Write-Host "Installing the debug app and setup test on $Serial."
& $adb -s $Serial install -r $apk
if ($LASTEXITCODE -ne 0) { throw 'Debug app installation failed.' }
& $adb -s $Serial install -r $testApk
if ($LASTEXITCODE -ne 0) { throw 'Setup test APK installation failed.' }

Write-Host 'Enter your Gemini API key at the hidden prompt to configure the phone and verify a reply.'
& $python $verifier
if ($LASTEXITCODE -ne 0) { throw 'Gemini setup or verification failed. Review the verifier output before retrying.' }

& $adb -s $Serial shell am start -n com.mnemos.mobile.dev/com.mnemos.mobile.MainActivity
if ($LASTEXITCODE -ne 0) { throw 'Setup succeeded, but the app could not be opened. Open Mnemos Dev on your phone.' }
Write-Host 'Gemini setup and verification succeeded. Mnemos Dev is ready on your phone.'
