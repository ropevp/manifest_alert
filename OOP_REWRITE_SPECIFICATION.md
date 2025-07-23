# Manifest Alert System - OOP Rewrite Specification

## Overview
This document provides a comprehensive specification for rewriting the manifest alert system from a 2910-line monolithic application into a clean Object-Oriented Python architecture. The rewrite preserves ALL existing functionality while implementing proper separation of concerns, maintainable design patterns, and scalable architecture.

## Current System Analysis

### Existing Features Inventory
The current `alert_display.py` implements the following features in a single AlertDisplay class:

#### Core Alert Functionality
- **Manifest Time Tracking**: Monitors configured time slots (07:00, 11:00, 12:30, etc.)
- **Carrier Management**: Multiple carriers per time slot (Australia Post Metro, EParcel Express, DHL Express, etc.)
- **Real-time Status Cards**: Visual display of current/upcoming manifests with countdown timers
- **Alert Triggering**: Automatic alerts when manifest times are reached
- **Sound Management**: Audio alerts with volume control and timing
- **Background Flashing**: Visual alarm indication with customizable timing

#### Multi-Monitor & Display
- **Fullscreen Mode**: Toggle between windowed and fullscreen display
- **Multi-Monitor Support**: Detect and move application between monitors
- **TV Fullscreen Timer**: Automatic fullscreen activation on designated monitors
- **Monitor Selection Menu**: Dynamic menu for monitor switching
- **Alert Screen Positioning**: Ensure alerts appear on correct monitor

#### Mute & Snooze System
- **Centralized Mute Manager**: Network-shared mute status via `\\Prddpkmitlgt004\ManifestPC\`
- **Multi-PC Synchronization**: Mute status shared across multiple computers
- **Snooze Functionality**: 5-minute temporary mute with auto-resume
- **Snooze Countdown**: Visual countdown timer display
- **Mute Status Caching**: Performance optimization with 30s network cache and 5s fast cache

#### Individual Acknowledgments
- **Per-Carrier Acknowledgment**: Individual acknowledgment of specific carriers
- **User Tracking**: Record which user acknowledged each carrier
- **Reason Selection**: Optional reason for acknowledgment (dropdown with presets)
- **Timestamp Recording**: Precise timestamp for each acknowledgment
- **Visual Status Indicators**: Color-coded display of acknowledgment status

#### Settings Management
- **Settings Dialog**: Comprehensive configuration interface
- **Data Folder Configuration**: Custom path for data files
- **Volume Control**: Audio volume adjustment
- **Alert Timing Settings**: Configurable flash timing and intervals
- **Monitor Preferences**: Default monitor selection
- **User Interface Preferences**: Various UI customization options

#### Data Import/Export
- **CSV Export**: Export acknowledgment data to CSV format
- **Config Export**: Export configuration to CSV
- **CSV Import**: Import configuration from CSV files
- **Backup Creation**: Automatic backups before imports
- **Data Validation**: Validate imported data integrity

#### Multi-User Support
- **User Identification**: Track which user performs actions
- **Concurrent Access**: Multiple users can acknowledge different carriers
- **User-specific Preferences**: Per-user settings capability
- **Action Logging**: Complete audit trail of user actions

#### Performance Features
- **Aggressive Caching**: 30-second network cache, 5-second UI cache
- **Timeout Protection**: 1-second timeout on network operations
- **Non-blocking Operations**: Threading for network calls
- **UI Responsiveness**: Prevent UI blocking during file operations

#### Enhanced Alert Display
- **Single Alert Scaling**: When only one active alert exists (no missed alerts), the alert card scales to maximum size
- **Transparent Card Backgrounds**: Alert cards use transparent backgrounds during active alerts to show red flashing through
- **Dynamic Layout Switching**: Automatic layout changes between normal grid and single-card maximized views
- **Emphasis on Active Alerts**: Visual enhancement makes single critical alerts more prominent and visible

## Target OOP Architecture

### Domain Layer (Business Logic)
```
domain/
├── models/
│   ├── manifest.py          # Manifest time slot with carriers
│   ├── carrier.py           # Individual carrier entity
│   ├── acknowledgment.py    # Individual acknowledgment record
│   ├── alert.py            # Alert state and timing
│   ├── user.py             # User entity and preferences
│   └── settings.py         # Application settings model
├── services/
│   ├── alert_service.py     # Core alert logic and timing
│   ├── mute_service.py      # Mute/snooze management
│   ├── acknowledgment_service.py  # Acknowledgment business logic
│   └── time_service.py      # Time calculation and scheduling
└── repositories/
    ├── manifest_repository.py     # Manifest data access
    ├── acknowledgment_repository.py # Acknowledgment data access
    ├── settings_repository.py     # Settings persistence
    └── mute_repository.py         # Mute status data access
```

### Infrastructure Layer (Data & External Services)
```
infrastructure/
├── persistence/
│   ├── json_file_manager.py     # JSON file operations
│   ├── csv_manager.py           # CSV import/export
│   ├── network_file_manager.py  # Network file access with caching
│   └── backup_manager.py        # Backup creation and management
├── audio/
│   ├── sound_player.py          # Audio playback management
│   └── volume_controller.py     # Volume control
├── display/
│   ├── monitor_manager.py       # Multi-monitor detection and management
│   └── fullscreen_manager.py    # Fullscreen mode handling
└── caching/
    ├── cache_manager.py         # Generic caching framework
    ├── network_cache.py         # Network operation caching
    └── ui_cache.py             # UI state caching
```

### Application Layer (Use Cases)
```
application/
├── use_cases/
│   ├── manage_alerts.py         # Alert management use cases
│   ├── handle_acknowledgments.py # Acknowledgment workflows
│   ├── manage_settings.py       # Settings management
│   ├── import_export_data.py    # Data import/export operations
│   ├── manage_display.py        # Display and monitor management
│   └── manage_ui_layout.py      # Dynamic UI layout management for single alert scaling
└── dto/
    ├── alert_dto.py            # Data transfer objects
    ├── acknowledgment_dto.py
    ├── settings_dto.py
    └── layout_dto.py           # Layout state and configuration data
```

### Presentation Layer (UI)
```
presentation/
├── main_window.py              # Main application window
├── components/
│   ├── status_card.py          # Individual manifest status card
│   ├── alert_display.py        # Alert visualization component
│   ├── mute_button.py          # Mute/snooze controls
│   ├── settings_dialog.py      # Settings configuration dialog
│   ├── acknowledgment_panel.py # Individual acknowledgment controls
│   └── countdown_timer.py      # Timer display component
├── controllers/
│   ├── main_controller.py      # Main application controller
│   ├── alert_controller.py     # Alert handling controller
│   ├── settings_controller.py  # Settings management controller
│   └── display_controller.py   # Display and monitor controller
└── utils/
    ├── ui_helpers.py           # UI utility functions
    └── styling.py              # Style constants and themes
