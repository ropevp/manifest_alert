"""
Manifest Alerts V2 - SpaceX-Style Mission Control Display
Modern, professional TV display for warehouse operations
"""

import sys
import json
import os
import csv
import random
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QPushButton,
                             QMessageBox, QScrollArea, QApplication, QDialog,
                             QLineEdit, QDialogButtonBox, QFormLayout, QFileDialog, QComboBox)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import os
import json
import sys

# Import with error handling
try:
    from scheduler import get_manifest_status
    from data_manager import load_config
    from settings_manager import get_settings_manager
except ImportError:
    # Fallback if imports fail - should not happen in production
    print("WARNING: Failed to import core modules, using minimal fallback")
    
    def get_manifest_status(time_str, now):
        # Emergency fallback - try basic time comparison
        from datetime import datetime, timedelta
        try:
            today = now.date()
            manifest_time = datetime.strptime(time_str, "%H:%M").replace(year=today.year, month=today.month, day=today.day)
            if now >= manifest_time + timedelta(minutes=30):
                return "Missed"
            elif now >= manifest_time - timedelta(minutes=2):
                return "Active"
            else:
                return "Pending"
        except:
            return "Unknown"
    
    def load_config():
        return {"manifests": []}
    
    def get_settings_manager():
        class DummySettings:
            def get_acknowledgments_path(self):
                return "ack.json"
        return DummySettings()


