@echo off
REM Start ANPR backend and frontend on Windows.
REM Expects:
REM   backend\dist\anpr-backend.exe   (built via build-windows.bat)
REM   frontend\build\index.js         (built via: cd frontend && npm run build)
REM
REM Run this script from the repository root: scripts\start.bat
REM For auto-start on boot, register this script in Windows Task Scheduler
REM (see docs\DEPLOYMENT.md for step-by-step instructions).

setlocal

set "REPO_ROOT=%~dp0.."

REM ---- Backend -----------------------------------------------------------
set "BACKEND_EXE=%REPO_ROOT%\backend\dist\anpr-backend.exe"
if not exist "%BACKEND_EXE%" (
    echo [ERROR] Backend executable not found: %BACKEND_EXE%
    echo Run scripts\build-windows.bat first.
    pause
    exit /b 1
)

echo Starting ANPR backend on port 8000 ...
cmd /k start "ANPR Backend" /d "%REPO_ROOT%\backend" "%BACKEND_EXE%"

REM ---- Frontend ----------------------------------------------------------
set "FRONTEND_JS=%REPO_ROOT%\frontend\build\index.js"
if not exist "%FRONTEND_JS%" (
    echo [ERROR] Frontend build not found: %FRONTEND_JS%
    echo Run: cd frontend ^&^& npm run build
    pause
    exit /b 1
)

echo Starting ANPR frontend on port 80 ...
cmd /k start "ANPR Frontend" /d "%REPO_ROOT%\frontend" ^
    cmd /c "set HOST=0.0.0.0 && set PORT=80 && node build\index.js"

echo.
echo Both services started in separate windows.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:80