```

## Key Design Patterns

### Repository Pattern
- Abstract data access behind repository interfaces
- Concrete implementations for JSON files, network files, CSV
- Enable easy testing with mock repositories

### Service Layer Pattern
- Business logic isolated in service classes
- Services coordinate between repositories and domain models
- Clear separation of concerns

### Observer Pattern
- UI components observe domain model changes
- Loose coupling between business logic and presentation
- Event-driven updates for real-time synchronization

### Strategy Pattern
- Different mute strategies (local, network, centralized)
- Multiple audio playback strategies
- Configurable acknowledgment workflows

### Command Pattern
- User actions as command objects
- Undo/redo capability for future enhancements
- Action logging and audit trails

## Data Models

### Manifest Model
```python
@dataclass
class Manifest:
    time: datetime.time
    carriers: List[Carrier]
    date: datetime.date = field(default_factory=datetime.date.today)
    
    def is_current_time_window(self) -> bool:
        """Check if current time is within alert window"""
        
    def get_pending_carriers(self) -> List[Carrier]:
        """Get carriers not yet acknowledged"""
```

### Carrier Model
```python
@dataclass
class Carrier:
    name: str
    manifest_time: datetime.time
    acknowledgments: List[Acknowledgment] = field(default_factory=list)
    
    def is_acknowledged_today(self) -> bool:
        """Check if acknowledged for today"""
        
    def get_latest_acknowledgment(self) -> Optional[Acknowledgment]:
        """Get most recent acknowledgment"""
```

### Acknowledgment Model
```python
@dataclass
class Acknowledgment:
    carrier_name: str
    user: str
    timestamp: datetime.datetime
    reason: str = ""
    manifest_time: datetime.time
    date: datetime.date
```

### Alert Model
```python
@dataclass
class Alert:
    manifest: Manifest
    triggered_at: datetime.datetime
    is_active: bool = True
    flash_state: bool = False
    sound_enabled: bool = True
    
    def should_flash(self) -> bool:
        """Determine if alert should flash"""
        
    def get_pending_count(self) -> int:
        """Count unacknowledged carriers"""
        
    def is_missed(self) -> bool:
        """Check if this alert represents a missed manifest (past deadline)"""
        current_time = datetime.now().time()
        deadline = (datetime.combine(datetime.now().date(), self.manifest.time) + 
                   timedelta(minutes=30)).time()
        return current_time > deadline and self.get_pending_count() > 0
        
    def has_active_carriers(self) -> bool:
        """Check if alert has carriers that need immediate attention"""
        return self.is_active and not self.is_missed() and self.get_pending_count() > 0
```

## Service Layer Implementation

### AlertService
```python
class AlertService:
    def __init__(self, manifest_repo: ManifestRepository, 
                 time_service: TimeService, 
                 mute_service: MuteService):
        self.manifest_repo = manifest_repo
        self.time_service = time_service
        self.mute_service = mute_service
    
    def get_current_alerts(self) -> List[Alert]:
        """Get all currently active alerts"""
        
    def check_for_new_alerts(self) -> List[Alert]:
        """Check if any new alerts should be triggered"""
        
    def update_alert_states(self) -> None:
        """Update flash states and timing for active alerts"""
        
    def should_use_single_card_mode(self, alerts: List[Alert]) -> bool:
        """Determine if single card scaling should be used"""
        active_alerts = [a for a in alerts if a.is_active and not a.is_missed()]
        missed_alerts = [a for a in alerts if a.is_missed()]
        
        # Use single card mode when exactly one active alert and no missed alerts
        return len(active_alerts) == 1 and len(missed_alerts) == 0
        
    def get_single_card_alert(self, alerts: List[Alert]) -> Optional[Alert]:
        """Get the alert that should be displayed in single card mode"""
        if self.should_use_single_card_mode(alerts):
            active_alerts = [a for a in alerts if a.is_active and not a.is_missed()]
            return active_alerts[0] if active_alerts else None
        return None
```

### MuteService
```python
class MuteService:
    def __init__(self, mute_repo: MuteRepository, cache_manager: CacheManager):
        self.mute_repo = mute_repo
        self.cache_manager = cache_manager
    
    def is_muted(self) -> bool:
        """Check if system is currently muted (with caching)"""
        
    def mute_for_duration(self, minutes: int) -> None:
        """Mute system for specified duration"""
        
    def toggle_mute(self) -> bool:
        """Toggle mute state, return new state"""
        
    def get_snooze_remaining(self) -> Optional[timedelta]:
        """Get remaining snooze time if active"""
```

### AcknowledgmentService
```python
class AcknowledgmentService:
    def __init__(self, ack_repo: AcknowledgmentRepository):
        self.ack_repo = ack_repo
    
    def acknowledge_carrier(self, carrier: str, user: str, 
                          reason: str = "") -> Acknowledgment:
        """Acknowledge a specific carrier"""
        
    def get_todays_acknowledgments(self) -> List[Acknowledgment]:
        """Get all acknowledgments for today"""
        
    def bulk_acknowledge(self, carriers: List[str], 
                        user: str, reason: str = "") -> List[Acknowledgment]:
        """Acknowledge multiple carriers at once"""
```

## UI Layout Management

### Dynamic Layout Service
```python
class UILayoutService:
    def __init__(self, alert_service: AlertService):
        self.alert_service = alert_service
    
    def determine_layout_mode(self, alerts: List[Alert]) -> LayoutMode:
        """Determine if single card or normal grid layout should be used"""
        active_alerts = [a for a in alerts if a.has_active_carriers()]
        missed_alerts = [a for a in alerts if a.is_missed()]
        
        # Single card mode: exactly one active alert and no missed alerts
        if len(active_alerts) == 1 and len(missed_alerts) == 0:
            return LayoutMode.SINGLE_CARD
        else:
            return LayoutMode.NORMAL_GRID
    
    def get_enhanced_alert(self, alerts: List[Alert]) -> Optional[Alert]:
        """Get the alert that should be enhanced in single card mode"""
        if self.determine_layout_mode(alerts) == LayoutMode.SINGLE_CARD:
            active_alerts = [a for a in alerts if a.has_active_carriers()]
            return active_alerts[0] if active_alerts else None
        return None
    
    def calculate_card_properties(self, alert: Alert, layout_mode: LayoutMode) -> CardProperties:
        """Calculate visual properties for a status card"""
        if layout_mode == LayoutMode.SINGLE_CARD and self.get_enhanced_alert([alert]) == alert:
            return CardProperties(
                height=400,
                font_size=36,
                background_style="transparent",
                border_width=3,
                spacing=20
            )
        else:
            return CardProperties(
                height=80,
                font_size=28,
                background_style="normal",
                border_width=1,
                spacing=10
            )
```

### Layout Data Models
```python
from enum import Enum

class LayoutMode(Enum):
    NORMAL_GRID = "normal_grid"
    SINGLE_CARD = "single_card"

@dataclass
class CardProperties:
    height: int
    font_size: int
    background_style: str
    border_width: int
    spacing: int
    
