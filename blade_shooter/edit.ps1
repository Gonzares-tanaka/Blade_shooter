$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = Join-Path $PSScriptRoot '..\..\shooting_1\.venv\Scripts\python.exe'
}
if (!(Test-Path -LiteralPath $pythonExe)) { throw 'Create .venv and install requirements.txt first.' }
& $pythonExe -m pyxel edit (Join-Path $PSScriptRoot 'assets\blade.pyxres')
