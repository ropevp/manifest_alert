import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from alert_display import AlertDisplay
import os

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = AlertDisplay()
    window.setWindowState(window.windowState() | Qt.WindowMaximized)
    window.show()

    sys.exit(app.exec_())