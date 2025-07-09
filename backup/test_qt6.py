#!/usr/bin/env python3
"""Test script to verify PyQt6 upgrade is successful"""

import sys
import os

def test_imports():
    """Test all PyQt6 imports"""
    print("Testing PyQt6 imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        print("✓ PyQt6.QtWidgets imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtWidgets: {e}")
        return False
        
    try:
        from PyQt6.QtGui import QIcon, QAction
        print("✓ PyQt6.QtGui imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtGui: {e}")
        return False
        
    try:
        from PyQt6.QtCore import Qt, QTimer
        print("✓ PyQt6.QtCore imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtCore: {e}")
        return False
    
    try:
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        print("✓ PyQt6.QtMultimedia imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtMultimedia: {e}")
        return False
    
    return True

def test_application_imports():
    """Test application module imports"""
    print("\nTesting application imports...")
    
    try:
        from alert_display import AlertDisplay
        print("✓ AlertDisplay imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import AlertDisplay: {e}")
        return False
        
    try:
        from main import load_main_settings, position_window_on_monitor
        print("✓ Main functions imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import main functions: {e}")
        return False
    
    return True

def test_qt_application():
    """Test creating a QApplication instance"""
    print("\nTesting QApplication creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        print("✓ QApplication created successfully")
        
        # Test screen detection
        from PyQt6.QtGui import QGuiApplication
        screens = QGuiApplication.screens()
        print(f"✓ Detected {len(screens)} monitor(s)")
        
        app.quit()
        return True
    except Exception as e:
        print(f"✗ Failed to create QApplication: {e}")
        return False

if __name__ == "__main__":
    print("PyQt6 Migration Test")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test application imports
    if not test_application_imports():
        all_tests_passed = False
    
    # Test Qt application
    if not test_qt_application():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! PyQt6 migration successful!")
        print("\nYou can now run the application with:")
        print("  python main.py")
    else:
        print("❌ SOME TESTS FAILED! Check the errors above.")
    
    print("\nOld PyQt5 files have been moved to the backup/ folder:")
    print("  - alert_display_pyqt5_backup.py (old PyQt5 version)")
    print("  - ui_display_original.py (original PyQt6 version)")
