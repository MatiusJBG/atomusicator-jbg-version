$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$executable = Join-Path $root "dist\SeparadorVocal.exe"
if (-not (Test-Path -LiteralPath $executable)) {
    throw "No existe el ejecutable empaquetado: $executable"
}

function Invoke-DesktopExecutable([string]$Argument) {
    $process = Start-Process -FilePath $executable -ArgumentList $Argument -PassThru -Wait
    return $process.ExitCode
}

$appData = Join-Path $env:LOCALAPPDATA "Separador Vocal\Separador Vocal"
$projects = Join-Path $appData "projects"
$logFile = Join-Path $appData "logs\separador-vocal.log"
$logBeforeDiagnostics = Get-Content -LiteralPath $logFile -Raw -ErrorAction SilentlyContinue
if ($null -eq $logBeforeDiagnostics) { $logBeforeDiagnostics = "" }
$diagnosticsExitCode = Invoke-DesktopExecutable "--diagnostics"
if ($diagnosticsExitCode -ne 0) {
    throw "El ejecutable empaquetado no pudo validar FFmpeg y el almacenamiento local."
}

if (-not (Test-Path -LiteralPath $projects -PathType Container)) {
    throw "La aplicación no creó su carpeta local de proyectos: $projects"
}
if (-not (Test-Path -LiteralPath $logFile -PathType Leaf)) {
    throw "La aplicación no pudo crear el registro local: $logFile"
}
$log = Get-Content -LiteralPath $logFile -Raw
$newDiagnosticLog = if ($log.StartsWith($logBeforeDiagnostics)) {
    $log.Substring($logBeforeDiagnostics.Length)
}
else {
    $log
}
$checkLine = ($newDiagnosticLog -split "`r?`n" | Where-Object { $_ -match "Desktop self-check passed" } | Select-Object -Last 1)
if (-not $checkLine -or $checkLine -notmatch [regex]::Escape($projects)) {
    throw "El diagnóstico empaquetado no confirmó la ruta local de proyectos."
}
if ($checkLine -notmatch "nms=ok") {
    throw "El diagnóstico empaquetado no pudo ejecutar la extensión nativa de TorchVision."
}
if ($checkLine -match "WinGet[\\/]Links[\\/]ffmpeg\.exe") {
    throw "El diagnóstico siguió usando el enlace WinGet en lugar del ejecutable real."
}

$modelDirectory = Join-Path $appData "models"
$requiredModels = @(
    "UVR_MDXNET_Main.onnx",
    "UVR_MDXNET_KARA_2.onnx",
    "kuielab_a_drums.onnx",
    "kuielab_a_bass.onnx"
)
$modelsAvailable = @($requiredModels | Where-Object {
    Test-Path -LiteralPath (Join-Path $modelDirectory $_) -PathType Leaf
}).Count -eq $requiredModels.Count
if ($modelsAvailable) {
    $logBeforeSeparation = Get-Content -LiteralPath $logFile -Raw
    $separationExitCode = Invoke-DesktopExecutable "--diagnostics-separation"
    if ($separationExitCode -ne 0) {
        throw "El flujo empaquetado de cuatro etapas no generó y validó los cinco stems."
    }
    $log = Get-Content -LiteralPath $logFile -Raw
    $newSeparationLog = if ($log.StartsWith($logBeforeSeparation)) {
        $log.Substring($logBeforeSeparation.Length)
    }
    else {
        $log
    }
    if ($newSeparationLog -notmatch "Separation self-test passed; stems=5; stages=4") {
        throw "El autodiagnóstico no confirmó que se validaron cinco stems en cuatro etapas."
    }
}
else {
    Write-Host "Model inference test skipped: reviewed model weights are not cached locally."
}

$logBeforeGui = Get-Content -LiteralPath $logFile -Raw
$guiExitCode = Invoke-DesktopExecutable "--diagnostics-ui"
if ($guiExitCode -ne 0) {
    throw "La aplicación no pudo crear y mostrar la ventana Qt."
}
$log = Get-Content -LiteralPath $logFile -Raw
$newGuiLog = if ($log.StartsWith($logBeforeGui)) {
    $log.Substring($logBeforeGui.Length)
}
else {
    $log
}
if ($newGuiLog -notmatch "GUI self-test passed; window_created=true; window_shown=true") {
    throw "El autodiagnóstico no confirmó que la ventana se mostrara."
}

Write-Host "Desktop smoke test passed: FFmpeg, local storage, TorchVision nms, optional five-stem inference, and Qt GUI launch."
