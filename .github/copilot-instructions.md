# Manifest Alert System - AI Coding Agent Instructions

## 🏗️ Architecture Overview

This is a **warehouse-grade PyQt5 desktop application** for shipping manifest alerts with real-time synchronization across multiple PCs. The system follows a modular architecture with clear separation of concerns:

- **`main.py`**: Entry point with Windows taskbar integration (`SetCurrentProcessExplicitAppUserModelID`)
- **`alert_display.py`**: Core UI widget (1400+ lines) with system tray, audio, and window management
- **`data_manager.py`**: JSON file operations for `config.json` and `acknowledgments.json`
- **`scheduler.py`**: Time-based manifest status calculation (Active/Missed/Pending)
- **`settings_manager.py`**: Configurable data storage paths with validation UI
- **`sound_handler.py`**: Simple audio alert wrapper around PyQt5.QtMultimedia

## 🔧 Critical Development Patterns

### Virtual Environment Architecture
- **Always use `.venv\Scripts\python.exe`** in batch files - system Python causes PyQt5 import failures
- The `INSTALL.bat` handles both fresh installs and updates via Git detection
- All launchers (`launch_*.bat`) must use virtual environment Python paths

### Window Management Anti-Patterns
**⚠️ NEVER call `show()` after `setWindowFlag()` operations** - this causes unwanted minimization:
```python
# ❌ WRONG - causes window to minimize
self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
self.show()  # This breaks window state

# ✅ CORRECT - flag changes without show()
self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
```

### Alert Priority Logic
The system has **strict priority ordering**: `Active > Missed > Open`
- Active alerts force window maximized + always-on-top
- Snooze functionality temporarily disables always-on-top behavior
- Check `has_unsnooze_alerts()` before forcing window prominence

### Data Storage Pattern
Settings use **dual-location strategy**:
- `app_data/settings.json`: App settings (persistent location)
- Configurable path (via settings): `config.json` and `acknowledgments.json` for multi-PC sync
- Always check write permissions with `validate_path()` before using new storage locations

## 🚀 Essential Development Commands

### Local Development
```bash
# Use virtual environment Python (critical!)
.venv\Scripts\python.exe main.py

# Install dependencies in venv
.venv\Scripts\pip install -r requirements.txt

# Create shortcuts (Windows integration)
.venv\Scripts\python.exe install_shortcuts.py
```

### Testing Multi-PC Sync
```bash
# Test shared storage (Google Drive, network drives)
# Edit settings.json to point data_folder to shared location
# Run multiple instances from different folders pointing to same data path
```

### Debugging Audio Issues
```bash
# Voice synthesis testing
.venv\Scripts\python.exe -c "import pyttsx3; engine = pyttsx3.init(); engine.say('test'); engine.runAndWait()"

# Test WAV file playback
.venv\Scripts\python.exe -c "from PyQt5.QtMultimedia import QSound; QSound.play('resources/alert.wav')"
```

## 🎯 Component Integration Points

### System Tray ↔ Main Window
- Tray menu dynamically enables/disables based on alert status
- Monitor switching creates dynamic submenus based on `QApplication.screens()`
- All main window functions accessible via tray context menu

### Snooze System ↔ Audio/Visual
- Snooze affects **both** WAV alerts (`sound_handler.py`) and TTS announcements (`pyttsx3`)
- Window management respects snooze state - no forced maximization when snoozed
- Snooze timers automatically re-enable alerts when expired

### Settings ↔ Multi-PC Sync
- Settings validation occurs in real-time with visual indicators (green/orange/red)
- Path changes immediately affect `get_config_path()` and `get_acknowledgments_path()`
- Google Drive Desktop compatibility requires polling file timestamps for external changes

## 📝 Code Conventions Specific to This Project

### Error Handling Pattern
```python
# Always backup before overwriting JSON files
try:
    backup_path = config_path + ".bak"
    shutil.copyfile(config_path, backup_path)
except Exception:
    pass  # Silent backup failure acceptable
```

### Time Display Formatting
- Use natural language for TTS: `"eleven thirty"` not `"11:30"`
- Digital display uses 12-hour format with `strftime('%I:%M %p')`
- Manifest times stored as `"HH:MM"` 24-hour format internally

### PyQt5 Resource Loading
```python
# Always check resource existence before loading
icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))
```

## 🔄 Deployment Architecture

- **Production**: Users run `INSTALL.bat` which clones from GitHub and sets up virtual environment
- **Updates**: Same `INSTALL.bat` detects existing Git repo and pulls latest changes
- **Windows Integration**: Desktop shortcuts point to `launch_manifest_alerts_silent.bat`
- **Multi-PC**: Shared data folders enable real-time acknowledgment sync across warehouse PCs

## 📚 Key Files for Understanding Context

- **`tickets.md`**: Complete feature development history and architectural decisions
- **`alert_display.py`**: Main UI component with all interaction patterns
- **`INSTALL.bat`**: Deployment strategy and dependency management
- **`settings_manager.py`**: Configurable storage and validation patterns
