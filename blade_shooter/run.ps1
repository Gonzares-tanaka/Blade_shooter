$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) {
    $existingPython = Join-Path $PSScriptRoot '..\..\shooting_1\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $existingPython) { $pythonExe = $existingPython }
}
if (!(Test-Path -LiteralPath $pythonExe)) {
    throw 'Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
}
& $pythonExe main.py @args
