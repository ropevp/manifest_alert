# Manifest Alert System - Deployment Guide

This guide explains how to deploy the Manifest Alert System to another Windows PC, including single-PC and multi-PC enterprise setups.

## 🚀 Quick Start (Single PC)

### 1. Prerequisites Setup

#### Install Python
1. **Download Python 3.8 or newer**:
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.x.x" (latest version)
   - **IMPORTANT**: Check "Add Python to PATH" during installation
   - Choose "Install Now"

2. **Verify Python Installation**:
   - Open Command Prompt (cmd)
   - Type: `python --version`
   - Should show: `Python 3.x.x`

#### Install Git (Optional - for updates)
1. **Download Git**:
   - Go to: https://git-scm.com/download/win
   - Download and run the installer
   - Use default settings (just click "Next" through all screens)

2. **Verify Git Installation**:
   - Open Command Prompt
   - Type: `git --version`
   - Should show: `git version x.x.x`

#### System Requirements
- **Windows 10/11** PC
- **Administrator access** (for initial setup)
- **Internet connection** (for downloading dependencies)

### 2. Get the Application
**Option A: From Git Repository**

```cmd
# Clone the repository
git clone https://github.com/ropevp/manifest_alert.git
cd manifest_alert

# Optional: Switch to latest release branch
git checkout main
```

**Option B: Copy Files**
- Copy the entire `manifest_alerts` folder to the target PC
- Ensure all files and subfolders are included

### 3. Install Python Dependencies
Open **Command Prompt** or **PowerShell** in the project folder:

```cmd
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 4. Run the Application
```cmd
# Make sure virtual environment is activated
.venv\Scripts\activate

# Start the application
python main.py
```

### 5. First Run Setup
- Application automatically creates `app_data/` folder
- Default empty manifest schedule is created
- Ready to configure your manifest times!

---

## 🏢 Enterprise Deployment (Multi-PC)

### Scenario: Multiple warehouse PCs sharing manifest data

### 1. Choose Shared Storage Location
**Options:**
- **Network Drive**: `\\server\shared\ManifestData\`
- **Cloud Storage**: `C:\GoogleDrive\ManifestData\`
- **Local Share**: `C:\Shared\ManifestData\`

### 2. Deploy Application to Each PC
Repeat **Quick Start steps 1-4** on each PC.

### 3. Configure Data Sharing

**Option A: Pre-configure (IT Deployment)**
Create `app_data\settings.json` with shared location:
```json
{
  "app_data_folder": "\\\\server\\shared\\ManifestData"
}
```

**Option B: User Configuration**
1. Run application on each PC
2. Click **"Settings"** button
3. Browse to shared folder location
4. Click **"Save"**

### 4. Set Up Manifest Schedule
1. On **one PC**, configure manifest times in the shared location
2. **All other PCs** automatically use the same schedule
3. All acknowledgments are logged to the shared location

---

## 📁 File Structure After Deployment

### Single PC Setup
```
manifest_alerts/
├── main.py
├── requirements.txt
├── .venv/                  # Virtual environment
├── app_data/               # Created automatically
│   ├── settings.json       # Points to app_data/ by default
│   ├── config.json         # Manifest schedule
│   └── acknowledgments.json # Activity logs
└── resources/
    └── alert.wav
```

### Multi-PC Setup
```
PC 1, PC 2, PC 3:
manifest_alerts/
├── main.py
├── requirements.txt
├── .venv/
├── app_data/
│   └── settings.json       # Points to shared location
└── resources/

Shared Location (Network/Cloud):
\\server\shared\ManifestData\
├── config.json             # Shared manifest schedule
└── acknowledgments.json    # Shared activity logs
```

---

## 🔧 Configuration Commands

### Essential Setup Commands
```cmd
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test installation
python -c "import PyQt5; print('PyQt5 installed successfully')"

# Run application
python main.py
```

### Verify Installation
```cmd
# Check Python version
python --version

# Check installed packages
pip list

# Test audio (optional)
python -c "import pygame; pygame.mixer.init(); print('Audio support ready')"
```

### Troubleshooting Commands
```cmd
# Recreate virtual environment if issues
rmdir /s .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Check file permissions
dir app_data\
icacls app_data\

