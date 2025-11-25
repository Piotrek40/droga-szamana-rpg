@echo off
chcp 65001 > nul
title Droga Szamana - Testy
cd /d "%~dp0"
echo ========================================
echo    DROGA SZAMANA RPG - Testy
echo ========================================
echo.
echo Uruchamianie testow...
echo.
set PYTHONIOENCODING=utf-8
python tests/test_all.py
echo.
pause