@dataclass
class LayoutState:
    mode: LayoutMode
    enhanced_alert_id: Optional[str]
    total_cards: int
    active_cards: int
    missed_cards: int
```

## UI Design & Layout Specification

### Overall Application Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ Header Bar: Title, Controls, Clock                              │
├─────────────────────────────────────────────────────────────────┤
│ Status Summary Bar: System Status Message                       │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Scrollable Cards Area                                       │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ StatusCard: Time + Status | Carriers | Acknowledgments  │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ StatusCard: Time + Status | Carriers | Acknowledgments  │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Header Bar Layout (Fixed Height: 80px)
```
┌──────────┬─────────┬─────────┬─────────┬─────────┬──────────────┐
│ MANIFEST │ Monitor │ Full    │ Settings│ Mute/   │ Digital Clock│
│ ALERTS   │ Select  │ Screen  │         │ Snooze  │ HH:MM:SS     │
│ (Title)  │ Button  │ Button  │ Button  │ Button  │              │
└──────────┴─────────┴─────────┴─────────┴─────────┴──────────────┘
```

### Status Summary Bar (Dynamic Height: 50-60px)
- **Purpose**: System-wide status message
- **Background Colors**:
  - Green (#2ed573): "SYSTEM NOMINAL"
  - Red (#ff4757): "ACTIVE ALERTS"
  - Purple (#c44569): "MISSED MANIFESTS"
  - Blue (#3742fa): "Next manifest in XX:XX"

### StatusCard Layout Specifications

#### Normal Mode Card (Height: 80px, Width: 1200px)
```
┌─────────────┬──────────────────────────────────────────┬─────────────┐
│ Time+Status │ Carriers Section                         │ Ack Section │
│ 07:00-ACTIVE│ • Australia Post Metro                   │ [User Names]│
│ (280px)     │ • EParcel Express                        │ (200px)     │
│             │ • EParcel Postplus                       │             │
└─────────────┴──────────────────────────────────────────┴─────────────┘
```

#### Single Alert Mode Card (Height: 400px, Width: 1200px)
```
┌─────────────┬──────────────────────────────────────────┬─────────────┐
│             │                                          │             │
│ Time+Status │ Carriers Section                         │ Ack Section │
│ 07:00-ACTIVE│ • Australia Post Metro                   │ [User Names]│
│ (280px)     │ • EParcel Express                        │ (200px)     │
│             │ • EParcel Postplus                       │             │
│             │                                          │             │
│             │ (Larger fonts, more spacing)             │             │
└─────────────┴──────────────────────────────────────────┴─────────────┘
```

### Typography Specifications

#### Header Elements
- **Application Title**: "MANIFEST ALERTS"
  - Font: Segoe UI, 24px, Bold
  - Color: #ffffff (white)
  - Position: Left-aligned in header

- **Digital Clock**: HH:MM:SS format
  - Font: DS-Digital, 42px, Bold (7-segment display style)
  - Color: #FFD700 (golden yellow)
  - Text Shadow: 0px 0px 5px #B8860B
  - Position: Right-aligned in header

#### StatusCard Typography

##### Normal Mode
- **Time + Status Label**: "07:00 - ACTIVE"
  - Font: Segoe UI, 28px, Bold
  - Width: 280px (fixed for alignment)
  - Colors by Status:
    - OPEN: #ffffff (white)
    - ACTIVE: #ff4757 (red)
    - MISSED: #c44569 (dark red)
    - DONE: #2ed573 (green)

- **Carrier Names**: Bullet list format
  - Font: Segoe UI, 22px, Normal (current implementation)
  - Colors by Status:
    - Normal: #ffffff (white)
    - Acknowledged: #2ed573 (green)
    - Late Acknowledgment: #ffb347 (orange)
    - Active/Pending: #ff4757 (red)

- **Acknowledgment Labels**: User names
  - Font: Segoe UI, 14px, Normal
  - Colors:
    - Normal: #2ed573 (green)
    - Late: #ffb347 (orange)

##### Single Alert Mode (Enhanced Scaling)
- **Time + Status Label**: "07:00 - ACTIVE"
  - Font: Segoe UI, 36px, Bold (increased from 28px)
  - Width: 280px (maintained for consistency)

- **Carrier Names**: Bullet list format
  - Font: Segoe UI, 28px, Normal (increased from 22px)
  - Enhanced spacing between items

- **Acknowledgment Labels**: User names
  - Font: Segoe UI, 18px, Normal (increased from 14px)

### Color Palette

#### Background Colors
- **Application Background**: #1a1a2e (dark navy)
- **Header Background**: #16213e (darker navy)
- **Card Normal Background**: Gradient from #2c2c54 to #40407a
- **Card Enhanced Background**: Transparent (for flash visibility)

#### Alert Flash Colors
- **Flash State ON**: #ff0000 (pure red)
- **Flash State OFF**: #000000 (pure black)
- **Flash Timing**: 100-500ms intervals, 3 cycles with 2-second pause

#### Status Colors
- **Active**: #ff4757 (bright red)
- **Missed**: #c44569 (dark red/maroon)
- **Acknowledged**: #2ed573 (green)
- **Late Acknowledged**: #ffb347 (orange)
- **Open/Pending**: #ffffff (white)

#### Button Colors
- **Normal State**: #2c2c54 background, #3742fa border
- **Hover State**: #3742fa background
- **Pressed State**: #1f2ecc background
- **Text Color**: #ffffff (white)

### Spacing and Margins

#### Card Layout Spacing
- **Card Margins**: 10px top/bottom, 10px left/right
- **Card Spacing**: 4px between cards (vertical)
- **Internal Padding**: 
  - Normal mode: 10px horizontal, 3px vertical
  - Enhanced mode: 15px horizontal, 10px vertical

#### Section Spacing
- **Between Sections**: 15px horizontal spacing
- **Header Height**: 80px
- **Summary Bar Height**: 50px (normal), 60px (with countdown)

#### Element Alignment
- **Time Section**: Left-aligned, fixed 280px width
- **Carriers Section**: Left-aligned, flexible width (remaining space)
- **Acknowledgment Section**: Right-aligned, fixed 200px width

### Interactive Elements

#### Clickable Areas
- **Time Header**: Double-click to acknowledge all carriers in time slot
- **Individual Carriers**: Click to acknowledge single carrier
- **Buttons**: Standard button hover/press states

#### Hover Effects
- **Time Header**: 
  - Background: rgba(55, 66, 250, 0.3) (blue overlay)
  - Cursor: pointer
- **Carrier Labels**: 
  - Background: rgba(255, 255, 255, 0.1) (white overlay)
  - Cursor: pointer

### Responsive Behavior

#### Window Sizing
- **Minimum Size**: 1200px width × 800px height
- **Fullscreen**: Scales to full monitor resolution
- **Multi-Monitor**: Remembers last position per monitor

#### Card Scaling Logic
- **Normal Grid Mode**: All cards 80px height, standard fonts
- **Single Alert Mode**: Enhanced card 400px height, larger fonts
- **Transition**: Smooth height animation over 200ms

### Accessibility Features

#### Visual Accessibility
- **High Contrast**: Strong color differentiation
- **Font Sizes**: Minimum 14px for readability
- **Color Coding**: Consistent color meanings throughout
- **Flash Alerts**: High contrast red/black flashing for visibility

#### Keyboard Navigation
- **Tab Order**: Header buttons → card elements → scroll area
- **Space/Enter**: Activate focused elements
- **Arrow Keys**: Navigate between cards

### Animation Specifications

#### Flash Animation
- **Timing**: Random 100-500ms intervals for intensity
- **Pattern**: 3 flash cycles, 2-second pause, repeat
- **Colors**: Pure red (#ff0000) to pure black (#000000)
- **Scope**: Application background during alerts

#### Layout Transitions
- **Card Scaling**: 200ms ease-in-out animation
- **Font Changes**: Instant (no animation needed)
- **Background Changes**: Instant transition to transparent

### Print/Export Layout
- **Card Representation**: Maintain visual hierarchy
- **Color Mapping**: Status colors preserved
- **Font Scaling**: Proportional scaling for different media

## UI Component Architecture

### StatusCard Component
```python
class StatusCard(QWidget):
    """Individual manifest status display with dynamic scaling"""
    acknowledgment_requested = pyqtSignal(str, str)  # carrier, user
    
    def __init__(self, manifest: Manifest):
        super().__init__()
        self.manifest = manifest
        self.is_maximized = False
        self.setup_ui()
        
    def update_display(self, manifest: Manifest) -> None:
        """Update display with new manifest data"""
        
    def set_flash_state(self, flashing: bool) -> None:
        """Set visual flash state for alerts"""
        
    def set_maximized_mode(self, maximized: bool) -> None:
        """Scale card for single alert emphasis"""
        self.is_maximized = maximized
        if maximized:
            self.setStyleSheet("background: transparent;")  # Remove background for flash visibility
            self.setMinimumHeight(400)  # Larger height for prominence
        else:
            self.setStyleSheet("")  # Normal background
            self.setMinimumHeight(80)   # Normal height
