# Phase 4 ADRS-4 Start Launcher for Windows PowerShell
param (
    [string]$Config = "configs/phase4/target_1000.json",
    [switch]$Resume,
    [switch]$DryRun,
    [int]$Workers = 1
)

Write-Host "=== Starting Phase 4 ADRS-4 Twin-Prime Search Launcher ===" -ForegroundColor Cyan
Write-Host "Config: $Config"
Write-Host "Workers: $Workers"

$pythonCmd = "python"
try {
    & $pythonCmd --version
} catch {
    Write-Host "Error: Python not found in PATH." -ForegroundColor Red
    exit 1
}

$cmdArgs = @("-m", "src.phase4", "search", "--config", $Config, "--workers", $Workers)
if ($Resume) { $cmdArgs += "--resume" }
if ($DryRun) { $cmdArgs += "--dry-run" }

& $pythonCmd $cmdArgs
