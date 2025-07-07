# Manifest Alert System V2 - AI Coding Agent Instructions

## 🏗️ Architecture Overview

This is a **warehouse-grade PyQt6 desktop application** for shipping manifest alerts with modern SpaceX-style UI and real-time synchronization across multiple PCs. The system follows a modular architecture with clean separation of concerns:

- **`main.py`**: Entry point with Windows taskbar integration (`SetCurrentProcessExplicitAppUserModelID`)
- **`alert_display.py`**: Modern card-based UI (400 lines) with SpaceX-style mission control design
- **`data_manager.py`**: JSON file operations for `config.json` and `acknowledgments.json`
- **`scheduler.py`**: Time-based manifest status calculation (Active/Missed/Pending)
- **`settings_manager.py`**: Configurable data storage paths with validation UI
- **`sound_handler.py`**: Audio alert wrapper (currently unused in V2)

## 🎨 V2 Modern UI Design Principles

### Dark Theme - Mission Control Interface
- **Dark theme**: Deep space background (#0f0f23) with bright accent colors
- **Card-based layout**: 320x200px status cards in responsive 3-column grid
- **Large typography**: TV-optimized fonts (36pt title, 32pt clock, 28pt headers)
- **Professional aesthetics**: Gradients, smooth borders, mission control styling

### Color Coding System
```python
# Status color palette
ACTIVE = "#ff4757"      # Bright red for urgent alerts
MISSED = "#c44569"      # Dark red for missed manifests  
PENDING = "#3742fa"     # Blue for upcoming manifests
ACKNOWLEDGED = "#2ed573" # Green for completed items
```

### Card Layout Architecture
```python
class StatusCard(QFrame):
    # Fixed 320x200px cards with:
    # - Large time header (36pt)
    # - Status indicator (20pt) 
    # - Manifest details (18pt)
    # - Gradient status bar at bottom
```

## 🔧 Critical V2 Development Patterns

### Virtual Environment Architecture
- **Always use `.venv\Scripts\python.exe`** in batch files - system Python causes import failures
- **PyQt6 framework**: Modern Qt6 APIs with better performance than PyQt5
- The `INSTALL.bat` handles both fresh installs and updates via Git detection
- All launchers (`launch_*.bat`) must use virtual environment Python paths

### Modern UI Update Patterns
**✅ SAFE: Card-based updates without window disruption**
```python
# V2 approach - update data, refresh cards
def populate_data(self):
    # Clear existing cards cleanly
    for card in self.status_cards.values():
        card.setParent(None)
    self.status_cards.clear()
    
    # Recreate cards with new data
    # NO tree operations, NO window state issues
```

**⚠️ OBSOLETE: Old tree widget anti-patterns**
The complex window state preservation code from V1 is **no longer needed** in V2:
- No tree widgets that cause window movement
- No expand/collapse operations that disrupt state
- Clean card-based design eliminates window state issues

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

# Install PyQt6 dependencies
.venv\Scripts\pip install PyQt6

# Create shortcuts (Windows integration)
.venv\Scripts\python.exe install_shortcuts.py
```

### V2 UI Development
```bash
# Test modern UI in different resolutions
# UI scales well from 1200x800 minimum to 4K displays
# Cards auto-wrap in responsive 3-column grid

# Color testing - status cards update dynamically
# Test with different manifest statuses to see color changes
```

## 🎯 V2 Component Architecture

### Modern Card System
- **StatusCard class**: Self-contained widgets with status-based styling
- **Grid layout**: Responsive 3-column arrangement with auto-wrapping
- **Dynamic updates**: Cards recreated on data refresh, no state issues
- **TV optimized**: Large fonts and high contrast for warehouse displays

### Simplified Data Flow
```python
# V2 data flow - clean and simple
populate_data() → create cards → update summary bar
# No complex tree operations, no window state preservation needed
```

### Acknowledgment System (Stubbed)
- Current V2 shows placeholder dialog
- Ready for incremental acknowledgment feature development
- Will integrate with existing logger module when implemented

## 📝 V2 Code Conventions

### PyQt6 Resource Loading
```python
# Always check resource existence before loading
icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
if os.path.exists(icon_path):
    self.setWindowIcon(QIcon(icon_path))
```

### Modern Styling Approach
```python
# Use f-strings for dynamic CSS
self.setStyleSheet(f"""
    StatusCard {{
        background-color: {bg_color};
        border: 2px solid {border_color};
        border-radius: 12px;
    }}
""")
```

### Error Handling Pattern
```python
# Always backup before overwriting JSON files
try:
    backup_path = config_path + ".bak"
    shutil.copyfile(config_path, backup_path)
except Exception:
    pass  # Silent backup failure acceptable
```

## 🔄 Deployment Architecture

- **Production**: Users run `INSTALL.bat` which clones from GitHub and sets up virtual environment
- **Updates**: Same `INSTALL.bat` detects existing Git repo and pulls latest changes  
- **Windows Integration**: Desktop shortcuts point to `launch_manifest_alerts_silent.bat`
- **Multi-PC**: Shared data folders enable real-time acknowledgment sync across warehouse PCs

## 📚 Key Files for V2 Context

- **`v2.md`**: V2 rebuild log and development history
- **`alert_display.py`**: Modern card-based UI (400 lines vs 1400+ in V1)
- **`main.py`**: PyQt6 entry point with Windows integration
- **`requirements.txt`**: Updated for PyQt6 dependencies
- **`settings_manager.py`**: Configurable storage and validation patterns

## 🚫 Obsolete V1 Patterns (Do Not Use)

- ~~Tree widget operations and expand/collapse anti-patterns~~
- ~~Complex window state preservation code~~
- ~~PyQt5 imports and old Qt APIs~~
- ~~Snooze system complexity (removed in V2)~~
- ~~Audio/TTS integration (simplified in V2)~~
- ~~1400+ line monolithic UI class~~