class StatusCard(QFrame):
    """Modern status card widget"""
    
    def __init__(self, time_str, status="OPEN", parent_display=None):
        super().__init__()
        self.time_str = time_str
        self.status = status
        self.manifests = []
        self.parent_display = parent_display  # Reference to main display for acknowledgments
        
        self.setMinimumSize(1200, 80)  # Reduced minimum height significantly
        self.setFrameStyle(QFrame.Shape.Box)
        self.setup_ui()
        self.update_styling()
        
        # Remove card-level hover tracking - we'll handle individual carrier hover instead
        
        # Make card clickable (but we'll override for time header double-click)
        self.mousePressEvent = self.card_clicked
    
    def setup_ui(self):
        layout = QHBoxLayout()  # Main horizontal layout
        layout.setContentsMargins(10, 3, 10, 3)  # Even smaller margins - reduced from 15,5 to 10,3
        layout.setSpacing(15)  # Reduced spacing between sections
        
        # Left side - Time and Status (fixed width for consistent alignment)
        time_status_layout = QVBoxLayout()
        time_status_layout.setSpacing(0)  # No spacing in time section
        time_status_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Combined time and status header
        self.time_status_label = QLabel(f"{self.time_str} - {self.status}")
        self.time_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.time_status_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))  # Increased from 24 to 28
        self.time_status_label.setFixedWidth(280)  # Consistent fixed width for alignment
        self.time_status_label.mouseDoubleClickEvent = self.time_header_double_clicked
        # Set up hover effects with mouse events
        self.time_status_label.enterEvent = self.time_header_hover_enter
        self.time_status_label.leaveEvent = self.time_header_hover_leave
        self.time_status_label.setStyleSheet("""
            QLabel {
                padding: 2px;
                border-radius: 8px;
                background: transparent;
            }
        """)
        time_status_layout.addWidget(self.time_status_label)
        time_status_layout.addStretch()
        
        layout.addLayout(time_status_layout)
        
        # Center - Manifest details (carriers) - takes remaining space
        center_layout = QVBoxLayout()
        center_layout.setSpacing(0)  # No spacing in center section
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a horizontal layout for carriers and acknowledgment side by side
        carriers_ack_layout = QHBoxLayout()
        carriers_ack_layout.setSpacing(15)  # Reduced spacing between carriers and ack  
        carriers_ack_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Left part: carriers (will be recreated as clickable labels)
        self.carriers_widget = QWidget()
        self.carriers_layout = QVBoxLayout(self.carriers_widget)
        self.carriers_layout.setContentsMargins(0, 0, 0, 0)
        self.carriers_layout.setSpacing(1)  # Extremely tight - reduced from 2 to 1
        carriers_ack_layout.addWidget(self.carriers_widget)
        
        # Right part: acknowledgment (consistent fixed width)
        ack_widget = QWidget()
        ack_widget.setFixedWidth(250)  # Consistent fixed width for all cards
        ack_widget.setStyleSheet("background: transparent;")
        
        ack_layout = QVBoxLayout(ack_widget)
        ack_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        ack_layout.setSpacing(0)  # No spacing between status and details
        
        # Acknowledgment status text
        self.ack_status_label = QLabel("")
        self.ack_status_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))  # Reduced from 22 to 18 to prevent clipping
        self.ack_status_label.setStyleSheet("color: #2ed573; background: transparent;")
        self.ack_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Left align
        ack_layout.addWidget(self.ack_status_label)
        
        # Reason/details text
        self.ack_details_label = QLabel("")
        self.ack_details_label.setFont(QFont("Segoe UI", 16))  # Reduced from 20 to 16 to prevent clipping
        self.ack_details_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.ack_details_label.setWordWrap(True)
        self.ack_details_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Left align
        ack_layout.addWidget(self.ack_details_label)
        
        ack_layout.addStretch()
        carriers_ack_layout.addWidget(ack_widget)
        # Removed addStretch here to let sections naturally space out
        
        center_layout.addLayout(carriers_ack_layout)
        center_layout.addStretch()
        
        layout.addLayout(center_layout)
        
        # Remove redundant status bar - card border provides sufficient visual indication
        self.setLayout(layout)
    
    def update_styling(self):
        """Update colors based on status - only borders and font colors on black background"""
        if self.status == "ACTIVE":
            border_color = "#ff4757"
            text_color = "#ffffff"
            status_color = "#ff4757"
        elif self.status == "MISSED":
            border_color = "#c44569"
            text_color = "#ffffff"
            status_color = "#c44569"
        elif self.status == "ACKNOWLEDGED":
            border_color = "#2ed573"
            text_color = "#ffffff"
            status_color = "#2ed573"
        else:  # OPEN
            border_color = "#3742fa"
            text_color = "#ffffff"
            status_color = "#3742fa"
        
        self.setStyleSheet(f"""
            StatusCard {{
                background: transparent;
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        self.time_status_label.setStyleSheet(f"color: {status_color}; background: transparent;")
    
    def set_manifests(self, manifests):
        """Update manifest details"""
        self.manifests = manifests
        if manifests:
            self.update_manifest_display()
        else:
            self.details_label.setText("")
    
    def set_acknowledgment(self, user_info, reason=None):
        """Update acknowledgment display with user details"""
        if user_info:
            if reason == "late":
                # For missed deliveries - show user and time
                self.ack_status_label.setText("Done Late")
                self.ack_details_label.setText(f"by {user_info}")
                self.ack_status_label.setStyleSheet("color: #ffb347; background: transparent;")  # Lighter orange
                self.ack_details_label.setStyleSheet("color: #ffb347; background: transparent;")  # Match color
            else:
                # For completed/acknowledged - show user and time
                self.ack_status_label.setText("Done")
                self.ack_details_label.setText(f"by {user_info}")
                self.ack_status_label.setStyleSheet("color: #2ed573; background: transparent;")  # Green for done
                self.ack_details_label.setStyleSheet("color: #2ed573; background: transparent;")  # Match color
        else:
            # Clear acknowledgment
            self.ack_status_label.setText("")
            self.ack_details_label.setText("")
    
    def card_clicked(self, event):
        """Handle card click - disabled for now, use double-click on time header"""
        pass  # Disabled card clicking, only time header double-click works
    
    def card_hover_enter(self, event):
        """Handle mouse enter on card border"""
        # Add subtle card border highlight
        current_style = self.styleSheet()
        if "border: 3px solid" not in current_style:
            # Increase border thickness slightly for hover effect
            for status in ["ACTIVE", "MISSED", "ACKNOWLEDGED", "OPEN"]:
                if status.lower() in current_style.lower():
                    current_style = current_style.replace("border: 2px solid", "border: 3px solid")
                    break
            self.setStyleSheet(current_style)
    
    def card_hover_leave(self, event):
        """Handle mouse leave on card"""
        # Remove card border highlight
        current_style = self.styleSheet()
        current_style = current_style.replace("border: 3px solid", "border: 2px solid")
        self.setStyleSheet(current_style)
        # Also ensure time header highlight is removed
        self.time_header_hover_leave(event)
    
    def time_header_double_clicked(self, event):
        """Handle double-click on time header to acknowledge whole card"""
        if (self.status in ["ACTIVE", "MISSED"] and 
            self.parent_display and 
            hasattr(self.parent_display, 'acknowledge_time_slot')):
            self.parent_display.acknowledge_time_slot(self.time_str)
    
    def time_header_hover_enter(self, event):
        """Handle mouse enter on time header - no background colors"""
        # No background color hover effects - keep clean appearance
        pass
    
    def time_header_hover_leave(self, event):
        """Handle mouse leave on time header - no background colors"""
        # No background color hover effects - keep clean appearance
        pass
    
    def update_manifest_display(self):
        """Update the manifest display with individual clickable carriers"""
        # Clear existing carrier labels
        for i in reversed(range(self.carriers_layout.count())):
            child = self.carriers_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if self.manifests:
            for carrier, status in self.manifests:
                # Create individual carrier label
                carrier_label = QLabel()
                carrier_label.setFont(QFont("Segoe UI", 22))  # Increased from 18 to 22
                carrier_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                # No padding at all for minimal line height
                
                # Set text and styling based on status (clean display)
                if status == "Acknowledged":
                    carrier_label.setText(carrier)
                    carrier_label.setStyleSheet("color: #2ed573; background: transparent;")
                elif status == "AcknowledgedLate":
                    carrier_label.setText(carrier)
                    carrier_label.setStyleSheet("color: #ffb347; background: transparent;")
                elif status == "Active":
                    carrier_label.setText(carrier)
                    carrier_label.setStyleSheet("color: #ffffff; background: transparent; border-radius: 5px;")
                    # Make active items clickable and hoverable
                    carrier_label.mousePressEvent = lambda event, c=carrier: self.acknowledge_single_carrier(c)
                    carrier_label.enterEvent = lambda event, label=carrier_label: self.carrier_hover_enter(label, "#ff4757")
                    carrier_label.leaveEvent = lambda event, label=carrier_label: self.carrier_hover_leave(label)
                elif status == "Missed":
                    carrier_label.setText(carrier)
                    carrier_label.setStyleSheet("color: #ff4757; background: transparent; border-radius: 5px;")
                    # Make missed items clickable and hoverable
                    carrier_label.mousePressEvent = lambda event, c=carrier: self.acknowledge_single_carrier(c)
                    carrier_label.enterEvent = lambda event, label=carrier_label: self.carrier_hover_enter(label, "#c44569")
                    carrier_label.leaveEvent = lambda event, label=carrier_label: self.carrier_hover_leave(label)
                else:  # Open
                    carrier_label.setText(carrier)
                    carrier_label.setStyleSheet("color: #ffffff; background: transparent;")
                
                self.carriers_layout.addWidget(carrier_label)
            
            # Extremely compact height calculation for minimal vertical space
            line_count = len(self.manifests)
            base_height = 35       # Even smaller base height
            line_height = 22       # Tight but readable height per carrier line  
            padding = 10           # Minimal padding
            new_height = base_height + (line_count * line_height) + padding
            self.setFixedHeight(new_height)  # Use fixed height for consistent appearance
            
            # Update overall card status
            self.update_card_status()
    
    def carrier_hover_enter(self, label, color):
        """Handle hover enter on individual carrier - no background colors"""
        # Just add a subtle text glow effect by increasing brightness
        current_style = label.styleSheet()
        # For now, just leave the existing style - no background colors
        pass
    
    def carrier_hover_leave(self, label):
        """Handle hover leave on individual carrier - no background colors"""
        # No background colors to remove, just leave as is
        pass
    
    def hex_to_rgba(self, hex_color, alpha):
        """Convert hex color to RGBA string"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"({r}, {g}, {b}, {alpha})"
    
    def acknowledge_single_carrier(self, carrier):
        """Acknowledge a single carrier"""
        if self.parent_display and hasattr(self.parent_display, 'acknowledge_single_carrier'):
            self.parent_display.acknowledge_single_carrier(self.time_str, carrier)
    
    def update_card_status(self):
        """Update card status based on manifest states"""
        if not self.manifests:
            return
            
        acknowledged_count = sum(1 for _, status in self.manifests if status in ["Acknowledged", "AcknowledgedLate"])
        missed_count = sum(1 for _, status in self.manifests if status == "Missed")
        active_count = sum(1 for _, status in self.manifests if status == "Active")
        total_count = len(self.manifests)
        
        # Determine card status and acknowledgment display
        if acknowledged_count == total_count:
            # All acknowledged
            self.status = "ACKNOWLEDGED"
            # Show acknowledgment info from the first acknowledged item
            if self.parent_display:
                ack_info = self.get_acknowledgment_info()
                if ack_info:
                    user_name = ack_info.get('user', 'Unknown')
                    reason = ack_info.get('reason', '')
                    timestamp = ack_info.get('timestamp', '')
                    if timestamp:
                        try:
                            # Parse timestamp and format time
                            ack_time = datetime.fromisoformat(timestamp)
                            time_str = ack_time.strftime('%H:%M')
                            if reason:  # Late acknowledgment
                                self.set_acknowledgment(f"{user_name} at {time_str}", "late")
                            else:  # Regular acknowledgment
                                self.set_acknowledgment(f"{user_name} at {time_str}")
                        except:
                            if reason:
                                self.set_acknowledgment(user_name, "late")
                            else:
                                self.set_acknowledgment(user_name)
                    else:
                        if reason:
                            self.set_acknowledgment(user_name, "late")
                        else:
                            self.set_acknowledgment(user_name)
        elif missed_count > 0:
            # Has missed items - card becomes MISSED
            self.status = "MISSED"
            if acknowledged_count > 0:
                # Partially acknowledged
                self.ack_status_label.setText(f"{acknowledged_count}/{total_count} Done")
                self.ack_status_label.setStyleSheet("color: #ffb347; background: transparent;")  # Lighter orange for partial
                self.ack_details_label.setText("")
            else:
                self.set_acknowledgment("")  # Clear acknowledgment display
        elif active_count > 0:
            # Has active items - card becomes ACTIVE
            self.status = "ACTIVE"
            if acknowledged_count > 0:
                # Partially acknowledged
                self.ack_status_label.setText(f"{acknowledged_count}/{total_count} Done")
                self.ack_status_label.setStyleSheet("color: #ffb347; background: transparent;")  # Lighter orange for partial
                self.ack_details_label.setText("")
            else:
                self.set_acknowledgment("")  # Clear acknowledgment display
        else:
            # Open items
            self.status = "OPEN"
            self.set_acknowledgment("")  # Clear acknowledgment display
        
        # Update the combined time/status label - change ACKNOWLEDGED to DONE
        display_status = "DONE" if self.status == "ACKNOWLEDGED" else self.status
        self.time_status_label.setText(f"{self.time_str} - {display_status}")
        self.update_styling()
    
    def get_acknowledgment_info(self):
        """Get acknowledgment info for the first acknowledged item"""
        if not self.parent_display:
            return None
            
        try:
            acks = self.parent_display.load_acknowledgments()
            today = datetime.now().date().isoformat()
            
            for carrier, status in self.manifests:
                if status in ["Acknowledged", "AcknowledgedLate"]:
                    ack_key = f"{today}_{self.time_str}_{carrier}"
                    if ack_key in acks:
                        return acks[ack_key]
            return None
        except:
            return None


class AlertDisplay(QWidget):
    def get_acknowledgments_path(self):
        """Get path to acknowledgments file"""
        try:
            settings = self.load_settings()
            data_folder = settings.get('data_folder', '')
            
            if data_folder and os.path.exists(data_folder):
                return os.path.join(data_folder, 'ack.json')
            
            # Fallback to app_data folder
            return os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json')
        except Exception:
            return os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json')
    
    def load_settings(self):
        """Load application settings"""
        try:
            settings_path = os.path.join(os.path.dirname(__file__), 'app_data', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manifest Times")
        self.setMinimumSize(1200, 800)
        
        # Alert state management
        self.alert_active = False
        self.acknowledging_in_progress = False  # Flag to prevent window restoration during acknowledgments
        
        # Track previous window state for fullscreen toggle
        self.previous_window_state = Qt.WindowState.WindowNoState
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            window_icon = QIcon(icon_path)
            if not window_icon.isNull():
                self.setWindowIcon(window_icon)
        
        self.status_cards = {}
        self.clock_timer = None
        self.refresh_timer = None
        self.flash_timer = None  # Timer for alarm background flashing
        self.pause_timer = None  # Timer for pause between flash cycles
        self.flash_state = False  # Track flash on/off state
        self.flash_cycle_count = 0  # Track number of flashes in current cycle
        self.is_paused = False  # Track if we're in pause mode
        
        # Initialize sound effect
        self.setup_sound()
        
        self.setup_ui()
        self.setup_timers()
        self.apply_background_style()  # Initialize background
        self.populate_data()
    
    def setup_ui(self):
        """Create the modern mission control layout"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 10, 30, 30)  # Reduced top margin from 30 to 10
        main_layout.setSpacing(10)  # Reduced spacing from 20 to 10
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("MANIFEST TIMES")
        title_label.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))  # Increased from 36 to 42
        title_label.setStyleSheet("color: #ffffff; padding: 0px;")  # Removed bottom padding
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Multi-monitor button
        self.monitor_btn = QPushButton("🖥️")
        self.monitor_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.monitor_btn.setFixedSize(60, 40)
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c54;
                color: #ffffff;
                border: 2px solid #3742fa;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3742fa;
            }
            QPushButton:pressed {
                background-color: #1f2ecc;
            }
        """)
        self.monitor_btn.clicked.connect(self.show_monitor_menu)
        header_layout.addWidget(self.monitor_btn)
        
        # Fullscreen button
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.fullscreen_btn.setFixedSize(60, 40)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c54;
                color: #ffffff;
                border: 2px solid #3742fa;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3742fa;
            }
            QPushButton:pressed {
                background-color: #1f2ecc;
            }
        """)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        header_layout.addWidget(self.fullscreen_btn)
        
        # Settings button with cog icon
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.settings_btn.setFixedSize(60, 40)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c54;
                color: #ffffff;
                border: 2px solid #3742fa;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3742fa;
            }
            QPushButton:pressed {
                background-color: #1f2ecc;
            }
        """)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        header_layout.addWidget(self.settings_btn)
        
        # Refresh Data button in header with refresh icon
        self.reload_btn = QPushButton("🔄")
        self.reload_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.reload_btn.setFixedSize(60, 40)
        self.reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c54;
                color: #ffffff;
                border: 2px solid #3742fa;
                border-radius: 20px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3742fa;
            }
            QPushButton:pressed {
                background-color: #1f2ecc;
            }
        """)
        self.reload_btn.clicked.connect(self.populate_data)
        header_layout.addWidget(self.reload_btn)
        
        # Clock - DS-Digital font for 7-segment display look
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("DS-Digital", 38, QFont.Weight.Bold))  # Increased from 32 to 38
        self.clock_label.setStyleSheet("color: #FFD700; padding: 0px; margin-left: 20px; text-shadow: 0px 0px 5px #B8860B;")  # Golden yellow with subtle glow
        header_layout.addWidget(self.clock_label)
        
        main_layout.addLayout(header_layout)
        
        # Status summary bar
        self.summary_label = QLabel("SYSTEM NOMINAL")
        self.summary_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))  # Increased from 18 to 22
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setStyleSheet("""
            background-color: #2ed573;
            color: #000000;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(self.summary_label)
        
        # Scrollable cards area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2c2c54;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3742fa;
                border-radius: 6px;
            }
        """)
        
        # Cards container
        cards_widget = QWidget()
        self.cards_layout = QGridLayout(cards_widget)
        self.cards_layout.setSpacing(15)  # Reduced from 20 to 15
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(cards_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
        # Initialize fullscreen icon to correct state
        self.update_fullscreen_icon()
    
    def setup_sound(self):
        """Initialize sound effect for alerts using QMediaPlayer for MP3 support"""
        try:
            sound_path = os.path.join(os.path.dirname(__file__), 'resources', 'alert.mp3')
            if os.path.exists(sound_path):
                self.alert_sound = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.alert_sound.setAudioOutput(self.audio_output)
                self.alert_sound.setSource(QUrl.fromLocalFile(sound_path))
                self.audio_output.setVolume(0.7)  # 70% volume
                
                # Set up looping - when playback finishes, restart if still in alarm mode
                self.alert_sound.mediaStatusChanged.connect(self.on_media_status_changed)
            else:
                self.alert_sound = None
                self.audio_output = None
        except Exception:
            self.alert_sound = None
            self.audio_output = None

    def on_media_status_changed(self, status):
        """Handle media status changes to implement looping during alarm mode"""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        # When playback ends, restart if we're still in alarm mode
        if (status == QMediaPlayer.MediaStatus.EndOfMedia and 
            getattr(self, 'alarm_sound_playing', False) and 
            getattr(self, 'alert_active', False)):
            # Wait 500ms before restarting to ensure clean playback (3-second file needs breathing room)
            QTimer.singleShot(500, self.restart_alarm_audio)

    def restart_alarm_audio(self):
        """Restart alarm audio if still in alarm mode"""
        if (getattr(self, 'alarm_sound_playing', False) and 
            getattr(self, 'alert_active', False) and
            self.alert_sound):
            # Stop and restart for cleaner playback
            self.alert_sound.stop()
            # Small delay to ensure stop completes
            QTimer.singleShot(100, lambda: self.alert_sound.play() if self.alert_sound else None)

    def changeEvent(self, event):
        """Handle window state changes to update fullscreen icon"""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            # Update icon when window state changes (including external changes)
            self.update_fullscreen_icon()
        super().changeEvent(event)
    
    def apply_dark_theme(self):
        """Apply SpaceX-style dark theme"""
        self.setStyleSheet("""
            QWidget {
                background-color: #0f0f23;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                background: transparent;
                color: inherit;
            }
            QPushButton {
                background-color: #3742fa;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f69ff;
            }
            QPushButton:pressed {
                background-color: #2c35e6;
            }
            QMessageBox {
                background-color: #1a1a2e;
                color: #ffffff;
                font-size: 16px;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 16px;
            }
            QMessageBox QPushButton {
                background-color: #3742fa;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #4f69ff;
            }
        """)
    
    def setup_timers(self):
        """Setup update timers"""
        # Stop existing timers if they exist
        if hasattr(self, 'clock_timer') and self.clock_timer:
            self.clock_timer.stop()
        if hasattr(self, 'refresh_timer') and self.refresh_timer:
            self.refresh_timer.stop()
        if hasattr(self, 'flash_timer') and self.flash_timer:
            self.flash_timer.stop()
        if hasattr(self, 'pause_timer') and self.pause_timer:
            self.pause_timer.stop()
        
        # Initialize alarm state tracking
        self.alarm_sound_playing = False  # Track if sound is currently playing
        
        # Clock timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
        # Data refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.populate_data)
        self.refresh_timer.start(10000)  # 10 seconds (default when not in alert mode)
        
        # Flash timer for alarm background - SINGLE SHOT to prevent overlap
        self.flash_timer = QTimer(self)
        self.flash_timer.setSingleShot(False)  # Will be managed manually
        self.flash_timer.timeout.connect(self.toggle_flash)
        
        # Pause timer for breaks between flash cycles - SINGLE SHOT
        self.pause_timer = QTimer(self)
        self.pause_timer.timeout.connect(self.resume_flashing)
        self.pause_timer.setSingleShot(True)  # One-shot timer for pauses
        
        # Timer starts/stops based on alert state in update_flash_timer()
        
        self.update_clock()
    
    def update_refresh_timer(self):
        """Update refresh timer interval based on alert state"""
        if self.refresh_timer:
            if self.alert_active:
                # Alert mode: 1 second for real-time updates
                self.refresh_timer.start(1000)
            else:
                # Normal mode: 10 seconds
                self.refresh_timer.start(10000)
    
    def update_flash_timer(self):
        """Start or stop flash timer based on alert state with single alarm instance"""
        if self.flash_timer and self.pause_timer:
            if self.alert_active:
                # Only start alarm if not already running
                if not self.flash_timer.isActive() and not self.pause_timer.isActive():
                    # ALARM ACTIVATION: Bring to foreground and fullscreen on selected monitor
                    self.activate_alarm_display()
                    
                    # Start the flash cycle with 3 red flashes
                    self.flash_cycle_count = 0
                    self.is_paused = False
                    # Faster random flash speed between 2-10 Hz (100ms to 500ms) for more intense alarm
                    import random
                    flash_interval = random.randint(100, 500)  # 10Hz to 2Hz
                    self.flash_timer.start(flash_interval)
                    
                    # Start continuous alarm sound when alarm starts
                    if self.alert_sound and not getattr(self, 'alarm_sound_playing', False):
                        self.alarm_sound_playing = True
                        self.alert_sound.play()  # Will loop automatically via media status handler
            else:
                # Stop all flashing and sound when alert is cleared
                self.stop_all_alarms()
    
    def reset_sound_flag(self):
        """Reset sound flag (fallback method)"""
        self.alarm_sound_playing = False
    
    def stop_all_alarms(self):
        """Stop all alarm timers and reset state"""
        # Stop all timers
        if self.flash_timer and self.flash_timer.isActive():
            self.flash_timer.stop()
        if self.pause_timer and self.pause_timer.isActive():
            self.pause_timer.stop()
            
        # Reset all alarm state
        self.flash_state = False
        self.is_paused = False
        self.alarm_sound_playing = False
        
        # Stop sound if playing
        if self.alert_sound:
            self.alert_sound.stop()
        
        # Only restore window state if NO alerts are active AND not in the middle of acknowledging
        print(f"DEBUG: stop_all_alarms, alert_active={getattr(self, 'alert_active', False)}, acknowledging_in_progress={getattr(self, 'acknowledging_in_progress', False)}")
        if not getattr(self, 'alert_active', False) and not getattr(self, 'acknowledging_in_progress', False):
            print("DEBUG: Calling restore_alarm_display because no alerts active and not acknowledging")
            self.restore_alarm_display()
        else:
            if getattr(self, 'alert_active', False):
                print("DEBUG: NOT restoring window - alerts still active")
            if getattr(self, 'acknowledging_in_progress', False):
                print("DEBUG: NOT restoring window - acknowledgment in progress")
            
        # Ensure normal background
        self.apply_background_style()
    
    def activate_alarm_display(self):
        """Bring window to foreground and fullscreen on selected monitor when alarm starts"""
        try:
            # Load settings to get selected monitor
            settings = self.load_settings()
            target_monitor = settings.get('alarm_monitor', 0)
            
            # Get available screens
            from PyQt6.QtGui import QGuiApplication
            screens = QGuiApplication.screens()
            
            if target_monitor < len(screens):
                target_screen = screens[target_monitor]
                
                # Store current state for restoration
                if not hasattr(self, 'alarm_previous_state'):
                    if self.isFullScreen():
                        self.alarm_previous_state = 'fullscreen'
                    elif self.isMaximized():
                        self.alarm_previous_state = 'maximized'
                    else:
                        self.alarm_previous_state = 'normal'
                        self.alarm_previous_geometry = self.geometry()
                
                # Move to target screen center first (this ensures proper screen association)
                screen_geometry = target_screen.geometry()
                center_x = screen_geometry.x() + screen_geometry.width() // 2
                center_y = screen_geometry.y() + screen_geometry.height() // 2
                
                # Position window at center of target monitor
                self.move(center_x - self.width() // 2, center_y - self.height() // 2)
                
                # Bring to foreground
                self.raise_()
                self.activateWindow()
                self.show()
                
                # Small delay to ensure window is properly positioned before fullscreen
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(50, self.do_alarm_fullscreen)
                
                # Force focus
                self.setFocus()
                
            else:
                # Fallback: just bring to front on current monitor
                self.raise_()
                self.activateWindow()
                self.showFullScreen()
                
        except Exception as e:
            # Fallback: just bring to front
            self.raise_()
            self.activateWindow()
            self.show()
    
    def restore_alarm_display(self):
        """Restore window to previous state when alarm ends"""
        print(f"DEBUG: restore_alarm_display called, alert_active={getattr(self, 'alert_active', False)}")
        if hasattr(self, 'alarm_previous_state'):
            print(f"DEBUG: Restoring from state: {self.alarm_previous_state}")
            try:
                if self.alarm_previous_state == 'fullscreen':
                    # Was already fullscreen, stay fullscreen
                    pass
                elif self.alarm_previous_state == 'maximized':
                    self.showMaximized()
                elif self.alarm_previous_state == 'normal':
                    self.showNormal()
                    if hasattr(self, 'alarm_previous_geometry'):
                        self.setGeometry(self.alarm_previous_geometry)
                
                # Clean up alarm state tracking
                delattr(self, 'alarm_previous_state')
                if hasattr(self, 'alarm_previous_geometry'):
                    delattr(self, 'alarm_previous_geometry')
                    
            except Exception:
                # Fallback to normal window if restore fails
                self.showNormal()
        else:
            print("DEBUG: No alarm_previous_state found")
    
    def do_alarm_fullscreen(self):
        """Complete the fullscreen transition for alarm (called after positioning)"""
        # Ensure window is normal state first, then go fullscreen
        if self.isMaximized():
            self.showNormal()
        # Use a small delay to ensure proper state transition
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, lambda: self.showFullScreen())

    def toggle_flash(self):
        """Toggle flash state with 3 red flashes then random pause"""
        if self.is_paused:
            return
            
        self.flash_state = not self.flash_state
        
        # Count flashes (only count "on" states)
        if self.flash_state:
            self.flash_cycle_count += 1
            
            # After 3 red flashes, start random pause (3-10 seconds)
            if self.flash_cycle_count >= 3:
                self.flash_timer.stop()
                self.is_paused = True
                self.flash_state = False  # Ensure background goes to normal during pause
                self.apply_background_style()
                
                # Random pause between 3-10 seconds
                import random
                pause_duration = random.randint(3000, 10000)  # 3-10 seconds in milliseconds
                self.pause_timer.start(pause_duration)
                return
        
        self.apply_background_style()
    
    def resume_flashing(self):
        """Resume flashing after random pause with new random speed"""
        # Only resume if alert is still active and we're not already flashing
        if self.alert_active and not self.flash_timer.isActive():
            self.flash_cycle_count = 0
            self.is_paused = False
            # New faster random flash speed for next cycle (2-10 Hz)
            import random
            flash_interval = random.randint(100, 500)  # 10Hz to 2Hz
            self.flash_timer.start(flash_interval)
    
    def apply_background_style(self):
        """Apply background style with pure black default and pure red flash"""
        if self.alert_active and self.flash_state and not self.is_paused:
            # Pure red flash
            bg_color = "#FF0000"
        else:
            # Pure black background
            bg_color = "#000000"
            
        # Apply to main widget
        self.setStyleSheet(f"""
            AlertDisplay {{
                background-color: {bg_color};
            }}
            QWidget {{
                background-color: {bg_color};
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                background: transparent;
                color: inherit;
            }}
            QPushButton {{
                background-color: #3742fa;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4f69ff;
            }}
            QPushButton:pressed {{
                background-color: #2c35e6;
            }}
            QMessageBox {{
                background-color: #1a1a2e;
                color: #ffffff;
                font-size: 16px;
            }}
            QMessageBox QLabel {{
                color: #ffffff;
                font-size: 16px;
            }}
            QMessageBox QPushButton {{
                background-color: #3742fa;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #4f69ff;
            }}
        """)
    
    def update_clock(self):
        """Update the clock display"""
        now = datetime.now()
        self.clock_label.setText(now.strftime('%H:%M:%S'))
    
    def load_config(self):
        """Load configuration from settings-specified folder or fallback"""
        try:
            settings = self.load_settings()
            data_folder = settings.get('data_folder', '')
            
            # Try settings-specified folder first
            if data_folder and os.path.exists(data_folder):
                config_path = os.path.join(data_folder, 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # Fallback to default locations
            for folder in ['data', 'app_data', '.']:
                config_path = os.path.join(os.path.dirname(__file__), folder, 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # Return fallback data if no config found
            return load_config()
            
        except Exception:
            return load_config()
    
    def populate_data(self):
        """Populate cards with manifest data"""
        # Clear existing cards
        for card in self.status_cards.values():
            card.setParent(None)
        self.status_cards.clear()
        
        # Load configuration
        config = self.load_config()
        manifests = config.get('manifests', [])
        
        if not manifests:
            # Show "no data" message
            no_data_label = QLabel("NO MANIFEST DATA AVAILABLE")
            no_data_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet("color: #ff4757; padding: 100px;")
            self.cards_layout.addWidget(no_data_label, 0, 0)
            self.update_summary("NO DATA")
            return
        
        # Sort manifests by time
        manifests = sorted(manifests, key=lambda m: m['time'])
        
        # Load acknowledgments
        acks = self.load_acknowledgments()
        
        now = datetime.now()
        today = now.date().isoformat()
        
        # Create status cards - one per row
        row = 0
        cols_per_row = 1  # One card per row for wider layout
        
        active_count = 0
        missed_count = 0
        open_count = 0
        acked_count = 0
        
        for manifest in manifests:
            time_str = manifest['time']
            
            # Create status card with parent reference
            card = StatusCard(time_str, parent_display=self)
            self.status_cards[time_str] = card
            
            # Process carriers for this time - determine overall time slot status first
            manifest_data = []
            time_slot_status = get_manifest_status(time_str, now)
            print(f"DEBUG: Processing time {time_str}, time_slot_status={time_slot_status}")
            
            for carrier in manifest.get('carriers', []):
                ack_key = f"{today}_{time_str}_{carrier}"
                is_acked = ack_key in acks
                print(f"DEBUG: Carrier {carrier}, ack_key={ack_key}, is_acked={is_acked}")
                
                if is_acked:
                    # Check if it was a late acknowledgment
                    ack_info = acks[ack_key]
                    reason = ack_info.get('reason', '')
                    if reason and reason.strip():  # Has reason = late acknowledgment
                        status = "AcknowledgedLate"
                    else:
                        status = "Acknowledged"
                    acked_count += 1
                    
                    # Set acknowledgment display
                    user_name = ack_info.get('user', 'Unknown')
                    card.set_acknowledgment(user_name, reason if reason else None)
                else:
                    # Use the time slot status for all non-acknowledged items
                    status = time_slot_status
                    if status == "Active":
                        active_count += 1
                    elif status == "Missed":
                        missed_count += 1
                    else:
                        open_count += 1
                
                manifest_data.append((carrier, status))
            
            card.set_manifests(manifest_data)
            
            # Add to grid - one per row
            self.cards_layout.addWidget(card, row, 0)
            row += 1
        
        # Update alert state
        print(f"DEBUG populate_data: active_count={active_count}, missed_count={missed_count}, open_count={open_count}, acked_count={acked_count}")
        self.alert_active = (active_count > 0 or missed_count > 0)
        print(f"DEBUG populate_data: alert_active={self.alert_active}")
        
        # Update refresh timer interval based on alert state
        self.update_refresh_timer()
        
        # Update flash timer based on alert state
        self.update_flash_timer()
        
        # Update summary with next manifest countdown
        next_manifest_info = self.get_next_manifest_info(manifests, now)
        if active_count > 0:
            self.update_summary("ACTIVE ALERTS", "#ff4757")
        elif missed_count > 0:
            self.update_summary("MISSED MANIFESTS", "#c44569")
        elif next_manifest_info:
            self.update_summary(next_manifest_info, "#3742fa")
        else:
            self.update_summary("ALL SYSTEMS NOMINAL", "#2ed573")
    
    def get_next_manifest_info(self, manifests, now):
        """Get countdown to next manifest"""
        try:
            current_time = now.time()
            next_manifest = None
            
            for manifest in manifests:
                manifest_time = datetime.strptime(manifest['time'], '%H:%M').time()
                
                # Check if this manifest is in the future today
                if manifest_time > current_time:
                    next_manifest = manifest
                    break
            
            # If no manifest found for today, check tomorrow's first manifest
            if not next_manifest and manifests:
                next_manifest = manifests[0]
                # Calculate time to tomorrow's first manifest
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                manifest_time = datetime.strptime(next_manifest['time'], '%H:%M').time()
                next_time = tomorrow.replace(hour=manifest_time.hour, minute=manifest_time.minute)
            else:
                # Calculate time to today's next manifest
                manifest_time = datetime.strptime(next_manifest['time'], '%H:%M').time()
                next_time = now.replace(hour=manifest_time.hour, minute=manifest_time.minute, second=0, microsecond=0)
            
            # Calculate time difference
            time_diff = next_time - now
            
            # Convert to hours and minutes
            total_seconds = int(time_diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            if hours > 0:
                return f"NEXT MANIFEST IN {hours}h {minutes}m ({next_manifest['time']})"
            else:
                return f"NEXT MANIFEST IN {minutes}m ({next_manifest['time']})"
                
        except Exception:
            return "NEXT MANIFEST OPEN"
    
    def update_summary(self, text, color="#2ed573"):
        """Update the status summary bar"""
        text_color = "#000000" if color == "#2ed573" else "#ffffff"
        self.summary_label.setText(text)
        self.summary_label.setStyleSheet(f"""
            background-color: {color};
            color: {text_color};
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
    
    def get_ack_path(self):
        """Get the correct path for ack.json using settings"""
        settings = self.load_settings()
        data_folder = settings.get('data_folder', '')
        
        if data_folder and os.path.exists(data_folder):
            return os.path.join(data_folder, 'ack.json')
        else:
            # This should not happen if settings are configured correctly
            print(f"WARNING: data_folder '{data_folder}' not found, this may cause sync issues")
            return os.path.join(os.path.dirname(__file__), 'ack.json')
    
    def load_acknowledgments(self):
        """Load acknowledgment data from ack.json"""
        try:
            ack_path = self.get_ack_path()
            
            if not os.path.exists(ack_path):
                return {}
            
            with open(ack_path, 'r', encoding='utf-8') as f:
                ack_data = json.load(f)
            
            # Convert to lookup dict
            acks = {}
            today = datetime.now().date().isoformat()
            
            for ack in ack_data:
                if ack.get('date') == today:
                    key = f"{ack['date']}_{ack['manifest_time']}_{ack['carrier']}"
                    acks[key] = ack
            
            return acks
            
        except Exception as e:
            return {}
    
    def show_settings_dialog(self):
        """Show settings configuration dialog with CSV export/import functionality"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setFixedSize(600, 550)  # Increased size for monitor selection
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #2c2c54;
                border: 2px solid #3742fa;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4f69ff;
            }
            QLineEdit.error {
                border-color: #ff4757;
                background-color: #3d1a1a;
            }
            QPushButton {
                background-color: #3742fa;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #4f69ff;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            .status-label {
                font-size: 12px;
                padding: 5px;
                border-radius: 3px;
            }
            .status-valid {
                color: #2ed573;
                background-color: #1b2d1b;
            }
            .status-invalid {
                color: #ff4757;
                background-color: #3d1a1a;
            }
        """)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Load current settings - ensure we get the actual values
        current_settings = self.load_settings()
        
        # Username field
        self.username_edit = QLineEdit()
        username_value = current_settings.get('username', '')
        self.username_edit.setText(username_value)
        self.username_edit.setPlaceholderText("Enter username...")
        form_layout.addRow("Username:", self.username_edit)
        
        # Folder path field with validation
        folder_widget = QWidget()
        folder_layout = QVBoxLayout(folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(5)
        
        self.folder_edit = QLineEdit()
        folder_value = current_settings.get('data_folder', '')
        self.folder_edit.setText(folder_value)
        self.folder_edit.setPlaceholderText("Enter folder path for JSON files...")
        self.folder_edit.textChanged.connect(self.validate_folder_path)
        
        # Status label for folder validation
        self.folder_status_label = QLabel("")
        self.folder_status_label.setWordWrap(True)
        
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(self.folder_status_label)
        
        form_layout.addRow("Data Folder:", folder_widget)
        
        # Alarm Monitor Selection
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        monitor_layout.setContentsMargins(0, 0, 0, 0)
        monitor_layout.setSpacing(5)
        
        self.monitor_combo = QComboBox()
        self.monitor_combo.setStyleSheet("""
            QComboBox {
                background-color: #2c2c54;
                border: 2px solid #3742fa;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }d
        """)
        
        # Populate monitor list
        from PyQt6.QtGui import QGuiApplication
        screens = QGuiApplication.screens()
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            # Get the actual monitor name/manufacturer if available
            monitor_name = screen.name() if hasattr(screen, 'name') and screen.name() else f"Monitor {i+1}"
            # Create descriptive label with monitor name and resolution
            label = f"{monitor_name} ({geometry.width()}x{geometry.height()})"
            self.monitor_combo.addItem(label, i)
        
        # Set current selection
        current_monitor = current_settings.get('alarm_monitor', 0)
        if current_monitor < self.monitor_combo.count():
            self.monitor_combo.setCurrentIndex(current_monitor)
        
        monitor_layout.addWidget(self.monitor_combo)
        
        # Monitor help text
        monitor_help = QLabel("Monitor where fullscreen alarm will appear")
        monitor_help.setStyleSheet("color: #888888; font-size: 12px;")
        monitor_layout.addWidget(monitor_help)
        
        form_layout.addRow("Alarm Monitor:", monitor_widget)
        layout.addLayout(form_layout)
        
        # CSV Operations Section
        csv_group = QWidget()
        csv_group.setStyleSheet("""
            QWidget {
                background-color: #2c2c54;
                border: 1px solid #3742fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        csv_layout = QVBoxLayout(csv_group)
        csv_layout.setContentsMargins(15, 15, 15, 15)
        
        csv_title = QLabel("CSV Operations:")
        csv_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        csv_title.setStyleSheet("background: transparent; border: none; color: #ffffff;")
        csv_layout.addWidget(csv_title)
        
        # CSV buttons layout
        csv_buttons_layout = QHBoxLayout()
        
        # Export Acknowledgments button
        self.export_ack_btn = QPushButton("Export Ack")
        self.export_ack_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.export_ack_btn.clicked.connect(self.export_to_csv_from_settings)
        csv_buttons_layout.addWidget(self.export_ack_btn)
        
        # Export Config button
        self.export_config_btn = QPushButton("Export Config")
        self.export_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #f1c40f;
            }
            QPushButton:pressed {
                background-color: #d68910;
            }
        """)
        self.export_config_btn.clicked.connect(self.export_config_to_csv_from_settings)
        csv_buttons_layout.addWidget(self.export_config_btn)
        
        # Import Config button
        self.import_config_btn = QPushButton("Import Config")
        self.import_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #ec7063;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        self.import_config_btn.clicked.connect(self.import_config_from_csv)
        csv_buttons_layout.addWidget(self.import_config_btn)
        
        # Open CSV Folder button
        self.open_folder_btn = QPushButton("Open CSV Folder")
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #af7ac5;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.open_folder_btn.clicked.connect(self.open_csv_folder)
        csv_buttons_layout.addWidget(self.open_folder_btn)
        
        csv_layout.addLayout(csv_buttons_layout)
        layout.addWidget(csv_group)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(lambda: self.save_settings_and_close(dialog, current_settings))
        self.button_box.rejected.connect(dialog.reject)
        layout.addWidget(self.button_box)
        
        dialog.setLayout(layout)
        
        # Initial validation
        self.validate_folder_path()
        
        dialog.exec()
    
    def validate_folder_path(self):
        """Validate the folder path in real-time"""
        folder_path = self.folder_edit.text().strip()
        
        if not folder_path:
            # Empty path is allowed (will use default)
            self.folder_status_label.setText("Using default data locations")
            self.folder_status_label.setProperty("class", "status-label")
            self.folder_status_label.setStyleSheet("color: #999999; font-size: 12px;")
            self.folder_edit.setProperty("class", "")
            self.folder_edit.setStyleSheet("")
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            return True
        
        # Check if path exists and is accessible
        if os.path.exists(folder_path):
            if os.path.isdir(folder_path):
                # Check if we can write to this directory
                try:
                    test_file = os.path.join(folder_path, 'test_write.tmp')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    
                    self.folder_status_label.setText("✓ Valid folder with write access")
                    self.folder_status_label.setProperty("class", "status-label status-valid")
                    self.folder_status_label.setStyleSheet("color: #2ed573; background-color: #1b2d1b; font-size: 12px; padding: 5px; border-radius: 3px;")
                    self.folder_edit.setProperty("class", "")
                    self.folder_edit.setStyleSheet("")
                    self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
                    return True
                except (PermissionError, OSError):
                    self.folder_status_label.setText("✗ Folder exists but no write permission")
                    self.folder_status_label.setProperty("class", "status-label status-invalid")
                    self.folder_status_label.setStyleSheet("color: #ff4757; background-color: #3d1a1a; font-size: 12px; padding: 5px; border-radius: 3px;")
                    self.folder_edit.setProperty("class", "error")
                    self.folder_edit.setStyleSheet("border-color: #ff4757; background-color: #3d1a1a;")
                    self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
                    return False
            else:
                self.folder_status_label.setText("✗ Path exists but is not a folder")
                self.folder_status_label.setProperty("class", "status-label status-invalid")
                self.folder_status_label.setStyleSheet("color: #ff4757; background-color: #3d1a1a; font-size: 12px; padding: 5px; border-radius: 3px;")
                self.folder_edit.setProperty("class", "error")
                self.folder_edit.setStyleSheet("border-color: #ff4757; background-color: #3d1a1a;")
                self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
                return False
        else:
            self.folder_status_label.setText("✗ Folder does not exist")
            self.folder_status_label.setProperty("class", "status-label status-invalid")
            self.folder_status_label.setStyleSheet("color: #ff4757; background-color: #3d1a1a; font-size: 12px; padding: 5px; border-radius: 3px;")
            self.folder_edit.setProperty("class", "error")
            self.folder_edit.setStyleSheet("border-color: #ff4757; background-color: #3d1a1a;")
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return False
    
    def load_settings(self):
        """Load settings from settings.json"""
        try:
            settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Ensure we have default values for missing keys
                    return {
                        'username': settings.get('username', ''),
                        'data_folder': settings.get('data_folder', '')
                    }
        except Exception:
            pass
        return {'username': '', 'data_folder': ''}
    
    def save_settings_and_close(self, dialog, original_settings):
        """Save settings with validation and preserve existing values"""
        try:
            # Get new values
            new_username = self.username_edit.text().strip()
            new_folder = self.folder_edit.text().strip()
            
            # Validate folder if provided
            if new_folder and not self.validate_folder_path():
                QMessageBox.warning(self, "Invalid Folder", 
                                   "Please fix the folder path before saving.")
                return
            
            # Preserve existing values if new ones are empty (except for intentional clearing)
            final_username = new_username if new_username else original_settings.get('username', '')
            final_folder = new_folder  # Allow empty folder (uses defaults)
            final_monitor = self.monitor_combo.currentData() if hasattr(self, 'monitor_combo') else 0
            
            settings = {
                'username': final_username,
                'data_folder': final_folder,
                'alarm_monitor': final_monitor
            }
            
            settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            QMessageBox.information(self, "Settings", "Settings saved successfully!")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event with proper cleanup"""
        # Stop all alarms first
        self.stop_all_alarms()
        
        # Stop all timers
        if self.clock_timer:
            self.clock_timer.stop()
            self.clock_timer = None
        if self.refresh_timer:
            self.refresh_timer.stop()
            self.refresh_timer = None
        if self.flash_timer:
            self.flash_timer.stop()
            self.flash_timer = None
        if self.pause_timer:
            self.pause_timer.stop()
            self.pause_timer = None
        
        # Clean up status cards
        for card in self.status_cards.values():
            card.setParent(None)
        self.status_cards.clear()
        
        # Accept the close event
        event.accept()
    
    def acknowledge_time_slot(self, time_str):
        """Acknowledge all items in a time slot"""
        if time_str not in self.status_cards:
            return
            
        card = self.status_cards[time_str]
        if not card.manifests:
            return
        
        # Set flag to prevent window restoration during acknowledgment
        self.acknowledging_in_progress = True
        
        # Get username from settings
        settings = self.load_settings()
        username = settings.get('username', '').strip()
        
        if not username:
            self.acknowledging_in_progress = False
            QMessageBox.warning(self, "No Username", 
                              "Please set your username in Settings before acknowledging.")
            return
        
        # Determine if this is a late acknowledgment (any missed items)
        has_missed = any(status == "Missed" for _, status in card.manifests)
        
        # Save acknowledgments immediately
        try:
            current_time = datetime.now()
            today = current_time.date().isoformat()
            timestamp = current_time.isoformat()
            
            # Load existing acknowledgments using centralized path method
            ack_path = self.get_ack_path()
            
            # Load existing data
            ack_data = []
            if os.path.exists(ack_path):
                try:
                    with open(ack_path, 'r', encoding='utf-8') as f:
                        ack_data = json.load(f)
                except:
                    ack_data = []
            
            # Add acknowledgments for all carriers in this time slot
            for carrier, status in card.manifests:
                # Check if already acknowledged
                existing_ack = None
                for ack in ack_data:
                    if (ack.get('date') == today and 
                        ack.get('manifest_time') == time_str and 
                        ack.get('carrier') == carrier):
                        existing_ack = ack
                        break
                
                if not existing_ack:
                    # Add new acknowledgment
                    ack_entry = {
                        'date': today,
                        'manifest_time': time_str,
                        'carrier': carrier,
                        'user': username,
                        'reason': 'Done Late' if has_missed else '',
                        'timestamp': timestamp
                    }
                    ack_data.append(ack_entry)
            
            # Save to file
            with open(ack_path, 'w', encoding='utf-8') as f:
                json.dump(ack_data, f, indent=2)
            
            # Refresh display immediately to show changes
            self.populate_data()
            
            # Clear acknowledgment flag after data refresh
            self.acknowledging_in_progress = False
            
            # No success dialog - visual feedback from card color change is sufficient
            
        except Exception as e:
            self.acknowledging_in_progress = False
            QMessageBox.warning(self, "Error", f"Failed to save acknowledgment: {e}")
    
    def acknowledge_single_carrier(self, time_str, carrier):
        """Acknowledge a single carrier for a specific time"""
        # Set flag to prevent window restoration during acknowledgment
        self.acknowledging_in_progress = True
        
        # Get username from settings
        settings = self.load_settings()
        username = settings.get('username', '').strip()
        
        if not username:
            self.acknowledging_in_progress = False
            QMessageBox.warning(self, "No Username", 
                              "Please set your username in Settings before acknowledging.")
            return
        
        # Determine if this is a late acknowledgment based on card status
        is_late = False
        if time_str in self.status_cards:
            card = self.status_cards[time_str]
            # Check if this specific carrier is in missed status
            for car, status in card.manifests:
                if car == carrier and status == "Missed":
                    is_late = True
                    break
        
        try:
            current_time = datetime.now()
            today = current_time.date().isoformat()
            timestamp = current_time.isoformat()
            
            # Load existing acknowledgments using centralized path method
            ack_path = self.get_ack_path()
            
            # Load existing data
            ack_data = []
            if os.path.exists(ack_path):
                try:
                    with open(ack_path, 'r', encoding='utf-8') as f:
                        ack_data = json.load(f)
                except:
                    ack_data = []
            
            # Check if already acknowledged
            existing_ack = None
            for ack in ack_data:
                if (ack.get('date') == today and 
                    ack.get('manifest_time') == time_str and 
                    ack.get('carrier') == carrier):
                    existing_ack = ack
                    break
            
            if not existing_ack:
                # Add new acknowledgment
                ack_entry = {
                    'date': today,
                    'manifest_time': time_str,
                    'carrier': carrier,
                    'user': username,
                    'reason': 'Done Late' if is_late else '',
                    'timestamp': timestamp
                }
                ack_data.append(ack_entry)
                
                # Save to file
                with open(ack_path, 'w', encoding='utf-8') as f:
                    json.dump(ack_data, f, indent=2)
                
                # Refresh display immediately to show changes
                self.populate_data()
                
                # Clear acknowledgment flag after data refresh
                self.acknowledging_in_progress = False
            else:
                # Clear acknowledgment flag if no new acknowledgment was made
                self.acknowledging_in_progress = False
            
        except Exception as e:
            self.acknowledging_in_progress = False
            QMessageBox.warning(self, "Error", f"Failed to save acknowledgment: {e}")

    def toggle_fullscreen(self):
        """Toggle between fullscreen and previous window state"""
        if self.isFullScreen():
            # From fullscreen -> restore to previous state
            if self.previous_window_state == Qt.WindowState.WindowMaximized:
                self.showMaximized()
            else:
                self.showNormal()
            # Set icon immediately for non-fullscreen state (can go fullscreen)
            self.fullscreen_btn.setText("⛶")
        else:
            # From normal or maximized -> fullscreen
            # Remember current state before going fullscreen
            if self.isMaximized():
                self.previous_window_state = Qt.WindowState.WindowMaximized
            else:
                self.previous_window_state = Qt.WindowState.WindowNoState
            
            self.showFullScreen()
            # Set icon immediately for fullscreen state (can restore)
            self.fullscreen_btn.setText("🗗")

    def update_fullscreen_icon(self):
        """Update fullscreen button icon based on current window state"""
        # Use a delayed check to ensure window state has fully changed
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._delayed_icon_update)
    
    def _delayed_icon_update(self):
        """Delayed icon update to ensure accurate state detection"""
        if self.isFullScreen():
            self.fullscreen_btn.setText("🗗")  # Restore icon (can exit fullscreen)
        else:
            self.fullscreen_btn.setText("⛶")  # Fullscreen icon (can go fullscreen)

    def show_monitor_menu(self):
        """Show monitor selection menu"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 2px solid #3742fa;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3742fa;
            }
        """)
        
        # Get available screens
        screens = QApplication.screens()
        
        for i, screen in enumerate(screens):
            # Get screen geometry and name
            geometry = screen.geometry()
            name = screen.name() if hasattr(screen, 'name') and screen.name() else f"Monitor {i+1}"
            resolution = f"{geometry.width()}x{geometry.height()}"
            
            action_text = f"{name} ({resolution})"
            action = menu.addAction(action_text)
            action.triggered.connect(lambda checked, idx=i: self.move_to_monitor(idx))
        
        # Show menu at button position
        button_pos = self.monitor_btn.mapToGlobal(self.monitor_btn.rect().bottomLeft())
        menu.exec(button_pos)

    def move_to_monitor(self, monitor_index):
        """Move window to specified monitor"""
        try:
            screens = QApplication.screens()
            if 0 <= monitor_index < len(screens):
                target_screen = screens[monitor_index]
                
                # Get screen geometry
                screen_geometry = target_screen.geometry()
                
                # If fullscreen, exit fullscreen first, move, then re-enter fullscreen
                was_fullscreen = self.isFullScreen()
                if was_fullscreen:
                    self.showNormal()
                
                # Move window to center of target screen
                window_size = self.size()
                new_x = screen_geometry.x() + (screen_geometry.width() - window_size.width()) // 2
                new_y = screen_geometry.y() + (screen_geometry.height() - window_size.height()) // 2
                
                self.move(new_x, new_y)
                
                # Re-enter fullscreen if it was fullscreen before
                if was_fullscreen:
                    self.showFullScreen()
                
                # Update icon to reflect current state
                self.update_fullscreen_icon()
                    
        except Exception as e:
            print(f"Error moving to monitor {monitor_index}: {e}")
    
    def export_to_csv(self):
        """Export acknowledgment data to CSV file (deprecated - use export_to_csv_from_settings)"""
        QMessageBox.information(self, "Feature Moved", 
                              "CSV export functionality has been moved to Settings.\nPlease use the ⚙️ Settings button.")
    
    def export_config_to_csv(self):
        """Export config data to CSV file (deprecated - use export_config_to_csv_from_settings)"""
        QMessageBox.information(self, "Feature Moved", 
                              "CSV export functionality has been moved to Settings.\nPlease use the ⚙️ Settings button.")
    
    def get_csv_folder_path(self):
        """Get the CSV folder path based on settings"""
        settings = self.load_settings()
        data_folder = settings.get('data_folder', '').strip()
        
        if not data_folder:
            return None
            
        csv_folder = os.path.join(data_folder, 'csv')
        return csv_folder
    
    def ensure_csv_folder_exists(self):
        """Ensure CSV folder exists, create if needed"""
        csv_folder = self.get_csv_folder_path()
        if not csv_folder:
            return False
            
        try:
            os.makedirs(csv_folder, exist_ok=True)
            return True
        except Exception:
            return False
    
    def export_to_csv_from_settings(self):
        """Export acknowledgment data to CSV in data folder and open Excel"""
        settings = self.load_settings()
        data_folder = settings.get('data_folder', '').strip()
        
        if not data_folder:
            QMessageBox.warning(self, "No Data Folder", 
                              "Please set a data folder in settings before exporting.")
            return
        
        if not self.ensure_csv_folder_exists():
            QMessageBox.critical(self, "Folder Error", 
                               "Could not create CSV folder in data directory.")
            return
        
        try:
            # Load acknowledgment data
            ack_path = self.get_acknowledgments_path()
            if not os.path.exists(ack_path):
                QMessageBox.information(self, "No Data", "No acknowledgment data found to export.")
                return
            
            with open(ack_path, 'r') as f:
                ack_data = json.load(f)
            
            if not ack_data:
                QMessageBox.information(self, "No Data", "No acknowledgment data found to export.")
                return
            
            # Generate filename with current date
            current_date = datetime.now().strftime("%d%m%Y")
            filename = f"manifest_ack-{current_date}.csv"
            csv_folder = self.get_csv_folder_path()
            file_path = os.path.join(csv_folder, filename)
            
            # Export CSV data
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['Date', 'Time', 'Carrier', 'User', 'Reason', 'Timestamp'])
                
                # Handle list format (correct format used by the system)
                if isinstance(ack_data, list):
                    for ack_item in ack_data:
                        if isinstance(ack_item, dict):
                            date = ack_item.get('date', '')
                            time = ack_item.get('manifest_time', '')
                            carrier = ack_item.get('carrier', '')
                            user = ack_item.get('user', '')
                            reason = ack_item.get('reason', '')
                            timestamp = ack_item.get('timestamp', '')
                            
                            writer.writerow([date, time, carrier, user, reason, timestamp])
                else:
                    # Handle old nested dictionary format for backward compatibility
                    for date_key, date_data in ack_data.items():
                        if isinstance(date_data, dict):
                            for time_key, time_data in date_data.items():
                                if isinstance(time_data, dict):
                                    user = time_data.get('user', '')
                                    reason = time_data.get('reason', '')
                                    timestamp = time_data.get('timestamp', '')
                                    
                                    writer.writerow([date_key, time_key, '', user, reason, timestamp])
            
            # Open in Excel
            self.open_file_in_excel(file_path)
            
            QMessageBox.information(self, "Export Complete", 
                                  f"Data exported successfully to:\n{file_path}\n\nOpening in Excel...")
            
        except PermissionError as e:
            QMessageBox.critical(self, "Export Error", 
                               f"Failed to export acknowledgment data:\n\n"
                               f"The file may be open in Excel or another program.\n"
                               f"Please close the file and try again.\n\n"
                               f"File: {file_path}\n"
                               f"Error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", 
                               f"Failed to export acknowledgment data:\n\n{str(e)}")
    
    def export_config_to_csv_from_settings(self):
        """Export config data to CSV in data folder and open Excel"""
        settings = self.load_settings()
        data_folder = settings.get('data_folder', '').strip()
        
        if not data_folder:
            QMessageBox.warning(self, "No Data Folder", 
                              "Please set a data folder in settings before exporting.")
            return
        
        if not self.ensure_csv_folder_exists():
            QMessageBox.critical(self, "Folder Error", 
                               "Could not create CSV folder in data directory.")
            return
        
        try:
            # Load config data
            config = self.load_config()
            
            if not config or not config.get('manifests'):
                QMessageBox.information(self, "No Data", "No manifest configuration data found to export.")
                return
            
            # Generate filename with current date
            current_date = datetime.now().strftime("%d%m%Y")
            filename = f"manifest_config-{current_date}.csv"
            csv_folder = self.get_csv_folder_path()
            file_path = os.path.join(csv_folder, filename)
            
            # Export in importable format
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header matching import format
                writer.writerow(['time', 'carriers'])
                
                # Write data rows in importable format
                manifests = config.get('manifests', [])
                for manifest in manifests:
                    time_slot = manifest.get('time', '')
                    carriers = manifest.get('carriers', [])
                    # Join carriers with semicolon for easy import parsing
                    carriers_str = ';'.join(carriers) if carriers else ''
                    
                    writer.writerow([time_slot, carriers_str])
            
            # Open in Excel
            self.open_file_in_excel(file_path)
            
            QMessageBox.information(self, "Export Complete", 
                                  f"Configuration exported successfully to:\n{file_path}\n\nFormat: time,carriers (semicolon-separated)\nThis file can be imported back into the system.\n\nOpening in Excel...")
            
        except PermissionError as e:
            QMessageBox.critical(self, "Export Error", 
                               f"Failed to export configuration data:\n\n"
                               f"The file may be open in Excel or another program.\n"
                               f"Please close the file and try again.\n\n"
                               f"File: {file_path}\n"
                               f"Error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", 
                               f"Failed to export configuration data:\n\n{str(e)}")
    
    def open_file_in_excel(self, file_path):
        """Open file in Excel or default CSV application"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            print(f"Could not open file in Excel: {e}")
    
    def open_csv_folder(self):
        """Open the CSV folder in file explorer"""
        csv_folder = self.get_csv_folder_path()
        
        if not csv_folder:
            QMessageBox.warning(self, "No Data Folder", 
                              "Please set a data folder in settings first.")
            return
        
        if not os.path.exists(csv_folder):
            if not self.ensure_csv_folder_exists():
                QMessageBox.critical(self, "Folder Error", 
                                   "Could not create CSV folder.")
                return
        
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(csv_folder)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', csv_folder])
            else:  # Linux
                subprocess.call(['xdg-open', csv_folder])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder:\n{str(e)}")
    
    def create_backup_config(self):
        """Create timestamped backup of current config"""
        try:
            settings = self.load_settings()
            data_folder = settings.get('data_folder', '').strip()
            
            if not data_folder:
                return False
            
            # Create backup folder if it doesn't exist
            backup_folder = os.path.join(data_folder, 'backup')
            os.makedirs(backup_folder, exist_ok=True)
            
            # Get current config path
            config_path = os.path.join(data_folder, 'config.json')
            if not os.path.exists(config_path):
                return False
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = os.path.join(backup_folder, backup_filename)
            
            # Copy file
            import shutil
            shutil.copy2(config_path, backup_path)
            
            return True
            
        except Exception as e:
            print(f"Backup creation failed: {e}")
            return False
    
    def import_config_from_csv(self):
        """Import configuration from CSV file with backup"""
        settings = self.load_settings()
        data_folder = settings.get('data_folder', '').strip()
        
        if not data_folder:
            QMessageBox.warning(self, "No Data Folder", 
                              "Please set a data folder in settings before importing.")
            return
        
        # Open file dialog in the CSV folder
        csv_folder = os.path.join(data_folder, 'csv')
        if not os.path.exists(csv_folder):
            csv_folder = data_folder  # Fallback to data folder
        
        # Get CSV file from user
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration",
            csv_folder,  # Start in CSV folder
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Create backup first
            if not self.create_backup_config():
                if not QMessageBox.question(self, "Backup Failed", 
                                           "Could not create backup. Continue with import?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    return
            
            # Read CSV file
            manifests = []
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Skip header
                next(reader, None)
                
                for row in reader:
                    if len(row) >= 2:
                        time_slot = row[0].strip()
                        carriers_str = row[1].strip()
                        
                        # Parse carriers (semicolon-separated)
                        if carriers_str:
                            carriers = [c.strip() for c in carriers_str.split(';') if c.strip()]
                        else:
                            carriers = []
                        
                        if time_slot and carriers:
                            manifests.append({
                                "time": time_slot,
                                "carriers": carriers
                            })
            
            if not manifests:
                QMessageBox.warning(self, "Import Error", "No valid manifest data found in CSV file.")
                return
            
            # Create new config
            new_config = {
                "manifests": manifests
            }
            
            # Save new config
            config_path = os.path.join(data_folder, 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2)
            
            # Refresh display
            self.populate_data()
            
            QMessageBox.information(self, "Import Complete", 
                                  f"Configuration imported successfully!\n\nImported {len(manifests)} manifest time slots.\nBackup created in backup folder.")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import configuration:\n{str(e)}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlertDisplay()
    window.show()
    sys.exit(app.exec())
