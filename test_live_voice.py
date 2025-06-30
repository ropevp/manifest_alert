#!/usr/bin/env python3
"""
Test script to create realistic alert scenarios and test voice announcements
in the live application. This will temporarily modify the config to create
manifests that should be alerting right now.
"""
import json
import os
from datetime import datetime, timedelta
import shutil

def backup_config():
    """Backup the current config"""
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    backup_path = config_path + '.test_backup'
    if os.path.exists(config_path):
        shutil.copyfile(config_path, backup_path)
        print(f"✅ Backed up config to {backup_path}")
    return backup_path

def restore_config():
    """Restore the original config"""
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    backup_path = config_path + '.test_backup'
    if os.path.exists(backup_path):
        shutil.copyfile(backup_path, config_path)
        os.remove(backup_path)
        print(f"✅ Restored original config")
    else:
        print("❌ No backup found to restore")

def create_test_scenarios():
    """Create different test scenarios for voice announcements"""
    now = datetime.now()
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    
    scenarios = {
        "1": {
            "name": "Single Active Manifest",
            "description": "One manifest 5 minutes overdue (Active)",
            "manifests": [
                {
                    "time": (now - timedelta(minutes=5)).strftime("%H:%M"),
                    "carriers": ["Test Carrier 1"]
                }
            ]
        },
        "2": {
            "name": "Single Missed Manifest", 
            "description": "One manifest 45 minutes overdue (Missed)",
            "manifests": [
                {
                    "time": (now - timedelta(minutes=45)).strftime("%H:%M"),
                    "carriers": ["Test Carrier 2"]
                }
            ]
        },
        "3": {
            "name": "Multiple Active Manifests",
            "description": "Two different times, both Active (5 and 10 minutes late)",
            "manifests": [
                {
                    "time": (now - timedelta(minutes=5)).strftime("%H:%M"),
                    "carriers": ["Test Carrier 1", "Test Carrier 2"]
                },
                {
                    "time": (now - timedelta(minutes=10)).strftime("%H:%M"),
                    "carriers": ["Test Carrier 3"]
                }
            ]
        },
        "4": {
            "name": "Multiple Missed Manifests",
            "description": "Two different times, both Missed (35 and 50 minutes late)",
            "manifests": [
                {
                    "time": (now - timedelta(minutes=35)).strftime("%H:%M"),
                    "carriers": ["Test Carrier 1"]
                },
                {
                    "time": (now - timedelta(minutes=50)).strftime("%H:%M"),
                    "carriers": ["Test Carrier 2", "Test Carrier 3"]
                }
            ]
        },
        "5": {
            "name": "Mixed Active and Missed",
            "description": "One Active (10 min late) and one Missed (40 min late)",
            "manifests": [
                {
                    "time": (now - timedelta(minutes=10)).strftime("%H:%M"),
                    "carriers": ["Active Carrier"]
                },
                {
                    "time": (now - timedelta(minutes=40)).strftime("%H:%M"),
                    "carriers": ["Missed Carrier 1", "Missed Carrier 2"]
                }
            ]
        }
    }
    
    print("🎙️ Voice Announcement Test Scenarios")
    print("=" * 40)
    for key, scenario in scenarios.items():
        print(f"{key}. {scenario['name']}")
        print(f"   {scenario['description']}")
    print("0. Restore original config and exit")
    print()
    
    choice = input("Select a scenario to test (0-5): ").strip()
    
    if choice == "0":
        restore_config()
        return False
    
    if choice in scenarios:
        scenario = scenarios[choice]
        print(f"\n🔧 Setting up: {scenario['name']}")
        print(f"📋 {scenario['description']}")
        
        # Create the test config
        test_config = {
            "manifests": scenario["manifests"]
        }
        
        # Write to config file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2)
        
        print(f"✅ Test config created")
        print(f"🎙️ Expected voice announcement:")
        
        # Predict what the voice should say
        if choice == "1":
            time_str = scenario["manifests"][0]["time"]
            print(f"   'Manifest at {time_str}' (spoken as words)")
        elif choice == "2":
            time_str = scenario["manifests"][0]["time"]
            print(f"   'Manifest Missed at {time_str}. Manifest is 45 minutes Late'")
        elif choice == "3":
            print(f"   'Multiple manifests Active. Please acknowledge'")
        elif choice == "4":
            print(f"   'Multiple missed manifests. Please acknowledge'")
        elif choice == "5":
            print(f"   'Multiple Missed and Active Manifests. Please acknowledge'")
        
        print(f"\n🚀 Now run the main application to test!")
        print(f"📝 The voice should announce every 20 seconds")
        print(f"💡 You can acknowledge manifests to stop the alerts")
        print(f"🔄 Run this script again with option 0 to restore original config")
        return True
    else:
        print("❌ Invalid choice")
        return False

if __name__ == "__main__":
    print("Voice Announcement Test Setup")
    print("This will temporarily modify your manifest config to create test alerts.")
    print()
    
    # Backup the original config first
    backup_config()
    
    # Create test scenario
    if create_test_scenarios():
        print(f"\n⚠️  IMPORTANT: Run this script with option 0 to restore your original config when done testing!")
    else:
        print("✅ Test complete or cancelled")
