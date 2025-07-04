import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QFileDialog, QMessageBox,
                            QComboBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsManager:
    def __init__(self):
        # settings.json stays in app_data folder (default location)
        # but user can configure where config.json and acknowledgments.json are stored
        app_data_folder = os.path.join(os.path.dirname(__file__), 'app_data')
        self.settings_file = os.path.join(app_data_folder, 'settings.json')
        
        # Also read from main settings.json for monitor settings
        self.main_settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        
        self.default_settings = {
            'app_data_folder': app_data_folder,
            'ack_name': '',  # Custom acknowledgment name, empty means use Windows username
            'alarm_monitor': 0  # Monitor index for startup positioning
        }
        # Ensure app_data folder exists
        os.makedirs(app_data_folder, exist_ok=True)
        self.settings = self.load_settings()

    def load_settings(self):
        """Load settings from JSON file or create with defaults"""
        settings = self.default_settings.copy()
        
        # First load from app_data settings file
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Handle empty file
                        app_settings = json.loads(content)
                        settings.update(app_settings)
            except Exception as e:
                print(f"Error loading app settings: {e}")
        
        # Then load monitor setting from main settings.json
        if os.path.exists(self.main_settings_file):
            try:
                with open(self.main_settings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        main_settings = json.loads(content)
                        if 'alarm_monitor' in main_settings:
                            settings['alarm_monitor'] = main_settings['alarm_monitor']
            except Exception as e:
                print(f"Error loading main settings: {e}")
        
        # Ensure all required keys exist
        for key, value in self.default_settings.items():
            if key not in settings:
                settings[key] = value
                
        return settings
    
    def save_settings(self, settings=None):
        """Save settings to JSON file"""
        if settings is None:
            settings = self.settings
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.settings = settings
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_app_data_folder(self):
        """Get the configured app data folder path"""
        return self.settings.get('app_data_folder', self.default_settings['app_data_folder'])
    
    def get_data_folder(self):
        """Get the configured app data folder path (legacy compatibility)"""
        return self.get_app_data_folder()
    
    def get_logs_folder(self):
        """Get the configured app data folder path (legacy compatibility)"""
        return self.get_app_data_folder()
    
    def get_config_path(self):
        """Get the full path to config.json"""
        return os.path.join(self.get_app_data_folder(), 'config.json')
    
    def get_acknowledgments_path(self):
        """Get the full path to acknowledgments.json"""
        return os.path.join(self.get_app_data_folder(), 'acknowledgments.json')
    
    def set_app_data_folder(self, folder_path):
        """Set new app data folder path"""
        self.settings['app_data_folder'] = folder_path
        return self.save_settings()
    
    def get_ack_name(self):
        """Get the custom acknowledgment name"""
        return self.settings.get('ack_name', '')
    
    def set_ack_name(self, name):
        """Set custom acknowledgment name"""
        self.settings['ack_name'] = name.strip()
        return self.save_settings()
    
    def get_effective_ack_name(self):
        """Get the acknowledgment name to use (custom name or fallback to Windows username)"""
        import getpass
        custom_name = self.get_ack_name()
        return custom_name if custom_name else getpass.getuser()
    
    def get_alarm_monitor(self):
        """Get the alarm monitor index"""
        return self.settings.get('alarm_monitor', 0)
    
    def set_alarm_monitor(self, monitor_index):
        """Set the alarm monitor index"""
        self.settings['alarm_monitor'] = monitor_index
        
        # Save to both app settings and main settings
        app_saved = self.save_settings()
        main_saved = self.save_to_main_settings('alarm_monitor', monitor_index)
        
        return app_saved and main_saved
    
    def save_to_main_settings(self, key, value):
        """Save a specific setting to the main settings.json file"""
        try:
            # Load existing main settings
            main_settings = {}
            if os.path.exists(self.main_settings_file):
                with open(self.main_settings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        main_settings = json.loads(content)
            
            # Update the specific key
            main_settings[key] = value
            
            # Save back to main settings file
            with open(self.main_settings_file, 'w', encoding='utf-8') as f:
                json.dump(main_settings, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Error saving to main settings: {e}")
            return False

# Global settings manager instance
_settings_manager = None

def get_settings_manager():
    """Get the global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.resize(600, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Ensure dialog stays on top and maintains focus
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Application Settings")
        title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Configure application settings including data storage and acknowledgment name.")
        desc.setFont(QFont('Segoe UI', 10))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        layout.addSpacing(20)
        
        # Acknowledgment name setting
        ack_name_group = QVBoxLayout()
        ack_name_label = QLabel("👤 Acknowledgment Name:")
        ack_name_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        ack_name_group.addWidget(ack_name_label)
        
        ack_name_info = QLabel("Display name for acknowledgments (leave blank to use Windows username)")
        ack_name_info.setFont(QFont('Segoe UI', 9))
        ack_name_info.setStyleSheet("color: #666; margin-left: 10px;")
        ack_name_group.addWidget(ack_name_info)
        
        self.ack_name_edit = QLineEdit()
        self.ack_name_edit.setMaxLength(20)
        self.ack_name_edit.setPlaceholderText("Enter your name (optional)")
        ack_name_group.addWidget(self.ack_name_edit)
        
        layout.addLayout(ack_name_group)
        
        layout.addSpacing(15)
        
        # Monitor selection setting
        monitor_group = QVBoxLayout()
        monitor_label = QLabel("🖥️ Startup Monitor:")
        monitor_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        monitor_group.addWidget(monitor_label)
        
        monitor_info = QLabel("Select which monitor the alarm window should start on")
        monitor_info.setFont(QFont('Segoe UI', 9))
        monitor_info.setStyleSheet("color: #666; margin-left: 10px;")
        monitor_group.addWidget(monitor_info)
        
        self.monitor_combo = QComboBox()
        self.populate_monitor_list()
        monitor_group.addWidget(self.monitor_combo)
        
        layout.addLayout(monitor_group)
        
        layout.addSpacing(15)
        
        # App data folder setting
        app_data_group = QVBoxLayout()
        app_data_label = QLabel("📁 Data Storage Location:")
        app_data_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        app_data_group.addWidget(app_data_label)
        
        folder_info = QLabel("Contains: config.json, acknowledgments.json (for multi-PC sync, use shared folder)")
        folder_info.setFont(QFont('Segoe UI', 9))
        folder_info.setStyleSheet("color: #666; margin-left: 10px;")
        app_data_group.addWidget(folder_info)
        
        app_data_row = QHBoxLayout()
        self.app_data_path_edit = QLineEdit()
        self.app_data_path_edit.setPlaceholderText("Enter folder path or use Browse button")
        self.app_data_path_edit.textChanged.connect(self.validate_path_realtime)
        app_data_row.addWidget(self.app_data_path_edit)
        
        self.app_data_browse_btn = QPushButton("Browse...")
        self.app_data_browse_btn.clicked.connect(self.browse_app_data_folder)
        app_data_row.addWidget(self.app_data_browse_btn)
        
        # Path validation status label
        self.path_status_label = QLabel("")
        self.path_status_label.setFont(QFont('Segoe UI', 8))
        self.path_status_label.setWordWrap(True)
        
        app_data_group.addLayout(app_data_row)
        app_data_group.addWidget(self.path_status_label)
        layout.addLayout(app_data_group)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def populate_monitor_list(self):
        """Populate the monitor combo box with available monitors"""
        from PyQt6.QtGui import QGuiApplication
        
        self.monitor_combo.clear()
        screens = QGuiApplication.screens()
        
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            # Get screen name/model if available
            screen_name = screen.name() if hasattr(screen, 'name') else f"Monitor {i + 1}"
            resolution = f"{geometry.width()}x{geometry.height()}"
            
            # Create descriptive text
            if i == 0:
                display_text = f"Monitor {i + 1} (Primary) - {screen_name} ({resolution})"
            else:
                display_text = f"Monitor {i + 1} - {screen_name} ({resolution})"
                
            self.monitor_combo.addItem(display_text, i)
        
        if len(screens) == 1:
            self.monitor_combo.addItem("Only one monitor detected", 0)
            self.monitor_combo.setEnabled(False)
        else:
            self.monitor_combo.setEnabled(True)
    
    def load_current_settings(self):
        """Load current settings into the UI"""
        self.ack_name_edit.setText(self.settings_manager.get_ack_name())
        self.app_data_path_edit.setText(self.settings_manager.get_app_data_folder())
        
        # Set monitor selection
        current_monitor = self.settings_manager.get_alarm_monitor()
        # Find the combo box item with matching monitor index
        for i in range(self.monitor_combo.count()):
            if self.monitor_combo.itemData(i) == current_monitor:
                self.monitor_combo.setCurrentIndex(i)
                break
        
        # Trigger initial path validation
        self.validate_path_realtime()
    
    def browse_app_data_folder(self):
        """Browse for app data folder"""
        current_path = self.app_data_path_edit.text().strip()
        if not current_path:
            current_path = os.path.expanduser("~")
        
        # Create file dialog with proper focus handling
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Application Data Folder")
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setDirectory(current_path)
        
        # Ensure dialog stays on top and maintains focus
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        dialog.activateWindow()
        dialog.raise_()
        
        if dialog.exec_() == QFileDialog.Accepted:
            selected_folders = dialog.selectedFiles()
            if selected_folders:
                folder = selected_folders[0]
                self.app_data_path_edit.setText(folder)
                self.validate_path_realtime()
    
    def validate_path_realtime(self):
        """Real-time path validation as user types"""
        path = self.app_data_path_edit.text().strip()
        
        if not path:
            self.path_status_label.setText("")
            self.path_status_label.setStyleSheet("")
            return
        
        # Expand environment variables and relative paths
        expanded_path = os.path.expandvars(os.path.expanduser(path))
        
        if os.path.exists(expanded_path):
            if os.path.isdir(expanded_path):
                # Test write access
                test_file = os.path.join(expanded_path, 'test_write.tmp')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    self.path_status_label.setText("✅ Valid folder with write access")
                    self.path_status_label.setStyleSheet("color: green; margin-left: 10px;")
                except Exception:
                    self.path_status_label.setText("❌ Folder exists but no write access")
                    self.path_status_label.setStyleSheet("color: red; margin-left: 10px;")
            else:
                self.path_status_label.setText("❌ Path exists but is not a folder")
                self.path_status_label.setStyleSheet("color: red; margin-left: 10px;")
        else:
            # Check if parent directory exists (for creation)
            parent_dir = os.path.dirname(expanded_path)
            if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
                self.path_status_label.setText("⚠️ Folder will be created (parent exists)")
                self.path_status_label.setStyleSheet("color: orange; margin-left: 10px;")
            else:
                self.path_status_label.setText("❌ Invalid path or parent directory missing")
                self.path_status_label.setStyleSheet("color: red; margin-left: 10px;")
    
    def reset_to_defaults(self):
        """Reset path to default values"""
        self.ack_name_edit.setText(self.settings_manager.default_settings['ack_name'])
        self.app_data_path_edit.setText(self.settings_manager.default_settings['app_data_folder'])
        
        # Reset monitor to default (0 - primary monitor)
        default_monitor = self.settings_manager.default_settings['alarm_monitor']
        for i in range(self.monitor_combo.count()):
            if self.monitor_combo.itemData(i) == default_monitor:
                self.monitor_combo.setCurrentIndex(i)
                break
        
        # Trigger path validation after reset
        self.validate_path_realtime()
    
    def validate_paths(self):
        """Validate that the selected path is writable"""
        app_data_path = self.app_data_path_edit.text().strip()
        
        if not app_data_path:
            QMessageBox.warning(self, "Invalid Path", "Please enter a valid folder path.")
            return False
        
        # Expand environment variables and relative paths
        expanded_path = os.path.expandvars(os.path.expanduser(app_data_path))
        
        # Check if path exists and is writable
        if not os.path.exists(expanded_path):
            reply = QMessageBox.question(
                self, 
                "Create Folder?", 
                f"Application data folder does not exist:\n{expanded_path}\n\nCreate it now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(expanded_path, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create application data folder:\n{e}")
                    return False
            else:
                return False
        
        # Test write access
        test_file = os.path.join(expanded_path, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Application data folder is not writable:\n{expanded_path}\n\n{e}")
            return False
        
        # Update the text field with the expanded path
        if expanded_path != app_data_path:
            self.app_data_path_edit.setText(expanded_path)
        
        return True
    
    def save_settings(self):
        """Save the settings and close dialog"""
        if not self.validate_paths():
            return
        
        ack_name = self.ack_name_edit.text().strip()
        app_data_path = self.app_data_path_edit.text().strip()
        
        # Get selected monitor index
        selected_monitor = self.monitor_combo.currentData()
        if selected_monitor is None:
            selected_monitor = 0  # Default to primary monitor
        
        # Save settings
        if not self.settings_manager.set_ack_name(ack_name):
            QMessageBox.critical(self, "Error", "Failed to save acknowledgment name setting")
            return
            
        if not self.settings_manager.set_app_data_folder(app_data_path):
            QMessageBox.critical(self, "Error", "Failed to save application data folder setting")
            return
        
        if not self.settings_manager.set_alarm_monitor(selected_monitor):
            QMessageBox.critical(self, "Error", "Failed to save monitor setting")
            return
        
        # Show success message
        effective_name = self.settings_manager.get_effective_ack_name()
        monitor_text = self.monitor_combo.currentText()
        QMessageBox.information(
            self, 
            "Settings Saved", 
            f"Settings have been updated successfully!\n\n"
            f"Acknowledgment name: {effective_name}\n"
            f"Data storage location: {app_data_path}\n"
            f"Startup monitor: {monitor_text}\n\n"
            "Monitor changes will take effect on next application restart."
        )
        
        self.accept()