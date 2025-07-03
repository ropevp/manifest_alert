import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from ui_display import AlertDisplay
import os

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application properties for better Windows integration
    app.setApplicationName("Manifest Alerts")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Warehouse Systems")
    
    # Set application icon for taskbar display
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'icon.ico')
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
    
    # Windows-specific: Set application ID to avoid Python grouping in taskbar
    try:
        import ctypes
        # Set a unique AppUserModelID for Windows taskbar grouping
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('WarehouseSystems.ManifestAlerts.1.0')
    except:
        pass  # Ignore if not on Windows or if ctypes fails
    
    # Allow application to quit when window is closed
    app.setQuitOnLastWindowClosed(True)
    window = AlertDisplay()
    window.setWindowState(window.windowState() | Qt.WindowState.WindowMaximized)
    window.show()

    sys.exit(app.exec())