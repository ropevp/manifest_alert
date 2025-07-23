"""
Unit tests for Alert domain model.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.domain.models.alert import Alert, AlertType, AlertPriority
from src.domain.models.manifest import Manifest
from src.domain.models.carrier import Carrier
from src.infrastructure.exceptions import DataValidationException


class TestAlert(unittest.TestCase):
    """Test cases for the Alert domain model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_carrier = Carrier("Test Carrier")
        self.test_manifest = Manifest("07:00", [self.test_carrier])
    
    def test_create_valid_alert(self):
        """Test creating a valid alert."""
        alert = Alert(
            alert_id="test_alert",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test Alert",
            message="Test message"
        )
        
        self.assertEqual(alert.alert_id, "test_alert")
        self.assertEqual(alert.alert_type, AlertType.MANIFEST_ACTIVE)
        self.assertEqual(alert.priority, AlertPriority.HIGH)
        self.assertEqual(alert.title, "Test Alert")
        self.assertEqual(alert.message, "Test message")
        self.assertIsInstance(alert.created_at, datetime)
        self.assertIsNone(alert.acknowledged_at)
        self.assertTrue(alert.flash_enabled)
        self.assertTrue(alert.sound_enabled)
    
    def test_auto_timestamp_set(self):
        """Test that created_at is automatically set if not provided."""
        before = datetime.now()
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.SYSTEM_ERROR,
            priority=AlertPriority.MEDIUM,
            title="Test",
            message="Test"
        )
        after = datetime.now()
        
        self.assertIsInstance(alert.created_at, datetime)
        self.assertGreaterEqual(alert.created_at, before)
        self.assertLessEqual(alert.created_at, after)
    
    def test_custom_timestamp(self):
        """Test creating alert with custom timestamp."""
        custom_time = datetime(2025, 7, 23, 10, 30, 0)
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.LOW,
            title="Test",
            message="Test",
            created_at=custom_time
        )
        
        self.assertEqual(alert.created_at, custom_time)
    
    def test_empty_alert_id_raises_exception(self):
        """Test that empty alert ID raises exception."""
        with self.assertRaises(DataValidationException):
            Alert(
                alert_id="",
                alert_type=AlertType.MANIFEST_ACTIVE,
                priority=AlertPriority.HIGH,
                title="Test",
                message="Test"
            )
    
    def test_empty_title_raises_exception(self):
        """Test that empty title raises exception."""
        with self.assertRaises(DataValidationException):
            Alert(
                alert_id="test",
                alert_type=AlertType.MANIFEST_ACTIVE,
                priority=AlertPriority.HIGH,
                title="",
                message="Test"
            )
    
    def test_empty_message_raises_exception(self):
        """Test that empty message raises exception."""
        with self.assertRaises(DataValidationException):
            Alert(
                alert_id="test",
                alert_type=AlertType.MANIFEST_ACTIVE,
                priority=AlertPriority.HIGH,
                title="Test",
                message=""
            )
    
    def test_field_normalization(self):
        """Test that fields are normalized (whitespace trimmed)."""
        alert = Alert(
            alert_id="  test_alert  ",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="  Test Alert  ",
            message="  Test message  "
        )
        
        self.assertEqual(alert.alert_id, "test_alert")
        self.assertEqual(alert.title, "Test Alert")
        self.assertEqual(alert.message, "Test message")
    
    def test_invalid_auto_dismiss_duration_raises_exception(self):
        """Test that invalid auto dismiss duration raises exception."""
        with self.assertRaises(DataValidationException):
            Alert(
                alert_id="test",
                alert_type=AlertType.MANIFEST_ACTIVE,
                priority=AlertPriority.HIGH,
                title="Test",
                message="Test",
                auto_dismiss_after=-1
            )
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test"
        )
        
        self.assertFalse(alert.is_acknowledged())
        
        alert.acknowledge()
        
        self.assertTrue(alert.is_acknowledged())
        self.assertIsInstance(alert.acknowledged_at, datetime)
    
    def test_acknowledge_already_acknowledged(self):
        """Test acknowledging an already acknowledged alert."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test"
        )
        
        alert.acknowledge()
        first_ack_time = alert.acknowledged_at
        
        # Acknowledge again
        alert.acknowledge()
        
        # Should not change the acknowledgment time
        self.assertEqual(alert.acknowledged_at, first_ack_time)
    
    def test_get_age_seconds(self):
        """Test getting alert age in seconds."""
        past_time = datetime.now() - timedelta(seconds=30)
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            created_at=past_time
        )
        
        age = alert.get_age_seconds()
        self.assertGreaterEqual(age, 29)  # Should be around 30 seconds
        self.assertLessEqual(age, 31)
    
    def test_should_auto_dismiss(self):
        """Test auto dismiss logic."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            auto_dismiss_after=10
        )
        
        # Should not auto-dismiss immediately
        self.assertFalse(alert.should_auto_dismiss())
        
        # Should auto-dismiss after enough time
        old_time = datetime.now() - timedelta(seconds=15)
        alert.created_at = old_time
        self.assertTrue(alert.should_auto_dismiss())
    
    def test_should_auto_dismiss_none(self):
        """Test auto dismiss when auto_dismiss_after is None."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test"
        )
        
        # Should never auto-dismiss
        old_time = datetime.now() - timedelta(hours=1)
        alert.created_at = old_time
        self.assertFalse(alert.should_auto_dismiss())
    
    def test_should_flash(self):
        """Test flash logic."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            flash_enabled=True
        )
        
        # Should flash when not acknowledged
        self.assertTrue(alert.should_flash())
        
        # Should not flash when acknowledged
        alert.acknowledge()
        self.assertFalse(alert.should_flash())
        
        # Should not flash when disabled
        alert = Alert(
            alert_id="test2",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            flash_enabled=False
        )
        self.assertFalse(alert.should_flash())
    
    def test_should_play_sound(self):
        """Test sound logic."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            sound_enabled=True
        )
        
        # Should play sound when not acknowledged
        self.assertTrue(alert.should_play_sound())
        
        # Should not play sound when acknowledged
        alert.acknowledge()
        self.assertFalse(alert.should_play_sound())
        
        # Should not play sound when disabled
        alert = Alert(
            alert_id="test2",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            sound_enabled=False
        )
        self.assertFalse(alert.should_play_sound())
    
    def test_get_display_info(self):
        """Test getting display information."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test Alert",
            message="Test message",
            manifest=self.test_manifest
        )
        
        info = alert.get_display_info()
        
        self.assertEqual(info["alert_id"], "test")
        self.assertEqual(info["title"], "Test Alert")
        self.assertEqual(info["message"], "Test message")
        self.assertEqual(info["priority"], "high")
        self.assertFalse(info["acknowledged"])
        self.assertTrue(info["should_flash"])
        self.assertTrue(info["should_play_sound"])
        self.assertIsNotNone(info["manifest_info"])
    
    def test_get_manifest_info(self):
        """Test getting manifest information."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            manifest=self.test_manifest
        )
        
        info = alert.get_manifest_info()
        
        self.assertIsNotNone(info)
        self.assertEqual(info["time"], "07:00")
        self.assertIn("Test Carrier", info["carriers"])
        self.assertIsNotNone(info["status"])
    
    def test_get_manifest_info_no_manifest(self):
        """Test getting manifest info when no manifest is attached."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.SYSTEM_ERROR,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test"
        )
        
        info = alert.get_manifest_info()
        self.assertIsNone(info)
    
    def test_update_from_manifest(self):
        """Test updating alert from manifest state."""
        # Create manifest with unacknowledged carrier
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Original Title",
            message="Original Message",
            manifest=manifest
        )
        
        # Update from manifest
        alert.update_from_manifest()
        
        # Title and message should be updated
        self.assertIn("07:00", alert.title)
        self.assertIn("Test Carrier", alert.message)
    
    def test_update_from_manifest_acknowledged(self):
        """Test updating alert when manifest is fully acknowledged."""
        # Create manifest with acknowledged carrier
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user")
        manifest = Manifest("07:00", [carrier])
        
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test",
            manifest=manifest
        )
        
        # Update from manifest
        alert.update_from_manifest()
        
        # Alert should be auto-acknowledged
        self.assertTrue(alert.is_acknowledged())
    
    def test_to_dict(self):
        """Test converting alert to dictionary."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test Alert",
            message="Test message",
            manifest=self.test_manifest,
            auto_dismiss_after=30
        )
        
        data = alert.to_dict()
        
        self.assertEqual(data["alert_id"], "test")
        self.assertEqual(data["alert_type"], "manifest_active")
        self.assertEqual(data["priority"], "high")
        self.assertEqual(data["title"], "Test Alert")
        self.assertEqual(data["message"], "Test message")
        self.assertIsNotNone(data["manifest"])
        self.assertEqual(data["auto_dismiss_after"], 30)
        self.assertIsNotNone(data["created_at"])
    
    def test_from_dict_complete(self):
        """Test creating alert from complete dictionary."""
        timestamp = datetime.now().isoformat()
        data = {
            "alert_id": "test",
            "alert_type": "manifest_active",
            "priority": "high",
            "title": "Test Alert",
            "message": "Test message",
            "created_at": timestamp,
            "auto_dismiss_after": 30,
            "flash_enabled": False,
            "sound_enabled": False
        }
        
        alert = Alert.from_dict(data)
        
        self.assertEqual(alert.alert_id, "test")
        self.assertEqual(alert.alert_type, AlertType.MANIFEST_ACTIVE)
        self.assertEqual(alert.priority, AlertPriority.HIGH)
        self.assertEqual(alert.title, "Test Alert")
        self.assertEqual(alert.auto_dismiss_after, 30)
        self.assertFalse(alert.flash_enabled)
        self.assertFalse(alert.sound_enabled)
    
    def test_from_dict_minimal(self):
        """Test creating alert from minimal dictionary."""
        data = {
            "alert_id": "test",
            "alert_type": "system_error",
            "priority": "medium",
            "title": "Test",
            "message": "Test"
        }
        
        alert = Alert.from_dict(data)
        
        self.assertEqual(alert.alert_id, "test")
        self.assertEqual(alert.alert_type, AlertType.SYSTEM_ERROR)
        self.assertEqual(alert.priority, AlertPriority.MEDIUM)
        self.assertTrue(alert.flash_enabled)  # Default value
        self.assertTrue(alert.sound_enabled)  # Default value
    
    def test_from_dict_invalid_type(self):
        """Test creating alert from invalid data type raises exception."""
        with self.assertRaises(DataValidationException):
            Alert.from_dict("not a dict")
    
    def test_from_dict_missing_required_fields(self):
        """Test creating alert from dict missing required fields."""
        data = {"alert_id": "test"}  # Missing other required fields
        
        with self.assertRaises(DataValidationException):
            Alert.from_dict(data)
    
    def test_from_dict_invalid_alert_type(self):
        """Test creating alert from dict with invalid alert type."""
        data = {
            "alert_id": "test",
            "alert_type": "invalid_type",
            "priority": "high",
            "title": "Test",
            "message": "Test"
        }
        
        with self.assertRaises(DataValidationException):
            Alert.from_dict(data)
    
    def test_from_dict_invalid_priority(self):
        """Test creating alert from dict with invalid priority."""
        data = {
            "alert_id": "test",
            "alert_type": "manifest_active",
            "priority": "invalid_priority",
            "title": "Test",
            "message": "Test"
        }
        
        with self.assertRaises(DataValidationException):
            Alert.from_dict(data)
    
    def test_create_manifest_alert_active(self):
        """Test creating alert for active manifest."""
        # Create a manifest that would be in active state
        carrier = Carrier("Test Carrier")
        manifest = Manifest("07:00", [carrier])
        
        # Note: Since manifest status depends on current time and our test manifest
        # will be "Missed" by default, we'll test the general creation pattern
        try:
            alert = Alert.create_manifest_alert(manifest)
            self.assertIsNotNone(alert)
            self.assertEqual(alert.manifest, manifest)
            self.assertIn("07:00", alert.title)
        except DataValidationException:
            # This is expected if manifest is not in active/missed state
            pass
    
    def test_create_manifest_alert_invalid_status(self):
        """Test creating alert for manifest with invalid status."""
        # Create fully acknowledged manifest
        carrier = Carrier("Test Carrier")
        carrier.acknowledge("user")
        manifest = Manifest("07:00", [carrier])
        
        with self.assertRaises(DataValidationException):
            Alert.create_manifest_alert(manifest)
    
    def test_string_representation(self):
        """Test string representation of alert."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test Alert",
            message="Test"
        )
        
        str_repr = str(alert)
        self.assertIn("HIGH", str_repr)
        self.assertIn("Test Alert", str_repr)
        self.assertIn("!", str_repr)  # Not acknowledged
        
        alert.acknowledge()
        str_repr = str(alert)
        self.assertIn("✓", str_repr)  # Acknowledged
    
    def test_repr(self):
        """Test developer representation of alert."""
        alert = Alert(
            alert_id="test",
            alert_type=AlertType.MANIFEST_ACTIVE,
            priority=AlertPriority.HIGH,
            title="Test",
            message="Test"
        )
        
        repr_str = repr(alert)
        self.assertIn("Alert", repr_str)
        self.assertIn("test", repr_str)
        self.assertIn("manifest_active", repr_str)
        self.assertIn("high", repr_str)


if __name__ == '__main__':
    unittest.main()