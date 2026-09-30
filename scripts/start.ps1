param([switch]$WithModel, [switch]$DeviceB)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run the setup commands in README.md first.' }
& $python -m scripts.configure_local
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'data/logs') | Out-Null
function Test-LocalPort([int]$Port) {
    $probe = [System.Net.Sockets.TcpClient]::new()
    try { $probe.Connect('127.0.0.1', $Port); return $true } catch { return $false } finally { $probe.Dispose() }
}
if ($WithModel -and -not (Test-LocalPort 8081)) {
    $llm = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'data/llm/runtime') -Filter llama-server.exe -Recurse | Select-Object -First 1
    if (-not $llm) { throw 'Run python -m scripts.setup_llm first.' }
    $model = Join-Path $projectRoot 'data/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf'
    Start-Process -FilePath $llm.FullName -ArgumentList @('-m', ('"' + $model + '"'), '--host','127.0.0.1','--port','8081','-c','8192','-t','4','--alias','ps3-local','--log-disable') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput 'data/logs/model.log' -RedirectStandardError 'data/logs/model-error.log' | Out-Null
}
if ($DeviceB) {
    $previousDataDir = $env:PS3_DATA_DIR
    $env:PS3_DATA_DIR = 'data/device-b'
    try { & $python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --no-access-log }
    finally { $env:PS3_DATA_DIR = $previousDataDir }
} else {
    if (-not (Test-LocalPort 8090)) {
        Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','backend.cloud:app','--host','127.0.0.1','--port','8090','--no-access-log') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput 'data/logs/cloud.log' -RedirectStandardError 'data/logs/cloud-error.log' | Out-Null
    }
    Write-Host 'Open http://127.0.0.1:8000. Ctrl+C stops the device server.'
    & $python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
}
