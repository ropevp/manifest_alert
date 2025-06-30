import pyttsx3
import threading
import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout, QFrame, QSizePolicy
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer
from scheduler import get_manifest_status
from data_manager import load_config
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QStyle
from PyQt5.QtMultimedia import QSound
import os, shutil

# Backup current file for Ticket 4 refactor
backup_path = os.path.join(os.path.dirname(__file__), 'alert_display.ticket4.bak.py')
if not os.path.exists(backup_path):
    shutil.copyfile(__file__, backup_path)

class AlertDisplay(QWidget):
    def __init__(self):
        super().__init__()        # Start with normal stacking (not always-on-top)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowTitle("Manifest Alerts")
        self.resize(int(350 * 1.25), int(250 * 1.5 * 1.25))  # height increased by 25%
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        # Ultra-slim margins and spacing for compact UI
        layout.setContentsMargins(4, 2, 4, 2)       
        
        layout.setSpacing(2)
        
        # Clock label centered at top
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignCenter)
        digital_font = QFont('Segoe UI', 48, QFont.Bold)
        self.clock_label.setFont(digital_font)
        self.clock_label.setStyleSheet("""
            color: white;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
        """)        
        
        layout.addWidget(self.clock_label)
        
        # Combined message bar for speech ticker and countdown/status messages
        self.message_bar = QFrame()
        self.message_bar.setFixedHeight(50)
        self.message_bar.setStyleSheet("background-color: rgba(0, 0, 0, 0.1);")  # Subtle background
        
        # Layout for the message bar content
        message_layout = QHBoxLayout(self.message_bar)
        message_layout.setContentsMargins(20, 5, 20, 5)
        
        # Combined label for both speech ticker and countdown messages
        self.combined_message_label = QLabel()
        self.combined_message_label.setAlignment(Qt.AlignCenter)
        message_font = QFont('Segoe UI', 18, QFont.Bold)
        self.combined_message_label.setFont(message_font)
        self.combined_message_label.setStyleSheet("""
            color: white;
            background: transparent;
            padding: 5px;
        """)
        message_layout.addWidget(self.combined_message_label)
        
        layout.addWidget(self.message_bar)
        # Manifest list as collapsible tree
        from PyQt5.QtWidgets import QAbstractItemView
        self.tree_widget = QTreeWidget()
        self.tree_widget.setFont(QFont('Segoe UI', 16))
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Use default expand/collapse icons
        layout.addWidget(self.tree_widget, 1)
        # Double-click to acknowledge
        self.tree_widget.itemDoubleClicked.connect(lambda item, col: self.acknowledge_selected())

        # Bottom control bar layout
        btn_layout = QHBoxLayout()
        # Core actions on left
        self.ack_btn = QPushButton("Acknowledge")
        self.ack_btn.clicked.connect(self.acknowledge_selected)
        btn_layout.addWidget(self.ack_btn)
        self.reload_btn = QPushButton("Reload Config")
        self.reload_btn.clicked.connect(self.reload_config)
        btn_layout.addWidget(self.reload_btn)
        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.clicked.connect(self.collapse_all)
        btn_layout.addWidget(self.collapse_btn)
        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.clicked.connect(self.expand_all)
        btn_layout.addWidget(self.expand_btn)
        # Spacer to push secondary actions to right
        btn_layout.addStretch()
        # Secondary actions on right
        self.snooze_btn = QPushButton("Snooze")
        self.snooze_btn.clicked.connect(self.snooze_alerts)
        self.snooze_btn.hide()
        btn_layout.addWidget(self.snooze_btn)
        self.monitor_btn = QPushButton("⇔ Switch Monitor")
        self.monitor_btn.setToolTip("Switch Monitor")
        self.monitor_btn.clicked.connect(self.switch_monitor)
        btn_layout.addWidget(self.monitor_btn)
        
        self.full_btn = QPushButton()
        self.full_btn.setToolTip("Toggle Fullscreen/Maximize")
        self.full_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.full_btn.clicked.connect(self.toggle_fullscreen)
        # Always show fullscreen button for warehouse TV displays
        btn_layout.addWidget(self.full_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)        # Timers and sound (start only once)
        # Snooze tracker
        self.snooze_until = None
        self.flashing_items = []
        self.flashing_on = True
        self.sound = None
        
        # Background flashing for alerts
        self.background_flash_state = 0  # 0=normal, 1=red, 2=white, 3=black
        self.background_flashing = False
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
          # Initialize speech timer before first update
        self.speech_timer = QTimer(self)
        self.speech_timer.timeout.connect(self.speak_active_alert)
        self.last_spoken_time = None
          # Speech ticker animation for combined message
        self.ticker_text = ""
        self.countdown_text = ""  # Separate countdown text
        self.ticker_position = 0
        self.ticker_timer = QTimer(self)
        self.ticker_timer.timeout.connect(self.update_combined_message)
        self.ticker_timer.start(100)  # Update every 100ms for smooth scrolling
        
        # Flag to apply auto-expansion only once
        self.first_populate = True
        self.populate_list()
        self.update_clock_and_countdown()        # System tray integration
        from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
        tray_icon = QSystemTrayIcon(
            QIcon(icon_path) if os.path.exists(icon_path) else self.windowIcon(), parent=self
        )
        tray_icon.setToolTip("Manifest Alerts")
        
        menu = QMenu()
        show_action = QAction("Bring to Front", self)
        exit_action = QAction("Exit", self)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        tray_icon.setContextMenu(menu)
        show_action.triggered.connect(lambda: self._toggle_visibility())
        exit_action.triggered.connect(lambda: tray_icon.hide() or QApplication.instance().quit())
        tray_icon.activated.connect(lambda r: self._toggle_visibility() if r == QSystemTrayIcon.Trigger else None)
        tray_icon.show()

    def speak_active_alert(self):
        # Analyze all alerting manifests to create a smart, consolidated announcement
        alerting_groups = []
        has_active = False
        has_missed = False
        
        for i in range(self.tree_widget.topLevelItemCount()):
            group = self.tree_widget.topLevelItem(i)
            time_str = group.text(0)
            group_has_active = False
            group_has_missed = False
            
            # Check what types of alerts this time group has
            for j in range(group.childCount()):
                child_text = group.child(j).text(0)
                if child_text.endswith(' - Active'):
                    group_has_active = True
                    has_active = True
                elif child_text.endswith(' - Missed'):
                    group_has_missed = True
                    has_missed = True
            
            # If this group has any alerts, add it to our list
            if group_has_active or group_has_missed:
                alerting_groups.append({
                    'time': time_str,
                    'has_active': group_has_active,
                    'has_missed': group_has_missed
                })
        
        if not alerting_groups:
            # No alerting manifests found
            self.last_spoken_time = None
            return
          # Create smart consolidated announcement based on situation
        if len(alerting_groups) == 1:
            # Single time group - speak the specific time normally
            single_group = alerting_groups[0]
            self._trigger_speech(single_group['time'])
        else:
            # Multiple time groups - give consolidated announcement
            if has_active and has_missed:
                # Mix of active and missed
                text = "Multiple Missed and Active Manifests. Please acknowledge"
            elif has_missed:
                # All missed
                text = "Multiple missed manifests. Please acknowledge"
            else:
                # All active
                text = "Multiple manifests Active. Please acknowledge"
            
            # Update ticker and speak the consolidated message
            self.set_ticker_text(text)
            threading.Thread(target=self._speak, args=(text,), daemon=True).start()
        self.last_spoken_time = None

    def _trigger_speech(self, time_str):
        # Convert '13:40' to 'one forty' or '15:03' to 'three oh three'
        try:
            hour, minute = map(int, time_str.split(':'))
            hour_12 = hour % 12 or 12
            spoken_hour = self._number_to_words(hour_12)
            
            # Handle minutes properly - if 0-9, say "oh X", otherwise normal
            if minute == 0:
                spoken_minute = "o'clock"
            elif minute < 10:
                spoken_minute = f"oh {self._number_to_words(minute)}"
            else:
                spoken_minute = self._number_to_words(minute)
            
            if minute == 0:
                spoken_time = f"{spoken_hour} o'clock"
            else:
                spoken_time = f"{spoken_hour} {spoken_minute}"
            
            # Check how late the manifest is
            from datetime import datetime
            now = datetime.now()
            manifest_time = datetime.strptime(time_str, '%H:%M').replace(
                year=now.year, month=now.month, day=now.day
            )
            minutes_late = int((now - manifest_time).total_seconds() / 60)
            
            if minutes_late >= 30:  # Missed (30+ minutes late)
                text = f"Manifest Missed, at {spoken_time}. Manifest is {minutes_late} minutes Late"
            else:  # Active (0-29 minutes late)
                text = f"Manifest. at {spoken_time}"
                
        except Exception:
            text = f"Manifest"
        
        # Update ticker and speak
        self.set_ticker_text(text)
        threading.Thread(target=self._speak, args=(text,), daemon=True).start()

    def _speak(self, text):
        try:
            import time
            engine = pyttsx3.init()
            # Use Zira voice (better quality female voice)
            voices = engine.getProperty('voices')
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id)  # Zira (female)
            # Get current speech rate and reduce by 20%
            rate = engine.getProperty('rate')
            engine.setProperty('rate', int(rate * 0.9))  # 20% slower
              # Handle pause by splitting on period and adding delay
            if '. ' in text:
                parts = text.split('. ')
                for i, part in enumerate(parts):
                    if part.strip():  # Skip empty parts
                        engine.say(part)
                        engine.runAndWait()
                        if i < len(parts) - 1:  # Don't pause after the last part
                            time.sleep(1)  # 1 second pause between parts
            else:
                engine.say(text)
                engine.runAndWait()
        except Exception:
            pass

    def _number_to_words(self, n):
        # Simple number to words for 0-59
        words = [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
            'twenty', 'twenty one', 'twenty two', 'twenty three', 'twenty four', 'twenty five', 'twenty six', 'twenty seven', 'twenty eight', 'twenty nine',
            'thirty', 'thirty one', 'thirty two', 'thirty three', 'thirty four', 'thirty five', 'thirty six', 'thirty seven', 'thirty eight', 'thirty nine',
            'forty', 'forty one', 'forty two', 'forty three', 'forty four', 'forty five', 'forty six', 'forty seven', 'forty eight', 'forty nine',
            'fifty', 'fifty one', 'fifty two', 'fifty three', 'fifty four', 'fifty five', 'fifty six', 'fifty seven', 'fifty eight', 'fifty nine'
        ]
        return words[n] if 0 <= n < 60 else str(n)

    def _toggle_visibility(self):
        """Toggle the visibility of the window - Disabled for warehouse TV display."""
        # In warehouse environment, window should always remain visible
        # Just bring to front and focus instead of hiding
        self.show()
        self.raise_()
        self.activateWindow()
        if self.isMinimized():
            self.setWindowState(Qt.WindowMaximized)

    def reload_config(self):
        self.populate_list()
        self.update_clock_and_countdown()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Config Reloaded", "Configuration reloaded from disk.")
    def update_clock_and_countdown(self):
        now = datetime.now()
        # Skip updates (maximize/hide logic) during snooze period
        if self.snooze_until and now < self.snooze_until:
            return        # Day-change logic
        if now.date() != self.current_date:
            self.current_date = now.date()
            self.populate_list()
        
        self.clock_label.setText(now.strftime('%H:%M'))
        
        # Update status band and background based on most urgent status
        self.update_visual_alerts()# If any Active or Missed exists in tree, focus group and maximize
        any_alerting = any(
            ("Active" in self.tree_widget.topLevelItem(i).child(j).text(0) or
             "Missed" in self.tree_widget.topLevelItem(i).child(j).text(0))
            for i in range(self.tree_widget.topLevelItemCount())
            for j in range(self.tree_widget.topLevelItem(i).childCount())
        )
        if any_alerting:
            # Collapse all groups except the alerting ones, bring window to front
            for i in range(self.tree_widget.topLevelItemCount()):
                group = self.tree_widget.topLevelItem(i)
                has_alerting = any(
                    ("Active" in group.child(j).text(0) or "Missed" in group.child(j).text(0))
                    for j in range(group.childCount())
                )
                group.setExpanded(has_alerting)
            if not (self.snooze_until and datetime.now() < self.snooze_until):
                # Only maximize if not in fullscreen
                if not (self.windowState() & Qt.WindowFullScreen):
                    self.setWindowState(Qt.WindowMaximized)
                self.show()
                self.raise_()
                self.activateWindow()                # Keep on top while active
                self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                self.show()
                # Play sound immediately on active
                self.check_and_play_sound()
            # Continue to check for late message (don't return early)
        # Check for any late manifests (past due but not acknowledged)
        late_manifest = None
        max_late_minutes = 0
        for i in range(self.tree_widget.topLevelItemCount()):
            group = self.tree_widget.topLevelItem(i)
            raw_text = group.text(0)
            if raw_text.startswith('+ ') or raw_text.startswith('− '):
                time_str = raw_text[2:]
            else:
                time_str = raw_text
            # Check if this time has any missed or active manifests
            has_unacknowledged = any(
                child_text.endswith(' - Active') or child_text.endswith(' - Missed')
                for j in range(group.childCount())
                for child_text in [group.child(j).text(0)]
            )
            if has_unacknowledged:
                manifest_time = datetime.strptime(time_str, '%H:%M').replace(
                    year=now.year, month=now.month, day=now.day
                )
                if now > manifest_time:  # Past due
                    minutes_late = int((now - manifest_time).total_seconds() / 60)
                    if minutes_late > max_late_minutes:
                        max_late_minutes = minutes_late
                        late_manifest = time_str
        if late_manifest and max_late_minutes > 0:
            # Show late manifest message
            self.set_countdown_text(f"Manifest Late by {max_late_minutes} mins")
            return
        
        # If no late manifests but we have alerting manifests, clear countdown
        if any_alerting:
            self.set_countdown_text("")
            return
        
        # Clear ticker when no alerts are active
        if not any_alerting:
            self.set_ticker_text("")
        
        # Find next "Open" entry in the tree
        next_time = None
        for i in range(self.tree_widget.topLevelItemCount()):
            group = self.tree_widget.topLevelItem(i)
            # Strip expand/collapse prefix when parsing time
            raw_text = group.text(0)
            if raw_text.startswith('+ ') or raw_text.startswith('− '):
                time_str = raw_text[2:]
            else:
                time_str = raw_text
            for j in range(group.childCount()):
                child_text = group.child(j).text(0)
                if child_text.endswith(' - Open'):
                    next_time = datetime.strptime(time_str, '%H:%M').replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    break
            if next_time:
                break
                
        if next_time:
            delta = next_time - now
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Format the message nicely
            if hours > 0:
                time_msg = f"{hours} hr {minutes} mins"
            else:                time_msg = f"{minutes} mins"
            
            self.set_countdown_text(f"Next Manifest in {time_msg}")
        else:
            self.set_countdown_text("")
        # No longer active: disable always-on-top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        # Ensure window stays visible state
        if self.isVisible(): 
            self.show()
            
        # Check sound without altering group expansion (retain manual state)
        self.check_and_play_sound()

    def update_visual_alerts(self):
        """Update status band and background based on most urgent manifest status"""
        # Priority order: Active > Missed > Open > All Acknowledged
        
        # Check for Active manifests (highest priority - red)
        has_active = any(
            "Active" in self.tree_widget.topLevelItem(i).child(j).text(0)
            for i in range(self.tree_widget.topLevelItemCount())
            for j in range(self.tree_widget.topLevelItem(i).childCount())
        )
        
        # Check for Missed manifests (second priority - dark red)
        has_missed = any(
            "Missed" in self.tree_widget.topLevelItem(i).child(j).text(0)
            for i in range(self.tree_widget.topLevelItemCount())
            for j in range(self.tree_widget.topLevelItem(i).childCount())
            if not ("Acknowledged" in self.tree_widget.topLevelItem(i).child(j).text(0))
        )
        
        # Check for Open manifests (third priority - blue)
        has_open = any(
            "Open" in self.tree_widget.topLevelItem(i).child(j).text(0)
            for i in range(self.tree_widget.topLevelItemCount())
            for j in range(self.tree_widget.topLevelItem(i).childCount())
        )        # Determine colors based on status
        if has_active:
            clock_bg_color = "rgba(255, 0, 0, 0.8)"  # Semi-transparent red
            message_bar_color = "rgb(255, 0, 0)"  # Red for message bar
            self.background_flashing = True
        elif has_missed:
            clock_bg_color = "rgba(139, 0, 0, 0.8)"  # Semi-transparent dark red
            message_bar_color = "rgb(139, 0, 0)"  # Dark red for message bar
            self.background_flashing = True
        elif has_open:
            clock_bg_color = "rgba(38, 132, 255, 0.8)"  # Semi-transparent blue
            message_bar_color = "rgb(38, 132, 255)"  # Blue for message bar
            self.background_flashing = False
        else:
            clock_bg_color = "rgba(0, 200, 0, 0.8)"  # Semi-transparent green
            message_bar_color = "rgb(0, 200, 0)"  # Green for message bar
            self.background_flashing = False
        
        # Update clock background
        self.clock_label.setStyleSheet(f"""
            color: white;
            background: {clock_bg_color};
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
        """)
        
        # Update message bar background
        self.message_bar.setStyleSheet(f"background-color: {message_bar_color};")
        
        # Set clean background for the whole interface
        self.setStyleSheet("""
            QWidget {{
                background-color: #f5f5f5;
            }}
            QTreeWidget {{
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }}
            QPushButton {{
                background-color: white;
                color: black;
                border: 1px solid #999;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;            }}
        """)

    def refresh_list(self):
        # Skip full rebuild to preserve manual expand state
        self.check_and_play_sound()
        self.update_clock_and_countdown()
    def check_and_play_sound(self):
        # Skip alerts during snooze
        if self.snooze_until and datetime.now() < self.snooze_until:
            return        # Play and loop sound if any manifest is active or missed (flashing)
        from PyQt5.QtMultimedia import QSound
        import os
        sound_path = os.path.join(os.path.dirname(__file__), 'resources', 'alert.wav')
        any_alerting = any(
            ("Active" in self.tree_widget.topLevelItem(i).child(j).text(0) or 
             "Missed" in self.tree_widget.topLevelItem(i).child(j).text(0))
            for i in range(self.tree_widget.topLevelItemCount())
            for j in range(self.tree_widget.topLevelItem(i).childCount())
        )
        if any_alerting:
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
                    self.sound.play()            # Start speech timer if not already running
            if not self.speech_timer.isActive():
                self.speech_timer.start(20000)  # every 20 seconds
                self.speak_active_alert()  # speak immediately only when starting timer
        else:
            if self.sound:
                self.sound.stop()
                self.sound = None
            # Stop speech timer
            if self.speech_timer.isActive():
                self.speech_timer.stop()
    def acknowledge_selected(self):
        # Mark selected item or group as acknowledged and stop flashing
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        selected = self.tree_widget.currentItem()
        if not selected:
            return        # Group acknowledgment (top-level item selected)
        if selected.parent() is None:
            # Strip prefix for manifest_time
            manifest_time = selected.text(0)
            if manifest_time.startswith('+ ') or manifest_time.startswith('− '):
                manifest_time = manifest_time[2:]
            
            # Check if this is a missed group (has any missed manifests)
            has_missed_manifests = any(
                selected.child(i).text(0).endswith(' - Missed')
                for i in range(selected.childCount())
            )
            
            # If group has missed manifests, require a note
            reason = None
            if has_missed_manifests:
                reason, ok = QInputDialog.getText(
                    self, "Missed Group Reason", 
                    f"This group has missed manifests. Please enter reason for missed manifests at {manifest_time}:"
                )
                if not (ok and reason.strip()):
                    QMessageBox.information(self, "No Reason", "Acknowledgment cancelled: reason required for missed manifests.")
                    return
                reason = reason.strip()
            
            # Acknowledge each Active/Missed child in the group
            from logger import log_acknowledgment
            any_acked = False
            for i in range(selected.childCount()):
                child = selected.child(i)
                text = child.text(0)
                # Acknowledge any Active or Missed items
                if text.endswith(' - Active') or text.endswith(' - Missed'):
                    carrier = text.split(' - ')[0]
                    status = 'Active' if text.endswith(' - Active') else 'Missed'
                    try:
                        # Pass reason for missed items, None for active items
                        log_reason = reason if status == 'Missed' else None
                        log_acknowledgment(manifest_time, carrier, status, log_reason)
                        any_acked = True
                    except Exception as e:
                        QMessageBox.warning(self, 'Log Error', f'Failed to log acknowledgment for {carrier}: {e}')
            
            if any_acked:
                QMessageBox.information(self, 'Acknowledged', f'All Active/Missed manifests at {manifest_time} acknowledged.')
                self.populate_list()
                self.update_clock_and_countdown()
                # Ensure window remains visible and stays on top
                self.show()
                self.raise_()
                self.activateWindow()
            return
        text = selected.text(0)
        # Only children (manifests) are acknowledgeable
        parent = selected.parent()
        if parent is None:
            return
        # Parse manifest time from parent and carrier/status from child
        manifest_time = parent.text(0)
        if manifest_time.startswith('+ ') or manifest_time.startswith('− '):
            manifest_time = manifest_time[2:]
        parts = text.split(' - ')
        carrier = parts[0] if parts else ''
        status = parts[1] if len(parts) > 1 else ''

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
                # Ensure window remains visible and stays on top
                self.show()
                self.raise_()
                self.activateWindow()
            else:
                QMessageBox.information(self, "No Reason", "Acknowledgment cancelled: reason required.")
            return

        if "Active" in text or "Open" in text:
            try:
                from logger import log_acknowledgment
                log_acknowledgment(manifest_time, carrier, status)
            except Exception as e:
                QMessageBox.warning(self, "Log Error", f"Failed to log acknowledgment: {e}")            # Refresh list and countdown
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
        # Define custom status colors
        open_color = QColor(38, 132, 255)   # Jira blue
        active_color = QColor(255, 0, 0)    # Red
        missed_color = QColor(139, 0, 0)    # DarkRed
        ack_color = QColor(0, 200, 0)       # Green
        ack_late_color = QColor(255, 140, 0) # Orange (Ack Late)
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
        # Build tree: group per time
        for m in manifests:
            time = m['time']
            group = QTreeWidgetItem([time])
            # Make group header selectable
            group.setFlags(group.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            # Determine group color: default Open
            group_color = open_color
            has_active = False
            has_missed = False
            has_open = False
            has_ack = False
            has_ack_late = False
            # Add to tree
            self.tree_widget.addTopLevelItem(group)
            for carrier in m.get('carriers', []):
                    key = (time, carrier)
                    ack = ack_lookup.get(key)
                    status = get_manifest_status(time, now)
                    if ack:
                        # Always show acknowledged as green, except 'Missed' (Ack Late is orange)
                        if ack['status'] == 'Missed':
                            reason = ack.get('reason')
                            text = f"{carrier} - Acknowledged Late"
                            if reason:
                                text += f" - {reason}"
                            color = ack_late_color
                            has_ack_late = True
                        else:
                            text = f"{carrier} - Acknowledged"
                            color = ack_color
                            has_ack = True
                    else:
                        if status == 'Pending':
                            text = f"{carrier} - Open"
                            color = open_color
                            has_open = True
                        elif status == 'Active':
                            text = f"{carrier} - Active"
                            color = active_color
                            has_active = True
                        else:
                            text = f"{carrier} - Missed"
                            color = missed_color
                            has_missed = True
                    child = QTreeWidgetItem([text])
                    child.setFlags(child.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    child.setForeground(0, color)
                    group.addChild(child)
                    # Only flash Active items
                    if 'Active' in text:
                        self.flashing_items.append(child)
            # After adding children, set group header color by priority
            if has_ack_late:
                group_color = ack_late_color
            elif has_ack:
                group_color = ack_color
            elif has_active:
                group_color = active_color
            elif has_missed:
                group_color = missed_color
            elif has_open:
                group_color = open_color
            group.setForeground(0, group_color)
        # No custom plus/minus prefixes; use default icons
        # Auto-size columns
        self.tree_widget.resizeColumnToContents(0)        # Smart auto-expansion logic:
        # 1. Collapse groups where all manifests are acknowledged (Ack or Ack Late)
        # 2. Expand groups with Active or Missed manifests
        # 3. Expand the next upcoming Open manifest group
        
        # Find next Open group (earliest time with Open manifests)
        next_open_group = None
        next_open_time = None
        now_time = now.time()
        
        for i in range(self.tree_widget.topLevelItemCount()):
            grp = self.tree_widget.topLevelItem(i)
            group_time_str = grp.text(0)
            try:
                group_time = datetime.strptime(group_time_str, '%H:%M').time()
                
                # Check if group has any Open manifests
                has_open_manifests = any(
                    ' - Open' in grp.child(j).text(0)
                    for j in range(grp.childCount())
                )
                
                # If this group has Open manifests and is the next upcoming time
                if has_open_manifests and group_time >= now_time:
                    if next_open_time is None or group_time < next_open_time:
                        next_open_time = group_time
                        next_open_group = i
            except ValueError:
                continue  # Skip if time parsing fails
        
        # Apply expansion logic
        for i in range(self.tree_widget.topLevelItemCount()):
            grp = self.tree_widget.topLevelItem(i)
            
            # Check what types of manifests this group has
            has_active = any(' - Active' in grp.child(j).text(0) for j in range(grp.childCount()))
            has_missed = any(' - Missed' in grp.child(j).text(0) for j in range(grp.childCount()))
            has_open = any(' - Open' in grp.child(j).text(0) for j in range(grp.childCount()))
            has_only_acknowledged = all(
                (' - Acknowledged' in grp.child(j).text(0) or ' - Acknowledged Late' in grp.child(j).text(0))
                for j in range(grp.childCount())
            )
            
            # Expansion rules:
            if has_active or has_missed:
                # Always expand Active or Missed
                grp.setExpanded(True)
            elif has_only_acknowledged:
                # Collapse if everything is acknowledged
                grp.setExpanded(False)
            elif has_open and i == next_open_group:
                # Expand next upcoming Open group
                grp.setExpanded(True)
            else:                # Collapse other Open groups
                grp.setExpanded(False)
        
        self.first_populate = False
        
        # Show Snooze button only when there are active flashing items
        # Fullscreen button is always visible for warehouse TV displays
        if self.flashing_items:
            self.snooze_btn.show()
        else:
            self.snooze_btn.hide()
    
    def update_combined_message(self):
        """Update combined message bar with either speech ticker or countdown message"""
        # Priority: speech ticker over countdown message
        if self.ticker_text:
            self.display_scrolling_text(self.ticker_text)
        elif self.countdown_text:
            self.combined_message_label.setText(self.countdown_text)
        else:
            self.combined_message_label.setText("")
    
    def display_scrolling_text(self, text):
        """Display scrolling text animation"""
        if not text:
            self.combined_message_label.setText("")
            return
            
        # Calculate visible portion of text
        label_width = self.combined_message_label.width() - 30  # Account for padding
        font_metrics = self.combined_message_label.fontMetrics()
        text_width = font_metrics.horizontalAdvance(text)
        
        if text_width <= label_width:
            # Text fits, just center it
            self.combined_message_label.setText(text)
            return
            
        # Scroll the text
        visible_chars = max(1, label_width // font_metrics.averageCharWidth())
        
        if self.ticker_position > len(text) + 10:  # Reset after scrolling past
            self.ticker_position = -visible_chars
            
        start_pos = max(0, self.ticker_position)
        end_pos = min(len(text), self.ticker_position + visible_chars)
        
        if start_pos < len(text):
            visible_text = text[start_pos:end_pos]
        else:
            visible_text = ""
            
        self.combined_message_label.setText(visible_text)
        self.ticker_position += 1

    def set_ticker_text(self, text):
        """Set new text for the scrolling ticker"""
        self.ticker_text = text
        self.ticker_position = 0

    def set_countdown_text(self, text):
        """Set countdown/status message text"""
        self.countdown_text = text

    def toggle_flashing(self):
        # Skip flashing during snooze
        if self.snooze_until and datetime.now() < self.snooze_until:
            return
        
        # Toggle the color of flashing (Active) items
        for item in self.flashing_items:
            if self.flashing_on:
                item.setForeground(0, Qt.red)
            else:
                item.setForeground(0, Qt.white)
        self.flashing_on = not self.flashing_on
        
        # Also check sound on every flash
        self.check_and_play_sound()

    def snooze_alerts(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        # Ask for snooze duration in minutes
        duration, ok = QInputDialog.getInt(self, "Snooze Alerts", "Snooze duration (minutes):", value=2, min=1, max=30)
        if not ok:
            return        # Calculate end time
        self.snooze_until = datetime.now() + timedelta(minutes=duration)
        # Stop any playing sound
        if self.sound:
            self.sound.stop()
            self.sound = None
        # Keep window visible during snooze for warehouse TV display
        # Window stays visible but alerts are silenced
        # Inform user
        QMessageBox.information(self, "Snoozed", f"Alerts snoozed for {duration} minutes. Window will remain visible.")
        # Schedule end of snooze
        QTimer.singleShot(duration * 60 * 1000, self.end_snooze)

    def end_snooze(self):
        # Clear snooze and show window
        self.snooze_until = None
        self.show()
        self.populate_list()
        self.update_clock_and_countdown()        # Ensure always-on-top when coming out of snooze if alerts active
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()

    def switch_monitor(self):
        """Cycle window to the next available screen"""
        from PyQt5.QtWidgets import QApplication
        screens = QApplication.screens()
        if len(screens) <= 1:
            return  # No other screens to switch to
        
        # Get current screen
        fg = self.frameGeometry()
        center = fg.center()
        current_screen_idx = 0
        for i, screen in enumerate(screens):
            if screen.geometry().contains(center):
                current_screen_idx = i
                break
        
        # Get next screen
        next_screen_idx = (current_screen_idx + 1) % len(screens)
        next_screen = screens[next_screen_idx]
        
        # Remember current state
        was_fullscreen = bool(self.windowState() & Qt.WindowFullScreen)
        was_maximized = bool(self.windowState() & Qt.WindowMaximized)
        
        # Reset to normal state first to avoid issues
        self.setWindowState(Qt.WindowNoState)
        self.show()
        
        # Move to center of next screen
        next_rect = next_screen.geometry()
        self.move(next_rect.center() - self.rect().center())
        
        # Apply the same state on the new screen
        if was_fullscreen:
            self.setWindowState(Qt.WindowFullScreen)
        elif was_maximized:
            self.setWindowState(Qt.WindowMaximized)
        else:
            # Default to maximized for warehouse TV display
            self.setWindowState(Qt.WindowMaximized)
        
        # Ensure window is visible and focused
        self.show()
        self.raise_()
        self.activateWindow()
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

    def closeEvent(self, event):
        """Prevent accidental closing in warehouse environment."""
        # For warehouse TV displays, don't minimize or hide the window
        # Just ignore the close event to prevent accidental closure
        event.ignore()
        # Keep window visible and focused
        self.show()
        self.raise_()
        self.activateWindow()
    
    def handle_item_expanded(self, item):
        """Update prefix when a group is expanded"""
        if item.parent() is None:
            text = item.text(0)
            # Strip existing prefix
            base = text[2:] if text.startswith(('+ ', '− ')) else text
            item.setText(0, f"− {base}")

    def handle_item_collapsed(self, item):
        """Update prefix when a group is collapsed"""
        if item.parent() is None:
            text = item.text(0)
            base = text[2:] if text.startswith(('+ ', '− ')) else text
            item.setText(0, f"+ {base}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlertDisplay()
    window.show()
    sys.exit(app.exec_())
