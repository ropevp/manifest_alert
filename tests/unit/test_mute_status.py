"""
Unit tests for MuteStatus domain model.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.domain.models.mute_status import MuteStatus, MuteType
from src.infrastructure.exceptions import DataValidationException


class TestMuteStatus(unittest.TestCase):
    """Test cases for the MuteStatus domain model."""
    
    def test_create_unmuted_status(self):
        """Test creating an unmuted status."""
        status = MuteStatus()
        
        self.assertFalse(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.DISABLED)
        self.assertIsNone(status.muted_at)
        self.assertIsNone(status.mute_end_time)
        self.assertEqual(status.snooze_duration_minutes, 5)
    
    def test_create_unmuted_class_method(self):
        """Test creating unmuted status using class method."""
        status = MuteStatus.create_unmuted()
        
        self.assertFalse(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.DISABLED)
    
    def test_mute_indefinitely(self):
        """Test muting indefinitely."""
        status = MuteStatus()
        status.mute(None, "john.doe", "Testing")
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.MANUAL)
        self.assertEqual(status.muted_by, "john.doe")
        self.assertEqual(status.reason, "Testing")
        self.assertIsNotNone(status.muted_at)
        self.assertIsNone(status.mute_end_time)
    
    def test_mute_with_duration(self):
        """Test muting with specific duration."""
        status = MuteStatus()
        before = datetime.now()
        status.mute(10, "jane.doe", "Meeting")
        after = datetime.now()
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
        self.assertEqual(status.muted_by, "jane.doe")
        self.assertEqual(status.reason, "Meeting")
        self.assertIsNotNone(status.mute_end_time)
        
        # Check that end time is approximately 10 minutes from now
        expected_end = before + timedelta(minutes=10)
        self.assertLessEqual(abs((status.mute_end_time - expected_end).total_seconds()), 5)
    
    def test_snooze_default_duration(self):
        """Test snoozing with default duration."""
        status = MuteStatus()
        status.snooze(user="user")
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
        self.assertEqual(status.reason, "Snoozed")
        
        # Should use default 5 minute duration
        remaining = status.get_remaining_minutes()
        self.assertIsNotNone(remaining)
        self.assertLessEqual(remaining, 5)
        self.assertGreaterEqual(remaining, 4)  # Should be close to 5
    
    def test_snooze_custom_duration(self):
        """Test snoozing with custom duration."""
        status = MuteStatus()
        status.snooze(15, "user", "Long meeting")
        
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
        self.assertEqual(status.reason, "Long meeting")
        
        remaining = status.get_remaining_minutes()
        self.assertIsNotNone(remaining)
        self.assertLessEqual(remaining, 15)
        self.assertGreaterEqual(remaining, 14)  # Should be close to 15
    
    def test_create_snoozed_class_method(self):
        """Test creating snoozed status using class method."""
        status = MuteStatus.create_snoozed(8, "user")
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
        self.assertEqual(status.snooze_duration_minutes, 8)
    
    def test_unmute(self):
        """Test unmuting."""
        status = MuteStatus()
        status.mute(5, "user", "test")
        
        # Verify it's muted first
        self.assertTrue(status.is_muted)
        
        # Unmute
        status.unmute("other_user")
        
        self.assertFalse(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.DISABLED)
        self.assertIsNone(status.muted_at)
        self.assertIsNone(status.mute_end_time)
        self.assertEqual(status.muted_by, "other_user")
        self.assertIsNone(status.reason)
    
    def test_toggle_mute_to_muted(self):
        """Test toggling from unmuted to muted."""
        status = MuteStatus()
        result = status.toggle_mute(10, "user")
        
        self.assertTrue(result)  # Should return True when muted
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
    
    def test_toggle_mute_to_unmuted(self):
        """Test toggling from muted to unmuted."""
        status = MuteStatus()
        status.mute(5, "user")
        
        result = status.toggle_mute(user="other_user")
        
        self.assertFalse(result)  # Should return False when unmuted
        self.assertFalse(status.is_muted)
    
    def test_is_currently_muted_simple(self):
        """Test is_currently_muted for simple cases."""
        status = MuteStatus()
        
        # Initially not muted
        self.assertFalse(status.is_currently_muted())
        
        # After muting
        status.mute(user="user")
        self.assertTrue(status.is_currently_muted())
        
        # After unmuting
        status.unmute()
        self.assertFalse(status.is_currently_muted())
    
    def test_is_currently_muted_expired_snooze(self):
        """Test is_currently_muted with expired snooze."""
        status = MuteStatus()
        
        # Set up snooze that expired 1 minute ago
        past_time = datetime.now() - timedelta(minutes=1)
        status.mute(5, "user")
        status.mute_end_time = past_time
        
        # Should auto-unmute when checking
        self.assertFalse(status.is_currently_muted())
        self.assertFalse(status.is_muted)
    
    def test_get_remaining_time(self):
        """Test getting remaining time."""
        status = MuteStatus()
        
        # No remaining time when not muted
        self.assertIsNone(status.get_remaining_time())
        
        # No remaining time for indefinite mute
        status.mute(user="user")
        self.assertIsNone(status.get_remaining_time())
        
        # Remaining time for snooze
        status.snooze(10, "user")
        remaining = status.get_remaining_time()
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining.total_seconds(), 9 * 60)  # More than 9 minutes
        self.assertLess(remaining.total_seconds(), 10 * 60 + 5)  # Less than 10 minutes + 5 seconds
    
    def test_get_remaining_minutes(self):
        """Test getting remaining minutes."""
        status = MuteStatus()
        status.snooze(7, "user")
        
        remaining = status.get_remaining_minutes()
        self.assertIsNotNone(remaining)
        self.assertIn(remaining, [6, 7])  # Should be 6 or 7 depending on timing
    
    def test_extend_snooze(self):
        """Test extending snooze duration."""
        status = MuteStatus()
        status.snooze(5, "user")
        
        original_end = status.mute_end_time
        status.extend_snooze(3, "other_user")
        
        # End time should be 3 minutes later
        expected_end = original_end + timedelta(minutes=3)
        self.assertEqual(status.mute_end_time, expected_end)
        self.assertEqual(status.muted_by, "other_user")
    
    def test_extend_snooze_not_muted_raises_exception(self):
        """Test extending snooze when not muted raises exception."""
        status = MuteStatus()
        
        with self.assertRaises(DataValidationException):
            status.extend_snooze(5, "user")
    
    def test_extend_snooze_not_snooze_type_raises_exception(self):
        """Test extending snooze for manual mute raises exception."""
        status = MuteStatus()
        status.mute(None, "user")  # Indefinite mute
        
        with self.assertRaises(DataValidationException):
            status.extend_snooze(5, "user")
    
    def test_get_mute_summary_unmuted(self):
        """Test getting mute summary when unmuted."""
        status = MuteStatus()
        summary = status.get_mute_summary()
        
        self.assertEqual(summary, "Alerts active")
    
    def test_get_mute_summary_manual(self):
        """Test getting mute summary for manual mute."""
        status = MuteStatus()
        status.mute(None, "john.doe", "Maintenance")
        
        summary = status.get_mute_summary()
        self.assertIn("Muted indefinitely", summary)
        self.assertIn("john.doe", summary)
        self.assertIn("Maintenance", summary)
    
    def test_get_mute_summary_snooze(self):
        """Test getting mute summary for snooze."""
        status = MuteStatus()
        status.snooze(8, "jane.smith")
        
        summary = status.get_mute_summary()
        self.assertIn("Snoozed for", summary)
        self.assertIn("jane.smith", summary)
    
    def test_validation_negative_snooze_duration(self):
        """Test that negative snooze duration raises exception."""
        with self.assertRaises(DataValidationException):
            MuteStatus(snooze_duration_minutes=-1)
    
    def test_validation_zero_snooze_duration(self):
        """Test that zero snooze duration raises exception."""
        with self.assertRaises(DataValidationException):
            MuteStatus(snooze_duration_minutes=0)
    
    def test_validation_muted_with_disabled_type_raises_exception(self):
        """Test that is_muted=True with disabled type raises exception."""
        with self.assertRaises(DataValidationException):
            MuteStatus(is_muted=True, mute_type=MuteType.DISABLED)
    
    def test_validation_clears_type_when_not_muted(self):
        """Test that mute type is set to disabled when not muted."""
        status = MuteStatus(is_muted=False, mute_type=MuteType.MANUAL)
        
        self.assertEqual(status.mute_type, MuteType.DISABLED)
    
    def test_mute_with_negative_duration_raises_exception(self):
        """Test that muting with negative duration raises exception."""
        status = MuteStatus()
        
        with self.assertRaises(DataValidationException):
            status.mute(-5, "user")
    
    def test_extend_snooze_negative_minutes_raises_exception(self):
        """Test that extending with negative minutes raises exception."""
        status = MuteStatus()
        status.snooze(5, "user")
        
        with self.assertRaises(DataValidationException):
            status.extend_snooze(-2, "user")
    
    def test_to_dict(self):
        """Test converting mute status to dictionary."""
        status = MuteStatus()
        status.snooze(10, "user", "Meeting")
        
        data = status.to_dict()
        
        self.assertTrue(data["is_muted"])
        self.assertEqual(data["mute_type"], "snooze")
        self.assertEqual(data["muted_by"], "user")
        self.assertEqual(data["reason"], "Meeting")
        self.assertIsNotNone(data["muted_at"])
        self.assertIsNotNone(data["mute_end_time"])
        self.assertEqual(data["snooze_duration_minutes"], 5)  # Default value
    
    def test_from_dict_complete(self):
        """Test creating mute status from complete dictionary."""
        now = datetime.now()
        end_time = now + timedelta(minutes=10)
        
        data = {
            "is_muted": True,
            "mute_type": "snooze",
            "muted_at": now.isoformat(),
            "mute_end_time": end_time.isoformat(),
            "muted_by": "user",
            "reason": "Meeting",
            "snooze_duration_minutes": 8
        }
        
        status = MuteStatus.from_dict(data)
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
        self.assertEqual(status.muted_by, "user")
        self.assertEqual(status.reason, "Meeting")
        self.assertEqual(status.snooze_duration_minutes, 8)
        self.assertIsInstance(status.muted_at, datetime)
        self.assertIsInstance(status.mute_end_time, datetime)
    
    def test_from_dict_minimal(self):
        """Test creating mute status from minimal dictionary."""
        data = {"is_muted": False}
        status = MuteStatus.from_dict(data)
        
        self.assertFalse(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.DISABLED)
    
    def test_from_dict_invalid_type(self):
        """Test creating mute status from invalid data type raises exception."""
        with self.assertRaises(DataValidationException):
            MuteStatus.from_dict("not a dict")
    
    def test_from_dict_invalid_mute_type(self):
        """Test creating mute status from dict with invalid mute type."""
        data = {"mute_type": "invalid_type"}
        
        with self.assertRaises(DataValidationException):
            MuteStatus.from_dict(data)
    
    def test_from_dict_invalid_timestamps(self):
        """Test creating mute status from dict with invalid timestamps."""
        data = {
            "is_muted": True,
            "muted_at": "invalid-timestamp"
        }
        
        with self.assertRaises(DataValidationException):
            MuteStatus.from_dict(data)
    
    def test_create_muted_class_method(self):
        """Test creating muted status using class method."""
        status = MuteStatus.create_muted(10, "user", "reason")
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.SNOOZE)
        self.assertEqual(status.muted_by, "user")
        self.assertEqual(status.reason, "reason")
    
    def test_create_muted_indefinite(self):
        """Test creating indefinitely muted status using class method."""
        status = MuteStatus.create_muted(None, "user", "reason")
        
        self.assertTrue(status.is_muted)
        self.assertEqual(status.mute_type, MuteType.MANUAL)
        self.assertIsNone(status.mute_end_time)
    
    def test_string_representation(self):
        """Test string representation of mute status."""
        status = MuteStatus()
        self.assertEqual(str(status), "Alerts active")
        
        status.mute(None, "user")
        str_repr = str(status)
        self.assertIn("Muted indefinitely", str_repr)
    
    def test_repr(self):
        """Test developer representation of mute status."""
        status = MuteStatus()
        repr_str = repr(status)
        
        self.assertIn("MuteStatus", repr_str)
        self.assertIn("is_muted=False", repr_str)
        self.assertIn("type=disabled", repr_str)


if __name__ == '__main__':
    unittest.main()