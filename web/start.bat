@echo off
echo ============================================
echo  ICC Code Development Platform — Starting...
echo ============================================
echo.

pip install -r requirements.txt --quiet 2>nul

echo.
echo Server starting at http://localhost:8080
echo.
echo  Dashboard:  http://localhost:8080
echo  Portal:     http://localhost:8080/meeting/88/portal
echo.
echo Press Ctrl+C to stop.
echo ============================================
cd /d "%~dp0"
python -m uvicorn main:app --host 127.0.0.1 --port 8080 --reload