```

### MuteButton Component
```python
class MuteButton(QPushButton):
    """Mute/snooze control with countdown display"""
    mute_toggled = pyqtSignal(bool)  # new mute state
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.timer = QTimer()
        
    def update_countdown(self, remaining: Optional[timedelta]) -> None:
        """Update countdown display"""
        
    def set_mute_state(self, muted: bool) -> None:
        """Update button state based on mute status"""
```

## Error Handling & Logging

### Exception Hierarchy
```python
class ManifestAlertException(Exception):
    """Base exception for all manifest alert system errors"""
    pass

class NetworkAccessException(ManifestAlertException):
    """Raised when network file operations fail"""
    pass

class DataValidationException(ManifestAlertException):
    """Raised when data validation fails"""
    pass

class ConfigurationException(ManifestAlertException):
    """Raised when configuration is invalid or missing"""
    pass

class AudioException(ManifestAlertException):
    """Raised when audio operations fail"""
    pass

class DisplayException(ManifestAlertException):
    """Raised when display/monitor operations fail"""
    pass
```

### Logging Framework
```python
import logging
from typing import Optional
from datetime import datetime

class ManifestLogger:
    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.setup_logging(log_level)
    
    def setup_logging(self, log_level: str):
        """Configure logging with file and console handlers"""
        # File handler for persistent logging
        file_handler = logging.FileHandler("manifest_alerts.log")
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(getattr(logging, log_level.upper()))
    
    def log_network_operation(self, operation: str, path: str, success: bool, duration: float):
        """Log network file operations with performance metrics"""
        if success:
            self.logger.info(f"Network {operation} successful: {path} ({duration:.2f}s)")
        else:
            self.logger.error(f"Network {operation} failed: {path} ({duration:.2f}s)")
    
    def log_user_action(self, user: str, action: str, details: dict):
        """Log user actions for audit trail"""
        self.logger.info(f"User {user} performed {action}: {details}")
    
    def log_system_state(self, component: str, state: str, context: dict):
        """Log system state changes"""
        self.logger.info(f"{component} state changed to {state}: {context}")
