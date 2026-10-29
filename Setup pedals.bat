@echo off
chcp 65001 >nul
cd /d "%~dp0"
title pedals2rudder - setup
python rudder.py --setup
echo.
pause
