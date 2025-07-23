"""
Unit tests for Acknowledgment domain model.
"""

import unittest
import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.domain.models.acknowledgment import Acknowledgment
from src.infrastructure.exceptions import DataValidationException


class TestAcknowledgment(unittest.TestCase):
    """Test cases for the Acknowledgment domain model."""
    
    def test_create_valid_acknowledgment(self):
        """Test creating a valid acknowledgment."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Australia Post Metro",
            user="john.doe",
            reason="On time"
        )
        
        self.assertEqual(ack.date, "2025-07-23")
        self.assertEqual(ack.manifest_time, "07:00")
        self.assertEqual(ack.carrier, "Australia Post Metro")
        self.assertEqual(ack.user, "john.doe")
        self.assertEqual(ack.reason, "On time")
        self.assertIsInstance(ack.timestamp, datetime)
    
    def test_create_acknowledgment_without_reason(self):
        """Test creating acknowledgment without reason."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="11:00",
            carrier="DHL Express",
            user="jane.smith"
        )
        
        self.assertIsNone(ack.reason)
    
    def test_auto_timestamp_set(self):
        """Test that timestamp is automatically set if not provided."""
        before = datetime.now()
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user"
        )
        after = datetime.now()
        
        self.assertIsInstance(ack.timestamp, datetime)
        self.assertGreaterEqual(ack.timestamp, before)
        self.assertLessEqual(ack.timestamp, after)
    
    def test_custom_timestamp(self):
        """Test creating acknowledgment with custom timestamp."""
        custom_time = datetime(2025, 7, 23, 10, 30, 0)
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user",
            timestamp=custom_time
        )
        
        self.assertEqual(ack.timestamp, custom_time)
    
    def test_invalid_date_format(self):
        """Test that invalid date format raises exception."""
        with self.assertRaises(DataValidationException) as context:
            Acknowledgment(
                date="23-07-2025",  # Wrong format
                manifest_time="07:00",
                carrier="Test Carrier",
                user="user"
            )
        
        self.assertIn("Invalid date format", str(context.exception))
    
    def test_empty_date(self):
        """Test that empty date raises exception."""
        with self.assertRaises(DataValidationException):
            Acknowledgment(
                date="",
                manifest_time="07:00",
                carrier="Test Carrier",
                user="user"
            )
    
    def test_invalid_time_format(self):
        """Test that invalid time format raises exception."""
        with self.assertRaises(DataValidationException) as context:
            Acknowledgment(
                date="2025-07-23",
                manifest_time="7:00 AM",  # Invalid format with AM/PM
                carrier="Test Carrier",
                user="user"
            )
        
        self.assertIn("Invalid manifest time format", str(context.exception))
    
    def test_invalid_time_range(self):
        """Test that invalid time range raises exception."""
        with self.assertRaises(DataValidationException):
            Acknowledgment(
                date="2025-07-23",
                manifest_time="25:00",  # Hour out of range
                carrier="Test Carrier",
                user="user"
            )
    
    def test_empty_carrier(self):
        """Test that empty carrier raises exception."""
        with self.assertRaises(DataValidationException):
            Acknowledgment(
                date="2025-07-23",
                manifest_time="07:00",
                carrier="",
                user="user"
            )
    
    def test_empty_user(self):
        """Test that empty user raises exception."""
        with self.assertRaises(DataValidationException):
            Acknowledgment(
                date="2025-07-23",
                manifest_time="07:00",
                carrier="Test Carrier",
                user=""
            )
    
    def test_field_normalization(self):
        """Test that fields are normalized (whitespace trimmed)."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="  Australia Post Metro  ",
            user="  john.doe  ",
            reason="  On time  "
        )
        
        self.assertEqual(ack.carrier, "Australia Post Metro")
        self.assertEqual(ack.user, "john.doe")
        self.assertEqual(ack.reason, "On time")
    
    def test_empty_reason_normalized_to_none(self):
        """Test that empty reason is normalized to None."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user",
            reason="   "  # Only whitespace
        )
        
        self.assertIsNone(ack.reason)
    
    def test_get_manifest_key(self):
        """Test getting manifest key."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user"
        )
        
        self.assertEqual(ack.get_manifest_key(), "2025-07-23_07:00")
    
    def test_get_carrier_key(self):
        """Test getting carrier key."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Australia Post Metro",
            user="user"
        )
        
        self.assertEqual(ack.get_carrier_key(), "2025-07-23_07:00_Australia Post Metro")
    
    def test_is_same_manifest(self):
        """Test checking if acknowledgment is for same manifest."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user"
        )
        
        self.assertTrue(ack.is_same_manifest("2025-07-23", "07:00"))
        self.assertFalse(ack.is_same_manifest("2025-07-24", "07:00"))
        self.assertFalse(ack.is_same_manifest("2025-07-23", "11:00"))
    
    def test_is_same_carrier(self):
        """Test checking if acknowledgment is for same carrier."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Australia Post Metro",
            user="user"
        )
        
        self.assertTrue(ack.is_same_carrier("2025-07-23", "07:00", "Australia Post Metro"))
        self.assertFalse(ack.is_same_carrier("2025-07-23", "07:00", "DHL Express"))
        self.assertFalse(ack.is_same_carrier("2025-07-24", "07:00", "Australia Post Metro"))
    
    def test_get_formatted_timestamp(self):
        """Test getting formatted timestamp."""
        custom_time = datetime(2025, 7, 23, 10, 30, 45)
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user",
            timestamp=custom_time
        )
        
        self.assertEqual(ack.get_formatted_timestamp(), "2025-07-23 10:30:45")
    
    def test_to_dict(self):
        """Test converting acknowledgment to dictionary."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="john.doe",
            reason="Test reason"
        )
        
        data = ack.to_dict()
        
        self.assertEqual(data["date"], "2025-07-23")
        self.assertEqual(data["manifest_time"], "07:00")
        self.assertEqual(data["carrier"], "Test Carrier")
        self.assertEqual(data["user"], "john.doe")
        self.assertEqual(data["reason"], "Test reason")
        self.assertIsNotNone(data["timestamp"])
    
    def test_to_dict_empty_reason(self):
        """Test converting acknowledgment with no reason to dictionary."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user"
        )
        
        data = ack.to_dict()
        self.assertEqual(data["reason"], "")
    
    def test_from_dict_complete(self):
        """Test creating acknowledgment from complete dictionary."""
        timestamp = datetime.now().isoformat()
        data = {
            "date": "2025-07-23",
            "manifest_time": "07:00",
            "carrier": "Test Carrier",
            "user": "john.doe",
            "reason": "Test reason",
            "timestamp": timestamp
        }
        
        ack = Acknowledgment.from_dict(data)
        
        self.assertEqual(ack.date, "2025-07-23")
        self.assertEqual(ack.manifest_time, "07:00")
        self.assertEqual(ack.carrier, "Test Carrier")
        self.assertEqual(ack.user, "john.doe")
        self.assertEqual(ack.reason, "Test reason")
        self.assertIsInstance(ack.timestamp, datetime)
    
    def test_from_dict_minimal(self):
        """Test creating acknowledgment from minimal dictionary."""
        data = {
            "date": "2025-07-23",
            "manifest_time": "07:00",
            "carrier": "Test Carrier",
            "user": "user"
        }
        
        ack = Acknowledgment.from_dict(data)
        
        self.assertEqual(ack.date, "2025-07-23")
        self.assertEqual(ack.user, "user")
        self.assertIsNone(ack.reason)
    
    def test_from_dict_invalid_type(self):
        """Test creating acknowledgment from invalid data type raises exception."""
        with self.assertRaises(DataValidationException):
            Acknowledgment.from_dict("not a dict")
    
    def test_from_dict_missing_required_fields(self):
        """Test creating acknowledgment from dict missing required fields."""
        data = {"date": "2025-07-23"}  # Missing other required fields
        
        with self.assertRaises(DataValidationException):
            Acknowledgment.from_dict(data)
    
    def test_from_dict_invalid_timestamp(self):
        """Test creating acknowledgment from dict with invalid timestamp."""
        data = {
            "date": "2025-07-23",
            "manifest_time": "07:00",
            "carrier": "Test Carrier",
            "user": "user",
            "timestamp": "invalid-timestamp"
        }
        
        with self.assertRaises(DataValidationException):
            Acknowledgment.from_dict(data)
    
    def test_equality(self):
        """Test acknowledgment equality comparison."""
        ack1 = Acknowledgment("2025-07-23", "07:00", "Carrier", "user")
        ack2 = Acknowledgment("2025-07-23", "07:00", "Carrier", "user")
        ack3 = Acknowledgment("2025-07-23", "07:00", "Carrier", "other_user")
        
        self.assertEqual(ack1, ack2)
        self.assertNotEqual(ack1, ack3)
        self.assertNotEqual(ack1, "not an acknowledgment")
    
    def test_hash(self):
        """Test acknowledgment hashing for use in sets/dicts."""
        ack1 = Acknowledgment("2025-07-23", "07:00", "Carrier", "user")
        ack2 = Acknowledgment("2025-07-23", "07:00", "Carrier", "user")
        
        # Should have same hash
        self.assertEqual(hash(ack1), hash(ack2))
        
        # Should work in a set
        ack_set = {ack1, ack2}
        self.assertEqual(len(ack_set), 1)
    
    def test_string_representation(self):
        """Test string representation of acknowledgment."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="john.doe",
            reason="Test reason"
        )
        
        str_repr = str(ack)
        self.assertIn("Test Carrier", str_repr)
        self.assertIn("john.doe", str_repr)
        self.assertIn("Test reason", str_repr)
    
    def test_repr(self):
        """Test developer representation of acknowledgment."""
        ack = Acknowledgment(
            date="2025-07-23",
            manifest_time="07:00",
            carrier="Test Carrier",
            user="user"
        )
        
        repr_str = repr(ack)
        self.assertIn("Acknowledgment", repr_str)
        self.assertIn("2025-07-23", repr_str)
        self.assertIn("07:00", repr_str)


if __name__ == '__main__':
    unittest.main()