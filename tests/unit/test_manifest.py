"""
Unit tests for Manifest domain model.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.domain.models.manifest import Manifest, ManifestStatus
from src.domain.models.carrier import Carrier
from src.domain.models.acknowledgment import Acknowledgment
from src.infrastructure.exceptions import DataValidationException


class TestManifest(unittest.TestCase):
    """Test cases for the Manifest domain model."""
    
    def test_create_valid_manifest(self):
        """Test creating a valid manifest."""
        carriers = [Carrier("Australia Post Metro"), Carrier("DHL Express")]
        manifest = Manifest("07:00", carriers)
        
        self.assertEqual(manifest.time, "07:00")
        self.assertEqual(len(manifest.carriers), 2)
        self.assertEqual(manifest.date, datetime.now().strftime("%Y-%m-%d"))
        self.assertFalse(manifest.acknowledged)
        self.assertEqual(manifest.alert_window_minutes, 30)
        self.assertEqual(len(manifest.acknowledgments), 0)
    
    def test_create_manifest_with_custom_date(self):
        """Test creating manifest with custom date."""
        manifest = Manifest("11:00", [], date="2025-07-25")
        
        self.assertEqual(manifest.date, "2025-07-25")
    
    def test_create_manifest_empty_carriers(self):
        """Test creating manifest with empty carriers list."""
        manifest = Manifest("07:00", [])
        
        self.assertEqual(len(manifest.carriers), 0)
        self.assertTrue(manifest.acknowledged)  # Empty manifest is considered acknowledged
    
    def test_empty_time_raises_exception(self):
        """Test that empty time raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest("", [])
    
    def test_invalid_time_format_raises_exception(self):
        """Test that invalid time format raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest("7:00 AM", [])
    
    def test_invalid_time_range_raises_exception(self):
        """Test that invalid time range raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest("25:00", [])
    
    def test_invalid_date_format_raises_exception(self):
        """Test that invalid date format raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest("07:00", [], date="23-07-2025")
    
    def test_invalid_carriers_type_raises_exception(self):
        """Test that invalid carriers type raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest("07:00", "not a list")
    
    def test_negative_alert_window_raises_exception(self):
        """Test that negative alert window raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest("07:00", [], alert_window_minutes=-1)
    
    def test_get_manifest_datetime(self):
        """Test getting manifest datetime."""
        manifest = Manifest("14:30", [], date="2025-07-23")
        dt = manifest.get_manifest_datetime()
        
        expected = datetime(2025, 7, 23, 14, 30, 0)
        self.assertEqual(dt, expected)
    
    def test_add_carrier(self):
        """Test adding a carrier to manifest."""
        manifest = Manifest("07:00", [])
        carrier = manifest.add_carrier("Australia Post Metro")
        
        self.assertEqual(len(manifest.carriers), 1)
        self.assertEqual(carrier.name, "Australia Post Metro")
        self.assertIn(carrier, manifest.carriers)
    
    def test_add_carrier_normalize_name(self):
        """Test adding carrier with whitespace gets normalized."""
        manifest = Manifest("07:00", [])
        carrier = manifest.add_carrier("  DHL Express  ")
        
        self.assertEqual(carrier.name, "DHL Express")
    
    def test_add_empty_carrier_raises_exception(self):
        """Test that adding empty carrier name raises exception."""
        manifest = Manifest("07:00", [])
        
        with self.assertRaises(DataValidationException):
            manifest.add_carrier("")
    
    def test_add_duplicate_carrier_raises_exception(self):
        """Test that adding duplicate carrier raises exception."""
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        with self.assertRaises(DataValidationException):
            manifest.add_carrier("Test Carrier")
    
    def test_remove_carrier(self):
        """Test removing a carrier from manifest."""
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        result = manifest.remove_carrier("Test Carrier")
        
        self.assertTrue(result)
        self.assertEqual(len(manifest.carriers), 0)
    
    def test_remove_nonexistent_carrier(self):
        """Test removing non-existent carrier."""
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        result = manifest.remove_carrier("Nonexistent Carrier")
        
        self.assertFalse(result)
        self.assertEqual(len(manifest.carriers), 1)
    
    def test_get_carrier(self):
        """Test getting a carrier by name."""
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        found_carrier = manifest.get_carrier("Test Carrier")
        
        self.assertEqual(found_carrier, carrier)
    
    def test_get_nonexistent_carrier(self):
        """Test getting non-existent carrier returns None."""
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        found_carrier = manifest.get_carrier("Nonexistent Carrier")
        
        self.assertIsNone(found_carrier)
    
    def test_acknowledge_carrier(self):
        """Test acknowledging a specific carrier."""
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        result = manifest.acknowledge_carrier("Test Carrier", "john.doe", "On time")
        
        self.assertTrue(result)
        self.assertTrue(carrier.is_acknowledged())
        self.assertEqual(len(manifest.acknowledgments), 1)
        
        ack = manifest.acknowledgments[0]
        self.assertEqual(ack.carrier, "Test Carrier")
        self.assertEqual(ack.user, "john.doe")
        self.assertEqual(ack.reason, "On time")
    
    def test_acknowledge_nonexistent_carrier(self):
        """Test acknowledging non-existent carrier."""
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        result = manifest.acknowledge_carrier("Nonexistent Carrier", "user")
        
        self.assertFalse(result)
        self.assertEqual(len(manifest.acknowledgments), 0)
    
    def test_clear_carrier_acknowledgment(self):
        """Test clearing acknowledgment for a carrier."""
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        # First acknowledge
        manifest.acknowledge_carrier("Test Carrier", "user")
        self.assertTrue(carrier.is_acknowledged())
        self.assertEqual(len(manifest.acknowledgments), 1)
        
        # Then clear
        result = manifest.clear_carrier_acknowledgment("Test Carrier")
        
        self.assertTrue(result)
        self.assertFalse(carrier.is_acknowledged())
        self.assertEqual(len(manifest.acknowledgments), 0)
    
    def test_clear_acknowledgment_nonexistent_carrier(self):
        """Test clearing acknowledgment for non-existent carrier."""
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        result = manifest.clear_carrier_acknowledgment("Nonexistent Carrier")
        
        self.assertFalse(result)
    
    def test_acknowledge_all(self):
        """Test acknowledging all carriers."""
        carriers = [Carrier("Carrier 1"), Carrier("Carrier 2")]
        manifest = Manifest("07:00", carriers)
        
        manifest.acknowledge_all("john.doe", "All done")
        
        self.assertTrue(manifest.acknowledged)
        for carrier in carriers:
            self.assertTrue(carrier.is_acknowledged())
        self.assertEqual(len(manifest.acknowledgments), 2)
    
    def test_acknowledge_all_partial(self):
        """Test acknowledging all when some are already acknowledged."""
        carrier1 = Carrier("Carrier 1")
        carrier2 = Carrier("Carrier 2")
        carrier1.acknowledge("previous_user")
        
        manifest = Manifest("07:00", [carrier1, carrier2])
        
        manifest.acknowledge_all("john.doe", "Finishing up")
        
        # Should only create acknowledgment for carrier2
        acks_by_user = [ack for ack in manifest.acknowledgments if ack.user == "john.doe"]
        self.assertEqual(len(acks_by_user), 1)
        self.assertEqual(acks_by_user[0].carrier, "Carrier 2")
    
    def test_get_unacknowledged_carriers(self):
        """Test getting unacknowledged carriers."""
        carrier1 = Carrier("Carrier 1")
        carrier2 = Carrier("Carrier 2")
        carrier1.acknowledge("user")
        
        manifest = Manifest("07:00", [carrier1, carrier2])
        
        unack = manifest.get_unacknowledged_carriers()
        
        self.assertEqual(len(unack), 1)
        self.assertEqual(unack[0], carrier2)
    
    def test_get_acknowledged_carriers(self):
        """Test getting acknowledged carriers."""
        carrier1 = Carrier("Carrier 1")
        carrier2 = Carrier("Carrier 2")
        carrier1.acknowledge("user")
        
        manifest = Manifest("07:00", [carrier1, carrier2])
        
        ack = manifest.get_acknowledged_carriers()
        
        self.assertEqual(len(ack), 1)
        self.assertEqual(ack[0], carrier1)
    
    def test_get_acknowledgment_summary(self):
        """Test getting acknowledgment summary."""
        carrier1 = Carrier("Carrier 1")
        carrier2 = Carrier("Carrier 2")
        carrier1.acknowledge("user")
        
        manifest = Manifest("07:00", [carrier1, carrier2])
        
        summary = manifest.get_acknowledgment_summary()
        
        self.assertEqual(summary, "1/2 carriers acknowledged")
    
    def test_status_pending(self):
        """Test manifest status when pending."""
        # Create manifest for future time
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        manifest = Manifest(future_time, [Carrier("Test Carrier")])
        
        status = manifest.get_status()
        self.assertEqual(status, ManifestStatus.PENDING)
    
    def test_status_acknowledged(self):
        """Test manifest status when acknowledged."""
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user")
        manifest = Manifest("07:00", [carrier])
        
        status = manifest.get_status()
        self.assertEqual(status, ManifestStatus.ACKNOWLEDGED)
    
    def test_is_active_for_active_manifest(self):
        """Test is_active for active/missed manifest."""
        # Create manifest that would be missed (past time)
        past_time = (datetime.now() - timedelta(minutes=10)).strftime("%H:%M")
        manifest = Manifest(past_time, [Carrier("Test Carrier")])
        
        # Missed manifests should be considered active for alerts
        self.assertTrue(manifest.is_active())
    
    def test_is_active_for_acknowledged_manifest(self):
        """Test is_active for acknowledged manifest."""
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user")
        manifest = Manifest("07:00", [carrier])
        
        self.assertFalse(manifest.is_active())
    
    def test_to_dict(self):
        """Test converting manifest to dictionary."""
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier], date="2025-07-23")
        
        data = manifest.to_dict()
        
        self.assertEqual(data["time"], "07:00")
        self.assertEqual(data["date"], "2025-07-23")
        self.assertEqual(len(data["carriers"]), 1)
        self.assertEqual(data["carriers"][0]["name"], "Test Carrier")
        self.assertFalse(data["acknowledged"])
        self.assertEqual(data["alert_window_minutes"], 30)
    
    def test_from_dict_complete(self):
        """Test creating manifest from complete dictionary."""
        timestamp = datetime.now().isoformat()
        data = {
            "time": "11:00",
            "date": "2025-07-23",
            "carriers": [{"name": "Test Carrier", "acknowledged": True, "acknowledged_by": "user", "acknowledged_at": timestamp}],
            "acknowledged": True,
            "missed": False,
            "acknowledgments": [],
            "alert_window_minutes": 45
        }
        
        manifest = Manifest.from_dict(data)
        
        self.assertEqual(manifest.time, "11:00")
        self.assertEqual(manifest.date, "2025-07-23")
        self.assertEqual(len(manifest.carriers), 1)
        self.assertEqual(manifest.carriers[0].name, "Test Carrier")
        self.assertTrue(manifest.acknowledged)
        self.assertEqual(manifest.alert_window_minutes, 45)
    
    def test_from_dict_minimal(self):
        """Test creating manifest from minimal dictionary."""
        data = {"time": "07:00"}
        
        manifest = Manifest.from_dict(data)
        
        self.assertEqual(manifest.time, "07:00")
        self.assertEqual(len(manifest.carriers), 0)
    
    def test_from_dict_string_carriers(self):
        """Test creating manifest from dict with string carriers."""
        data = {
            "time": "07:00",
            "carriers": ["Australia Post Metro", "DHL Express"]
        }
        
        manifest = Manifest.from_dict(data)
        
        self.assertEqual(len(manifest.carriers), 2)
        self.assertEqual(manifest.carriers[0].name, "Australia Post Metro")
        self.assertEqual(manifest.carriers[1].name, "DHL Express")
    
    def test_from_dict_invalid_type(self):
        """Test creating manifest from invalid data type raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest.from_dict("not a dict")
    
    def test_from_dict_missing_time(self):
        """Test creating manifest from dict without time raises exception."""
        with self.assertRaises(DataValidationException):
            Manifest.from_dict({"carriers": []})
    
    def test_from_dict_invalid_carrier_data(self):
        """Test creating manifest from dict with invalid carrier data."""
        data = {
            "time": "07:00",
            "carriers": [123]  # Invalid carrier data
        }
        
        with self.assertRaises(DataValidationException):
            Manifest.from_dict(data)
    
    def test_from_config_format(self):
        """Test creating manifest from config.json format."""
        data = {
            "time": "07:00",
            "carriers": ["Australia Post Metro", "DHL Express"]
        }
        
        manifest = Manifest.from_config_format(data)
        
        self.assertEqual(manifest.time, "07:00")
        self.assertEqual(len(manifest.carriers), 2)
        self.assertEqual(manifest.carriers[0].name, "Australia Post Metro")
        self.assertEqual(manifest.carriers[1].name, "DHL Express")
    
    def test_from_config_format_invalid_data(self):
        """Test creating manifest from invalid config format."""
        with self.assertRaises(DataValidationException):
            Manifest.from_config_format({"carriers": []})  # Missing time
    
    def test_from_config_format_empty_carriers(self):
        """Test creating manifest from config format with empty carriers."""
        data = {"time": "07:00", "carriers": []}
        
        manifest = Manifest.from_config_format(data)
        
        self.assertEqual(len(manifest.carriers), 0)
    
    def test_update_status_all_acknowledged(self):
        """Test status update when all carriers acknowledged."""
        carrier1 = Carrier("Carrier 1")
        carrier2 = Carrier("Carrier 2")
        manifest = Manifest("07:00", [carrier1, carrier2])
        
        # Initially not acknowledged
        self.assertFalse(manifest.acknowledged)
        
        # Acknowledge all carriers
        carrier1.acknowledge("user1")
        carrier2.acknowledge("user2")
        manifest._update_status()
        
        self.assertTrue(manifest.acknowledged)
    
    def test_update_status_partial_acknowledged(self):
        """Test status update when partially acknowledged."""
        carrier1 = Carrier("Carrier 1")
        carrier2 = Carrier("Carrier 2")
        carrier1.acknowledge("user")
        manifest = Manifest("07:00", [carrier1, carrier2])
        
        self.assertFalse(manifest.acknowledged)
    
    def test_validation_with_acknowledged_carriers(self):
        """Test validation when creating manifest with acknowledged carriers."""
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user")
        
        manifest = Manifest("07:00", [carrier])
        
        # Should properly set acknowledgment status
        self.assertTrue(manifest.acknowledged)
    
    def test_string_representation(self):
        """Test string representation of manifest."""
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        str_repr = str(manifest)
        self.assertIn("07:00", str_repr)
        self.assertIn("0/1", str_repr)  # Acknowledgment summary
    
    def test_repr(self):
        """Test developer representation of manifest."""
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        repr_str = repr(manifest)
        self.assertIn("Manifest", repr_str)
        self.assertIn("07:00", repr_str)
        self.assertIn("carriers=1", repr_str)
    
    def test_complex_acknowledgment_scenario(self):
        """Test complex scenario with multiple carriers and acknowledgments."""
        # Create manifest with multiple carriers
        carriers = [
            Carrier("Australia Post Metro"),
            Carrier("DHL Express"),
            Carrier("EParcel Express")
        ]
        manifest = Manifest("07:00", carriers, date="2025-07-23")
        
        # Acknowledge some carriers
        manifest.acknowledge_carrier("Australia Post Metro", "john.doe", "On time")
        manifest.acknowledge_carrier("DHL Express", "jane.smith")
        
        # Check state
        self.assertFalse(manifest.acknowledged)  # Not all acknowledged
        self.assertEqual(len(manifest.get_unacknowledged_carriers()), 1)
        self.assertEqual(len(manifest.get_acknowledged_carriers()), 2)
        self.assertEqual(len(manifest.acknowledgments), 2)
        
        # Acknowledge remaining carrier
        manifest.acknowledge_carrier("EParcel Express", "bob.wilson", "Late but done")
        
        # Check final state
        self.assertTrue(manifest.acknowledged)
        self.assertEqual(len(manifest.get_unacknowledged_carriers()), 0)
        self.assertEqual(len(manifest.acknowledgments), 3)
        
        # Check acknowledgment details
        ack = manifest.acknowledgments[0]
        self.assertEqual(ack.date, "2025-07-23")
        self.assertEqual(ack.manifest_time, "07:00")
        self.assertEqual(ack.user, "john.doe")


if __name__ == '__main__':
    unittest.main()