@echo off
title Cognitive Digital Twin - Crime Hotspot Detection
echo ======================================================================
echo Starting Cognitive Digital Twin for Crime Hotspot Detection & Analysis
echo ======================================================================
echo.
echo Launching server on http://127.0.0.1:5000 ...
start "" "http://127.0.0.1:5000"
if exist "C:\Users\hanuc\anaconda3\python.exe" (
    "C:\Users\hanuc\anaconda3\python.exe" app.py
) else (
    python app.py
)
pause
