#!/usr/bin/env python3
"""Test UI status calculation"""

import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication

# Test the UI status calculation  
def test_ui_status():
    app = QApplication(sys.argv)
    
    # Import after QApplication is created
    from alert_display import AlertDisplay
    
    # Create the display
    display = AlertDisplay()
    
    # Test the get_manifest_status function being used
    test_time = datetime.now().replace(hour=12, minute=9, second=0, microsecond=0)
    
    print(f"Testing UI status calculation at {test_time.strftime('%H:%M:%S')}")
    
    # Test various manifest times
    test_manifests = ["11:00", "12:10", "12:30", "13:45"]
    
    for manifest_time in test_manifests:
        # Check if the import worked or if fallback is being used
        try:
            from scheduler import get_manifest_status as scheduler_status
            status = scheduler_status(manifest_time, test_time)
            print(f"Scheduler function - Manifest {manifest_time}: {status}")
        except Exception as e:
            print(f"Scheduler import failed: {e}")
            
        # Test what the UI would use by calling its method
        try:
            # Simulate what populate_data does
            config = display.load_config()
            print(f"Config loaded: {len(config.get('manifests', []))} manifests")
            
            # Test the actual function the UI would call
            from alert_display import get_manifest_status
            ui_status = get_manifest_status(manifest_time, test_time)
            print(f"UI function - Manifest {manifest_time}: {ui_status}")
        except Exception as e:
            print(f"UI status calculation failed: {e}")
    
    app.quit()

if __name__ == "__main__":
    test_ui_status()
