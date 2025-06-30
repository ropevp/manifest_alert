# 📁 Ticket 11 Implementation Plan: Configurable Data Location

## 🎯 Feature Overview
Add settings interface to configure where the application stores `config.json` and `acknowledgments.json`, enabling multi-PC deployments and cloud synchronization.

## 🔧 Technical Implementation Strategy

### 1. **Settings Storage** 
```python
# Use QSettings for Windows registry storage
from PyQt5.QtCore import QSettings

settings = QSettings("ManifestAlert", "DataLocation")
data_path = settings.value("data_path", default_path)
```

### 2. **UI Components to Add**
- **Settings Button**: Add to main window toolbar
- **Tray Menu Item**: "Data Location Settings..."
- **Settings Dialog**: Folder browser with current path display
- **Status Indicator**: Show current data location in status bar

### 3. **File Structure Changes**
```
manifest_alerts/
├── data_manager.py         # Modify to use configurable paths
├── settings_dialog.py      # NEW: Settings UI dialog
├── path_manager.py         # NEW: Path validation and management
└── alert_display.py        # Add settings button and menu item
```

### 4. **Key Functions to Implement**
```python
# In path_manager.py
def get_data_path():          # Get current configured path
def set_data_path(path):      # Set new data path with validation
def validate_path(path):      # Check if path is writable/accessible
def migrate_data(old, new):   # Copy files to new location
def create_folder_structure(): # Ensure folders exist

# In settings_dialog.py  
def open_folder_browser():    # QFileDialog.getExistingDirectory()
def preview_file_locations(): # Show where files will be stored
def test_path_access():       # Validate selected path works
```

### 5. **Google Drive Desktop Integration**
- **Detection**: Check for `G:\` drive and Google Drive folders
- **Path Examples**: 
  - `G:\My Drive\ManifestAlert\`
  - `G:\Shared drives\Warehouse\ManifestAlert\`
- **Sync Handling**: Wait for sync completion before file operations

## 🚀 Implementation Steps

### Phase 1: Core Settings Infrastructure
1. Create `path_manager.py` with path utilities
2. Modify `data_manager.py` to use configurable paths
3. Add QSettings integration for persistence

### Phase 2: UI Implementation  
1. Create `settings_dialog.py` with folder browser
2. Add settings button to main window
3. Add tray menu option
4. Implement path validation feedback

### Phase 3: Data Migration
1. Implement file copying for path changes
2. Add backup/restore functionality
3. Handle error cases (permissions, network issues)

### Phase 4: Cloud Integration Testing
1. Test with Google Drive Desktop paths
2. Validate network drive support
3. Test multi-PC sharing scenarios

## 🧪 Testing Scenarios

### Local Testing
- [x] Default local path works
- [ ] Change to custom local folder
- [ ] Validate file creation/access
- [ ] Test path persistence across restarts

### Google Drive Testing  
- [ ] Set path to `G:\My Drive\manifest_data\`
- [ ] Verify file sync works correctly
- [ ] Test multiple PCs accessing same Google Drive folder
- [ ] Handle sync conflicts gracefully

### Network Drive Testing
- [ ] Set path to `\\server\share\manifest_data\`
- [ ] Test with mapped drives (`Z:\manifest_data\`)
- [ ] Handle network connectivity issues
- [ ] Validate multi-user access

## 📋 User Experience Flow

1. **Initial Setup**: 
   - User clicks settings icon → folder browser opens
   - Current location shown: `C:\Users\...\manifest_alerts\data\`
   - User browses to `G:\My Drive\ManifestAlert\`

2. **Path Change**:
   - Validate new path is writable
   - Confirm data migration 
   - Copy existing files to new location
   - Update application to use new path

3. **Multi-PC Setup**:
   - PC1: Set path to Google Drive folder
   - PC2: Set same Google Drive path
   - Both PCs now share config and acknowledgments

## ⚡ Benefits This Enables

### For IT/Administrators
- **Centralized Config Management**: Update manifest times from any PC
- **Cloud Backup**: Automatic data backup via Google Drive
- **Multi-Site Deployment**: Share settings across multiple warehouses

### For Operations
- **Data Continuity**: No data loss during PC upgrades/replacements
- **Real-time Sync**: Acknowledgments visible across all warehouse PCs
- **Disaster Recovery**: Data preserved in cloud storage

## 🎯 Priority Justification

**HIGH PRIORITY** because this feature:
- Enables true multi-PC warehouse deployments
- Provides automatic cloud backup capability
- Simplifies IT management and configuration
- Supports business growth (multiple locations)
- Aligns with modern cloud-first infrastructure

This ticket would transform the application from a single-PC solution to an enterprise-ready, cloud-enabled warehouse management tool.

---

*Ready for implementation when development bandwidth is available*