```

### Input Validation for CSV Imports
```python
class CSVValidator:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
    
    def validate_manifest_csv(self, file_path: str) -> tuple[bool, list[str]]:
        """Validate manifest CSV file structure and content"""
        errors = []
        
        try:
            # Check file accessibility
            if not os.path.exists(file_path):
                errors.append(f"File does not exist: {file_path}")
                return False, errors
            
            # Check file size (prevent memory exhaustion)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                errors.append(f"File too large: {file_size} bytes (max 10MB)")
                return False, errors
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Validate header
                try:
                    header = next(reader)
                    if len(header) < 2:
                        errors.append("CSV must have at least 2 columns (Time, Carriers)")
                except StopIteration:
                    errors.append("CSV file is empty")
                    return False, errors
                
                # Validate data rows
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    row_count += 1
                    
                    # Limit number of rows to prevent DoS
                    if row_count > 1000:
                        errors.append("Too many rows (max 1000)")
                        break
                    
                    if len(row) < 2:
                        errors.append(f"Row {row_num}: Missing required columns")
                        continue
                    
                    # Validate time format
                    time_str = row[0].strip()
                    if not self.validate_time_format(time_str):
                        errors.append(f"Row {row_num}: Invalid time format '{time_str}' (expected HH:MM)")
                    
                    # Validate carriers
                    carriers_str = row[1].strip()
                    if not carriers_str:
                        errors.append(f"Row {row_num}: Empty carriers list")
                    else:
                        carriers = [c.strip() for c in carriers_str.split(';')]
                        for carrier in carriers:
                            if not self.validate_carrier_name(carrier):
                                errors.append(f"Row {row_num}: Invalid carrier name '{carrier}'")
            
            self.logger.log_system_state("CSV_Validation", "completed", {
                "file": file_path,
                "errors": len(errors),
                "rows": row_count
            })
            
            return len(errors) == 0, errors
            
        except Exception as e:
            error_msg = f"CSV validation failed: {str(e)}"
            errors.append(error_msg)
            self.logger.logger.error(error_msg)
            return False, errors
    
    def validate_time_format(self, time_str: str) -> bool:
        """Validate time string is in HH:MM format"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    def validate_carrier_name(self, carrier: str) -> bool:
        """Validate carrier name contains only allowed characters"""
        if len(carrier) == 0 or len(carrier) > 100:
            return False
        
        # Allow alphanumeric, spaces, hyphens, and common punctuation
        import re
        return bool(re.match(r'^[a-zA-Z0-9\s\-\.\&\(\)]+$', carrier))
```

### Error Recovery Mechanisms
```python
class ErrorRecoveryManager:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.recovery_strategies = {
            NetworkAccessException: self.recover_network_access,
            DataValidationException: self.recover_data_validation,
            ConfigurationException: self.recover_configuration,
            AudioException: self.recover_audio,
        }
    
    def handle_error(self, exception: Exception, context: dict) -> bool:
        """Handle error with appropriate recovery strategy"""
        exception_type = type(exception)
        
        if exception_type in self.recovery_strategies:
            try:
                return self.recovery_strategies[exception_type](exception, context)
            except Exception as recovery_error:
                self.logger.logger.error(f"Recovery failed: {recovery_error}")
                return False
        else:
            self.logger.logger.error(f"No recovery strategy for {exception_type}: {exception}")
            return False
    
    def recover_network_access(self, exception: NetworkAccessException, context: dict) -> bool:
        """Attempt to recover from network access failures"""
        # Fall back to local cache if available
        if 'cache_manager' in context and 'cache_key' in context:
            cached_data = context['cache_manager'].get_cached_data(context['cache_key'])
            if cached_data is not None:
                self.logger.logger.warning("Using cached data due to network failure")
                return True
        
        # Try alternative network paths if configured
        if 'alternative_paths' in context:
            for alt_path in context['alternative_paths']:
                try:
                    # Attempt to access alternative path
                    if os.path.exists(alt_path):
                        self.logger.logger.info(f"Using alternative path: {alt_path}")
                        return True
                except:
                    continue
        
        return False
    
    def recover_data_validation(self, exception: DataValidationException, context: dict) -> bool:
        """Attempt to recover from data validation failures"""
        # Load default configuration
        if 'config_manager' in context:
            try:
                context['config_manager'].load_default_config()
                self.logger.logger.warning("Loaded default configuration due to validation failure")
                return True
            except:
                pass
        
        return False
    
    def recover_configuration(self, exception: ConfigurationException, context: dict) -> bool:
        """Attempt to recover from configuration failures"""
        # Create minimal working configuration
        try:
            default_config = {
                "manifests": [],
                "settings": {
                    "volume": 0.5,
                    "flash_interval": 500,
                    "data_folder": ""
                }
            }
            
            if 'config_path' in context:
                with open(context['config_path'], 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                self.logger.logger.warning("Created default configuration file")
                return True
        except:
            pass
        
        return False
    
    def recover_audio(self, exception: AudioException, context: dict) -> bool:
        """Attempt to recover from audio failures"""
        # Disable audio and continue with visual alerts only
        if 'audio_manager' in context:
            context['audio_manager'].disable_audio()
            self.logger.logger.warning("Audio disabled due to failure, using visual alerts only")
            return True
        
        return False
```

## Performance Optimizations

### Caching Strategy
- **Network Cache**: 30-second cache for network file operations
- **UI Cache**: 5-second cache for rapid UI updates
- **Acknowledgment Cache**: Cache today's acknowledgments
- **Settings Cache**: Cache settings to avoid repeated file reads

### Threading Model
- **Background Workers**: Network operations on separate threads
- **Timeout Protection**: 1-second timeouts on all network calls
- **UI Thread Safety**: All UI updates on main thread
- **Event-driven Updates**: Minimize polling, use event signals

### Memory Management
- **Lazy Loading**: Load data only when needed
- **Cleanup Timers**: Regular cleanup of expired cache entries
- **Resource Management**: Proper disposal of QTimer and QThread objects

## Configuration Management

### Settings Structure
```python
@dataclass
class ApplicationSettings:
    data_folder: str = ""
    volume: float = 0.5
    flash_interval: int = 500
    flash_cycles: int = 3
    pause_between_cycles: int = 2000
    default_monitor: int = 0
    fullscreen_mode: bool = False
    tv_fullscreen_timeout: int = 30
    mute_duration_minutes: int = 5
    theme: str = "default"
```

### Configuration Sources
- JSON configuration files
- Environment variables
- Command-line arguments
- User preferences dialog

## Deployment Strategy

### Installation Scripts
```batch
REM install.bat - Main installation script for Windows
@echo off
setlocal EnableDelayedExpansion

echo Manifest Alerts v3.3 - Installation Script
echo ==========================================

REM Check for Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)

REM Verify Python version (3.11+)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create necessary directories
echo Creating application directories...
if not exist "app_data" mkdir app_data
if not exist "data" mkdir data
if not exist "backup" mkdir backup
if not exist "tickets" mkdir tickets

REM Copy default configuration if not exists
if not exist "config.json" (
    echo Creating default configuration...
    copy config_template.json config.json
)

REM Create desktop shortcuts
echo Creating desktop shortcuts...
python install_shortcuts.py

echo.
echo Installation completed successfully!
echo.
echo To start the application:
echo   1. Double-click the desktop shortcut
echo   2. Or run: launch_manifest_alerts.bat
echo.
pause
```

### Environment Configuration
```python
class EnvironmentManager:
    def __init__(self):
        self.env_config = self.detect_environment()
    
    def detect_environment(self) -> dict:
        """Detect current environment configuration"""
        import platform
        import psutil
        
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0],
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "display_count": len(psutil.sensors_temperatures()) if hasattr(psutil, 'sensors_temperatures') else 1,
            "network_drive_access": self.test_network_access()
        }
    
    def test_network_access(self) -> bool:
        """Test access to network drive"""
        try:
            test_path = r"\\Prddpkmitlgt004\ManifestPC\config.json"
            return os.path.exists(test_path)
        except:
            return False
    
    def validate_environment(self) -> tuple[bool, list[str]]:
        """Validate environment meets requirements"""
        errors = []
        
        # Check Python version
        python_version = tuple(map(int, self.env_config["python_version"].split('.')))
        if python_version < (3, 11):
            errors.append(f"Python 3.11+ required, found {self.env_config['python_version']}")
        
        # Check memory
        if self.env_config["memory_gb"] < 4:
            errors.append(f"Minimum 4GB RAM required, found {self.env_config['memory_gb']}GB")
        
        # Check OS
        if self.env_config["os"] != "Windows":
            errors.append(f"Windows OS required, found {self.env_config['os']}")
        
        # Check network access
        if not self.env_config["network_drive_access"]:
            errors.append("Cannot access network drive \\\\Prddpkmitlgt004\\ManifestPC\\")
        
        return len(errors) == 0, errors
    
    def create_environment_report(self) -> str:
        """Create detailed environment report for troubleshooting"""
        report = f"""
Environment Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================

System Information:
- OS: {self.env_config['os']} {self.env_config['os_version']}
- Architecture: {self.env_config['architecture']}
- Python: {self.env_config['python_version']}
- Memory: {self.env_config['memory_gb']} GB

Network Access:
- Manifest PC Drive: {'✓ Available' if self.env_config['network_drive_access'] else '✗ Unavailable'}

Display Configuration:
- Display Count: {self.env_config['display_count']}

