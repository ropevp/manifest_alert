"""
Test suite for Alert Service business logic.

Tests the core alert triggering, layout calculations, and 
single alert scaling feature.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.application.services.alert_service import AlertService, LayoutMode
from src.domain.models.manifest import Manifest, ManifestStatus
from src.domain.models.carrier import Carrier
from src.domain.models.alert import AlertPriority, AlertType
from src.domain.models.mute_status import MuteStatus, MuteType


class TestAlertService(unittest.TestCase):
    """Test cases for AlertService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manifest_repo = Mock()
        self.mute_repo = Mock()
        self.logger = Mock()
        
        self.alert_service = AlertService(
            self.manifest_repo,
            self.mute_repo,
            self.logger
        )
        
        # Mock current time for consistent testing
        self.test_time = datetime(2025, 7, 24, 10, 30)  # 10:30 AM today
    
    def _create_test_manifest(self, time_str: str, carrier_names: list, 
                            acknowledged: bool = False) -> Manifest:
        """Create a test manifest with carriers."""
        carriers = [Carrier(name) for name in carrier_names]
        manifest = Manifest(
            time=time_str, 
            date="2025-07-24",  # Explicit date matching test_time
            carriers=carriers
        )
        
        if acknowledged:
            for carrier in carriers:
                carrier.acknowledge("test_user", "test")
            # Update manifest status after acknowledging carriers
            manifest._update_status()
        
        return manifest
    
    def test_calculate_layout_mode_single_card(self):
        """Test single card layout mode calculation."""
        # Setup: One active manifest, no missed
        active_manifest = self._create_test_manifest("10:25", ["UPS", "FEDEX"])
        pending_manifest = self._create_test_manifest("11:00", ["DHL"])
        
        manifests = [active_manifest, pending_manifest]
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        layout_mode = self.alert_service.calculate_layout_mode(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout_mode, LayoutMode.SINGLE_CARD)
    
    def test_calculate_layout_mode_normal_multiple_active(self):
        """Test normal layout mode with multiple active manifests."""
        # Setup: Two active manifests
        active1 = self._create_test_manifest("10:25", ["UPS"])
        active2 = self._create_test_manifest("10:28", ["FEDEX"])
        
        manifests = [active1, active2]
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        layout_mode = self.alert_service.calculate_layout_mode(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout_mode, LayoutMode.NORMAL)
    
    def test_calculate_layout_mode_normal_with_missed(self):
        """Test normal layout mode when missed alerts exist."""
        # Setup: One active, one missed
        active_manifest = self._create_test_manifest("10:25", ["UPS"])
        missed_manifest = self._create_test_manifest("09:30", ["FEDEX"])  # Should be missed
        
        manifests = [active_manifest, missed_manifest]
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        layout_mode = self.alert_service.calculate_layout_mode(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout_mode, LayoutMode.NORMAL)
    
    def test_calculate_layout_mode_no_alerts(self):
        """Test no alerts layout mode."""
        # Setup: All acknowledged manifests
        manifest1 = self._create_test_manifest("10:25", ["UPS"], acknowledged=True)
        manifest2 = self._create_test_manifest("11:00", ["FEDEX"])  # Future/pending
        
        manifests = [manifest1, manifest2]
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        layout_mode = self.alert_service.calculate_layout_mode(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout_mode, LayoutMode.NO_ALERTS)
    
    def test_should_trigger_alert_active_not_muted(self):
        """Test alert triggering for active, unmuted manifest."""
        # Setup
        manifest = self._create_test_manifest("10:25", ["UPS", "FEDEX"])
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        should_trigger = self.alert_service.should_trigger_alert(manifest, self.test_time)
        
        # Verify
        self.assertTrue(should_trigger)
    
    def test_should_trigger_alert_muted_system(self):
        """Test alert triggering when system is muted."""
        # Setup
        manifest = self._create_test_manifest("10:25", ["UPS"])
        
        # Mock mute status as muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=True, mute_type=MuteType.MANUAL)
        
        # Test
        should_trigger = self.alert_service.should_trigger_alert(manifest, self.test_time)
        
        # Verify
        self.assertFalse(should_trigger)
    
    def test_should_trigger_alert_acknowledged(self):
        """Test alert triggering for acknowledged manifest."""
        # Setup
        manifest = self._create_test_manifest("10:25", ["UPS"], acknowledged=True)
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        should_trigger = self.alert_service.should_trigger_alert(manifest, self.test_time)
        
        # Verify
        self.assertFalse(should_trigger)
    
    def test_get_alert_summary(self):
        """Test alert summary generation."""
        # Setup
        active = self._create_test_manifest("10:25", ["UPS", "FEDEX"])  # 2 unack carriers
        missed = self._create_test_manifest("09:30", ["DHL"])  # 1 unack carrier
        acknowledged = self._create_test_manifest("10:00", ["USPS"], acknowledged=True)
        pending = self._create_test_manifest("11:00", ["TNT"])
        
        manifests = [active, missed, acknowledged, pending]
        
        # Mock mute status
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        summary = self.alert_service.get_alert_summary(manifests, self.test_time)
        
        # Verify
        self.assertEqual(summary['total_manifests'], 4)
        self.assertEqual(len(summary['active_manifests']), 1)
        self.assertEqual(len(summary['missed_manifests']), 1)
        self.assertEqual(len(summary['pending_manifests']), 1)
        self.assertEqual(len(summary['acknowledged_manifests']), 1)
        self.assertEqual(summary['active_alerts'], 2)  # UPS + FEDEX
        self.assertEqual(summary['missed_alerts'], 1)   # DHL
        self.assertEqual(summary['total_alerts'], 3)
        self.assertEqual(summary['layout_mode'], LayoutMode.NORMAL)  # Has missed alerts
    
    def test_create_alert_high_priority_missed(self):
        """Test creating high priority alert for missed manifest."""
        # Setup
        manifest = self._create_test_manifest("09:30", ["UPS"])  # Should be missed
        carrier = manifest.carriers[0]
        
        # Test
        alert = self.alert_service.create_alert(manifest, carrier, AlertType.VISUAL)
        
        # Verify
        self.assertEqual(alert.priority, AlertPriority.HIGH)
        self.assertEqual(alert.alert_type, AlertType.VISUAL)
        self.assertEqual(alert.manifest_time, "09:30")
        self.assertEqual(alert.carrier_name, "UPS")
        self.assertIn("MISSED", alert.message)
    
    def test_create_alert_medium_priority_active(self):
        """Test creating medium priority alert for active manifest."""
        # Setup
        manifest = self._create_test_manifest("10:25", ["FEDEX"])  # Should be active
        carrier = manifest.carriers[0]
        
        # Test
        alert = self.alert_service.create_alert(manifest, carrier, AlertType.CARRIER)
        
        # Verify
        self.assertEqual(alert.priority, AlertPriority.MEDIUM)
        self.assertEqual(alert.alert_type, AlertType.CARRIER)
        self.assertEqual(alert.manifest_time, "10:25")
        self.assertEqual(alert.carrier_name, "FEDEX")
        self.assertIn("ALERT", alert.message)
    
    def test_get_prioritized_alerts(self):
        """Test getting prioritized alerts list."""
        # Setup
        missed = self._create_test_manifest("09:30", ["UPS"])  # High priority
        active = self._create_test_manifest("10:25", ["FEDEX", "DHL"])  # Medium priority
        
        manifests = [active, missed]  # Order shouldn't matter
        
        # Mock mute status as not muted
        self.mute_repo.get_current_status.return_value = MuteStatus(is_muted=False, mute_type=MuteType.DISABLED)
        
        # Test
        alerts = self.alert_service.get_prioritized_alerts(manifests, self.test_time)
        
        # Verify
        self.assertEqual(len(alerts), 6)  # 2 manifest + 4 carrier alerts
        
        # Check priority ordering (high priority first)
        high_priority_alerts = [a for a in alerts if a.priority == AlertPriority.HIGH]
        medium_priority_alerts = [a for a in alerts if a.priority == AlertPriority.MEDIUM]
        
        self.assertEqual(len(high_priority_alerts), 2)  # 1 manifest + 1 carrier
        self.assertEqual(len(medium_priority_alerts), 4)  # 1 manifest + 2 carriers
        
        # First alert should be high priority
        self.assertEqual(alerts[0].priority, AlertPriority.HIGH)
    
    def test_error_handling_repository_failure(self):
        """Test error handling when repository fails."""
        # Setup
        manifests = [self._create_test_manifest("10:25", ["UPS"])]
        
        # Mock repository to raise exception
        self.mute_repo.get_current_status.side_effect = Exception("Network error")
        
        # Test - should not raise exception
        layout_mode = self.alert_service.calculate_layout_mode(manifests, self.test_time)
        
        # Verify fallback behavior
        self.assertEqual(layout_mode, LayoutMode.NORMAL)


if __name__ == '__main__':
    unittest.main()
