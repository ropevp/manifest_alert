#!/usr/bin/env python3
"""
Test script to verify day rollover behavior
"""
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from scheduler import get_manifest_status
    import json
    
    print("=== DAY ROLLOVER TEST ===")
    print(f"Current system time: {datetime.now()}")
    print(f"Current date: {datetime.now().date().isoformat()}")
    print()
    
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        manifests = config.get('manifests', [])
        print("MANIFEST STATUS CHECK:")
        print("-" * 50)
        
        now = datetime.now()
        for manifest in manifests:
            time_str = manifest['time']
            carriers = manifest.get('carriers', [])
            status = get_manifest_status(time_str, now)
            
            print(f"Time: {time_str}")
            print(f"  Status: {status}")
            print(f"  Carriers: {', '.join(carriers)}")
            print()
        
        # Check acknowledgments
        ack_path = os.path.join(os.path.dirname(__file__), 'ack.json')
        if os.path.exists(ack_path):
            with open(ack_path, 'r') as f:
                ack_data = json.load(f)
            
            print("ACKNOWLEDGMENT DATA:")
            print("-" * 50)
            today = now.date().isoformat()
            today_acks = [ack for ack in ack_data if ack.get('date') == today]
            yesterday_acks = [ack for ack in ack_data if ack.get('date') != today and ack.get('date')]
            
            print(f"Today ({today}): {len(today_acks)} acknowledgments")
            print(f"Previous days: {len(yesterday_acks)} acknowledgments")
            
            if yesterday_acks:
                print("\nPrevious day acknowledgments (should not affect today):")
                for ack in yesterday_acks[:3]:  # Show first 3
                    print(f"  {ack.get('date')} {ack.get('manifest_time')} - {ack.get('carrier')}")
        
    else:
        print("No config.json found!")
        
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== EXPECTED BEHAVIOR ===")
print("- All manifest times should show 'Pending' status")
print("- No acknowledgments should apply to new day")
print("- All cards should appear as OPEN (blue borders)")
print("- Summary should show countdown to first manifest")
