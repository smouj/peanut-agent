# 🥜 PEANUT-AGENT — 1-command installer (Windows PowerShell)
# - Creates/uses .venv
# - Installs deps
# - Launches the Wizard

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

$py = $null
try {
  $py = (Get-Command python -ErrorAction Stop).Source
} catch {
  try {
    $py = (Get-Command python3 -ErrorAction Stop).Source
  } catch {
    Write-Host "❌ No encuentro Python. Instala Python 3.10+ y reintenta." -ForegroundColor Red
    exit 1
  }
}

& $py .\wizard.py
