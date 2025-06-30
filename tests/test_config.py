#!/usr/bin/env python3
"""
Test script to verify the speech alert functionality by creating a temporary config
with a manifest time that should be active now.
"""
import json
import os
from datetime import datetime, timedelta

def create_test_config():
    # Get current time and create a manifest time 1 minute in the past (should be Active)
    now = datetime.now()
    active_time = (now - timedelta(minutes=1)).strftime("%H:%M")
    future_time = (now + timedelta(minutes=5)).strftime("%H:%M")
    
    test_config = {
        "manifests": [
            {
                "time": active_time,
                "carriers": [
                    "Test Carrier 1",
                    "Test Carrier 2"
                ]
            },
            {
                "time": future_time,
                "carriers": [
                    "Future Carrier"
                ]
            }
        ]
    }
    
    # Backup original config
    config_path = os.path.join("data", "config.json")
    backup_path = os.path.join("data", "config.json.backup")
    
    if os.path.exists(config_path):
        os.rename(config_path, backup_path)
        print(f"Backed up original config to {backup_path}")
    
    # Write test config
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print(f"Created test config with active time: {active_time}")
    print(f"Future time for testing: {future_time}")
    print("Run the application now - it should show active alerts and speak!")
    print("Press Ctrl+C to stop and restore original config")

def restore_config():
    config_path = os.path.join("data", "config.json")
    backup_path = os.path.join("data", "config.json.backup")
    
    if os.path.exists(backup_path):
        if os.path.exists(config_path):
            os.remove(config_path)
        os.rename(backup_path, config_path)
        print("Restored original config")
    else:
        print("No backup found")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_config()
    else:
        create_test_config()
