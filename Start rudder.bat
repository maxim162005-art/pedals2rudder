@echo off
chcp 65001 >nul
cd /d "%~dp0"
title pedals2rudder
python rudder.py
echo.
pause
