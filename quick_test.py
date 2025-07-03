#!/usr/bin/env python3
"""Quick test to verify the nuclear fix works"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from alert_display import AlertDisplay
import os

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    print("Creating window...")
    window = AlertDisplay()
    
    print("Setting to maximized...")
    window.setWindowState(Qt.WindowMaximized)
    window.show()
    
    print("Window state:", window.windowState())
    print("Is maximized:", bool(window.windowState() & Qt.WindowMaximized))
    print("Is fullscreen:", bool(window.windowState() & Qt.WindowFullScreen))
    
    print("\nTesting populate_list in maximized mode...")
    window.populate_list()
    print("After populate_list - Window state:", window.windowState())
    
    print("\nSetting to fullscreen...")
    window.setWindowState(Qt.WindowFullScreen)
    print("Fullscreen state:", window.windowState())
    
    print("\nTesting populate_list in fullscreen mode...")
    window.populate_list()
    print("After populate_list - Window state:", window.windowState())
    
    print("\nTest complete! Press Ctrl+Shift+Q to exit")
    sys.exit(app.exec_())
