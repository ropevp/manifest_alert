"""
Unit tests for Carrier domain model.
"""

import unittest
import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.domain.models.carrier import Carrier
from src.infrastructure.exceptions import DataValidationException


class TestCarrier(unittest.TestCase):
    """Test cases for the Carrier domain model."""
    
    def test_create_valid_carrier(self):
        """Test creating a valid carrier."""
        carrier = Carrier("Australia Post Metro")
        
        self.assertEqual(carrier.name, "Australia Post Metro")
        self.assertFalse(carrier.acknowledged)
        self.assertIsNone(carrier.acknowledged_by)
        self.assertIsNone(carrier.acknowledged_at)
        self.assertIsNone(carrier.acknowledgment_reason)
    
    def test_create_carrier_with_whitespace(self):
        """Test creating a carrier with whitespace gets normalized."""
        carrier = Carrier("  DHL Express  ")
        
        self.assertEqual(carrier.name, "DHL Express")
    
    def test_empty_carrier_name_raises_exception(self):
        """Test that empty carrier name raises DataValidationException."""
        with self.assertRaises(DataValidationException) as context:
            Carrier("")
        
        self.assertIn("Carrier name cannot be empty", str(context.exception))
    
    def test_whitespace_only_carrier_name_raises_exception(self):
        """Test that whitespace-only carrier name raises DataValidationException."""
        with self.assertRaises(DataValidationException) as context:
            Carrier("   ")
        
        self.assertIn("Carrier name cannot be empty", str(context.exception))
    
    def test_acknowledge_carrier(self):
        """Test acknowledging a carrier."""
        carrier = Carrier("EParcel Express")
        carrier.acknowledge("john.doe", "On time")
        
        self.assertTrue(carrier.acknowledged)
        self.assertEqual(carrier.acknowledged_by, "john.doe")
        self.assertIsInstance(carrier.acknowledged_at, datetime)
        self.assertEqual(carrier.acknowledgment_reason, "On time")
    
    def test_acknowledge_carrier_without_reason(self):
        """Test acknowledging a carrier without a reason."""
        carrier = Carrier("Toll Priority")
        carrier.acknowledge("jane.smith")
        
        self.assertTrue(carrier.acknowledged)
        self.assertEqual(carrier.acknowledged_by, "jane.smith")
        self.assertIsInstance(carrier.acknowledged_at, datetime)
        self.assertIsNone(carrier.acknowledgment_reason)
    
    def test_acknowledge_with_empty_user_raises_exception(self):
        """Test that acknowledging with empty user raises exception."""
        carrier = Carrier("Test Carrier")
        
        with self.assertRaises(DataValidationException) as context:
            carrier.acknowledge("")
        
        self.assertIn("User cannot be empty", str(context.exception))
    
    def test_acknowledge_with_whitespace_user_gets_normalized(self):
        """Test that user with whitespace gets normalized."""
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("  bob.wilson  ", "  Late delivery  ")
        
        self.assertEqual(carrier.acknowledged_by, "bob.wilson")
        self.assertEqual(carrier.acknowledgment_reason, "Late delivery")
    
    def test_clear_acknowledgment(self):
        """Test clearing acknowledgment."""
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user", "reason")
        
        # Verify it's acknowledged first
        self.assertTrue(carrier.acknowledged)
        
        # Clear acknowledgment
        carrier.clear_acknowledgment()
        
        self.assertFalse(carrier.acknowledged)
        self.assertIsNone(carrier.acknowledged_by)
        self.assertIsNone(carrier.acknowledged_at)
        self.assertIsNone(carrier.acknowledgment_reason)
    
    def test_is_acknowledged(self):
        """Test is_acknowledged method."""
        carrier = Carrier("Test Carrier")
        
        self.assertFalse(carrier.is_acknowledged())
        
        carrier.acknowledge("user")
        self.assertTrue(carrier.is_acknowledged())
        
        carrier.clear_acknowledgment()
        self.assertFalse(carrier.is_acknowledged())
    
    def test_get_acknowledgment_summary(self):
        """Test getting acknowledgment summary."""
        carrier = Carrier("Test Carrier")
        
        # No acknowledgment
        self.assertIsNone(carrier.get_acknowledgment_summary())
        
        # With acknowledgment
        carrier.acknowledge("john.doe", "Done")
        summary = carrier.get_acknowledgment_summary()
        
        self.assertIn("Acknowledged by john.doe", summary)
        self.assertIn("Reason: Done", summary)
    
    def test_to_dict(self):
        """Test converting carrier to dictionary."""
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user", "reason")
        
        data = carrier.to_dict()
        
        self.assertEqual(data["name"], "Test Carrier")
        self.assertTrue(data["acknowledged"])
        self.assertEqual(data["acknowledged_by"], "user")
        self.assertIsNotNone(data["acknowledged_at"])
        self.assertEqual(data["acknowledgment_reason"], "reason")
    
    def test_from_dict_minimal(self):
        """Test creating carrier from minimal dictionary."""
        data = {"name": "Test Carrier"}
        carrier = Carrier.from_dict(data)
        
        self.assertEqual(carrier.name, "Test Carrier")
        self.assertFalse(carrier.acknowledged)
    
    def test_from_dict_complete(self):
        """Test creating carrier from complete dictionary."""
        timestamp = datetime.now().isoformat()
        data = {
            "name": "Test Carrier",
            "acknowledged": True,
            "acknowledged_by": "user",
            "acknowledged_at": timestamp,
            "acknowledgment_reason": "reason"
        }
        
        carrier = Carrier.from_dict(data)
        
        self.assertEqual(carrier.name, "Test Carrier")
        self.assertTrue(carrier.acknowledged)
        self.assertEqual(carrier.acknowledged_by, "user")
        self.assertIsInstance(carrier.acknowledged_at, datetime)
        self.assertEqual(carrier.acknowledgment_reason, "reason")
    
    def test_from_dict_invalid_data_type(self):
        """Test creating carrier from invalid data type raises exception."""
        with self.assertRaises(DataValidationException):
            Carrier.from_dict("not a dict")
    
    def test_from_dict_missing_name(self):
        """Test creating carrier from dict without name raises exception."""
        with self.assertRaises(DataValidationException):
            Carrier.from_dict({"acknowledged": True})
    
    def test_from_dict_invalid_timestamp(self):
        """Test creating carrier from dict with invalid timestamp raises exception."""
        data = {
            "name": "Test Carrier",
            "acknowledged": True,
            "acknowledged_by": "user",
            "acknowledged_at": "invalid-timestamp"
        }
        
        with self.assertRaises(DataValidationException):
            Carrier.from_dict(data)
    
    def test_validation_acknowledged_without_user(self):
        """Test that acknowledged=True without user raises exception."""
        with self.assertRaises(DataValidationException):
            Carrier(
                name="Test Carrier",
                acknowledged=True,
                acknowledged_by=None
            )
    
    def test_validation_acknowledged_without_timestamp(self):
        """Test that acknowledged=True without timestamp raises exception."""
        with self.assertRaises(DataValidationException):
            Carrier(
                name="Test Carrier",
                acknowledged=True,
                acknowledged_by="user",
                acknowledged_at=None
            )
    
    def test_validation_clears_fields_when_not_acknowledged(self):
        """Test that fields are cleared when acknowledged=False."""
        carrier = Carrier(
            name="Test Carrier",
            acknowledged=False,
            acknowledged_by="user",  # This should be cleared
            acknowledgment_reason="reason"  # This should be cleared
        )
        
        self.assertIsNone(carrier.acknowledged_by)
        self.assertIsNone(carrier.acknowledgment_reason)
    
    def test_string_representation(self):
        """Test string representation of carrier."""
        carrier = Carrier("Test Carrier")
        self.assertEqual(str(carrier), "○ Test Carrier")
        
        carrier.acknowledge("user")
        self.assertEqual(str(carrier), "✓ Test Carrier")
    
    def test_repr(self):
        """Test developer representation of carrier."""
        carrier = Carrier("Test Carrier")
        repr_str = repr(carrier)
        
        self.assertIn("Carrier", repr_str)
        self.assertIn("Test Carrier", repr_str)
        self.assertIn("acknowledged=False", repr_str)


if __name__ == '__main__':
    unittest.main()