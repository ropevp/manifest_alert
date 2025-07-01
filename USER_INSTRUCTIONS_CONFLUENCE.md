h1. Manifest Alert System - User Instructions

h2. Quick Start Guide

h3. Installation (One-Time Setup)

# *Prerequisites*: Install Python and Git on your computer
** [Download Python|https://www.python.org/downloads/] (latest version)
** [Download Git|https://git-scm.com/downloads]
# *Download INSTALL.bat* from [GitHub Repository|https://github.com/ropevp/manifest_alert]
# *Run Installation*: Double-click {{INSTALL.bat}} → Everything is automated
# *Launch Application*: Use desktop shortcut like any Windows application

h3. Daily Usage

* *Launch*: Double-click desktop icon "Manifest Alert System"
* *Acknowledge Alerts*: Click manifest entries to mark them as handled
* *Monitor Status*: Window automatically updates and alerts for new manifests
* *Minimize to Tray*: Click system tray icon to hide/show window
* *Exit*: Right-click system tray icon → Exit

----

h2. How the Manifest Alert System Works

h3. Basic Operation

The Manifest Alert System monitors scheduled manifest deliveries and provides visual and audio alerts when manifests become active or missed. The system automatically tracks acknowledgments across multiple computers for warehouse coordination.

h3. Alert Types

# *Open Manifests*: Scheduled but not yet active (blue background)
# *Active Manifests*: Current time matches scheduled time (red background, audio alerts)
# *Missed Manifests*: Past due and unacknowledged (orange background, urgent alerts)
# *Acknowledged Manifests*: Completed and marked as handled (green background)

h3. Window Behavior

* *Always Visible*: Window stays on screen during alerts for maximum visibility
* *Auto-Sizing*: Automatically adjusts to fit all manifests
* *Monitor Switching*: "Switch Monitor" button cycles through all displays
* *System Tray*: Minimizes to system tray, click to restore

----

h2. Configuration System (config.json)

h3. File Location

The system uses *configurable data storage* via the Settings dialog:

* *Default*: {{app_data/config.json}} (local storage)
* *Network*: {{\\server\share\manifest_data\config.json}} (multi-PC sharing)
* *Cloud*: {{G:\My Drive\manifest_data\config.json}} (Google Drive Desktop sync)

h3. Configuration Structure

{code:json}
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
{code}

h3. Configuration Fields

* *{{carrier}}*: Display name for the manifest (e.g., "FedEx", "UPS Ground", "Amazon")
* *{{time}}*: Scheduled time in 24-hour format (e.g., "08:00", "14:30")
* *{{active}}*: Boolean - set to {{false}} to temporarily disable a manifest

h3. Adding/Editing Manifests

# *Manual Editing*: Edit {{config.json}} directly with any text editor
# *Reload Configuration*: Click "Reload Config" button to apply changes
# *Validation*: System validates time format and displays errors if invalid

h3. Time Format Requirements

* *24-Hour Format*: Use "HH:MM" (e.g., "08:00", "14:30", "23:45")
* *Leading Zeros*: Always include leading zeros (e.g., "08:00" not "8:00")
* *Valid Times*: 00:00 to 23:59 only

----

h2. Acknowledgment System (acknowledgments.json)

h3. File Purpose

Tracks which manifests have been acknowledged and by whom. Enables multi-PC coordination and accountability.

h3. File Location

Same configurable location as config.json:

* *Local*: {{app_data/acknowledgments.json}}
* *Shared*: User-configured network or cloud location

h3. Acknowledgment Structure

{code:json}
[
  {
    "carrier": "FedEx",
    "time": "08:00",
    "acknowledged_by": "John Smith",
    "acknowledged_at": "2025-07-01T08:05:23",
    "reason": "Package delivered to receiving dock"
  }
]
{code}

h3. Acknowledgment Fields

* *{{carrier}}*: Matches the carrier name from config.json
* *{{time}}*: Matches the scheduled time from config.json
* *{{acknowledged_by}}*: User's custom name or Windows username
* *{{acknowledged_at}}*: Timestamp when acknowledgment was made
* *{{reason}}*: User-entered reason for acknowledgment (required)

h3. Acknowledgment Process

# *Click Manifest*: Click any manifest entry in the list
# *Enter Reason*: Type reason for acknowledgment (required field)
# *Submit*: Click "Acknowledge" to save
# *Immediate Update*: Manifest turns gray and shows "- Acknowledged - [Your Name]"
# *Multi-PC Sync*: Other computers see acknowledgment within 0.5-2 seconds

----

h2. Timing and Refresh System

h3. Alert Timing

* *Pre-Alert*: Manifests appear 30 minutes before scheduled time
* *Active Alert*: Audio and visual alerts start at exact scheduled time
* *Missed Alert*: Continues alerting until acknowledged if past due

h3. Refresh Rates (Adaptive System)

The system uses intelligent refresh timing for optimal performance:

h4. Fast Refresh Mode (0.5 seconds)

*Triggers:*
* When any manifest becomes Active (red)
* When any manifest becomes Missed (orange)
* For 60 seconds after user acknowledgments

*Purpose:*
* Real-time multi-PC synchronization during critical periods
* Immediate visibility of acknowledgments across warehouse computers
* Ultra-responsive operation during active alerts

h4. Normal Refresh Mode (2 seconds)

*Triggers:*
* When all manifests are Open (blue) or acknowledged
* During idle periods with no active alerts
* System automatically switches from fast mode after alert resolution

*Purpose:*
* Resource-efficient operation during normal hours
* Preserves system performance for long-term 24/7 operation
* Maintains responsiveness while conserving CPU usage

h3. Multi-PC Synchronization

* *File Monitoring*: System detects changes to acknowledgments.json from other computers
* *Automatic Updates*: UI refreshes immediately when external changes detected
* *Conflict Resolution*: Last acknowledgment wins (no locking mechanism needed)
* *Network Compatibility*: Works with Windows network drives, Google Drive Desktop, and cloud storage

----

h2. Audio Alert System

h3. Voice Announcements

Professional text-to-speech announcements using Windows Zira voice:

h4. Announcement Patterns

* *Single Active*: "Manifest at eight thirty"
* *Single Missed*: "Manifest Missed, at eight thirty. Manifest is fifteen minutes Late"
* *Multiple Active*: "Multiple manifests Active. Please acknowledge"
* *Multiple Missed*: "Multiple missed manifests. Please acknowledge"
* *Mixed Status*: "Multiple Missed and Active Manifests. Please acknowledge"

h4. Timing Behavior

* *Announcement Interval*: Every 20 seconds during active alerts
* *Smart Logic*: Prevents repetitive announcements with consolidated messages
* *Background Operation*: Non-blocking speech processing
* *Error Recovery*: Silent failure if speech engine unavailable

h3. Sound Alerts

* *Alert Sound*: Professional alert tone (alert.wav)
* *Timing*: Plays with each voice announcement
* *Volume*: Uses system volume settings
* *File Location*: {{resources/alert.wav}}

----

h2. Settings and Customization

h3. Accessing Settings

* *Main Window*: Click "⚙ Settings" button
* *System Tray*: Right-click tray icon → Settings (if available)

h3. Settings Options

h4. Data Storage Location

Configure where the system stores config.json and acknowledgments.json:

*Local Storage (Default)*
* Path: Application's {{app_data}} folder
* Best for: Single computer installations

*Network Storage*
* Path: {{\\server\share\manifest_data\}}
* Best for: Multiple warehouse computers sharing configuration
* Requires: Network drive access with read/write permissions

*Cloud Storage*
* Path: {{G:\My Drive\manifest_data\}} (Google Drive Desktop)
* Best for: Automatic backup and remote management
* Requires: Google Drive Desktop installed and syncing

h4. Custom Acknowledgment Name

* *Default*: Uses Windows username (e.g., "e10120323")
* *Custom*: Set display name (e.g., "John Smith", "Warehouse Manager")
* *Character Limit*: 20 characters maximum
* *Display*: Shows in acknowledgment logs and manifest entries

h3. Path Validation

Real-time validation with visual indicators:

* *✅ Green*: Valid folder with write access
* *⚠️ Orange*: Folder will be created (parent exists)
* *❌ Red*: Invalid path or insufficient permissions

----

h2. Snooze and Silence Options

h3. Snooze Functionality

Temporarily silence alerts while keeping visual indicators:

h4. How to Snooze

# *Click "Snooze" Button*: Available during Active or Missed alerts
# *Select Duration*: Choose from 1-30 minutes
# *Confirmation*: Audio stops, window remains visible

h4. Snooze Behavior

* *Audio Silence*: Voice announcements and sound alerts stop
* *Visual Maintained*: Window stays visible with color-coded manifests
* *Automatic Resume*: Alerts resume automatically after snooze period
* *Multi-Status*: Works for both Active and Missed manifests

h4. Snooze Durations

* *Quick Options*: 1, 5, 10, 15 minutes
* *Extended Options*: 20, 25, 30 minutes
* *Custom*: Type specific duration in minutes

----

h2. Multi-Monitor Support

h3. Monitor Switching

* *Switch Monitor Button*: Cycles application through all available displays
* *Full Screen Display*: Window appears completely on target monitor
* *Automatic Detection*: Uses all connected monitors and displays
* *Memory*: Remembers last used monitor position

h3. Optimal Setup

* *Warehouse TV*: Large display visible to all staff
* *Manager Desktop*: Secondary monitor for acknowledgment management
* *Mobile Devices*: Works on laptop screens and tablets

----

h2. Day-Change Logic

h3. Automatic Reset

System automatically resets at midnight for fresh daily operation:

h4. Reset Behavior

* *Manifest List*: Clears all acknowledgments for new day
* *Log Rotation*: Saves previous day's acknowledgments
* *UI Refresh*: Updates display for current day's schedule
* *No Restart Required*: Continues operation seamlessly

h4. Log Management

* *Daily Files*: Each day creates new acknowledgment log
* *Historical Data*: Previous days' logs preserved
* *File Naming*: Includes date stamps for easy identification

----

h2. Troubleshooting

h3. Common Issues

h4. Desktop Shortcut Not Working

*Problem*: Icon opens terminal and immediately closes

*Solution*:
# Run {{launch_diagnostic.bat}} for detailed error information
# Verify virtual environment exists ({{.venv}} folder)
# Reinstall using {{INSTALL.bat}}

h4. No Audio Alerts

*Problem*: Visual alerts work but no sound

*Solutions*:
# Check system volume settings
# Verify {{resources/alert.wav}} file exists
# Test Windows text-to-speech in Settings → Ease of Access → Narrator

h4. Manifests Not Updating

*Problem*: Changes to config.json not appearing

*Solutions*:
# Click "Reload Config" button
# Check file permissions on data folder
# Verify JSON syntax using online JSON validator

h4. Multi-PC Sync Issues

*Problem*: Acknowledgments not appearing on other computers

*Solutions*:
# Verify all computers point to same data folder path
# Check network drive or cloud sync status
# Confirm write permissions on shared folder

h4. Settings Dialog Issues

*Problem*: Cannot change data storage location

*Solutions*:
# Run application as administrator if using network drives
# Verify target folder permissions
# Create target folder manually before setting path

h3. Diagnostic Tools

* {{launch_diagnostic.bat}}: Comprehensive system check
* {{launch_manifest_alerts.bat}}: Debug mode with error console
* Settings Dialog: Real-time path validation and testing

----

h2. Support and Maintenance

h3. Self-Maintenance

* *Updates*: Re-run {{INSTALL.bat}} to update to latest version
* *Backup*: Copy entire application folder for safety
* *Settings Backup*: Export settings before major changes

h3. Performance Optimization

* *24/7 Operation*: Designed for continuous warehouse operation
* *Resource Usage*: Minimal CPU and memory footprint
* *Network Efficiency*: Optimized for shared storage scenarios

h3. Advanced Configuration

* *Custom Sounds*: Replace {{resources/alert.wav}} with custom audio
* *Network Drives*: Full UNC path support ({{\\server\share\folder}})
* *Cloud Integration*: Compatible with Dropbox, OneDrive, Google Drive Desktop

----

h2. Best Practices

h3. Warehouse Deployment

# *Central Configuration*: Use network drive for shared config.json
# *User Training*: Train staff on acknowledgment process and reasons
# *Multiple Displays*: Deploy on visible warehouse TV screens
# *Backup Strategy*: Regular backup of configuration and logs

h3. Multi-PC Setup

# *Consistent Paths*: All computers use same network/cloud path
# *Synchronized Time*: Ensure all computers have accurate system time
# *User Names*: Configure custom names for accountability
# *Network Access*: Verify reliable access to shared storage

h3. Daily Operations

# *Morning Check*: Verify system running and configuration current
# *Acknowledgment Discipline*: Always provide clear, specific reasons
# *End-of-Day Review*: Check acknowledgment logs for completeness
# *Issue Reporting*: Document any system issues for IT resolution

----

h2. Summary

The Manifest Alert System provides professional, reliable manifest tracking with:

* *Zero-maintenance operation* for continuous 24/7 warehouse use
* *Ultra-fast synchronization* across multiple computers (0.5-2 second updates)
* *Professional audio/visual alerts* optimized for warehouse environments
* *Comprehensive acknowledgment tracking* with user accountability
* *Flexible configuration* supporting local, network, and cloud storage
* *Simple installation and updates* via one-click INSTALL.bat system

For technical support or advanced configuration assistance, refer to your IT department.

{info}
*Last Updated*: July 1, 2025 - Version: Production Release
{info}
