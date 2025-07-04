# Manifest Alert System V2

**Warehouse-grade PyQt6 desktop application for shipping manifest alerts with modern SpaceX-style UI.**

## 🚀 Quick Installation

### For End Users (Warehouse Staff)

**Option 1: Bootstrap Installer (Recommended for Google Drive sharing)**
1. Download: [BOOTSTRAP_INSTALL.bat](https://raw.githubusercontent.com/e10120323/manifest_alerts/main/BOOTSTRAP_INSTALL.bat)
2. Run from anywhere (USB, Google Drive, Downloads folder)
3. Automatically installs to `C:\ManifestAlerts`
4. Use desktop shortcut to launch

**Option 2: Manual Download & Install**
1. Download: [INSTALL.bat](https://raw.githubusercontent.com/e10120323/manifest_alerts/main/INSTALL.bat)
2. Create empty folder (e.g. `C:\ManifestAlerts`)
3. Put `INSTALL.bat` in the empty folder
4. Double-click `INSTALL.bat`
5. Use desktop shortcut to launch

**Option 3: Command Line Install**
```cmd
mkdir C:\ManifestAlerts
cd C:\ManifestAlerts
curl -o INSTALL.bat https://raw.githubusercontent.com/e10120323/manifest_alerts/main/INSTALL.bat
INSTALL.bat
```

### For IT Deployment

**Prerequisites:**
- Windows 7+ with Command Prompt
- Python 3.8+ installed and in PATH
- Git for Windows (for automatic updates)
- Internet connection for initial setup

**Installation:**
- Use `INSTALL.bat` - handles everything automatically
- Creates virtual environment for dependency isolation
- Installs professional Windows shortcuts (Desktop + Start Menu)
- Future updates: run `INSTALL.bat` again in same directory

## 🔄 Updates

To update an existing installation:
1. Navigate to installation folder
2. Double-click `INSTALL.bat` (or run in Command Prompt)
3. Installer detects existing installation and updates automatically

## 🎯 Features

- **Modern UI**: SpaceX-style mission control interface with card-based layout
- **Real-time Sync**: Multi-PC acknowledgment system via shared data folders
- **TV Optimized**: Large fonts and high contrast for warehouse displays
- **Professional Integration**: Windows shortcuts and taskbar integration

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

- **PyQt6**: Modern Qt6 framework with card-based UI
- **JSON Storage**: Simple file-based configuration and acknowledgments
- **Git Updates**: Automatic version management via GitHub
- **Virtual Environment**: Isolated dependencies for reliability

---

**Support**: See `USER_INSTRUCTIONS.md` for configuration help
