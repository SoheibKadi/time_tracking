# Desktop Agent — Development Setup

## Requirements
- Python 3.11+
- Windows 10/11 (primary); macOS and Linux supported with caveats

## Install dependencies
```
pip install -r requirements.txt
```

> **Windows note:** `pynput` requires no extra setup on Windows.
> **macOS note:** Grant Accessibility + Screen Recording permissions when prompted.
> **Linux note:** Works best under X11; Wayland may require `pynput` Wayland backend.

## Configuration
1. Copy `agent.env.example` to `agent.env`
2. Set `SERVER_URL` to your backend
3. Run the agent once — a **Login** dialog will appear automatically if `ACCESS_TOKEN` is empty

## Run
```
python main.py
```

## Build a Windows executable
```
pip install pyinstaller
pyinstaller --onefile --windowed --name TimeTrackerAgent main.py
```
The `.exe` will be in `dist/`.

## Signing (Windows Authenticode)
```
signtool sign /fd sha256 /tr http://timestamp.digicert.com /td sha256 ^
  /f your-cert.pfx /p your-password dist\TimeTrackerAgent.exe
```
