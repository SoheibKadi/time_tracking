@echo off
:: Install the desktop agent dependencies into a local virtual environment.
cd /d "%~dp0"

echo Installing Time Tracker Agent...
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: python not found. Install Python 3.11+ from python.org and try again.
    pause & exit /b 1
)

python -m venv .venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause & exit /b 1
)

call .venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo.
echo Done! Agent installed in .venv\
echo.
echo Next steps:
echo   1. Copy agent.env.example to agent.env
echo   2. Edit agent.env  --  set SERVER_URL and CONTRACT_ID
echo   3. Run run.bat
echo.
pause
