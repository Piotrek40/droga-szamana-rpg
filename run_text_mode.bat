@echo off
chcp 65001 > nul
title Droga Szamana RPG - Tryb Tekstowy
cd /d "%~dp0"
echo ========================================
echo    DROGA SZAMANA RPG - Tryb Tekstowy
echo ========================================
echo.
python main.py
if errorlevel 1 (
    echo.
    echo [BLAD] Gra nie uruchomila sie poprawnie.
    echo Sprawdz czy masz zainstalowany Python 3.8+
)
pause
