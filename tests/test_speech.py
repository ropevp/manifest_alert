#!/usr/bin/env python3
"""
Simple test script to verify speech functionality
"""
import pyttsx3
import threading

def test_speech():
    try:
        print("Testing speech synthesis...")
        engine = pyttsx3.init()
        engine.say("Manifest Due at eleven thirty")
        engine.runAndWait()
        print("Speech test completed successfully")
    except Exception as e:
        print(f"Speech test failed: {e}")

def test_speech_threaded():
    try:
        print("Testing threaded speech synthesis...")
        thread = threading.Thread(target=test_speech, daemon=True)
        thread.start()
        thread.join(timeout=10)  # Wait up to 10 seconds
        print("Threaded speech test completed")
    except Exception as e:
        print(f"Threaded speech test failed: {e}")

if __name__ == "__main__":
    print("=== Speech Functionality Test ===")
    test_speech()
    print()
    test_speech_threaded()
    print("\nTest completed.")
