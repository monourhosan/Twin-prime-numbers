<#
.SYNOPSIS
    Launches the Phase 4 ADRS-4 Twin-Prime Discovery Campaign optimized for
    Intel Core i5-10210U (4c/8t) + NVIDIA GeForce MX250 (2 GB VRAM).

.DESCRIPTION
    Runs the hybrid GPU-accelerated twin-prime search in unattended, resumable mode.
    Includes hardware safety checks, AC power enforcement, and checkpointing.

.PARAMETER Config
    Path to configuration JSON file (default: configs/laptop_i5_10210u_mx250.json).

.PARAMETER Workers
    Number of worker processes (default: 3 for maximum-sustainable, 2 for balanced).

.PARAMETER DryRun
    If set, validates configuration and planned windows without running search.

.EXAMPLE
    .\scripts\run_laptop_campaign.ps1
    .\scripts\run_laptop_campaign.ps1 -Workers 2
    .\scripts\run_laptop_campaign.ps1 -DryRun
#>

[CmdletBinding()]
param (
    [string]$Config = "configs/laptop_i5_10210u_mx250.json",
    [int]$Workers = 0,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location -LiteralPath $ProjectRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Phase 4 ADRS-4 Laptop Search Launcher (i5-10210U + NVIDIA MX250)    " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Run Diagnostics and Safety Pre-check
Write-Host "`n[1/3] Running hardware and safety pre-flight checks..." -ForegroundColor Yellow
python scripts/laptop_doctor.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Laptop diagnostics check failed. Halting startup." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Build Execution Command
Write-Host "`n[2/3] Preparing campaign execution..." -ForegroundColor Yellow
$CmdArgs = @("-m", "src.phase4", "search", "--config", $Config)

if ($Workers -gt 0) {
    $CmdArgs += @("--workers", $Workers.ToString())
}

if ($DryRun) {
    $CmdArgs += "--dry-run"
}

Write-Host "  Executing: python $($CmdArgs -join ' ')" -ForegroundColor Green

# 3. Launch Process
Write-Host "`n[3/3] Starting search campaign (survives editor session closing)..." -ForegroundColor Yellow
& python @CmdArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[COMPLETED] Search session finished cleanly." -ForegroundColor Green
} else {
    Write-Host "`n[PAUSED/STOPPED] Search exited with code $LASTEXITCODE." -ForegroundColor Yellow
}
