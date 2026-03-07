# Run backend from backend folder so 'app' module is found
Set-Location $PSScriptRoot
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
