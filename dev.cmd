@echo off
setlocal
title ProfitLens - Development launcher

:menu
echo.
echo ==============================
echo    ProfitLens Dev Launcher
echo ==============================
echo    1. Start servers
echo    2. Stop servers
echo    0. Exit launcher
echo.
choice /C 120 /N /M "Choose 1, 2 or 0: "
if errorlevel 3 goto end
if errorlevel 2 goto stop
if errorlevel 1 goto start
goto end

:start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev.ps1" -Action Start
goto menu

:stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev.ps1" -Action Stop
goto menu

:end
echo Closing launcher. Use option 2 first if you want to stop the servers.
exit /b 0
