# Desktop Agent — Setup & Development

## Quick start (recommended)

**Windows:**
```bat
install.bat            :: creates .venv and installs dependencies
copy agent.env.example agent.env
rem  Edit agent.env: SERVER_URL, CONTRACT_ID
run.bat
```

**macOS / Linux:**
```bash
./install.sh
cp agent.env.example agent.env
# Edit agent.env: SERVER_URL, CONTRACT_ID
./run.sh
```

A **Login dialog** appears on first run when `ACCESS_TOKEN` is empty.  
Enter your dashboard email and password — the token is saved to `agent.env` automatically.

## Finding your CONTRACT_ID

Open the dashboard in your browser, navigate to a contract, and copy the UUID from the page URL:
```
http://your-server/dashboard/contracts/<CONTRACT_ID>
```

## Requirements
- Python 3.11+
- Windows 10/11 (primary); macOS 13+; Ubuntu 22.04+ (X11)

## Manual install (without the scripts)

```bash
pip install -r requirements.txt
cp agent.env.example agent.env   # edit with your settings
python main.py
```

## Platform notes

**macOS:** grant Screen Recording and Accessibility permissions when prompted  
**Linux:** works best under X11; Wayland does not support global keyboard/mouse hooks (activity tracking falls back gracefully); install `xdotool` for blocklist foreground-window detection

## Build a Windows executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name TimeTrackerAgent main.py
# Output: dist/TimeTrackerAgent.exe
```

**Code signing (Windows Authenticode):**
```bat
signtool sign /fd sha256 /tr http://timestamp.digicert.com /td sha256 ^
  /f your-cert.pfx /p your-password dist\TimeTrackerAgent.exe
```

