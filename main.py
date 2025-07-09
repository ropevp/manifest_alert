import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from alert_display import AlertDisplay
import os

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlertDisplay()
    window.show()

    # System tray icon setup
    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
    tray_icon = QSystemTrayIcon(QIcon(icon_path) if os.path.exists(icon_path) else window.windowIcon(), parent=app)
    tray_icon.setToolTip("Manifest Alerts")

    # Tray menu
    menu = QMenu()
    show_action = QAction("Show/Hide Window")
    exit_action = QAction("Exit")
    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(exit_action)
    tray_icon.setContextMenu(menu)

    def toggle_window():
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.raise_()
            window.activateWindow()

    def exit_app():
        tray_icon.hide()
        app.quit()

    show_action.triggered.connect(toggle_window)
    exit_action.triggered.connect(exit_app)
    tray_icon.activated.connect(lambda reason: toggle_window() if reason == QSystemTrayIcon.Trigger else None)
    tray_icon.show()

    # Minimize to tray on close
    def closeEvent(event):
        event.ignore()
        window.hide()
    window.closeEvent = closeEvent

    sys.exit(app.exec_())
