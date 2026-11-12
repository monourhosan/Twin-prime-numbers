@echo off
setlocal
cd /d "%~dp0\.."

echo ======================================================================
echo   Phase 4 ADRS-4 Laptop Search Launcher (i5-10210U + NVIDIA MX250)
echo ======================================================================

echo.
echo [1/2] Running hardware diagnostics and safety check...
python scripts\laptop_doctor.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Safety check failed. Aborting startup.
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Launching Phase 4 Search Campaign...
python -m src.phase4 search --config configs\laptop_i5_10210u_mx250.json %*
