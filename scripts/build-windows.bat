@echo off
REM Build Windows executable for ANPR backend using PyInstaller.
REM Run this script from the repository root: scripts\build-windows.bat

setlocal

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "BACKEND_DIR=%REPO_ROOT%\backend"

echo === ANPR Backend Windows Build ===
echo Backend dir: %BACKEND_DIR%

cd /d "%BACKEND_DIR%"

REM Install PyInstaller if not present
pip show pyinstaller >nul 2>&1 || pip install pyinstaller

REM Build single-file executable
pyinstaller ^
    --onefile ^
    --name anpr-backend ^
    --add-data "alembic;alembic" ^
    --add-data "alembic.ini;." ^
    --hidden-import aiosqlite ^
    --hidden-import asyncpg ^
    --hidden-import passlib.handlers.bcrypt ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.loops ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import uvicorn.protocols ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed. Check output above.
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Build complete: %BACKEND_DIR%\dist\anpr-backend.exe
