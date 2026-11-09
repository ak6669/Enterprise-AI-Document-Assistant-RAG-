@echo off
title Enterprise AI Document Assistant
echo =====================================================================
echo  Starting Enterprise AI Document Assistant (RAG)
echo =====================================================================

echo [1/3] Starting Backend API on http://localhost:8000...
start "RAG Backend Server" cmd /k "cd /d %~dp0 && .\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"

echo [2/3] Starting Frontend UI on http://localhost:5173...
start "RAG Frontend Server" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo [3/3] Opening application in default browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo Both servers are running!
echo Frontend: http://localhost:5173
echo Backend:  http://127.0.0.1:8000/docs
echo =====================================================================
pause
