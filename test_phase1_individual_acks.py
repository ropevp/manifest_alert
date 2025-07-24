#!/usr/bin/env python3
"""
Phase 1 Testing Script - Individual Acknowledgment System
Test the foundational data structure for individual carrier acknowledgments
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from alert_display import AlertDisplay
from datetime import datetime

# Global QApplication instance
app_instance = None

def init_qt_app():
    """Initialize QApplication if not already created"""
    global app_instance
    if app_instance is None:
        app_instance = QApplication(sys.argv)
    return app_instance

def test_phase1():
    """Test Phase 1 individual acknowledgment foundation"""
    print("🧪 TESTING PHASE 1 - Individual Acknowledgment System Foundation")
    print("=" * 70)
    
    try:
        # Initialize Qt Application
        init_qt_app()
        
        # Create AlertDisplay instance
        app = AlertDisplay()
        
        # Run the comprehensive test
        print("Running comprehensive Phase 1 testing...")
        success = app.test_individual_acknowledgment_system()
        
        if success:
            print("\n✅ PHASE 1 TESTING PASSED!")
            print("📋 Individual acknowledgment foundation is ready")
            print("🚀 Ready to proceed to Phase 2 (UI Modifications)")
        else:
            print("\n❌ PHASE 1 TESTING FAILED!")
            print("🔧 Please review error messages above")
            
        return success
        
    except Exception as e:
        print(f"\n💥 TESTING ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_methods():
    """Test individual methods independently"""
    print("\n🔍 INDIVIDUAL METHOD TESTING")
    print("-" * 40)
    
    try:
        # Initialize Qt Application
        init_qt_app()
        
        # Test data loading
        app = AlertDisplay()
        
        print("1. Testing load_acknowledgments()...")
        acks = app.load_acknowledgments()
        print(f"   ✓ Loaded {len(acks)} acknowledgments")
        
        print("2. Testing get_all_individual_acknowledgments_for_today()...")
        individual_acks = app.get_all_individual_acknowledgments_for_today()
        print(f"   ✓ Found {len(individual_acks)} individual acknowledgments")
        
        if individual_acks:
            print("   Individual acknowledgments:")
            for ack in individual_acks[:3]:  # Show first 3
                print(f"     - {ack['time']} {ack['carrier']} by {ack['user']}")
            if len(individual_acks) > 3:
                print(f"     ... and {len(individual_acks)-3} more")
        
        print("3. Testing acknowledgment key format...")
        today = datetime.now().date().isoformat()
        for ack in individual_acks[:2]:  # Test first 2
            expected_key = f"{today}_{ack['time']}_{ack['carrier']}"
            if ack['key'] == expected_key:
                print(f"   ✓ Key format correct: {ack['key']}")
            else:
                print(f"   ✗ Key format error: Expected {expected_key}, got {ack['key']}")
        
        return True
        
    except Exception as e:
        print(f"   💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Phase 1 Individual Acknowledgment System - Test Suite")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    try:
        # Initialize Qt Application
        init_qt_app()
        
        # Run basic method tests first
        basic_success = test_individual_methods()
        
        if basic_success:
            # Run comprehensive testing
            comprehensive_success = test_phase1()
            
            if comprehensive_success:
                print("\n" + "=" * 70)
                print("🎯 PHASE 1 COMPLETE AND TESTED!")
                print("✅ All individual acknowledgment foundation methods working")
                print("✅ Data structure validation passed")
                print("✅ Individual carrier status retrieval working")
                print()
                print("📢 READY FOR USER TESTING:")
                print("   1. Launch the main application")
                print("   2. Verify acknowledgment loading works correctly")
                print("   3. Test individual carrier status display")
                print("   4. Confirm ack.json structure is preserved")
                print()
                print("🚀 After user validation, proceed to Phase 2!")
            else:
                print("\n❌ Comprehensive testing failed")
        else:
            print("\n❌ Basic method testing failed")
    
    except Exception as e:
        print(f"\n💥 INITIALIZATION ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest complete.")
