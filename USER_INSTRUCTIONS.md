# 📋 Manifest Alert System - User Instructions

## 🚀 Quick Start Guide

### Installation (One-Time Setup)
1. **Prerequisites**: Install Python and Git on your computer
   - [Download Python](https://www.python.org/downloads/) (latest version)
   - [Download Git](https://git-scm.com/downloads)
2. **Download INSTALL.bat** from [GitHub Repository](https://github.com/ropevp/manifest_alert)
3. **Run Installation**: Double-click `INSTALL.bat` → Everything is automated
4. **Launch Application**: Use desktop shortcut like any Windows application

### Daily Usage
- **Launch**: Double-click desktop icon "Manifest Alert System"
- **Acknowledge Alerts**: Click manifest entries to mark them as handled
- **Monitor Status**: Window automatically updates and alerts for new manifests
- **Minimize to Tray**: Click system tray icon to hide/show window
- **Exit**: Right-click system tray icon → Exit

---

## 🎯 How the Manifest Alert System Works

### Basic Operation
The Manifest Alert System monitors scheduled manifest deliveries and provides visual and audio alerts when manifests become active or missed. The system automatically tracks acknowledgments across multiple computers for warehouse coordination.

### Alert Types
1. **🟢 Open Manifests**: Scheduled but not yet active (green background)
2. **🔴 Active Manifests**: Current time matches scheduled time (red background, audio alerts)
3. **🟠 Missed Manifests**: Past due and unacknowledged (orange background, urgent alerts)

### Window Behavior
- **Always Visible**: Window stays on screen during alerts for maximum visibility
- **Auto-Sizing**: Automatically adjusts to fit all manifests
- **Monitor Switching**: "Switch Monitor" button cycles through all displays
- **System Tray**: Minimizes to system tray, click to restore

---

## ⚙️ Configuration System (config.json)

### File Location
The system uses **configurable data storage** via the Settings dialog:
- **Default**: `app_data/config.json` (local storage)
- **Network**: `\\server\share\manifest_data\config.json` (multi-PC sharing)
- **Cloud**: `G:\My Drive\manifest_data\config.json` (Google Drive Desktop sync)

### Configuration Structure
```json
{
  "manifests": [
    {
      "carrier": "FedEx",
      "time": "08:00",
      "active": true
    },
    {
      "carrier": "UPS",
      "time": "10:30",
      "active": true
    }
  ]
}
```

### Configuration Fields
- **`carrier`**: Display name for the manifest (e.g., "FedEx", "UPS Ground", "Amazon")
- **`time`**: Scheduled time in 24-hour format (e.g., "08:00", "14:30")
- **`active`**: Boolean - set to `false` to temporarily disable a manifest

### Adding/Editing Manifests
1. **Manual Editing**: Edit `config.json` directly with any text editor
2. **Reload Configuration**: Click "Reload Config" button to apply changes
3. **Validation**: System validates time format and displays errors if invalid

### Time Format Requirements
- **24-Hour Format**: Use "HH:MM" (e.g., "08:00", "14:30", "23:45")
- **Leading Zeros**: Always include leading zeros (e.g., "08:00" not "8:00")
- **Valid Times**: 00:00 to 23:59 only

---

## 📊 Acknowledgment System (acknowledgments.json)

### File Purpose
Tracks which manifests have been acknowledged and by whom. Enables multi-PC coordination and accountability.

### File Location
Same configurable location as config.json:
- **Local**: `app_data/acknowledgments.json`
- **Shared**: User-configured network or cloud location

### Acknowledgment Structure
```json
[
  {
    "carrier": "FedEx",
    "time": "08:00",
    "acknowledged_by": "John Smith",
    "acknowledged_at": "2025-07-01T08:05:23",
    "reason": "Package delivered to receiving dock"
  }
]
```

### Acknowledgment Fields
- **`carrier`**: Matches the carrier name from config.json
- **`time`**: Matches the scheduled time from config.json
- **`acknowledged_by`**: User's custom name or Windows username
- **`acknowledged_at`**: Timestamp when acknowledgment was made
- **`reason`**: User-entered reason for acknowledgment (required)

### Acknowledgment Process
1. **Click Manifest**: Click any manifest entry in the list
2. **Enter Reason**: Type reason for acknowledgment (required field)
3. **Submit**: Click "Acknowledge" to save
4. **Immediate Update**: Manifest turns gray and shows "- Acknowledged - [Your Name]"
5. **Multi-PC Sync**: Other computers see acknowledgment within 0.5-2 seconds

---

## ⏰ Timing and Refresh System

### Alert Timing
- **Pre-Alert**: Manifests appear 30 minutes before scheduled time
- **Active Alert**: Audio and visual alerts start at exact scheduled time
- **Missed Alert**: Continues alerting until acknowledged if past due

### Refresh Rates (Adaptive System)
The system uses intelligent refresh timing for optimal performance:

#### Fast Refresh Mode (0.5 seconds)
**Triggers:**
- When any manifest becomes Active (red)
- When any manifest becomes Missed (orange)
- For 60 seconds after user acknowledgments

**Purpose:**
- Real-time multi-PC synchronization during critical periods
- Immediate visibility of acknowledgments across warehouse computers
- Ultra-responsive operation during active alerts

#### Normal Refresh Mode (2 seconds)
**Triggers:**
- When all manifests are Open (green) or acknowledged
- During idle periods with no active alerts
- System automatically switches from fast mode after alert resolution

**Purpose:**
- Resource-efficient operation during normal hours
- Preserves system performance for long-term 24/7 operation
- Maintains responsiveness while conserving CPU usage

### Multi-PC Synchronization
- **File Monitoring**: System detects changes to acknowledgments.json from other computers
- **Automatic Updates**: UI refreshes immediately when external changes detected
- **Conflict Resolution**: Last acknowledgment wins (no locking mechanism needed)
- **Network Compatibility**: Works with Windows network drives, Google Drive Desktop, and cloud storage

---

## 🎙️ Audio Alert System

### Voice Announcements
Professional text-to-speech announcements using Windows Zira voice:

#### Announcement Patterns
- **Single Active**: "Manifest at eight thirty"
- **Single Missed**: "Manifest Missed, at eight thirty. Manifest is fifteen minutes Late"
- **Multiple Active**: "Multiple manifests Active. Please acknowledge"
- **Multiple Missed**: "Multiple missed manifests. Please acknowledge"
- **Mixed Status**: "Multiple Missed and Active Manifests. Please acknowledge"

#### Timing Behavior
- **Announcement Interval**: Every 20 seconds during active alerts
- **Smart Logic**: Prevents repetitive announcements with consolidated messages
- **Background Operation**: Non-blocking speech processing
- **Error Recovery**: Silent failure if speech engine unavailable

### Sound Alerts
- **Alert Sound**: Professional alert tone (alert.wav)
- **Timing**: Plays with each voice announcement
- **Volume**: Uses system volume settings
- **File Location**: `resources/alert.wav`

### Snooze Integration
Professional audio management during snooze periods:

#### Complete Audio Control
- **Voice Announcements**: Stopped immediately when snooze activated
- **Sound Alerts**: Stopped immediately when snooze activated
- **Speech Timer**: Paused during entire snooze period
- **Automatic Resume**: Both voice and sound alerts resume when snooze expires

#### Smart Audio Behavior
- **Unified Silence**: All audio systems respect snooze status
- **No Interruptions**: Zero audio during snooze period regardless of alert changes
- **Professional Operation**: Clean start/stop with no audio artifacts
- **Status Awareness**: Audio system automatically detects snooze state

---

## 🛠️ Settings and Customization

### Accessing Settings
- **Main Window**: Click "⚙ Settings" button
- **System Tray**: Right-click tray icon → Settings (if available)

### Settings Options

#### Data Storage Location
Configure where the system stores config.json and acknowledgments.json:

**Local Storage (Default)**
- Path: Application's `app_data` folder
- Best for: Single computer installations

**Network Storage**
- Path: `\\server\share\manifest_data\`
- Best for: Multiple warehouse computers sharing configuration
- Requires: Network drive access with read/write permissions

**Cloud Storage**
- Path: `G:\My Drive\manifest_data\` (Google Drive Desktop)
- Best for: Automatic backup and remote management
- Requires: Google Drive Desktop installed and syncing

#### Custom Acknowledgment Name
- **Default**: Uses Windows username (e.g., "e10120323")
- **Custom**: Set display name (e.g., "John Smith", "Warehouse Manager")
- **Character Limit**: 20 characters maximum
- **Display**: Shows in acknowledgment logs and manifest entries

### Path Validation
Real-time validation with visual indicators:
- **✅ Green**: Valid folder with write access
- **⚠️ Orange**: Folder will be created (parent exists)
- **❌ Red**: Invalid path or insufficient permissions

---

## 🖥️ System Tray Integration

### Enhanced System Tray Menu
Right-click the system tray icon for complete application control:

#### Available Functions
- **Bring to Front**: Restore window to foreground
- **Reload Config**: Refresh configuration from disk
- **Snooze Alerts**: Temporarily silence alerts (enabled only during active alerts)
- **Toggle Fullscreen**: Switch between fullscreen and maximized modes
- **Switch to Monitor**: Choose specific monitor from submenu
- **Exit**: Close application completely

#### Smart Monitor Selection
When multiple monitors are connected:
- **Dynamic Detection**: Automatically detects all available monitors
- **Current Monitor**: Shows which monitor currently displays the window
- **Direct Selection**: Click "Monitor 1", "Monitor 2", etc. to switch directly
- **Single Monitor**: Shows "Single Monitor (disabled)" when only one display available

#### Context-Aware Behavior
- **Snooze Option**: Only enabled when alerts are active (Active/Missed manifests present)
- **Menu Updates**: Automatically updates based on current alert status
- **Professional Operation**: Full application control without window interaction

---

## 🔄 Snooze and Silence Options

### Enhanced Snooze Functionality
Temporarily silence alerts with complete control over window behavior:

#### How to Snooze
1. **Main Window**: Click "Snooze" button (visible during Active or Missed alerts)
2. **System Tray**: Right-click tray icon → "Snooze Alerts" (context-aware)
3. **Select Duration**: Choose from 1-30 minutes
4. **Enhanced Control**: Window can now be minimized and moved during snooze

#### Snooze Behavior
- **Complete Audio Silence**: Both sound alerts and voice announcements stop
- **Normal Window Behavior**: During snooze, window can be minimized, moved, or resized
- **Always-on-Top Disabled**: Window no longer forces itself to front during snooze
- **Visual Indicators Maintained**: Alert colors and status remain visible when window is open
- **Automatic Resume**: All alerts resume when snooze period expires
- **Professional Control**: True break from alert pressure while maintaining visibility option

#### Snooze Benefits
- **User Control**: Window behaves like normal application during snooze
- **Warehouse Friendly**: Can minimize window during breaks without losing alert status
- **Complete Silence**: No audio interruptions during snooze period
- **Auto-Resume**: Returns to normal alert behavior when snooze ends

#### Snooze Durations
- **Quick Options**: 1, 5, 10, 15 minutes
- **Extended Options**: 20, 25, 30 minutes
- **Custom**: Type specific duration in minutes

---

## 🖥️ Multi-Monitor Support

### Enhanced Monitor Switching
Multiple ways to switch between monitors for optimal warehouse display setup:

#### Main Window Method
- **Switch Monitor Button**: Cycles application through all available displays sequentially
- **Full Screen Display**: Window appears completely on target monitor
- **State Preservation**: Maintains fullscreen/maximized state on new monitor

#### System Tray Method (NEW)
- **Right-click System Tray**: Access "Switch to Monitor" submenu
- **Direct Selection**: Choose specific monitor ("Monitor 1", "Monitor 2", etc.)
- **Current Monitor Indicator**: Shows which monitor currently displays the window
- **Intelligent Detection**: Automatically detects all connected displays

#### Monitor Management
- **Dynamic Detection**: Automatically detects when monitors are connected/disconnected
- **Professional Positioning**: Centers window on target monitor before applying state
- **State Management**: Preserves fullscreen/maximized state during monitor switches
- **Single Monitor Support**: Gracefully handles single-monitor setups

### Optimal Setup
- **Memory**: Remembers last used monitor position

### Optimal Setup
- **Warehouse TV**: Large display visible to all staff
- **Manager Desktop**: Secondary monitor for acknowledgment management
- **Mobile Devices**: Works on laptop screens and tablets

---

## 🕐 Day-Change Logic

### Automatic Reset
System automatically resets at midnight for fresh daily operation:

#### Reset Behavior
- **Manifest List**: Clears all acknowledgments for new day
- **Log Rotation**: Saves previous day's acknowledgments
- **UI Refresh**: Updates display for current day's schedule
- **No Restart Required**: Continues operation seamlessly

#### Log Management
- **Daily Files**: Each day creates new acknowledgment log
- **Historical Data**: Previous days' logs preserved
- **File Naming**: Includes date stamps for easy identification

---

## 🚨 Troubleshooting

### Common Issues

#### Desktop Shortcut Not Working
**Problem**: Icon opens terminal and immediately closes
**Solution**: 
1. Run `launch_diagnostic.bat` for detailed error information
2. Verify virtual environment exists (`.venv` folder)
3. Reinstall using `INSTALL.bat`

#### No Audio Alerts
**Problem**: Visual alerts work but no sound
**Solutions**:
1. Check system volume settings
2. Verify `resources/alert.wav` file exists
3. Test Windows text-to-speech in Settings → Ease of Access → Narrator

#### Manifests Not Updating
**Problem**: Changes to config.json not appearing
**Solutions**:
1. Click "Reload Config" button
2. Check file permissions on data folder
3. Verify JSON syntax using online JSON validator

#### Multi-PC Sync Issues
**Problem**: Acknowledgments not appearing on other computers
**Solutions**:
1. Verify all computers point to same data folder path
2. Check network drive or cloud sync status
3. Confirm write permissions on shared folder

#### Settings Dialog Issues
**Problem**: Cannot change data storage location
**Solutions**:
1. Run application as administrator if using network drives
2. Verify target folder permissions
3. Create target folder manually before setting path

### Diagnostic Tools
- **`launch_diagnostic.bat`**: Comprehensive system check
- **`launch_manifest_alerts.bat`**: Debug mode with error console
- **Settings Dialog**: Real-time path validation and testing

---

## 📞 Support and Maintenance

### Self-Maintenance
- **Updates**: Re-run `INSTALL.bat` to update to latest version
- **Backup**: Copy entire application folder for safety
- **Settings Backup**: Export settings before major changes

### Performance Optimization
- **24/7 Operation**: Designed for continuous warehouse operation
- **Resource Usage**: Minimal CPU and memory footprint
- **Network Efficiency**: Optimized for shared storage scenarios

### Advanced Configuration
- **Custom Sounds**: Replace `resources/alert.wav` with custom audio
- **Network Drives**: Full UNC path support (`\\server\share\folder`)
- **Cloud Integration**: Compatible with Dropbox, OneDrive, Google Drive Desktop

---

## 🎯 Best Practices

### Warehouse Deployment
1. **Central Configuration**: Use network drive for shared config.json
2. **User Training**: Train staff on acknowledgment process and reasons
3. **Multiple Displays**: Deploy on visible warehouse TV screens
4. **Backup Strategy**: Regular backup of configuration and logs

### Multi-PC Setup
1. **Consistent Paths**: All computers use same network/cloud path
2. **Synchronized Time**: Ensure all computers have accurate system time
3. **User Names**: Configure custom names for accountability
4. **Network Access**: Verify reliable access to shared storage

### Daily Operations
1. **Morning Check**: Verify system running and configuration current
2. **Acknowledgment Discipline**: Always provide clear, specific reasons for missed manifests
3. **System Tray Usage**: Use right-click system tray menu for quick access to functions
4. **Snooze Management**: Use snooze feature appropriately for breaks while maintaining awareness
5. **Monitor Setup**: Configure optimal monitor placement using enhanced switching options
6. **End-of-Day Review**: Check acknowledgment logs for completeness
7. **Issue Reporting**: Document any system issues for IT resolution

### Enhanced Features Usage
1. **System Tray Control**: Leverage system tray menu for efficient operation without window focus
2. **Smart Snoozing**: Use snooze when appropriate - window can be minimized during breaks
3. **Monitor Optimization**: Use direct monitor selection from system tray for multi-display setups
4. **Audio Management**: Trust snooze system for complete audio silence during break periods
5. **Professional Operation**: Maintain visual awareness even when audio is snoozed

---

## 📋 Summary

The Manifest Alert System provides professional, reliable manifest tracking with:
- **Zero-maintenance operation** for continuous 24/7 warehouse use
- **Ultra-fast synchronization** across multiple computers (0.5-2 second updates)
- **Professional audio/visual alerts** optimized for warehouse environments
- **Enhanced system tray integration** for complete remote control
- **Smart snooze functionality** with professional window management
- **Advanced multi-monitor support** with direct selection capabilities
- **Comprehensive acknowledgment tracking** with user accountability
- **Flexible configuration** supporting local, network, and cloud storage
- **Simple installation and updates** via one-click INSTALL.bat system

For technical support or advanced configuration assistance, refer to Analytics.

*Last Updated: July 2, 2025 - Version: Production Release with Latest Enhancements*
