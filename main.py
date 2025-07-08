import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from alert_display import AlertDisplay
import os

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
    window = AlertDisplay()
    window.setWindowState(window.windowState() | Qt.WindowMaximized)
    window.show()

    sys.exit(app.exec_())