"""
Test suite for Layout Service business logic.

Tests the single alert scaling feature and layout calculations.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.application.services.layout_service import (
    LayoutService, LayoutMode, CardSize, LayoutConfiguration
)
from src.application.services.alert_service import AlertService
from src.application.services.mute_service import MuteService
from src.domain.models.manifest import Manifest, ManifestStatus
from src.domain.models.carrier import Carrier
from src.domain.models.mute_status import MuteStatus


class TestLayoutService(unittest.TestCase):
    """Test cases for LayoutService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.alert_service = Mock(spec=AlertService)
        self.mute_service = Mock(spec=MuteService)
        self.logger = Mock()
        
        self.layout_service = LayoutService(
            self.alert_service,
            self.mute_service,
            logger=self.logger
        )
        
        # Mock current time
        self.test_time = datetime(2025, 1, 15, 10, 30)
    
    def _create_test_manifest(self, time_str: str, carrier_names: list, 
                            acknowledged: bool = False) -> Manifest:
        """Create a test manifest with carriers."""
        carriers = [Carrier(name) for name in carrier_names]
        manifest = Manifest(time=time_str, carriers=carriers)
        
        if acknowledged:
            for carrier in carriers:
                carrier.acknowledge("test_user", "test")
        
        return manifest
    
    def test_should_use_single_card_mode_true(self):
        """Test single card mode detection - should return True."""
        # Setup: One active manifest, no missed, not muted
        active_manifest = self._create_test_manifest("10:25", ["UPS", "FEDEX"])
        pending_manifest = self._create_test_manifest("11:00", ["DHL"])
        
        manifests = [active_manifest, pending_manifest]
        
        # Mock mute service
        self.mute_service.is_muted.return_value = False
        
        # Test
        should_use = self.layout_service.should_use_single_card_mode(manifests, self.test_time)
        
        # Verify
        self.assertTrue(should_use)
    
    def test_should_use_single_card_mode_false_multiple_active(self):
        """Test single card mode detection - multiple active manifests."""
        # Setup: Two active manifests
        active1 = self._create_test_manifest("10:25", ["UPS"])
        active2 = self._create_test_manifest("10:28", ["FEDEX"])
        
        manifests = [active1, active2]
        
        # Mock mute service
        self.mute_service.is_muted.return_value = False
        
        # Test
        should_use = self.layout_service.should_use_single_card_mode(manifests, self.test_time)
        
        # Verify
        self.assertFalse(should_use)
    
    def test_should_use_single_card_mode_false_has_missed(self):
        """Test single card mode detection - has missed alerts."""
        # Setup: One active, one missed
        active_manifest = self._create_test_manifest("10:25", ["UPS"])
        missed_manifest = self._create_test_manifest("09:30", ["FEDEX"])  # Should be missed
        
        manifests = [active_manifest, missed_manifest]
        
        # Mock mute service
        self.mute_service.is_muted.return_value = False
        
        # Test
        should_use = self.layout_service.should_use_single_card_mode(manifests, self.test_time)
        
        # Verify
        self.assertFalse(should_use)
    
    def test_should_use_single_card_mode_false_muted(self):
        """Test single card mode detection - system muted."""
        # Setup: One active manifest but system is muted
        active_manifest = self._create_test_manifest("10:25", ["UPS"])
        
        manifests = [active_manifest]
        
        # Mock mute service as muted
        self.mute_service.is_muted.return_value = True
        
        # Test
        should_use = self.layout_service.should_use_single_card_mode(manifests, self.test_time)
        
        # Verify
        self.assertFalse(should_use)
    
    def test_get_maximized_manifest(self):
        """Test getting the manifest that should be maximized."""
        # Setup: One active manifest that should be maximized
        active_manifest = self._create_test_manifest("10:25", ["UPS"])
        pending_manifest = self._create_test_manifest("11:00", ["FEDEX"])
        
        manifests = [active_manifest, pending_manifest]
        
        # Mock mute service
        self.mute_service.is_muted.return_value = False
        
        # Test
        maximized = self.layout_service.get_maximized_manifest(manifests, self.test_time)
        
        # Verify
        self.assertEqual(maximized.time, "10:25")
        self.assertEqual(maximized, active_manifest)
    
    def test_get_maximized_manifest_none(self):
        """Test getting maximized manifest when none should be maximized."""
        # Setup: Multiple active manifests
        active1 = self._create_test_manifest("10:25", ["UPS"])
        active2 = self._create_test_manifest("10:28", ["FEDEX"])
        
        manifests = [active1, active2]
        
        # Mock mute service
        self.mute_service.is_muted.return_value = False
        
        # Test
        maximized = self.layout_service.get_maximized_manifest(manifests, self.test_time)
        
        # Verify
        self.assertIsNone(maximized)
    
    def test_calculate_card_size_maximized(self):
        """Test card size calculation for maximized card."""
        # Setup
        manifest = self._create_test_manifest("10:25", ["UPS"])
        
        # Test
        card_size = self.layout_service.calculate_card_size(
            manifest, LayoutMode.SINGLE_CARD, is_maximized=True
        )
        
        # Verify
        self.assertEqual(card_size, CardSize.MAXIMIZED)
    
    def test_calculate_card_size_normal(self):
        """Test card size calculation for normal card."""
        # Setup
        manifest = self._create_test_manifest("10:25", ["UPS"])
        
        # Test
        card_size = self.layout_service.calculate_card_size(
            manifest, LayoutMode.NORMAL, is_maximized=False
        )
        
        # Verify
        self.assertEqual(card_size, CardSize.NORMAL)
    
    def test_get_card_dimensions(self):
        """Test getting card dimensions for different sizes."""
        # Test normal size
        width, height = self.layout_service.get_card_dimensions(CardSize.NORMAL)
        self.assertEqual(width, 1200)
        self.assertEqual(height, 80)
        
        # Test maximized size
        width, height = self.layout_service.get_card_dimensions(CardSize.MAXIMIZED)
        self.assertEqual(width, 1200)
        self.assertEqual(height, 200)
        
        # Test compact size
        width, height = self.layout_service.get_card_dimensions(CardSize.COMPACT)
        self.assertEqual(width, 1200)
        self.assertEqual(height, 60)
    
    def test_calculate_layout_single_card_mode(self):
        """Test complete layout calculation for single card mode."""
        # Setup
        active_manifest = self._create_test_manifest("10:25", ["UPS", "FEDEX"])
        pending_manifest = self._create_test_manifest("11:00", ["DHL"])
        
        manifests = [active_manifest, pending_manifest]
        
        # Mock services
        self.mute_service.is_muted.return_value = False
        self.alert_service.get_alert_summary.return_value = {
            'total_alerts': 2,
            'active_alerts': 2,
            'missed_alerts': 0,
            'active_manifests': [active_manifest],
            'missed_manifests': [],
            'pending_manifests': [pending_manifest],
            'acknowledged_manifests': []
        }
        self.alert_service.should_trigger_alert.side_effect = lambda m, t: m == active_manifest
        
        # Test
        layout = self.layout_service.calculate_layout(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout['mode'], LayoutMode.SINGLE_CARD)
        self.assertTrue(layout['single_card_active'])
        self.assertEqual(layout['maximized_manifest'], "10:25")
        self.assertEqual(layout['total_manifests'], 2)
        self.assertEqual(layout['visible_manifests'], 2)
        
        # Check card configurations
        card_configs = layout['card_configurations']
        self.assertEqual(len(card_configs), 2)
        
        # Find the maximized card
        maximized_card = next((c for c in card_configs if c['maximized']), None)
        self.assertIsNotNone(maximized_card)
        self.assertEqual(maximized_card['manifest'].time, "10:25")
        self.assertEqual(maximized_card['card_size'], CardSize.MAXIMIZED)
        self.assertEqual(maximized_card['height'], 200)
    
    def test_calculate_layout_normal_mode(self):
        """Test complete layout calculation for normal mode."""
        # Setup
        active1 = self._create_test_manifest("10:25", ["UPS"])
        active2 = self._create_test_manifest("10:28", ["FEDEX"])
        
        manifests = [active1, active2]
        
        # Mock services
        self.mute_service.is_muted.return_value = False
        self.alert_service.get_alert_summary.return_value = {
            'total_alerts': 2,
            'active_alerts': 2,
            'missed_alerts': 0,
            'active_manifests': [active1, active2],
            'missed_manifests': [],
            'pending_manifests': [],
            'acknowledged_manifests': []
        }
        self.alert_service.should_trigger_alert.return_value = True
        
        # Test
        layout = self.layout_service.calculate_layout(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout['mode'], LayoutMode.NORMAL)
        self.assertFalse(layout['single_card_active'])
        self.assertIsNone(layout['maximized_manifest'])
        
        # All cards should be normal size
        card_configs = layout['card_configurations']
        for config in card_configs:
            self.assertEqual(config['card_size'], CardSize.NORMAL)
            self.assertEqual(config['height'], 80)
            self.assertFalse(config['maximized'])
    
    def test_calculate_layout_no_alerts_mode(self):
        """Test layout calculation for no alerts mode."""
        # Setup
        acknowledged = self._create_test_manifest("10:00", ["UPS"], acknowledged=True)
        pending = self._create_test_manifest("11:00", ["FEDEX"])
        
        manifests = [acknowledged, pending]
        
        # Mock services
        self.mute_service.is_muted.return_value = False
        self.alert_service.get_alert_summary.return_value = {
            'total_alerts': 0,
            'active_alerts': 0,
            'missed_alerts': 0,
            'active_manifests': [],
            'missed_manifests': [],
            'pending_manifests': [pending],
            'acknowledged_manifests': [acknowledged]
        }
        self.alert_service.should_trigger_alert.return_value = False
        
        # Test
        layout = self.layout_service.calculate_layout(manifests, self.test_time)
        
        # Verify
        self.assertEqual(layout['mode'], LayoutMode.NO_ALERTS)
        self.assertFalse(layout['single_card_active'])
    
    def test_layout_configuration_customization(self):
        """Test custom layout configuration."""
        # Setup custom config
        custom_config = LayoutConfiguration()
        custom_config.single_card_enabled = False
        custom_config.maximized_card_height = 300
        
        layout_service = LayoutService(
            self.alert_service,
            self.mute_service,
            layout_config=custom_config
        )
        
        # Test single card mode (should be disabled)
        active_manifest = self._create_test_manifest("10:25", ["UPS"])
        manifests = [active_manifest]
        
        self.mute_service.is_muted.return_value = False
        
        should_use = layout_service.should_use_single_card_mode(manifests, self.test_time)
        self.assertFalse(should_use)  # Disabled by config
        
        # Test custom dimensions
        width, height = layout_service.get_card_dimensions(CardSize.MAXIMIZED)
        self.assertEqual(height, 300)  # Custom height
    
    def test_error_handling_service_failure(self):
        """Test error handling when services fail."""
        # Setup
        manifests = [self._create_test_manifest("10:25", ["UPS"])]
        
        # Mock service to raise exception
        self.alert_service.get_alert_summary.side_effect = Exception("Service error")
        
        # Test - should not raise exception
        layout = self.layout_service.calculate_layout(manifests, self.test_time)
        
        # Verify fallback behavior
        self.assertIsInstance(layout, dict)
        self.assertIn('mode', layout)


if __name__ == '__main__':
    unittest.main()
