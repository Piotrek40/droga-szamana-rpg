@echo off
chcp 65001 > nul
title Droga Szamana RPG
cd /d "%~dp0"
echo ========================================
echo    DROGA SZAMANA RPG - Launcher
echo ========================================
echo.
python integrated_gui.py
if errorlevel 1 (
    echo.
    echo [BLAD] Gra nie uruchomila sie poprawnie.
    echo Sprawdz czy masz zainstalowany Python 3.8+
    pause
)
