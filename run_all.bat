@echo off
cd /d "%~dp0"
echo ======================================================================
echo   Launching Complete Smart City Complaint Management System
echo   Backend: http://127.0.0.1:8000
echo   Frontend: http://localhost:3000
echo   Docs: http://127.0.0.1:8000/docs
echo ======================================================================

start "SmartCity Backend (FastAPI)" cmd /k "%~dp0run_backend.bat"
timeout /t 3 /nobreak > nul
start "SmartCity Frontend (Next.js)" cmd /k "%~dp0run_frontend.bat"
timeout /t 2 /nobreak > nul

start http://localhost:3000
echo Servers started successfully!
pause
