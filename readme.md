# Manifest Alert System V2

**Desktop application for shipping manifest alerts with modern dark theme UI.**

## 🚀 Quick Installation

### For End Users (Warehouse Staff)

**Simple 3-Command Installation:**
```cmd
git clone https://github.com/ropevp/manifest_alert.git C:\ManifestAlerts
cd C:\ManifestAlerts
INSTALL.bat
```

**What this does:**
1. Downloads the complete system to `C:\ManifestAlerts`
2. Sets up virtual environment and dependencies
3. Creates desktop and Start Menu shortcuts
4. Ready to use!

### For IT Deployment

**Prerequisites:**
- Windows 7+ with Command Prompt
- Python 3.8+ installed and in PATH
- Git for Windows (for automatic updates)
- Internet connection for initial setup

**Installation:**
- Use `INSTALL.bat` - handles setup automatically
- Creates virtual environment for dependency isolation
- Installs Windows shortcuts (Desktop + Start Menu)
- Future updates: run `INSTALL.bat` again in same directory

## 🔄 Updates

To update an existing installation:
```cmd
cd C:\ManifestAlerts
INSTALL.bat
```
The installer detects existing installations and updates automatically.

## 🎯 Features

- **Modern UI**: Dark theme interface with card-based layout
- **Multi-PC Sync**: Shared data folders for acknowledgment synchronization
- **Large Display**: Readable fonts and high contrast for warehouse displays
- **Windows Integration**: Desktop shortcuts and taskbar integration

## 📂 File Structure

After installation:
- `launch_manifest_alerts.bat` - Start with console window
- `launch_manifest_alerts_silent.bat` - Start without console
- `USER_INSTRUCTIONS.md` - Configuration guide
- `.venv\` - Isolated Python environment
- `app_data\` - Application settings
- `data\` or custom path - Manifest data and acknowledgments

## ⚙️ Configuration

See `USER_INSTRUCTIONS.md` for:
- Data folder configuration
- Multi-PC synchronization setup
- Manifest timing configuration

## 🛠️ Development

**Requirements:**
- Python 3.8+
- PyQt6 6.8.0+
- Git

**Setup:**
```cmd
git clone https://github.com/e10120323/manifest_alerts.git
cd manifest_alerts
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

## 📋 Architecture

- **PyQt6**: Qt6 framework with card-based UI
- **JSON Storage**: File-based configuration and acknowledgments
- **Git Updates**: Version management via GitHub
- **Virtual Environment**: Isolated dependencies

---

**Support**: See `USER_INSTRUCTIONS.md` for configuration help