Validation Results:
"""
        
        is_valid, errors = self.validate_environment()
        if is_valid:
            report += "✓ Environment meets all requirements\n"
        else:
            report += "✗ Environment validation failed:\n"
            for error in errors:
                report += f"  - {error}\n"
        
        return report
```

### Packaging and Distribution
```python
# setup.py - For creating distributable packages
from setuptools import setup, find_packages

setup(
    name="manifest-alerts",
    version="3.3.0",
    description="Centralized Manifest Alert Display System",
    author="Manifest Alert Team",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.5.0",
        "pygame>=2.5.0",
        "psutil>=5.9.0",
        "packaging>=21.0"
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "manifest-alerts=main:main",
        ]
    },
    package_data={
        "": ["*.json", "*.mp3", "*.wav", "*.md", "*.txt"]
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ]
)
```

### Update Management
```python
class UpdateManager:
    def __init__(self, current_version: str, logger: ManifestLogger):
        self.current_version = current_version
        self.logger = logger
        self.update_server = "\\\\Prddpkmitlgt004\\ManifestPC\\updates\\"
    
    def check_for_updates(self) -> Optional[dict]:
        """Check for available updates"""
        try:
            version_file = os.path.join(self.update_server, "latest_version.json")
            if not os.path.exists(version_file):
                return None
            
            with open(version_file, 'r') as f:
                update_info = json.load(f)
            
            if self.is_newer_version(update_info["version"], self.current_version):
                return update_info
            
            return None
            
        except Exception as e:
            self.logger.logger.error(f"Update check failed: {e}")
            return None
    
    def is_newer_version(self, remote_version: str, local_version: str) -> bool:
        """Compare version strings"""
        from packaging import version
        return version.parse(remote_version) > version.parse(local_version)
    
    def download_update(self, update_info: dict) -> bool:
        """Download and prepare update"""
        try:
            # Create backup of current installation
            self.create_backup()
            
            # Download update package
            update_package = os.path.join(self.update_server, update_info["package"])
            local_package = os.path.join("updates", update_info["package"])
            
            os.makedirs("updates", exist_ok=True)
            shutil.copy2(update_package, local_package)
            
            # Verify download integrity
            if self.verify_package(local_package, update_info.get("checksum")):
                self.logger.logger.info(f"Update {update_info['version']} downloaded successfully")
                return True
            else:
                self.logger.logger.error("Update package verification failed")
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Update download failed: {e}")
            return False
    
    def create_backup(self) -> None:
        """Create backup of current installation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup/manifest_alerts_{timestamp}"
        
        # Copy essential files
        files_to_backup = [
            "config.json",
            "app_data/",
            "data/",
            "main.py",
            "requirements.txt"
        ]
        
        for item in files_to_backup:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_dir, item))
                else:
                    os.makedirs(os.path.dirname(os.path.join(backup_dir, item)), exist_ok=True)
                    shutil.copy2(item, os.path.join(backup_dir, item))
    
    def verify_package(self, package_path: str, expected_checksum: Optional[str]) -> bool:
        """Verify package integrity"""
        if not expected_checksum:
            return True  # Skip verification if no checksum provided
        
        import hashlib
        
        with open(package_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        return file_hash == expected_checksum
```

### Monitoring and Health Checks
```python
class SystemHealthMonitor:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.health_checks = {
            "network_access": self.check_network_access,
            "memory_usage": self.check_memory_usage,
            "disk_space": self.check_disk_space,
            "configuration": self.check_configuration,
            "audio_system": self.check_audio_system
        }
    
    def run_health_check(self) -> dict:
        """Run comprehensive health check"""
        results = {}
        
        for check_name, check_func in self.health_checks.items():
            try:
                results[check_name] = check_func()
            except Exception as e:
                results[check_name] = {
                    "status": "ERROR",
                    "message": f"Health check failed: {str(e)}"
                }
        
        # Generate overall health status
        overall_status = "HEALTHY"
        if any(result["status"] == "ERROR" for result in results.values()):
            overall_status = "ERROR"
        elif any(result["status"] == "WARNING" for result in results.values()):
            overall_status = "WARNING"
        
        results["overall"] = {"status": overall_status}
        
        # Log health check results
        self.logger.log_system_state("HealthCheck", overall_status, results)
        
        return results
    
    def check_network_access(self) -> dict:
        """Check network drive accessibility"""
        try:
            test_path = r"\\Prddpkmitlgt004\ManifestPC\config.json"
            start_time = time.time()
            
            if os.path.exists(test_path):
                response_time = time.time() - start_time
                
                if response_time > 2.0:
                    return {
                        "status": "WARNING",
                        "message": f"Network slow: {response_time:.2f}s response time"
                    }
                else:
                    return {
                        "status": "OK",
                        "message": f"Network accessible ({response_time:.2f}s)"
                    }
            else:
                return {
                    "status": "ERROR",
                    "message": "Network drive not accessible"
                }
                
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Network check failed: {str(e)}"
            }
    
    def check_memory_usage(self) -> dict:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 90:
                return {
                    "status": "ERROR",
                    "message": f"Critical memory usage: {usage_percent}%"
                }
            elif usage_percent > 80:
                return {
                    "status": "WARNING",
                    "message": f"High memory usage: {usage_percent}%"
                }
            else:
                return {
                    "status": "OK",
                    "message": f"Memory usage: {usage_percent}%"
                }
                
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Memory check failed: {str(e)}"
            }
```

## Testing Strategy

### Unit Tests
- Domain models with full test coverage
- Service layer business logic testing
- Repository implementations with mock data
- UI components with PyQt test framework
- UILayoutService single alert detection logic
- CardProperties calculation for different modes
- Alert model methods for missed/active status

### Integration Tests
- End-to-end workflow testing
- Network file operations testing
- Multi-monitor scenarios
- Performance benchmarks
- Single alert scaling visual verification
- Layout switching between normal and enhanced modes
- Background transparency during flash states

### Performance Tests
- Cache effectiveness validation
- UI responsiveness measurements
- Memory usage profiling
- Network timeout handling
- Layout switching performance impact
- Card scaling rendering performance

### Single Alert Scaling Test Cases
```python
def test_single_alert_scaling():
    """Test single alert scaling conditions"""
    # Test Case 1: Single active alert, no missed -> Enable scaling
    alerts = [create_active_alert("07:00")]
    assert layout_service.determine_layout_mode(alerts) == LayoutMode.SINGLE_CARD
    
    # Test Case 2: Multiple active alerts -> Normal mode
    alerts = [create_active_alert("07:00"), create_active_alert("11:00")]
    assert layout_service.determine_layout_mode(alerts) == LayoutMode.NORMAL_GRID
    
    # Test Case 3: Single active + missed alert -> Normal mode
    alerts = [create_active_alert("07:00"), create_missed_alert("06:00")]
    assert layout_service.determine_layout_mode(alerts) == LayoutMode.NORMAL_GRID
    
    # Test Case 4: No active alerts -> Normal mode
    alerts = [create_acknowledged_alert("07:00")]
    assert layout_service.determine_layout_mode(alerts) == LayoutMode.NORMAL_GRID

