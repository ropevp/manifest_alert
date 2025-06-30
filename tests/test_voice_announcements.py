#!/usr/bin/env python3
"""
Test script to verify voice announcements for different manifest statuses.
This script will test all possible voice announcement scenarios.
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import the speech functionality from the main application
import pyttsx3
import threading
import time

def test_voice_announcements():
    """Test all different voice announcement scenarios"""
    
    def _speak(text):
        """Replicate the _speak method from AlertDisplay"""
        try:
            print(f"🎙️ Speaking: '{text}'")
            engine = pyttsx3.init()
            # Use Zira voice (better quality female voice)
            voices = engine.getProperty('voices')
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id)  # Zira (female)
            # Get current speech rate and reduce by 10%
            rate = engine.getProperty('rate')
            engine.setProperty('rate', int(rate * 0.9))  # 10% slower
              
            # Handle pause by splitting on period and adding delay
            if '. ' in text:
                parts = text.split('. ')
                for i, part in enumerate(parts):
                    if part.strip():  # Skip empty parts
                        engine.say(part)
                        engine.runAndWait()
                        if i < len(parts) - 1:  # Don't pause after the last part
                            time.sleep(1)  # 1 second pause between parts
            else:
                engine.say(text)
                engine.runAndWait()
            print("✅ Speech completed successfully")
        except Exception as e:
            print(f"❌ Speech failed: {e}")

    def _number_to_words(n):
        """Convert number to words for time"""
        words = [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
            'twenty', 'twenty one', 'twenty two', 'twenty three', 'twenty four', 'twenty five', 'twenty six', 'twenty seven', 'twenty eight', 'twenty nine',
            'thirty', 'thirty one', 'thirty two', 'thirty three', 'thirty four', 'thirty five', 'thirty six', 'thirty seven', 'thirty eight', 'thirty nine',
            'forty', 'forty one', 'forty two', 'forty three', 'forty four', 'forty five', 'forty six', 'forty seven', 'forty eight', 'forty nine',
            'fifty', 'fifty one', 'fifty two', 'fifty three', 'fifty four', 'fifty five', 'fifty six', 'fifty seven', 'fifty eight', 'fifty nine'
        ]
        return words[n] if 0 <= n < 60 else str(n)

    def _trigger_speech(time_str, minutes_late=0):
        """Generate speech for a specific time"""
        try:
            hour, minute = map(int, time_str.split(':'))
            hour_12 = hour % 12 or 12
            spoken_hour = _number_to_words(hour_12)
            
            # Handle minutes properly
            if minute == 0:
                spoken_minute = "o'clock"
            elif minute < 10:
                spoken_minute = f"oh {_number_to_words(minute)}"
            else:
                spoken_minute = _number_to_words(minute)
            
            if minute == 0:
                spoken_time = f"{spoken_hour} o'clock"
            else:
                spoken_time = f"{spoken_hour} {spoken_minute}"
            
            if minutes_late >= 30:  # Missed (30+ minutes late)
                text = f"Manifest Missed, at {spoken_time}. Manifest is {minutes_late} minutes Late"
            else:  # Active (0-29 minutes late)
                text = f"Manifest. at {spoken_time}"
                
            return text
        except Exception:
            return "Manifest"

    print("=== 🎙️ Voice Announcement Test Suite ===\n")
    
    # Test 1: Single Active Manifest
    print("📍 Test 1: Single Active Manifest (11:30)")
    text = _trigger_speech("11:30", 5)  # 5 minutes late = Active
    _speak(text)
    print()
    
    # Test 2: Single Missed Manifest
    print("📍 Test 2: Single Missed Manifest (12:30, 45 minutes late)")
    text = _trigger_speech("12:30", 45)  # 45 minutes late = Missed
    _speak(text)
    print()
    
    # Test 3: Multiple Active Manifests
    print("📍 Test 3: Multiple Active Manifests")
    text = "Multiple manifests Active. Please acknowledge"
    _speak(text)
    print()
    
    # Test 4: Multiple Missed Manifests
    print("📍 Test 4: Multiple Missed Manifests")
    text = "Multiple missed manifests. Please acknowledge"
    _speak(text)
    print()
    
    # Test 5: Mixed Active and Missed
    print("📍 Test 5: Mixed Active and Missed Manifests")
    text = "Multiple Missed and Active Manifests. Please acknowledge"
    _speak(text)
    print()
    
    # Test 6: Edge cases - Different times
    print("📍 Test 6: Edge Case - Time with single digit minute (15:03)")
    text = _trigger_speech("15:03", 10)  # Should say "three oh three"
    _speak(text)
    print()
    
    print("📍 Test 7: Edge Case - O'clock time (16:00)")
    text = _trigger_speech("16:00", 20)  # Should say "four o'clock"
    _speak(text)
    print()
    
    print("✅ All voice announcement tests completed!")

if __name__ == "__main__":
    print("Testing voice announcements for all manifest statuses...")
    print("Make sure your speakers are on and volume is up!\n")
    
    input("Press Enter to start the voice tests...")
    test_voice_announcements()