# Test settings manager
python -c "from settings_manager import get_settings_manager; print('Settings OK')"
```

---

## 🎯 Deployment Scenarios

### Scenario 1: Single Warehouse PC
1. **Deploy**: Copy files + install Python deps
2. **Configure**: Edit `app_data\config.json` with manifest times
3. **Test**: Run and verify alerts work
4. **Done**: Users can acknowledge manifests

### Scenario 2: Multiple PCs, Shared Network Drive
1. **Deploy**: Install app on each PC
2. **Configure**: Point all PCs to `\\server\ManifestData\`
3. **Setup**: Configure manifest schedule once
4. **Result**: All PCs share same data, separate acknowledgments

### Scenario 3: Cloud Storage (Google Drive)
1. **Deploy**: Install app on each PC  
2. **Configure**: Point to `C:\GoogleDrive\ManifestData\`
3. **Sync**: Google Drive syncs data between PCs
4. **Result**: Real-time data sharing via cloud

### Scenario 4: Offline PCs with Periodic Sync
1. **Deploy**: Use default local storage
2. **Sync**: Manually copy `app_data\` folder periodically
3. **Update**: Replace local files with master copy
4. **Result**: Offline operation with manual updates

---

## 🛠️ Advanced Configuration

### Create Windows Startup Shortcut
```cmd
# Create batch file: start_manifest_alerts.bat
@echo off
cd /d "C:\path\to\manifest_alerts"
call .venv\Scripts\activate
python main.py
```

### Pre-configure for IT Deployment
```json
# Create app_data\settings.json before deployment
{
  "app_data_folder": "\\\\your-server\\ManifestData"
}
```

### Network Share Setup (Windows)
```cmd
# Create shared folder (run as Administrator)
mkdir C:\ManifestData
net share ManifestData=C:\ManifestData /grant:everyone,full

# Access from other PCs
# \\computer-name\ManifestData
```

---

## 🔍 Testing Deployment

### Verify Installation
1. **Application starts**: `python main.py` runs without errors
2. **Files created**: `app_data\` folder appears
3. **Settings work**: Settings dialog opens and saves
4. **Audio works**: Alert sounds play
5. **Voice works**: Text-to-speech announces

### Test Multi-PC Setup
1. **Configure PC 1**: Set shared folder, add test manifest
2. **Configure PC 2**: Point to same shared folder
3. **Verify**: Both PCs show same manifest data
4. **Test sync**: Acknowledge on PC 1, check PC 2 sees it

---

## 📞 Troubleshooting

### Common Issues

#### Installation Problems
**"Python not found" or "'python' is not recognized"**
- Download Python from: https://www.python.org/downloads/
- **CRITICAL**: Check "Add Python to PATH" during installation
- Restart Command Prompt after installation
- Test with: `python --version`

**"pip not found" or "'pip' is not recognized"**
- Python 3.4+ includes pip automatically
- If missing, reinstall Python with "Add to PATH" checked
- Alternative: `python -m pip` instead of `pip`

**"git not found" (if using Git option)**
- Download Git from: https://git-scm.com/download/win
- Use default installation settings
- Alternative: Download ZIP from https://github.com/ropevp/manifest_alert/archive/main.zip

#### Runtime Problems
**"Module not found" errors**
- Activate virtual environment: `.venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`
- If virtual environment fails: `python -m venv .venv`

**Settings not saving**
- Check folder permissions
- Run as Administrator for initial setup
- Verify network connectivity for shared folders

**No audio alerts**
- Check system volume
- Verify `resources\alert.wav` exists
- Test: `python -c "import pygame; pygame.mixer.init()"`

**Voice announcements fail**
- Install Windows Speech Platform
- Check Text-to-Speech settings in Windows
- Test: `python -c "import pyttsx3; pyttsx3.init()"`

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Python 3.8+ installed on target PC
- [ ] Network/cloud storage accessible (if multi-PC)
- [ ] User permissions configured
- [ ] Manifest schedule prepared

### During Deployment  
- [ ] Copy application files
- [ ] Create virtual environment
- [ ] Install dependencies  
- [ ] Test application startup
- [ ] Configure data storage location
- [ ] Add manifest schedule
- [ ] Test alerts and acknowledgments

### Post-Deployment
- [ ] Create desktop shortcut (optional)
- [ ] Train users on interface
- [ ] Document local configuration
- [ ] Schedule regular backups
- [ ] Monitor system performance

---

*Last updated: June 30, 2025*
*Version: Enhanced for consolidated storage and enterprise deployment*
