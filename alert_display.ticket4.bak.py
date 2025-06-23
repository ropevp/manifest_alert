import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from scheduler import get_manifest_status
from data_manager import load_config
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QStyle
import os, shutil

# Backup current file for Ticket 4 refactor
backup_path = os.path.join(os.path.dirname(__file__), 'alert_display.ticket4.bak.py')
if not os.path.exists(backup_path):
    shutil.copyfile(__file__, backup_path)

class AlertDisplay(QWidget):
    def __init__(self):
        super().__init__()
        # Start with normal stacking (not always-on-top)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowTitle("Manifest Alerts")
        self.resize(int(350 * 1.25), int(250 * 1.5 * 1.25))  # height increased by 25%
        # Set window icon
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        # Clock and countdown label
        from PyQt5.QtGui import QFont
        # Clock label with professional font
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignCenter)
        digital_font = QFont('Segoe UI', 64, QFont.Bold)
        self.clock_label.setFont(digital_font)
        self.clock_label.setStyleSheet('color: yellow; background-color: black; padding: 8px; border-radius: 8px;')
        layout.addWidget(self.clock_label)
        # Countdown label with matching font
        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignCenter)
        countdown_font = QFont('Segoe UI', 36, QFont.Bold)
        self.countdown_label.setFont(countdown_font)
        self.countdown_label.setStyleSheet('color: #2196F3;')
        layout.addWidget(self.countdown_label)
        # Link to Shipping Management Console
        link_label = QLabel()
        link_label.setText('<a href="https://my.shipping.cimpress.io/manifests">Shipping Management Console - Manifests</a>')
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setTextFormat(Qt.RichText)
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)
        
        # Manifest list as collapsible tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setFont(QFont('Segoe UI', 24))
        self.tree_widget.setHeaderHidden(True)
        layout.addWidget(QLabel("Today's Manifests:"))
        layout.addWidget(self.tree_widget)

        # Add acknowledge, collapse/expand and reload config buttons
        btn_layout = QHBoxLayout()
        self.ack_btn = QPushButton("Acknowledge")
        self.ack_btn.clicked.connect(self.acknowledge_selected)
        btn_layout.addWidget(self.ack_btn)
        self.reload_btn = QPushButton("Reload Config")
        self.reload_btn.clicked.connect(self.reload_config)
        btn_layout.addWidget(self.reload_btn)
        # Collapse/Expand All buttons
        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.clicked.connect(self.collapse_all)
        btn_layout.addWidget(self.collapse_btn)
        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.clicked.connect(self.expand_all)
        btn_layout.addWidget(self.expand_btn)
        # Add Snooze button
        self.snooze_btn = QPushButton("Snooze")
        self.snooze_btn.clicked.connect(self.snooze_alerts)
        # Hide snooze until there's an active alert
        self.snooze_btn.hide()
        btn_layout.addWidget(self.snooze_btn)
        # Add Monitor Switch button next to controls
        self.monitor_btn = QPushButton("⇔ Switch Monitor")
        self.monitor_btn.setToolTip("Switch Monitor")
        self.monitor_btn.clicked.connect(self.switch_monitor)
        btn_layout.addWidget(self.monitor_btn)
        # Add Fullscreen toggle button (hidden until active)
        self.full_btn = QPushButton()
        self.full_btn.setToolTip("Toggle Fullscreen/Maximize")
        # Use standard maximize icon
        self.full_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.full_btn.setIconSize(self.full_btn.sizeHint())
        self.full_btn.clicked.connect(self.toggle_fullscreen)
        self.full_btn.hide()
        btn_layout.addWidget(self.full_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Timers and sound (start only once)
        # Snooze tracker
        self.snooze_until = None
        self.flashing_items = []
        self.flashing_on = True
        self.sound = None
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.toggle_flashing)
        self.flash_timer.start(500)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock_and_countdown)
        self.clock_timer.start(1000)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_list)
        self.refresh_timer.start(30000)
        self.current_date = datetime.now().date()
        self.populate_list()
        self.update_clock_and_countdown()
    def reload_config(self):
        self.populate_list()
        self.update_clock_and_countdown()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Config Reloaded", "Configuration reloaded from disk.")
    def update_clock_and_countdown(self):
        now = datetime.now()
        # Skip updates (maximize/hide logic) during snooze period
        if self.snooze_until and now < self.snooze_until:
            return
        # Day-change logic
        if now.date() != self.current_date:
            self.current_date = now.date()
            self.populate_list()
        self.clock_label.setText(now.strftime('%H:%M'))
        # If any Active exists in tree, hide countdown and focus group
        any_active = any(
            "Active" in self.tree_widget.topLevelItem(i).child(j).text(0)
            for i in range(self.tree_widget.topLevelItemCount())
            for j in range(self.tree_widget.topLevelItem(i).childCount())
        )
        if any_active:
            # Collapse all groups except the active one, bring window to front
            for i in range(self.tree_widget.topLevelItemCount()):
                group = self.tree_widget.topLevelItem(i)
                has_active = any(
                    "Active" in group.child(j).text(0)
                    for j in range(group.childCount())
                )
                group.setExpanded(has_active)
            if not (self.snooze_until and datetime.now() < self.snooze_until):
                # Only maximize if not in fullscreen
                if not (self.windowState() & Qt.WindowFullScreen):
                    self.setWindowState(Qt.WindowMaximized)
                self.show()
                self.raise_()
                self.activateWindow()
                # Keep on top while active
                self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                self.show()
                # Show fullscreen toggle button
                self.full_btn.show()
            self.countdown_label.setText("")
            return
        # No active alerts: proceed to countdown logic
        # Find next "Open" entry in the list widget
        next_time = None
        for i in range(self.list_widget.count()):
            text = self.list_widget.item(i).text()
            # Identify unacknowledged open items by status label
            if text.strip().endswith(' - Open'):
                time_str = text.split(' - ')[0]
                next_time = datetime.strptime(time_str, '%H:%M').replace(
                    year=now.year, month=now.month, day=now.day
                )
                break
        if next_time:
            delta = next_time - now
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            self.countdown_label.setText(f"Next: {next_time.strftime('%H:%M')} in {hours:02}:{minutes:02}")
        else:
            self.countdown_label.setText("")
        # No longer active: disable always-on-top and reset group expansion
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        # Ensure window stays visible state
        if self.isVisible(): self.show()
        # Reset group expansion: expand missed, collapse opens
        for i in range(self.tree_widget.topLevelItemCount()):
            group = self.tree_widget.topLevelItem(i)
            has_missed = any(
                "Missed" in group.child(j).text(0)
                for j in range(group.childCount())
            )
            group.setExpanded(has_missed)
        self.check_and_play_sound()

    def refresh_list(self):
        self.populate_list()
        self.check_and_play_sound()
    def check_and_play_sound(self):
        # Skip alerts during snooze
        if self.snooze_until and datetime.now() < self.snooze_until:
            return
        # Play and loop sound if any manifest is active (flashing)
        from PyQt5.QtMultimedia import QSound
        import os
        sound_path = os.path.join(os.path.dirname(__file__), 'resources', 'alert.wav')
        any_active = any("Active" in self.list_widget.item(i).text() for i in range(self.list_widget.count()))
        if any_active:
            if self.sound is None:
                if os.path.exists(sound_path):
                    self.sound = QSound(sound_path)
                    self.sound.setLoops(QSound.Infinite)
                    self.sound.play()
            else:
                # If sound exists but is not playing, play it
                if not self.sound.isFinished():
                    pass  # Already playing
                else:
                    self.sound.play()
        else:
            if self.sound:
                self.sound.stop()
                self.sound = None
    def acknowledge_selected(self):
        # Mark selected item as acknowledged and stop flashing
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        selected = self.list_widget.currentItem()
        if not selected:
            return
        text = selected.text()
        # Parse manifest time and carrier from item text
        try:
            parts = text.split(' - ')
            manifest_time, carrier, status = parts[0], parts[1], parts[2]
        except Exception:
            manifest_time, carrier, status = '', '', ''

        if "Open" in text:
            QMessageBox.information(self, "Cannot Acknowledge", "You cannot acknowledge an 'Open' manifest. Wait until it is Active or Missed.")
            return

        if "Missed" in text:
            # Prompt for missed reason
            reason, ok = QInputDialog.getText(self, "Missed Reason", "Please enter reason for missed manifest:")
            if ok and reason.strip():
                try:
                    from logger import log_acknowledgment
                    log_acknowledgment(manifest_time, carrier, "Missed", reason.strip())
                except Exception as e:
                    QMessageBox.warning(self, "Log Error", f"Failed to log acknowledgment: {e}")
                self.populate_list()
                self.update_clock_and_countdown()
            else:
                QMessageBox.information(self, "No Reason", "Acknowledgment cancelled: reason required.")
            return

        if "Active" in text or "Open" in text:
            try:
                from logger import log_acknowledgment
                log_acknowledgment(manifest_time, carrier, status)
            except Exception as e:
                QMessageBox.warning(self, "Log Error", f"Failed to log acknowledgment: {e}")
            # Refresh list and countdown
            self.populate_list()
            self.update_clock_and_countdown()
            # Ensure window remains visible and stays on top
            self.show()
            self.raise_()
            self.activateWindow()
            return

    def populate_list(self):
        self.tree_widget.clear()
        self.flashing_items = []
        config = load_config()
        manifests = sorted(config.get('manifests', []), key=lambda m: datetime.strptime(m['time'], "%H:%M"))
        now = datetime.now()
        today = now.date().isoformat()
        # Load today's acks
        ack_path = os.path.join(os.path.dirname(__file__), 'logs', 'acknowledgments.json')
        import shutil
        if os.path.exists(ack_path):
            try:
                with open(ack_path, 'r', encoding='utf-8') as f:
                    ack_data = json.load(f)
            except Exception as e:
                # Backup the corrupted file
                try:
                    backup_path = ack_path + ".bak"
                    shutil.copyfile(ack_path, backup_path)
                except Exception:
                    pass
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Log Error", f"Acknowledgment log is invalid and was backed up as {ack_path}.bak: {e}")
                ack_data = []
        else:
            ack_data = []
        # Build a lookup for today's acks
        ack_lookup = {}
        for ack in ack_data:
            if ack.get('date') == today:
                key = (ack.get('manifest_time'), ack.get('carrier'))
                ack_lookup[key] = ack

        if not manifests:
            # No manifests to display
            no_item = QTreeWidgetItem(["No manifests loaded. Check your config file."])
            self.tree_widget.addTopLevelItem(no_item)
            return
        else:
            # Build tree: group per time
            for m in manifests:
                time = m['time']
                group = QTreeWidgetItem([time])
                self.tree_widget.addTopLevelItem(group)
                for carrier in m.get('carriers', []):
                    key = (time, carrier)
                    ack = ack_lookup.get(key)
                    status = get_manifest_status(time, now)
                    if ack:
                        text = f"{carrier} - Acknowledged{' Late' if ack['status']=='Missed' else ''}"
                        color = Qt.green
                    else:
                        if status == 'Pending':
                            text = f"{carrier} - Open"
                            color = Qt.black
                        elif status == 'Active':
                            text = f"{carrier} - Active"
                            color = Qt.red
                        else:
                            text = f"{carrier} - Missed"
                            color = Qt.darkRed
                    child = QTreeWidgetItem([text])
                    child.setForeground(0, color)
                    group.addChild(child)
                    if 'Active' in text or 'Missed' in text:
                        self.flashing_items.append(child)
        # Auto-size columns
        self.tree_widget.resizeColumnToContents(0)
        # Set initial group expansion: expand groups with active/missed
        for i in range(self.tree_widget.topLevelItemCount()):
            grp = self.tree_widget.topLevelItem(i)
            has_active = any('Active' in grp.child(j).text(0) or 'Missed' in grp.child(j).text(0)
                             for j in range(grp.childCount()))
            grp.setExpanded(has_active)
        # Show Snooze and Fullscreen toggle only when there are active flashing items
        if self.flashing_items:
            self.snooze_btn.show()
            self.full_btn.show()
        else:
            self.snooze_btn.hide()
            self.full_btn.hide()

    def toggle_flashing(self):
        # Skip flashing during snooze
        if self.snooze_until and datetime.now() < self.snooze_until:
            return
        # Toggle the color of flashing (Active) items
        for item in self.flashing_items:
            if self.flashing_on:
                item.setForeground(Qt.red)
            else:
                item.setForeground(Qt.white)
        self.flashing_on = not self.flashing_on
        # Also check sound on every flash
        self.check_and_play_sound()

    def snooze_alerts(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        # Ask for snooze duration in minutes
        duration, ok = QInputDialog.getInt(self, "Snooze Alerts", "Snooze duration (minutes):", value=2, min=1, max=30)
        if not ok:
            return
        # Calculate end time
        self.snooze_until = datetime.now() + timedelta(minutes=duration)
        # Stop any playing sound
        if self.sound:
            self.sound.stop()
            self.sound = None
        # Hide window during snooze
        self.hide()
        # Inform user
        QMessageBox.information(self, "Snoozed", f"Alerts snoozed for {duration} minutes.")
        # Schedule end of snooze
        QTimer.singleShot(duration * 60 * 1000, self.end_snooze)

    def end_snooze(self):
        # Clear snooze and show window
        self.snooze_until = None
        self.show()
        self.populate_list()
        self.update_clock_and_countdown()
        # Ensure always-on-top when coming out of snooze if alerts active
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()

    def switch_monitor(self):
        """Cycle window to the next available screen"""
        from PyQt5.QtWidgets import QApplication
        screens = QApplication.screens()
        fg = self.frameGeometry()
        center = fg.center()
        idx = 0
        for i, screen in enumerate(screens):
            if screen.geometry().contains(center):
                idx = i
                break
        next_screen = screens[(idx + 1) % len(screens)]
        rect = next_screen.geometry()
        new_center = rect.center()
        fg.moveCenter(new_center)
        self.move(fg.topLeft())
        self.raise_()
        self.activateWindow()
        # Keep on top while moved
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()
    def toggle_fullscreen(self):
        # Toggle between fullscreen and maximized window
        if self.windowState() & Qt.WindowFullScreen:
            # Exit fullscreen
            self.setWindowState(Qt.WindowMaximized)
            # Update icon back to fullscreen symbol
            self.full_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        else:
            # Enter fullscreen
            self.setWindowState(Qt.WindowFullScreen)
            # Update icon to normal/restore symbol
            self.full_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.show()

    def collapse_all(self):
        """Collapse all manifest groups in the tree"""
        self.tree_widget.collapseAll()

    def expand_all(self):
        """Expand all manifest groups in the tree"""
        self.tree_widget.expandAll()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlertDisplay()
    window.show()
    sys.exit(app.exec_())
