# Manifest Alert System ✅ PRODUCTION READY

A professional warehouse desktop application for Windows providing intelligent voice alerts and visual tracking for shipping manifests. Optimized for 24/7 warehouse operations with robust error handling, user accountability, and zero-maintenance design.

## 🚀 DEPLOYMENT STATUS
- **GitHub Repository**: [manifest_alert](https://github.com/ropevp/manifest_alert) ✅
- **Production Ready**: All core functionality implemented and tested ✅  
- **Voice System**: Professional text-to-speech with intelligent announcements ✅
- **User Accountability**: Custom names and username tracking ✅
- **Documentation**: Complete user guides and technical documentation ✅

## Core Features ✅ ALL IMPLEMENTED

### 👤 **User Accountability & Custom Names**
*   **Custom Acknowledgment Names:** Set personalized display names in settings
*   **Windows Username Fallback:** Automatic fallback to Windows username
*   **Comprehensive Tracking:** All acknowledgments logged with user identification
*   **Professional Display:** Clean format showing "Carrier - Acknowledged - UserName"
*   **Settings Integration:** Easy configuration through settings dialog
*   **JSON Persistence:** User preferences saved automatically

### 🎙️ **Intelligent Voice Announcements**
*   **Professional Zira Voice:** Clear, warehouse-optimized speech synthesis
*   **Smart Announcement Logic:** Prevents repetition with consolidated messages
*   **Proper Time Pronunciation:** "eleven thirty", "three oh three", "four o'clock"
*   **Status-Specific Messages:**
    *   Single Active: "Manifest at [time]"
    *   Single Missed: "Manifest Missed, at [time]. Manifest is [X] minutes Late"
    *   Multiple Active: "Multiple manifests Active. Please acknowledge"
    *   Multiple Missed: "Multiple missed manifests. Please acknowledge" 
    *   Mixed: "Multiple Missed and Active Manifests. Please acknowledge"

### 🖥️ **Enhanced Window Management**
*   **Zero Minimization:** Robust window state preservation during all operations
*   **Smart Display Priority:** Active alerts override Missed for full-screen prominence
*   **Always-on-Top:** Stays above all windows during critical alerts
*   **Multi-Monitor Support:** Seamless cycling between all connected displays
*   **Adaptive Refresh:** 5-second refresh during alerts, 30-second normal operation
*   **Auto-Expand Logic:** Groups expand automatically when all items acknowledged

### 📊 **Advanced Visual Status System**
*   **Color-Coded Status Indicators:**
    *   **Open (Blue):** Upcoming manifest (0-15 minutes before due)
    *   **Active (Red):** Currently due manifest (0-29 minutes late)
    *   **Missed (Dark Red):** Overdue manifest (30+ minutes late)
    *   **Acknowledged (Green):** Successfully handled manifests
    *   **Acknowledged Late (Orange):** Late manifests with logged reasons
*   **Real-Time Updates:** Adaptive refresh timing with immediate alert responses
*   **Tree-Style Organization:** Smart collapsible groups with expansion logic
*   **Professional Icons:** Custom taskbar and system tray icons

### 🔊 **Multi-Layer Audio System**
*   **Continuous Alert Sound:** Immediate attention-grabbing beep (alert.wav)
*   **Voice Announcements:** Every 20 seconds with professional speech synthesis
*   **Synchronized Audio:** Both systems work harmoniously without conflicts
*   **Enhanced Snooze:** Works for both Active and Missed manifests
*   **Configurable Duration:** 1-30 minute snooze options

### 📝 **Comprehensive Logging & User Tracking**
*   **Complete Audit Trail:** All acknowledgments logged with timestamps and usernames
*   **Custom Name Support:** Display names or Windows usernames in logs
*   **Reason Tracking:** Mandatory reason entry for missed manifests
*   **Professional Format:** "Carrier - Acknowledged Late: reason - UserName"
*   **JSON Format:** Human-readable logs in `logs/acknowledgments.json`
*   **Data Validation:** Error recovery for corrupted log files

### 🛠️ **System Integration & Settings**
*   **Professional System Tray:** Custom icon integration
*   **Taskbar Icon Fix:** Proper Windows taskbar icon display
*   **Configurable Settings:** Comprehensive settings dialog with validation
*   **Path Management:** Customizable data and log file locations
*   **Auto-Configuration:** Intelligent defaults with user customization

### ⏰ **Advanced Scheduling**
*   **Flexible Configuration:** JSON-based manifest time and carrier setup
*   **Day-Change Logic:** Automatic reset at midnight without restart
*   **Timezone Aware:** Proper handling of date boundaries
*   **Config Reload:** Live configuration updates without application restart

### 🔧 **Robust Error Handling**
*   **Speech Failure Recovery:** Visual alerts continue if voice fails
*   **File Corruption Protection:** Automatic backup and recovery
*   **Network Resilience:** Graceful handling of resource unavailability  
*   **Silent Failures:** Non-critical errors don't disrupt operation

## Technical Stack

- **Language:** Python 3.x
- **GUI Framework:** PyQt5 
- **Audio:** PyQt5 QSound + Windows SAPI (pyttsx3)
- **Architecture:** Modular design with separation of concerns
- **Deployment:** Single-file executable or source installation
- **Compatibility:** Windows 10/11 (optimized for warehouse PCs)

## Project Structure

```
/manifest-alert-system/
|-- data/
|   `-- config.json         # Manifest schedules and carrier configuration
|-- logs/
|   `-- acknowledgments.json  # Complete audit trail of all actions
|-- resources/
|   |-- alert.wav           # Audio alert sound file
|   `-- icon.ico           # Application icon for tray and window
|-- alert_display.py        # Main GUI application with all functionality
|-- data_manager.py         # Configuration and data file management
|-- logger.py               # Acknowledgment logging system
|-- main.py                 # Application entry point and tray setup
|-- scheduler.py            # Manifest status calculation logic
|-- sound_handler.py        # Audio alert management
|-- test_voice_announcements.py  # Voice system testing suite
|-- test_live_voice.py      # Live testing scenarios
|-- USER_INSTRUCTIONS.md    # Complete operator user guide
|-- VOICE_TESTING_REPORT.md # Technical voice system documentation
|-- requirements.txt        # Python dependency list
`-- readme.md              # This file
```

## 🚀 Quick Start Deployment

### Prerequisites
- Windows 10/11
- Python 3.x installed
- Audio output available (speakers/headset)
- Internet connection for initial setup

### Installation Steps
1. **Clone Repository:**
   ```bash
   git clone https://github.com/ropevp/manifest_alert.git
   cd manifest_alert
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Manifest Schedule:**
   ```bash
   # Edit data/config.json with your manifest times
   {
     "manifests": [
       {
         "time": "11:00",
         "carriers": ["Carrier 1", "Carrier 2"]
       }
     ]
   }
   ```

4. **Test Voice System:**
   ```bash
   python test_voice_announcements.py
   ```

5. **Run Application:**
   ```bash
   python main.py
   ```

### Verification Steps
- ✅ Check system tray for manifest alert icon
- ✅ Verify voice announcements work with test script
- ✅ Test acknowledgment workflow with sample data
- ✅ Confirm window maximizes during alerts
- ✅ Validate multi-monitor support if applicable

## 🏭 Latest Enhancements (v2.0)

### ✨ **Recent Updates**
- **Custom User Names**: Personalized acknowledgment display names with 20-character limit
- **Enhanced Window Stability**: Zero minimization during color changes and operations  
- **Improved Snooze Logic**: Snooze button appears for both Active and Missed manifests
- **Professional Icon Integration**: Proper taskbar and system tray icon display
- **Adaptive Timer Logic**: Guaranteed 30-second timer operation in all states
- **Smart Expansion Rules**: Groups expand when all items are acknowledged
- **Username Format**: Clean "Carrier - Acknowledged - Name" display format

## 🛠️ Git Repository Cleanup Guide

### Current Status
- **Main Branch**: `Alert_and_UI_update` (current production code)
- **Recommended Action**: Merge to main and clean up old branches

### Step-by-Step Cleanup

#### 1. Merge Current Branch to Main
```bash
# Switch to main branch
git checkout main

# Merge your current branch
git merge Alert_and_UI_update

# Push updated main
git push origin main
```

#### 2. Delete Old Remote Branches
```bash
# List all remote branches
git branch -r

# Delete specific remote branches (replace branch-name with actual names)
git push origin --delete old-branch-name
git push origin --delete another-old-branch

# Example for common branch names:
git push origin --delete feature/initial-setup
git push origin --delete hotfix/bug-fixes
```

#### 3. Clean Up Local Branches
```bash
# List local branches
git branch

# Delete local branches
git branch -d old-branch-name
git branch -D force-delete-branch-name

# Clean up tracking references
git remote prune origin
```

#### 4. Set Main as Default Branch
```bash
# Ensure main is default locally
git checkout main

# Push and set upstream
git push -u origin main
```

### GitHub Web Interface Cleanup
1. Go to your repository on GitHub.com
2. Navigate to **Settings** → **Branches**
3. Set `main` as the default branch
4. Go to **Branches** tab and delete old branches using the trash icon

## 📖 Updated Documentation

### User Guides
- **`USER_INSTRUCTIONS.md`** - Complete operator manual with screenshots
- **`USER_INSTRUCTIONS_CONFLUENCE.txt`** - Confluence-ready documentation
- **`VOICE_TESTING_REPORT.md`** - Technical voice system details

### For Administrators
- **`tickets.md`** - Development progress and feature tracking
- **Test Scripts** - Comprehensive testing utilities included
- **Error Handling** - Built-in recovery and backup systems

## 🎯 Production Features

### Warehouse-Optimized
- **24/7 Operation:** Designed for continuous warehouse deployment
- **Zero-Maintenance:** Automatic recovery and day-change handling  
- **Professional Audio:** Clear voice announcements in noisy environments
- **Visual Prominence:** Maximum visibility during critical alerts
- **Reliable Logging:** Complete audit trail for compliance

### Administrative Benefits
- **Simple Configuration:** JSON-based setup, no database required
- **Version Control:** GitHub repository with full change tracking
- **Comprehensive Testing:** Built-in test suites for validation
- **Detailed Documentation:** Complete operator and admin guides
- **Modular Design:** Easy customization and future enhancements

## 🏭 Warehouse Deployment Ready

The Manifest Alert System is **production-ready** with all core functionality implemented, tested, and documented. Features professional voice announcements, robust error handling, and warehouse-optimized visual alerts for reliable 24/7 operation.

### ✅ Enhanced Deployment Checklist
- [x] Voice announcements tested and verified
- [x] Window management stability ensured (zero minimization)
- [x] Multi-monitor support implemented  
- [x] Custom user names and accountability tracking
- [x] Professional taskbar and system tray icons
- [x] Adaptive refresh timing (5s alerts, 30s normal)
- [x] Smart group expansion logic
- [x] Enhanced snooze functionality for Active/Missed
- [x] Comprehensive user documentation updated
- [x] Error handling and recovery systems in place
- [x] Test suites available for validation
- [x] GitHub repository with latest production code

**Ready for immediate warehouse deployment with enhanced user accountability and professional UI.**