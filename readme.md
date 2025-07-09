# Manifest Alert System

A simple, user-friendly desktop application for Windows to provide timely alerts for shipping manifests. It runs in the system tray and displays a clean, modern interface to track all manifest schedules.

## Core Features

*   **System Tray Operation:** The application lives in the system tray for easy access without cluttering the taskbar.
*   **Unified Schedule View:** A single, scrollable window displays all of today's manifests in a clear, chronological list.
*   **Clear Status Indicators:** Each item in the list is color-coded for at-a-glance status updates:
    *   **Active (Flashing Red):** An alert that is currently due or overdue and requires attention.
    *   **Acknowledged (Green):** An alert that has been successfully handled by the user.
    *   **Pending (Gray):** An upcoming scheduled manifest.
    *   **Missed (Dark Red):** A manifest that was not acknowledged during its active period.
*   **User-Friendly Controls:** A simple toolbar provides essential controls:
    *   **Snooze:** Temporarily dismisses and silences the alert window for a configurable duration (e.g., 1-5 minutes).
    *   **Minimize:** Hides the window. Can be configured to only work when no alerts are active.
    *   **Switch Monitor:** Cycles the application window through all available displays. This will be implemented correctly using screen geometry detection.
*   **Audible Alerts:** Plays a configurable sound when an alert becomes active.
*   **Centralized Configuration:** All schedules and carriers are managed in a simple `data/config.json` file.
*   **Persistent Logging:** All user acknowledgments are logged with timestamps to `logs/acknowledgments.json` for auditing purposes.

## Technical Stack

*   **Language:** Python 3
*   **GUI Framework:** PyQt5

## Proposed Project Structure

```
/manifest-alert-system/
|-- data/
|   `-- config.json         # Defines time slots and carriers
|-- logs/
|   `-- acknowledgments.json  # Logs all user actions
|-- resources/
|   |-- alert.wav           # Sound file for alerts
|   `-- app_icon.ico        # Application icon for tray and window
|-- alert_display.py        # Manages the main GUI window and widgets
|-- data_manager.py         # Handles reading/writing config and log files
|-- logger.py               # Handles logging logic
|-- main.py                 # Main application entry point, handles tray icon and orchestrates components
|-- scheduler.py            # Determines the status of each manifest based on time
|-- sound_handler.py        # Manages playing alert sounds
|-- requirements.txt        # Lists Python dependencies
`-- readme.md               # This file
```

## Setup and Installation

1.  **Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
2.  **Configure Schedules:**
    *   Edit `data/config.json` to define your manifest time slots and associated carriers.
3.  **Run the Application:**
    ```sh
    python main.py
    ```

## Key Improvements Over Previous Version

*   **Simplified Logic:** A single source of truth (the `scheduler`) will determine the state of all items, which are then rendered by the `alert_display`. This avoids complex state management and bugs.
*   **Robust UI:** The UI will be built from the ground up to be a standard, non-intrusive window with reliable controls.
*   **Correct Monitor Switching:** The monitor switching logic will be implemented using `QApplication.screens()` to correctly identify and cycle through all connected displays.
*   **Better Icons:** Standard, recognizable icons (e.g., from `QStyle.StandardPixmap`) will be used for a professional look and feel.