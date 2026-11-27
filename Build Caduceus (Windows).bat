@echo off
setlocal
title Caduceus E-M1 II firmware builder
cd /d "%~dp0" || exit /b 1
set CADUCEUS_LAUNCHER=1
echo Caduceus - E-M1 II firmware builder
echo.
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul
if not errorlevel 1 goto use_python
echo Python 3.10 or newer is needed. Get it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH" during install), then double-click this file again.
start "" https://www.python.org/downloads/
set "status=1"
goto close
:use_py
py -3 -u caduceus.py --camera em1mk2 %*
goto done
:use_python
python -u caduceus.py --camera em1mk2 %*
:done
set "status=%errorlevel%"
:close
echo.
pause
exit /b %status%
