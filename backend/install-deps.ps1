# Install backend dependencies and Playwright Chromium
# Run from backend folder. Uses Python 3.14 at default location if not on PATH.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Prefer Python on PATH; fallback to Python 3.14 in Local\Programs\Python
$py = $null
try {
    $v = & python -c "print(1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = "python" }
} catch {}
if (-not $py) {
    $py314 = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe"
    if (Test-Path $py314) { $py = $py314; Write-Host "Using: $py314" -ForegroundColor Yellow }
}
if (-not $py) {
    Write-Host "Python not found. Install from https://www.python.org/downloads/ and add to PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Installing Python packages from requirements.txt..." -ForegroundColor Cyan
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed." -ForegroundColor Red
    exit 1
}

Write-Host "Installing Playwright Chromium browser..." -ForegroundColor Cyan
& $py -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host "playwright install failed." -ForegroundColor Red
    exit 1
}

Write-Host "Done. Backend dependencies and Playwright Chromium are ready." -ForegroundColor Green
