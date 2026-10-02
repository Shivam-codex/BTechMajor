@echo off
echo ======================================================================
echo   Starting Smart City Backend Server (FastAPI on Port 8000)
echo ======================================================================
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
