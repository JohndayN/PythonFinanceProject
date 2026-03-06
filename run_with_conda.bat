@echo off
REM Run the Finance Application with Conda Environment
REM This script ensures the application runs on the conda base environment

echo Starting Finance Application with Conda Python...
echo.

REM Activate conda base environment and run the application
call C:\ProgramData\anaconda3\Scripts\activate.bat base
C:\ProgramData\anaconda3\python.exe run.py

pause
