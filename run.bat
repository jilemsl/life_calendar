@echo off
title Life Calendar

echo.
echo  Life Calendar
echo  -------------
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed or not in PATH.
    echo  Download it from https://python.org
    echo.
    pause
    exit /b 1
)

:: Install / update dependencies silently
echo  Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  ERROR: could not install dependencies.
    pause
    exit /b 1
)

:: Create data directory if it was not included in the repo
if not exist data mkdir data

echo  Done. Opening the app...
echo  (browser will open at http://localhost:8501)
echo.

streamlit run app.py
pause
