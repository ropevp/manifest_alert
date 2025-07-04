import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from alert_display import AlertDisplay
import os
import json

def load_main_settings():
    """Load settings from the main settings.json file"""
    settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
    default_settings = {
        "username": "",
        "data_folder": "",
        "alarm_monitor": 0
    }
    
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            # Ensure all required keys exist
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            return settings
        except Exception as e:
            print(f"Error loading main settings: {e}")
            return default_settings
    return default_settings

def position_window_on_monitor(window, monitor_index):
    """Position window on the specified monitor and maximize it"""
    from PyQt6.QtGui import QGuiApplication
    screens = QGuiApplication.screens()
    
    if monitor_index < 0 or monitor_index >= len(screens):
        # Invalid monitor index, use primary screen
        monitor_index = 0
        print(f"Invalid monitor index, using primary monitor (0)")
    
    if len(screens) > monitor_index:
        target_screen = screens[monitor_index]
        screen_geometry = target_screen.geometry()
        
        # Move window to the target monitor first
        window.move(screen_geometry.center() - window.rect().center())
        window.show()
        
        # Then maximize it on that monitor
        window.setWindowState(Qt.WindowState.WindowMaximized)
        print(f"Positioned window on monitor {monitor_index}")
    else:
        # Fallback to primary monitor
        window.setWindowState(Qt.WindowState.WindowMaximized)
        print(f"Only {len(screens)} monitor(s) available, using primary")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application properties for better Windows integration
    app.setApplicationName("Manifest Alerts")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Warehouse Systems")
    
    # Set application icon for taskbar display
    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Windows-specific: Set application ID to avoid Python grouping in taskbar
    try:
        import ctypes
        # Set a unique AppUserModelID for Windows taskbar grouping
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('WarehouseSystems.ManifestAlerts.1.0')
    except:
        pass  # Ignore if not on Windows or if ctypes fails
    
    app.setQuitOnLastWindowClosed(False)
    
    # Load main settings to get preferred monitor
    settings = load_main_settings()
    preferred_monitor = settings.get('alarm_monitor', 0)
    
    # Create and position window
    window = AlertDisplay()
    position_window_on_monitor(window, preferred_monitor)

    sys.exit(app.exec())