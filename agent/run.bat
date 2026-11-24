@echo off
:: Launch the Time Tracker desktop agent.
cd /d "%~dp0"

if not exist ".venv" (
    echo Virtual environment not found. Run install.bat first.
    pause & exit /b 1
)

if not exist "agent.env" (
    echo agent.env not found.
    echo Copy agent.env.example to agent.env and edit SERVER_URL and CONTRACT_ID.
    pause & exit /b 1
)

call .venv\Scripts\activate.bat
python main.py %*
