import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from alert_display import AlertDisplay

if __name__ == "__main__":
    # Hide console window in production (when run with pythonw.exe)
    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    except:
        pass  # Ignore if not on Windows or if console is already hidden
    
    # Suppress Qt debug output for cleaner production experience
    os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.ffmpeg.debug=false'
    
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
    window.setWindowState(window.windowState() | Qt.WindowState.WindowMaximized)
    window.show()

    sys.exit(app.exec())