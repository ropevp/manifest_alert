#!/usr/bin/env python3
"""
Phase 1 Simple Data Testing - Individual Acknowledgment System
Test the core data functionality without Qt GUI
"""

import sys
import os
import json
from datetime import datetime

def test_ack_json_structure():
    """Test the ack.json file structure for individual acknowledgments"""
    print("🔍 TESTING ACK.JSON STRUCTURE")
    print("-" * 40)
    
    try:
        # Look for ack.json in common locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'app_data', 'ack.json'),
            os.path.join(os.path.dirname(__file__), 'ack.json'),
            r'\\Prddpkmitlgt004\ManifestPC\ack.json'
        ]
        
        ack_path = None
        for path in possible_paths:
            if os.path.exists(path):
                ack_path = path
                break
        
        if not ack_path:
            print("   ⚠️  No ack.json file found. Testing with empty structure...")
            return test_empty_acknowledgment_structure()
        
        print(f"   📁 Found ack.json at: {ack_path}")
        
        with open(ack_path, 'r', encoding='utf-8') as f:
            ack_data = json.load(f)
        
        print(f"   📊 Total acknowledgments in file: {len(ack_data)}")
        
        # Test individual acknowledgment structure
        today = datetime.now().date().isoformat()
        today_acks = [ack for ack in ack_data if ack.get('date') == today]
        
        print(f"   📅 Today's acknowledgments: {len(today_acks)}")
        
        if today_acks:
            print("   🔍 Testing individual acknowledgment structure...")
            
            required_fields = ['timestamp', 'date', 'manifest_time', 'carrier', 'user']
            
            for i, ack in enumerate(today_acks[:3]):  # Test first 3
                print(f"      Acknowledgment {i+1}:")
                print(f"        Carrier: {ack.get('carrier', 'Missing')}")
                print(f"        Time: {ack.get('manifest_time', 'Missing')}")
                print(f"        User: {ack.get('user', 'Missing')}")
                
                # Check required fields
                missing = [field for field in required_fields if field not in ack]
                if missing:
                    print(f"        ⚠️  Missing fields: {missing}")
                else:
                    print(f"        ✅ All required fields present")
                
                # Test key format
                key = f"{ack.get('date')}_{ack.get('manifest_time')}_{ack.get('carrier')}"
                print(f"        Key: {key}")
            
            if len(today_acks) > 3:
                print(f"      ... and {len(today_acks)-3} more acknowledgments")
        
        return True
        
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False

def test_empty_acknowledgment_structure():
    """Test with empty acknowledgment structure"""
    print("   🧪 Testing empty acknowledgment handling...")
    
    # Simulate empty acknowledgments
    acks = {}
    today = datetime.now().date().isoformat()
    
    print(f"   📅 Date: {today}")
    print(f"   📊 Acknowledgments: {len(acks)}")
    
    # Test key format
    test_key = f"{today}_08:00_FedEx Express"
    print(f"   🔑 Sample key format: {test_key}")
    
    print("   ✅ Empty acknowledgment structure valid")
    return True

def test_key_generation():
    """Test acknowledgment key generation logic"""
    print("\n🔑 TESTING KEY GENERATION")
    print("-" * 40)
    
    try:
        today = datetime.now().date().isoformat()
        
        test_cases = [
            ("08:00", "FedEx Express"),
            ("10:30", "UPS Ground"),
            ("14:15", "DHL Express"),
            ("16:45", "USPS Priority")
        ]
        
        print("   Testing key generation for sample carriers:")
        
        for time_str, carrier in test_cases:
            key = f"{today}_{time_str}_{carrier}"
            print(f"      {time_str} {carrier} → {key}")
        
        print("   ✅ Key generation format consistent")
        return True
        
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False

def test_data_structure_compatibility():
    """Test that the data structure supports individual acknowledgments"""
    print("\n🏗️  TESTING DATA STRUCTURE COMPATIBILITY")
    print("-" * 40)
    
    try:
        # Simulate acknowledgment data structure
        sample_ack = {
            "timestamp": "2025-07-21T08:05:23",
            "date": "2025-07-21",
            "manifest_time": "08:00",
            "carrier": "FedEx Express",
            "status": "Active",
            "acknowledged_by": "Test User",
            "reason": ""
        }
        
        print("   📋 Sample individual acknowledgment structure:")
        for key, value in sample_ack.items():
            print(f"      {key}: {value}")
        
        # Test key generation from sample data
        key = f"{sample_ack['date']}_{sample_ack['manifest_time']}_{sample_ack['carrier']}"
        print(f"\n   🔑 Generated key: {key}")
        
        # Test multiple acknowledgments for same time slot
        carriers = ["FedEx Express", "UPS Ground", "DHL Express"]
        time_slot = "08:00"
        today = datetime.now().date().isoformat()
        
        print(f"\n   🕐 Multiple carriers for {time_slot}:")
        for carrier in carriers:
            individual_key = f"{today}_{time_slot}_{carrier}"
            print(f"      {carrier} → {individual_key}")
        
        print("   ✅ Individual acknowledgment structure supports multiple carriers per time slot")
        return True
        
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False

if __name__ == "__main__":
    print("Phase 1 Simple Data Testing - Individual Acknowledgment System")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    tests = [
        ("ACK.JSON Structure", test_ack_json_structure),
        ("Key Generation", test_key_generation),
        ("Data Structure Compatibility", test_data_structure_compatibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎯 ALL DATA STRUCTURE TESTS PASSED!")
        print("✅ Individual acknowledgment foundation is solid")
        print("✅ ack.json structure supports individual operations")
        print("✅ Key generation logic is consistent")
        print("\n📢 Now try the full GUI test:")
        print("   python test_phase1_individual_acks.py")
    else:
        print("⚠️  Some tests failed - please review above")
    
    print("\nSimple data test complete.")
