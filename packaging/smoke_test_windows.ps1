$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$executable = Join-Path $root "dist\SeparadorVocal.exe"
if (-not (Test-Path -LiteralPath $executable)) {
    throw "No existe el ejecutable empaquetado: $executable"
}

& $executable --diagnostics
if ($LASTEXITCODE -ne 0) {
    throw "El ejecutable empaquetado no pudo validar FFmpeg y el almacenamiento local."
}

$appData = Join-Path $env:LOCALAPPDATA "Separador Vocal\Separador Vocal"
$projects = Join-Path $appData "projects"
$logFile = Join-Path $appData "logs\separador-vocal.log"
if (-not (Test-Path -LiteralPath $projects -PathType Container)) {
    throw "La aplicación no creó su carpeta local de proyectos: $projects"
}
if (-not (Test-Path -LiteralPath $logFile -PathType Leaf)) {
    throw "La aplicación no pudo crear el registro local: $logFile"
}
$log = Get-Content -LiteralPath $logFile -Raw
$checkLine = ($log -split "`r?`n" | Where-Object { $_ -match "Desktop self-check passed" } | Select-Object -Last 1)
if (-not $checkLine -or $checkLine -notmatch [regex]::Escape($projects)) {
    throw "El diagnóstico empaquetado no confirmó la ruta local de proyectos."
}
if ($checkLine -match "WinGet[\\/]Links[\\/]ffmpeg\.exe") {
    throw "El diagnóstico siguió usando el enlace WinGet en lugar del ejecutable real."
}

$guiProcess = Start-Process -FilePath $executable -PassThru -WindowStyle Hidden
try {
    Start-Sleep -Seconds 8
    $guiProcess.Refresh()
    if ($guiProcess.HasExited) {
        throw "La interfaz gráfica se cerró antes de completar el smoke test."
    }
}
finally {
    if (-not $guiProcess.HasExited) {
        Stop-Process -Id $guiProcess.Id -Force
    }
}

Write-Host "Desktop smoke test passed: Qt app launched, FFmpeg ran from its real path, and local storage is writable."
