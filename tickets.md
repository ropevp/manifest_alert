# Manifest Alert System: Feature Implementation Tickets
# to update time manually in admin powershell:
"powershell -Command "Set-Date -Date (Get-Date).Date.AddDays(1).AddSeconds(-30)"

## Ticket 1: Day-Change Logic (Auto-Reset at Midnight) ✅
**Description:**
Automatically reset the manifest list and acknowledgment log at midnight, so each day starts fresh without needing to restart the app.

**Acceptance Test:**
- At midnight (or by simulating a day change), the UI and acknowledgment log reset for the new day.
- No previous day's acknowledgments are shown.

**Status:**
✅ Passed. Tested by simulating a day change; UI and log reset as expected.
---

## Ticket 2: System Tray Integration
**Description:**
Add a system tray icon with menu options: Show/Hide Window, Exit. The app should minimize to tray and restore from tray.

**Acceptance Test:**
 - Clicking the tray icon or menu shows/hides the main window.
 - Exiting from the tray menu closes the app cleanly.

**Status:**
 - ✅ Passed. Tray integration works as expected.
**Status:**
✅ Passed. Tray integration works as expected.
---

## Ticket 3: Snooze/Silence Alerts
**Description:**
Add a "Snooze" button to temporarily silence audible alerts and hide the window for a user-configurable duration (e.g., 1-5 minutes).

**Acceptance Test:**
- Clicking "Snooze" silences sound and hides the window for the selected duration.
- Alerts resume after snooze expires.

**Notes:**
- Snooze duration, pre-warning minutes (default 2), and missed time should be configurable and saved to JSON settings.
- Add a settings dialog accessible from the system tray menu or a cog/settings icon in the UI.

**Status:**
✅ Implemented. "Snooze" silences alerts, hides window, and resumes after the set duration.
---
**Status:**
 - ✅ Implemented. "Snooze" silences alerts, hides window, and resumes after the set duration.

## Ticket 4: Monitor Switching
**Description:**
Add a "Switch Monitor" button to cycle the application window through all available displays using QApplication.screens().

**Acceptance Test:**
- Clicking "Switch Monitor" moves the window to the next available screen.
- The window appears fully on the new screen.

**Status:**
- ✅ Passed. Monitor switching cycles screens correctly and displays the window fully on each monitor.

---

  
**---**
  
## Ticket 5: Always-on-Top Option
**Status:** In Progress
**Description:**
Add a toggle to keep the alert window always on top of other windows.

**Acceptance Test:**
- When enabled, the window stays above all other windows.
- When disabled, normal stacking order resumes.

---

## Ticket 6: Robust Error/Status Reporting
**Description:**
Improve error dialogs and add a status bar for non-intrusive feedback (e.g., config reloads, log errors, etc.).

**Acceptance Test:**
- All errors are reported clearly, and non-critical info appears in the status bar.

---

## Ticket 8: Shared Config and Log Storage (Network/Cloud/DB)
**Description:**
Allow the application to use a shared config and log location (e.g., network folder, Google Drive, or central database) so multiple PCs (warehouse, manager) can access the same data.

**Acceptance Test:**
- The app can be pointed to a shared folder or DB and will read/write config and logs from there.
- Multiple PCs can see the same manifests and logs.

**Notes:**
- Start with a shared network folder or cloud drive for simplicity.
- Consider SQLite for robust multi-user logging if needed.

---

## Ticket 9: SQLite Log/Config Storage & Export
**Description:**
Replace JSON log/config with SQLite database for robust, scalable, and queryable storage. Support exporting historical log data to a file (CSV or JSON) for a user-selected date range. If the export filename exists, append _01, _02, etc. Add a UI date selector for export.

**Acceptance Test:**
- All log and config data is stored in SQLite, not JSON.
- User can select a date range in the UI and export logs for that range.
- Exported file is named with the date range and, if needed, _01, _02, etc.
- Exported data matches the selected range and is complete.

**Notes:**
- Use SQLite for all logging and config.
- UI must allow date selection and export.
- Export format can be CSV or JSON (user choice or default).

---

## Ticket 7: Documentation and User Guide
**Description:**
Update the README and add a user guide for operators, including screenshots and troubleshooting.

**Acceptance Test:**
- Documentation is clear, up-to-date, and covers all features.

---

Ticket 10: UI Enhancements:

""
Manifest Times - Installation Instructions
Option 1: CustomTkinter (Recommended for Beginners)
Installation
bashpip install customtkinter
Key Features

Modern, clean UI with built-in theming
Easy to customize colors and fonts
Lightweight and responsive
Good documentation and community support

Usage
bashpython manifest_times_customtkinter.py

Option 2: PyQt6 (Most Professional)
Installation
bashpip install PyQt6
Key Features

Professional-grade UI framework
Advanced styling with QSS (CSS-like)
Superior performance and features
Industry standard for desktop applications

Usage
bashpython manifest_times_pyqt6.py

Design Features Implemented
Font Sizes (Maximized for Visibility)

Next Delivery Time: 96pt (huge and unmissable)
App Title: 42pt
Section Headers: 29pt
Schedule Times: 26pt
Current Time: 18pt
Countdown: 34pt
Services: 17pt

Professional Color Scheme

Background: Light gray-blue gradient
Cards: White with subtle shadows
Next Delivery: Green (#28a745)
Countdown: Red (#dc3545)
Text: Professional dark grays
Borders: Light gray (#e9ecef)

Visual Enhancements

Rounded corners on all cards
Subtle shadows and borders
Hover effects on schedule items
Highlighted next delivery slot
Scrollable schedule list
Real-time clock updates
Live countdown timer


Code Structure
Both implementations include:

Main Application Class

Window setup and configuration
UI component creation
Timer management


UI Setup Methods

Header with title and current time
Prominent next delivery card
Scrollable schedule list
Footer with status info


Data Management

Sample delivery schedule
Next delivery detection
Time calculations


Real-time Updates

Current time display
Countdown to next delivery
Automatic refresh every second




Customization Tips for GitHub Copilot
When sharing with GitHub Copilot Sonnet 4, mention:
For CustomTkinter:

"Use CTkFont for custom font sizes"
"Configure fg_color for backgrounds"
"Use CTkFrame for card-like containers"
"Implement threading for real-time updates"

For PyQt6:

"Use QSS stylesheets for advanced styling"
"Implement QTimer for real-time updates"
"Use QFont for precise typography control"
"Apply gradient backgrounds with qlineargradient"

Key Requirements:

"Maximum font sizes for visibility"
"Professional gray-blue color scheme"
"Real-time countdown timer"
"Highlighted next delivery slot"
"Scrollable schedule with hover effects"
"1200x800 window size"
"Clean, corporate appearance"


Data Integration
To integrate with your actual delivery data:

Replace the delivery_schedule list with your data source
Modify the time format parsing as needed
Add your specific delivery service names
Implement data refresh mechanisms
Add error handling for data connectivity

Both code examples are complete, runnable applications that demonstrate the professional design with maximum visibility fonts as requested.
""

**Implementation Plan:**
1. Implement Ticket 1 and write a test for day-change reset.
2. Proceed to Ticket 2 (System Tray Integration) and Ticket 3 (Snooze).
3. **Backup UI file** (`alert_display.py`) before starting Ticket 4.
4. Implement Ticket 4: collapse/expand tree UI with monitor switch and fullscreen.
5. After core UX (Tickets 2-6), implement Ticket 8 (shared config/log) and Ticket 9 (SQLite+export).
6. Finish with Ticket 7 (documentation/user guide).
7. After each feature, run regression tests to ensure previous features still work.
