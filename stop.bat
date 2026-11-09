@echo off
title Stop Enterprise RAG Assistant
echo =====================================================================
echo  Stopping Enterprise AI Document Assistant Servers...
echo =====================================================================

echo Stopping backend server (Port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Stopping frontend server (Port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo All services on port 8000 and 5173 have been stopped successfully!
echo =====================================================================
pause
