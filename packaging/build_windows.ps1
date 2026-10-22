$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    py -3.13 -m venv .venv
    $python = Join-Path $root ".venv\Scripts\python.exe"
}
& $python -m pip install --upgrade pip
& $python -m pip install -e ".[desktop,separation-cpu]"
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de empaquetado." }

& $python -m PyInstaller --noconfirm packaging/SeparadorVocal.spec
if ($LASTEXITCODE -ne 0) { throw "Falló PyInstaller." }

$iscc = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $candidate = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $candidate) { $iscc = $candidate }
}
if (-not $iscc) {
    $candidate = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
    if (Test-Path $candidate) { $iscc = $candidate }
}
if (-not $iscc) {
    throw "Instala Inno Setup 6 y vuelve a ejecutar este script para crear el instalador."
}
& $iscc "packaging\SeparadorVocal.iss"
if ($LASTEXITCODE -ne 0) { throw "Falló la compilación del instalador Inno Setup." }
Write-Host "Instalador generado en dist\SeparadorVocal-Setup.exe"
