<#
.SYNOPSIS
    One-Click Turnkey Deployment Script for Windows (PowerShell)
.DESCRIPTION
    Sets up python virtual environment, installs dependencies, initializes SQLite WAL database,
    trains production ML model bundle, and verifies end-to-end functionality.
#>

param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "   Intelligent Support Triage & Routing Engine | Turnkey Installer (Windows)" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Check Python
$PythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonExe) {
    Write-Error "Python 3.11+ is required but not found in PATH. Please install Python and retry."
}
Write-Host "[+] Found Python: $($PythonExe.Source)" -ForegroundColor Green

# 2. Virtual Environment Setup
$VenvDir = Join-Path $ScriptDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvDir)) {
    Write-Host "[*] Creating virtual environment at .venv..." -ForegroundColor Yellow
    python -m venv .venv
}
Write-Host "[+] Virtual environment ready." -ForegroundColor Green

# 3. Install Dependencies
Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -e . --quiet
& $VenvPython -c "import nltk; nltk.download('vader_lexicon', quiet=True)"
Write-Host "[+] Core dependencies and VADER lexicon installed." -ForegroundColor Green

# 4. Initialize Database
Write-Host "[*] Initializing SQLite WAL database & ERP seeds..." -ForegroundColor Yellow
& $VenvPython database\init_db.py

# 5. Train Model Bundle
Write-Host "[*] Training Department Classifier & building model bundle..." -ForegroundColor Yellow
& $VenvPython models\train_model.py

# 6. Verification
if (-not $SkipTests) {
    Write-Host "[*] Executing automated verification suite..." -ForegroundColor Yellow
    & $VenvPython -m unittest discover -s tests
}

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT COMPLETE! Engine is ready for production use." -ForegroundColor Green
Write-Host "   Run 1M Simulation:  & .venv\Scripts\python.exe scripts\simulate_1m_live_operations.py" -ForegroundColor Gray
Write-Host "==========================================================================" -ForegroundColor Cyan

