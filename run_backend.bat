@echo off
cd /d "%~dp0"
echo ======================================================================
echo   Starting Smart City Backend Server (FastAPI on Port 8000)
echo   Accessible at: http://127.0.0.1:8000 and http://localhost:8000
echo   Swagger Docs: http://127.0.0.1:8000/docs
echo ======================================================================
set PYTHONPATH=%~dp0
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
