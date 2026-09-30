$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$server = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'data/llm/runtime') -Filter llama-server.exe -Recurse | Select-Object -First 1
if (-not $server) { throw 'Run .venv\Scripts\python.exe -m scripts.setup_llm first.' }
& $server.FullName -m (Join-Path $projectRoot 'data/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf') --host 127.0.0.1 --port 8081 -c 8192 -t 4 --alias ps3-local --log-disable
