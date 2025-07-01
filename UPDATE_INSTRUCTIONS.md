# Update Scripts for Manifest Alert System

This folder contains batch files to automatically update your Manifest Alert System to the latest version from GitHub.

## 📁 File Placement Instructions

**IMPORTANT**: Place these batch files in the **root directory** of your manifest_alerts folder, alongside files like:
- `main.py`
- `alert_display.py` 
- `requirements.txt`
- `.git` folder

```
manifest_alerts/
├── main.py
├── alert_display.py
├── requirements.txt
├── .git/
├── update_manifest_alerts.bat          ← Place here
└── force_update_manifest_alerts.bat    ← Place here
```

## 🔄 Update Options

### Option 1: Safe Update (Recommended)
**File**: `update_manifest_alerts.bat`

- ✅ Preserves your local changes
- ✅ Safely updates to latest version
- ✅ Automatically installs new dependencies
- ✅ Restores your changes after update

**When to use**: When you have made local configuration changes that you want to keep.

### Option 2: Force Update (Clean Slate)
**File**: `force_update_manifest_alerts.bat`

- ⚠️ **WARNING**: Overwrites ALL local changes
- ✅ Guarantees exact match with GitHub
- ✅ Automatically installs new dependencies
- ✅ Cleans up any extra files

**When to use**: When you want a completely clean installation or have issues with conflicts.

## 🚀 How to Use

1. **Download** the appropriate `.bat` file
2. **Place** it in your manifest_alerts root directory
3. **Right-click** the batch file and select "Run as administrator" (recommended)
4. **Follow** the on-screen instructions

## 🆕 What You'll Get After Update

- **Ultra-fast acknowledgment sync** (0.5s during alerts, 2s normal)
- **Enhanced user accountability** with custom display names
- **Professional taskbar and system tray icons**
- **Window stability improvements** (no more minimization issues)
- **Complete requirements.txt** with all dependencies

## 🔧 Manual Alternative

If the batch files don't work, you can manually update using these commands:

```bash
# Safe update
git stash
git pull origin main
pip install -r requirements.txt
git stash pop

# Force update
git fetch origin
git reset --hard origin/main
git clean -fd
pip install -r requirements.txt
```

## 📞 Support

If you encounter any issues:
1. Make sure you have Git installed
2. Ensure you have internet connectivity
3. Verify the batch file is in the correct directory
4. Try running Command Prompt as Administrator

The update process typically takes 30-60 seconds depending on your internet connection.
