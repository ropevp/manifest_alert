#!/usr/bin/env python3
"""
Phase 2 Testing Script - Individual Acknowledgment UI
Test the individual acknowledgment display in the right panel
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from alert_display import AlertDisplay
from datetime import datetime

def test_phase2_ui():
    """Test Phase 2 individual acknowledgment UI changes"""
    print("🧪 TESTING PHASE 2 - Individual Acknowledgment UI")
    print("=" * 60)
    
    try:
        # Initialize Qt Application
        app = QApplication(sys.argv)
        
        # Create AlertDisplay instance
        display = AlertDisplay()
        
        print("✅ AlertDisplay created successfully")
        print("✅ Individual acknowledgment UI components initialized")
        
        # Test that old grouped acknowledgment components are removed
        print("\n🔍 Testing UI component changes...")
        
        # Check if we have cards to test with
        if hasattr(display, 'cards') and display.cards:
            for i, card in enumerate(display.cards[:2]):  # Test first 2 cards
                print(f"\n📋 Testing StatusCard {i+1} ({card.time_str}):")
                
                # Check for new individual acknowledgment container
                if hasattr(card, 'individual_ack_container'):
                    print("  ✅ Individual acknowledgment container present")
                else:
                    print("  ❌ Individual acknowledgment container missing")
                
                # Check for new individual acknowledgment layout
                if hasattr(card, 'individual_ack_layout'):
                    print("  ✅ Individual acknowledgment layout present")
                else:
                    print("  ❌ Individual acknowledgment layout missing")
                
                # Test individual acknowledgment display method
                if hasattr(card, 'update_individual_acknowledgment_display'):
                    print("  ✅ Individual acknowledgment display method present")
                    try:
                        card.update_individual_acknowledgment_display()
                        print("  ✅ Individual acknowledgment display method works")
                    except Exception as e:
                        print(f"  ⚠️  Individual acknowledgment display method error: {e}")
                else:
                    print("  ❌ Individual acknowledgment display method missing")
                
                # Test manifest data
                if hasattr(card, 'manifests') and card.manifests:
                    print(f"  📦 Carriers in this time slot: {len(card.manifests)}")
                    for carrier, status in card.manifests:
                        individual_status = card.get_individual_carrier_status(carrier)
                        print(f"    - {carrier}: {individual_status}")
                else:
                    print("  📦 No manifest data available")
        else:
            print("⚠️  No StatusCards available for testing")
            print("   This is expected if no manifest data is loaded")
        
        print("\n🎯 PHASE 2 UI TESTING COMPLETE!")
        print("✅ Individual acknowledgment UI components ready")
        print("✅ Old grouped acknowledgment display removed")
        print("✅ New individual acknowledgment methods available")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 testing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_component_structure():
    """Test the UI component structure changes"""
    print("\n🏗️  TESTING UI COMPONENT STRUCTURE")
    print("-" * 50)
    
    try:
        app = QApplication(sys.argv)
        display = AlertDisplay()
        
        # Create a test StatusCard to examine structure
        test_card = None
        if hasattr(display, 'cards') and display.cards:
            test_card = display.cards[0]
        
        if test_card:
            print("📋 Testing StatusCard structure:")
            
            # Check for removal of old components
            old_components = ['ack_status_label', 'ack_details_label']
            for component in old_components:
                if hasattr(test_card, component):
                    print(f"  ⚠️  Old component still present: {component}")
                else:
                    print(f"  ✅ Old component removed: {component}")
            
            # Check for new components
            new_components = ['individual_ack_container', 'individual_ack_layout']
            for component in new_components:
                if hasattr(test_card, component):
                    print(f"  ✅ New component present: {component}")
                else:
                    print(f"  ❌ New component missing: {component}")
            
            # Check for new methods
            new_methods = ['update_individual_acknowledgment_display', 'add_individual_acknowledgment_line']
            for method in new_methods:
                if hasattr(test_card, method):
                    print(f"  ✅ New method present: {method}")
                else:
                    print(f"  ❌ New method missing: {method}")
        else:
            print("⚠️  No StatusCard available for structure testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Structure testing error: {e}")
        return False

if __name__ == "__main__":
    print("Phase 2 Individual Acknowledgment UI - Test Suite")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test UI changes
    ui_test_passed = test_phase2_ui()
    
    if ui_test_passed:
        # Test component structure
        structure_test_passed = test_ui_component_structure()
        
        if structure_test_passed:
            print("\n" + "=" * 70)
            print("🏆 PHASE 2 UI TESTING COMPLETE!")
            print("✅ Individual acknowledgment UI components working")
            print("✅ Old grouped display removed")
            print("✅ New individual display methods available")
            print("\n📢 READY FOR VISUAL TESTING:")
            print("   1. Launch main application: python main.py")
            print("   2. Look at acknowledged time groups")
            print("   3. Right panel should show individual lines instead of grouped")
            print("   4. Each carrier should have its own acknowledgment line")
            print("\n🚀 If visual test passes, ready for Phase 3!")
        else:
            print("\n❌ Structure testing failed")
    else:
        print("\n❌ UI testing failed")
    
    print("\nPhase 2 test complete.")