def test_card_property_calculation():
    """Test card properties for different modes"""
    alert = create_active_alert("07:00")
    
    # Single card mode properties
    props = layout_service.calculate_card_properties(alert, LayoutMode.SINGLE_CARD)
    assert props.height == 400
    assert props.font_size == 36
    assert props.background_style == "transparent"
    
    # Normal mode properties
    props = layout_service.calculate_card_properties(alert, LayoutMode.NORMAL_GRID)
    assert props.height == 80
    assert props.font_size == 28
    assert props.background_style == "normal"
```

## Migration Strategy

### Phase 1: Domain Models
1. Create domain models (Manifest, Carrier, Acknowledgment, Alert)
2. Implement core business logic
3. Unit tests for domain layer

### Phase 2: Data Layer
1. Implement repository interfaces
2. Create concrete repository implementations
3. Add caching layer
4. Integration tests for data access

### Phase 3: Service Layer
1. Implement business services
2. Add performance optimizations
3. Service integration tests

### Phase 4: UI Refactoring
1. Extract UI components from monolithic class
2. Implement controllers
3. Connect services to UI
4. Implement single alert scaling and dynamic layout switching
5. UI component tests including layout management

### Phase 5: Integration & Polish
1. Complete end-to-end testing
2. Performance optimization including layout switching
3. Single alert scaling visual verification and testing
4. Documentation
5. Deployment preparation

## File Structure Overview
```
manifest_alerts_oop/
├── src/
│   ├── domain/
│   ├── infrastructure/
│   ├── application/
│   └── presentation/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── config/
├── resources/
├── docs/
├── requirements.txt
├── setup.py
└── main.py
```

## Benefits of OOP Rewrite

### Maintainability
- Clear separation of concerns
- Single responsibility principle
- Easier to understand and modify

### Testability
- Isolated components for unit testing
- Mock-friendly repository pattern
- Comprehensive test coverage

### Scalability
- Easy to add new features
- Pluggable architecture
- Performance optimization points clearly identified

### Code Quality
- Reduced code duplication
- Consistent patterns throughout
- Better error handling and logging

## Data Protection & Recovery

### Data Corruption Recovery
```python
class DataProtectionManager:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.backup_frequency = timedelta(hours=24)
        self.max_backups = 30  # Keep 30 days of backups
    
    def create_data_backup(self) -> bool:
        """Create backup of critical data files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backup/data_{timestamp}"
            
            # Files to backup
            critical_files = [
                "config.json",
                "app_data/acknowledgments.json",
                "app_data/manifest_cache.json",
                "data/*.csv"
            ]
            
            os.makedirs(backup_dir, exist_ok=True)
            
            for file_pattern in critical_files:
                if '*' in file_pattern:
                    # Handle wildcard patterns
                    import glob
                    for file_path in glob.glob(file_pattern):
                        if os.path.exists(file_path):
                            self.backup_file(file_path, backup_dir)
                else:
                    if os.path.exists(file_pattern):
                        self.backup_file(file_pattern, backup_dir)
            
            # Clean old backups
            self.cleanup_old_backups()
            
            self.logger.logger.info(f"Data backup created: {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Data backup failed: {e}")
            return False
    
    def backup_file(self, source: str, backup_dir: str) -> None:
        """Backup individual file maintaining directory structure"""
        relative_path = source
        target_path = os.path.join(backup_dir, relative_path)
        
        # Create target directory if needed
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Copy file with metadata
        shutil.copy2(source, target_path)
    
    def restore_from_backup(self, backup_name: str) -> bool:
        """Restore data from specific backup"""
        try:
            backup_dir = f"backup/{backup_name}"
            
            if not os.path.exists(backup_dir):
                self.logger.logger.error(f"Backup not found: {backup_name}")
                return False
            
            # Create safety backup of current state
            current_backup = f"backup/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_safety_backup(current_backup)
            
            # Restore files
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    backup_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(backup_file_path, backup_dir)
                    target_path = relative_path
                    
                    # Create target directory
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(backup_file_path, target_path)
            
            self.logger.logger.info(f"Data restored from backup: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Restore failed: {e}")
            return False
    
    def verify_data_integrity(self) -> dict:
        """Verify integrity of critical data files"""
        results = {}
        
        # Check config.json
        results["config"] = self.verify_config_file()
        
        # Check acknowledgments.json
        results["acknowledgments"] = self.verify_acknowledgments_file()
        
        # Check manifest cache
        results["cache"] = self.verify_cache_files()
        
        # Check CSV data files
        results["csv_data"] = self.verify_csv_files()
        
        return results
    
    def verify_config_file(self) -> dict:
        """Verify configuration file integrity"""
        try:
            if not os.path.exists("config.json"):
                return {"status": "MISSING", "message": "Configuration file not found"}
            
            with open("config.json", 'r') as f:
                config = json.load(f)
            
            # Check required fields
            required_fields = ["manifests", "settings"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                return {
                    "status": "INVALID",
                    "message": f"Missing required fields: {missing_fields}"
                }
            
            return {"status": "OK", "message": "Configuration file valid"}
            
        except json.JSONDecodeError as e:
            return {"status": "CORRUPT", "message": f"JSON parse error: {e}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Verification failed: {e}"}
    
    def verify_acknowledgments_file(self) -> dict:
        """Verify acknowledgments file integrity"""
        try:
            ack_file = "app_data/acknowledgments.json"
            
            if not os.path.exists(ack_file):
                return {"status": "MISSING", "message": "Acknowledgments file not found"}
            
            with open(ack_file, 'r') as f:
                ack_data = json.load(f)
            
            # Verify structure
            if not isinstance(ack_data, dict):
                return {"status": "INVALID", "message": "Invalid acknowledgments structure"}
            
            return {"status": "OK", "message": "Acknowledgments file valid"}
            
        except json.JSONDecodeError as e:
            return {"status": "CORRUPT", "message": f"JSON parse error: {e}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Verification failed: {e}"}
```

### Network Failure Handling
```python
class NetworkFailureHandler:
    def __init__(self, logger: ManifestLogger, cache_manager: CacheManager):
        self.logger = logger
        self.cache_manager = cache_manager
        self.fallback_strategies = [
            self.use_local_cache,
            self.use_last_known_good,
            self.use_default_config
        ]
    
    def handle_network_failure(self, operation: str, context: dict) -> tuple[bool, any]:
        """Handle network failures with fallback strategies"""
        self.logger.logger.warning(f"Network failure detected for operation: {operation}")
        
        for strategy in self.fallback_strategies:
            try:
                success, result = strategy(operation, context)
                if success:
                    self.logger.logger.info(f"Fallback successful using {strategy.__name__}")
                    return True, result
            except Exception as e:
                self.logger.logger.error(f"Fallback strategy {strategy.__name__} failed: {e}")
                continue
        
        self.logger.logger.error("All fallback strategies failed")
        return False, None
    
    def use_local_cache(self, operation: str, context: dict) -> tuple[bool, any]:
        """Use cached data as fallback"""
        if 'cache_key' in context:
            cached_data = self.cache_manager.get_cached_data(context['cache_key'])
            if cached_data is not None:
                return True, cached_data
        
        return False, None
    
    def use_last_known_good(self, operation: str, context: dict) -> tuple[bool, any]:
        """Use last known good configuration"""
        try:
            last_good_file = "app_data/last_known_good.json"
            if os.path.exists(last_good_file):
                with open(last_good_file, 'r') as f:
                    last_good_data = json.load(f)
                
                if operation in last_good_data:
                    return True, last_good_data[operation]
        except:
            pass
        
        return False, None
    
    def use_default_config(self, operation: str, context: dict) -> tuple[bool, any]:
        """Fall back to default configuration"""
        defaults = {
            "mute_status": {"muted": False, "until": None},
            "config": {
                "manifests": [],
                "settings": {
                    "volume": 0.5,
                    "flash_interval": 500,
                    "data_folder": ""
                }
            }
        }
        
        if operation in defaults:
            return True, defaults[operation]
        
        return False, None
    
    def save_last_known_good(self, operation: str, data: any) -> None:
        """Save successful operation data for future fallback"""
        try:
            last_good_file = "app_data/last_known_good.json"
            
            # Load existing data
            if os.path.exists(last_good_file):
                with open(last_good_file, 'r') as f:
                    last_good_data = json.load(f)
            else:
                last_good_data = {}
            
            # Update with new data
            last_good_data[operation] = data
            last_good_data[f"{operation}_timestamp"] = datetime.now().isoformat()
            
            # Save updated data
            os.makedirs("app_data", exist_ok=True)
            with open(last_good_file, 'w') as f:
                json.dump(last_good_data, f, indent=2)
                
        except Exception as e:
            self.logger.logger.error(f"Failed to save last known good data: {e}")
```

### Configuration Loss Recovery
```python
class ConfigurationRecoveryManager:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.config_hierarchy = [
            "config.json",
            "backup/config_backup.json",
            "config_template.json",
            self.create_minimal_config
        ]
    
    def recover_configuration(self) -> dict:
        """Attempt to recover configuration from various sources"""
        for source in self.config_hierarchy:
            try:
                if callable(source):
                    # Last resort: create minimal config
                    config = source()
                    self.logger.logger.warning("Created minimal configuration")
                    return config
                elif os.path.exists(source):
                    with open(source, 'r') as f:
                        config = json.load(f)
                    
                    # Validate recovered config
                    if self.validate_config(config):
                        self.logger.logger.info(f"Configuration recovered from {source}")
                        return config
                    
            except Exception as e:
                self.logger.logger.error(f"Failed to recover from {source}: {e}")
                continue
        
        # If we get here, use absolute minimal config
        return self.create_minimal_config()
    
    def validate_config(self, config: dict) -> bool:
        """Validate configuration structure"""
        required_keys = ["manifests", "settings"]
        return all(key in config for key in required_keys)
    
    def create_minimal_config(self) -> dict:
        """Create minimal working configuration"""
        return {
            "manifests": [],
            "settings": {
                "volume": 0.5,
                "flash_interval": 500,
                "flash_cycles": 3,
                "pause_between_cycles": 2000,
                "default_monitor": 0,
                "fullscreen_mode": False,
                "tv_fullscreen_timeout": 30,
                "mute_duration_minutes": 5,
                "theme": "default",
                "data_folder": ""
            }
        }
    
    def save_recovery_config(self, config: dict) -> bool:
        """Save recovered configuration"""
        try:
            # Save as main config
            with open("config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            # Also save as backup
            os.makedirs("backup", exist_ok=True)
            with open("backup/config_backup.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.logger.info("Recovered configuration saved")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to save recovered configuration: {e}")
            return False
```

### Acknowledgment Data Protection
```python
class AcknowledgmentProtectionManager:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.ack_file = "app_data/acknowledgments.json"
        self.backup_file = "app_data/acknowledgments_backup.json"
    
    def protect_acknowledgment_data(self, ack_data: dict) -> bool:
        """Protect acknowledgment data with backup and validation"""
        try:
            # Validate data before saving
            if not self.validate_acknowledgment_data(ack_data):
                self.logger.logger.error("Acknowledgment data validation failed")
                return False
            
            # Create backup of current data
            if os.path.exists(self.ack_file):
                shutil.copy2(self.ack_file, self.backup_file)
            
            # Save new data
            os.makedirs("app_data", exist_ok=True)
            with open(self.ack_file, 'w') as f:
                json.dump(ack_data, f, indent=2)
            
            # Verify save was successful
            if self.verify_acknowledgment_file():
                self.logger.logger.info("Acknowledgment data protected successfully")
                return True
            else:
                # Restore from backup if verification failed
                self.restore_acknowledgment_backup()
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Acknowledgment protection failed: {e}")
            self.restore_acknowledgment_backup()
            return False
    
    def validate_acknowledgment_data(self, ack_data: dict) -> bool:
        """Validate acknowledgment data structure"""
        if not isinstance(ack_data, dict):
            return False
        
        # Check each acknowledgment entry
        for key, value in ack_data.items():
            if not isinstance(value, dict):
                return False
            
            required_fields = ["timestamp", "user"]
            if not all(field in value for field in required_fields):
                return False
        
        return True
    
    def verify_acknowledgment_file(self) -> bool:
        """Verify acknowledgment file integrity"""
        try:
            if not os.path.exists(self.ack_file):
                return False
            
            with open(self.ack_file, 'r') as f:
                data = json.load(f)
            
            return self.validate_acknowledgment_data(data)
            
        except:
            return False
    
    def restore_acknowledgment_backup(self) -> bool:
        """Restore acknowledgments from backup"""
        try:
            if os.path.exists(self.backup_file):
                shutil.copy2(self.backup_file, self.ack_file)
                self.logger.logger.warning("Acknowledgment data restored from backup")
                return True
            else:
                # Create empty acknowledgments if no backup
                with open(self.ack_file, 'w') as f:
                    json.dump({}, f)
                self.logger.logger.warning("Created empty acknowledgments file")
                return True
        except Exception as e:
            self.logger.logger.error(f"Acknowledgment restore failed: {e}")
            return False
```

## Success Criteria

### Functional Requirements
- ✅ All existing features preserved
- ✅ Performance equal or better than current system
- ✅ UI responsiveness maintained
- ✅ Multi-PC mute synchronization working
- ✅ Data integrity maintained
- ✅ Single alert scaling functionality implemented
- ✅ Dynamic layout switching working correctly

### Technical Requirements
- ✅ Clean architecture with separation of concerns
- ✅ Comprehensive test coverage (>90%)
- ✅ Proper error handling and logging
- ✅ Configuration management
- ✅ Performance monitoring

### Quality Requirements
- ✅ Code maintainability improved
- ✅ Documentation complete
- ✅ Easy deployment
- ✅ Future enhancement capability
- ✅ User experience preserved

This specification provides the complete roadmap for transforming the current monolithic manifest alert system into a well-architected, maintainable, and scalable OOP application while preserving all existing functionality and performance characteristics.
