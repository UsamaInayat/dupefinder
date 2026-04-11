# DupeFinder backend — listen on all interfaces so phones on WiFi/hotspot can reach the API.
# Run from repo root:  powershell -File backend/start_lan.ps1
# Or from backend:     cd backend; .\start_lan.ps1
#
# If the phone still cannot connect:
#   1. On the PC, run: ipconfig  and add your current IPv4 to mobile/lib/services/api_service.dart _candidateIPs
#   2. Windows Firewall: allow inbound TCP 8000 (run PowerShell as Admin):
#        New-NetFirewallRule -DisplayName "DupeFinder API 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[DupeFinder] Starting API on 0.0.0.0:8000 (LAN + localhost)..." -ForegroundColor Cyan
Write-Host "[DupeFinder] Health: http://127.0.0.1:8000/health" -ForegroundColor Gray

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
