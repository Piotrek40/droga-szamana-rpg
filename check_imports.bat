@echo off
chcp 65001 > nul
title Droga Szamana - Sprawdzanie importow
cd /d "%~dp0"
echo ========================================
echo    Sprawdzanie importow modulow
echo ========================================
echo.
set PYTHONIOENCODING=utf-8
python -c "from core import *; from npcs import *; from mechanics import *; from quests import *; from ui import *; from player import *; from persistence import *; print('OK - Wszystkie importy prawidlowe')"
if errorlevel 1 (
    echo.
    echo [BLAD] Niektore importy nie dzialaja!
)
echo.
pause
