@echo off
chcp 65001 > nul
cd /d "%~dp0"
uv run python tools/build_manager.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Hubo un error en la ejecución.
    pause
)
