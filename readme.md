# 🚨 Manifest Alert System V2

Professional warehouse alert system for shipping manifests with modern SpaceX-style UI and real-time synchronization across multiple PCs.

## 🚀 Installation (New Users)

### Prerequisites
1. **Install Python**: Download from [python.org](https://python.org) 
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
2. **Install Git**: Download from [git-scm.com](https://git-scm.com/download/win)

### One-Click Installation
1. **Create folder**: Make a new folder where you want the application (e.g., `C:\ManifestAlerts`)
2. **Download installer**: Save `INSTALL.bat` to that folder
3. **Run installer**: Double-click `INSTALL.bat` and follow prompts
4. **Launch app**: Use desktop shortcut or Start Menu

## 🔄 Updates (Existing Users)

**To update to the latest version:**
1. **Run same file**: Double-click `INSTALL.bat` in your application folder
2. **Automatic update**: The installer detects existing installation and updates it
3. **Settings preserved**: Your configuration and data are automatically backed up and restored

## 🎯 Daily Usage

**Launch the application:**
- Double-click desktop shortcut "Manifest Alert System"
- Or press Windows key and type "Manifest Alert"

**For troubleshooting:**
- Use `launch_diagnostic.bat` to see detailed status
- All issues and solutions are shown clearly

## 📁 What Gets Installed

```
YourFolder/
├── INSTALL.bat                      # One installer for everything
├── main.py                          # Application entry point (PyQt6)
├── alert_display.py                 # Modern card-based UI (PyQt6)
├── data_manager.py                  # JSON file operations
├── scheduler.py                     # Manifest status calculation
├── settings_manager.py              # Configurable data storage
├── .venv/                          # Virtual environment (automatic)
├── data/                           # Your settings
├── backup/                         # Backup files
├── resources/                      # Icons and sounds
└── Desktop Shortcut Created        # Easy access
```

## ✅ Features

- **🎨 Modern UI**: SpaceX-style mission control interface with dark theme
- **💳 Card-Based Display**: Clean 320x200px status cards in responsive grid layout
- **🔥 Ultra-Fast Sync**: Real-time acknowledgment updates across PCs
- **👤 User Tracking**: Custom names and accountability logging
- **🖥️ Multi-PC Support**: Share data via Google Drive or network folders
- **� TV-Optimized**: Large fonts (36pt headers) for warehouse displays
- **️ Multi-Monitor**: Direct monitor selection with intelligent switching
- **⚡ Professional UI**: Modern PyQt6 framework with Windows integration
- **🔄 Auto-Updates**: Simple update process preserves all settings
- **� Status Cards**: Color-coded manifest status (Active/Missed/Pending/Acknowledged)

## 🆕 V2 Architecture (2025)

### Modern Technology Stack
- **PyQt6 Framework**: Latest Qt6 APIs with improved performance
- **Card-Based UI**: Clean, responsive design replacing complex tree widgets
- **Simplified Codebase**: 400-line display module vs 1400+ lines in V1
- **Professional Theming**: Deep space background (#0f0f23) with bright accents

### Enhanced UI Components
- **Status Cards**: 320x200px cards with gradient status bars
- **Large Typography**: 36pt title, 32pt clock, 28pt headers for TV displays
- **Color System**: Bright red (#ff4757) active, blue (#3742fa) pending, green (#2ed573) acknowledged
- **Responsive Layout**: 3-column grid with auto-wrapping for different screen sizes

### Improved Performance
- **No Window State Issues**: Eliminated complex tree widget anti-patterns
- **Clean Updates**: Card recreation without window disruption
- **Resource Efficient**: Modern Qt6 APIs with better memory management
- **Stable Operation**: No expand/collapse operations that cause state issues

## 🛠️ Technical Architecture

### Core Modules
- **`main.py`**: PyQt6 entry point with Windows taskbar integration
- **`alert_display.py`**: Modern card-based UI with SpaceX styling (400 lines)
- **`data_manager.py`**: JSON operations for config.json and acknowledgments.json
- **`scheduler.py`**: Time-based manifest status calculation
- **`settings_manager.py`**: Configurable storage paths with validation
- **`sound_handler.py`**: Audio alert wrapper

### Data Storage Strategy
- **Dual-location**: App settings in `app_data/settings.json`
- **Configurable sync**: User-defined path for `config.json` and `acknowledgments.json`
- **Multi-PC sync**: Shared network or cloud folders for real-time updates
- **Permission validation**: Automatic write-access testing before storage

## 🆘 Troubleshooting

### "Python is not recognized"

- Reinstall Python from python.org
- Check "Add Python to PATH" during installation

### "Git is not recognized"

- Install Git from git-scm.com
- Restart Command Prompt after installation

### Application won't start

- Run `launch_diagnostic.bat` for detailed status
- Follow the on-screen suggestions

### PyQt6 Import Errors

- Virtual environment automatically installs PyQt6==6.8.0
- Run `INSTALL.bat` again to rebuild dependencies

### Need help?

- All error messages include clear solutions
- Run `INSTALL.bat` again to fix most issues
- Check `backup/` folder for previous versions if needed

---

**🏭 Warehouse-grade PyQt6 desktop application with modern SpaceX-style mission control UI, ready for professional deployment with zero-maintenance operation.**