"""
Unit tests for repository pattern implementations.

Tests all repository classes with mocking for network operations
and validation of caching behavior.
"""

import unittest
import tempfile
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.infrastructure.repositories.manifest_repository import FileManifestRepository
from src.infrastructure.repositories.mute_repository import FileMuteRepository
from src.infrastructure.repositories.acknowledgment_repository import FileAcknowledgmentRepository
from src.infrastructure.repositories.config_repository import FileConfigRepository
from src.infrastructure.network import NetworkService
from src.infrastructure.cache import CacheManager
from src.domain.models.manifest import Manifest
from src.domain.models.carrier import Carrier
from src.domain.models.mute_status import MuteStatus
from src.domain.models.acknowledgment import Acknowledgment
from src.infrastructure.exceptions import NetworkAccessException, DataValidationException


class TestManifestRepository(unittest.TestCase):
    """Test cases for FileManifestRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_network_service = Mock(spec=NetworkService)
        self.mock_cache_manager = Mock(spec=CacheManager)
        self.temp_dir = tempfile.mkdtemp()
        
        self.repository = FileManifestRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager,
            local_data_path=self.temp_dir
        )
    
    def test_load_manifests_from_cache(self):
        """Test loading manifests using cache."""
        # Arrange
        test_manifests = [
            Manifest("07:00", [Carrier("Australia Post Metro")]),
            Manifest("13:00", [Carrier("DHL Express")])
        ]
        self.mock_cache_manager.get_network_cached.return_value = test_manifests
        
        # Act
        result = self.repository.load_manifests("2025-01-20")
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].time, "07:00")
        self.mock_cache_manager.get_network_cached.assert_called_once()
    
    def test_load_manifest_config(self):
        """Test loading manifest configuration."""
        # Arrange
        test_config = {
            "manifest_times": ["07:00", "13:00"],
            "carriers": ["Australia Post Metro", "DHL Express"]
        }
        self.mock_cache_manager.get_network_cached.return_value = test_config
        
        # Act
        result = self.repository.load_manifest_config()
        
        # Assert
        self.assertEqual(result["manifest_times"], ["07:00", "13:00"])
        self.mock_cache_manager.get_network_cached.assert_called_once()
    
    def test_save_manifest(self):
        """Test saving a manifest."""
        # Arrange
        manifest = Manifest("07:00", [Carrier("Test Carrier")])
        
        # Act
        result = self.repository.save_manifest(manifest)
        
        # Assert
        self.assertTrue(result)
        self.mock_cache_manager.invalidate.assert_called_once()
    
    def test_exists_check(self):
        """Test repository existence check."""
        # Arrange
        self.mock_network_service.file_exists.return_value = True
        
        # Act
        result = self.repository.exists()
        
        # Assert
        self.assertTrue(result)
        self.mock_network_service.file_exists.assert_called_once_with("config.json")
    
    def test_deduplicate_manifests(self):
        """Test manifest deduplication logic."""
        # Arrange
        manifests = [
            Manifest("07:00", [Carrier("Carrier 1")], date="2025-01-20"),
            Manifest("07:00", [Carrier("Carrier 2")], date="2025-01-20"),  # Duplicate time
            Manifest("13:00", [Carrier("Carrier 3")], date="2025-01-20"),
        ]
        
        # Act
        result = self.repository._deduplicate_manifests(manifests)
        
        # Assert
        self.assertEqual(len(result), 2)  # Should remove one duplicate
        times = [m.time for m in result]
        self.assertIn("07:00", times)
        self.assertIn("13:00", times)


class TestMuteRepository(unittest.TestCase):
    """Test cases for FileMuteRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_network_service = Mock(spec=NetworkService)
        self.mock_cache_manager = Mock(spec=CacheManager)
        
        self.repository = FileMuteRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager
        )
    
    def test_load_mute_status_from_cache(self):
        """Test loading mute status using fast cache."""
        # Arrange
        test_mute_status = MuteStatus.create_unmuted()
        self.mock_cache_manager.get_fast_cached.return_value = test_mute_status
        
        # Act
        result = self.repository.load_mute_status()
        
        # Assert
        self.assertFalse(result.is_muted)
        self.mock_cache_manager.get_fast_cached.assert_called_once()
    
    def test_save_mute_status(self):
        """Test saving mute status."""
        # Arrange
        mute_status = MuteStatus.create_snoozed(30)
        self.mock_network_service.save_json_file.return_value = True
        
        # Act
        result = self.repository.save_mute_status(mute_status)
        
        # Assert
        self.assertTrue(result)
        self.mock_network_service.save_json_file.assert_called_once()
        # Should invalidate both fast and network caches
        self.assertEqual(self.mock_cache_manager.invalidate.call_count, 2)
    
    def test_toggle_mute(self):
        """Test toggling mute status."""
        # Arrange
        current_status = MuteStatus.create_unmuted()
        self.mock_cache_manager.get_fast_cached.return_value = current_status
        self.mock_network_service.save_json_file.return_value = True
        
        # Act
        result = self.repository.toggle_mute()
        
        # Assert
        self.assertTrue(result.is_muted)
    
    def test_snooze(self):
        """Test snoozing alerts."""
        # Arrange
        self.mock_network_service.save_json_file.return_value = True
        
        # Act
        result = self.repository.snooze(45)
        
        # Assert
        self.assertTrue(result.is_muted)
        self.assertEqual(result.mute_type.value, "snooze")
    
    def test_cache_fallback_on_network_failure(self):
        """Test fallback to network cache when fast cache fails."""
        # Arrange
        self.mock_cache_manager.get_fast_cached.side_effect = Exception("Cache miss")
        fallback_status = MuteStatus.create_muted()
        self.mock_cache_manager.get_network_cached.return_value = fallback_status
        
        # Act
        result = self.repository.load_mute_status()
        
        # Assert
        self.assertTrue(result.is_muted)
        self.mock_cache_manager.get_fast_cached.assert_called_once()
        self.mock_cache_manager.get_network_cached.assert_called_once()


class TestAcknowledgmentRepository(unittest.TestCase):
    """Test cases for FileAcknowledgmentRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_network_service = Mock(spec=NetworkService)
        self.mock_cache_manager = Mock(spec=CacheManager)
        self.temp_dir = tempfile.mkdtemp()
        
        self.repository = FileAcknowledgmentRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager,
            local_data_path=self.temp_dir
        )
    
    def test_load_acknowledgments_from_cache(self):
        """Test loading acknowledgments using fast cache."""
        # Arrange
        test_acks = [
            Acknowledgment("2025-01-20", "07:00", "Australia Post Metro", "user1"),
            Acknowledgment("2025-01-20", "13:00", "DHL Express", "user2")
        ]
        self.mock_cache_manager.get_fast_cached.return_value = test_acks
        
        # Act
        result = self.repository.load_acknowledgments("2025-01-20")
        
        # Assert
        self.assertEqual(len(result), 2)
        self.mock_cache_manager.get_fast_cached.assert_called_once()
    
    def test_save_acknowledgment(self):
        """Test saving an acknowledgment."""
        # Arrange
        acknowledgment = Acknowledgment("2025-01-20", "07:00", "Test Carrier", "user1")
        
        # Mock the load and save operations
        self.repository._load_all_acknowledgments = Mock(return_value=[])
        self.repository._save_all_acknowledgments = Mock(return_value=True)
        
        # Act
        result = self.repository.save_acknowledgment(acknowledgment)
        
        # Assert
        self.assertTrue(result)
        self.repository._save_all_acknowledgments.assert_called_once()
        self.mock_cache_manager.invalidate.assert_called_once()
    
    def test_get_specific_acknowledgment(self):
        """Test retrieving a specific acknowledgment."""
        # Arrange
        test_acks = [
            Acknowledgment("2025-01-20", "07:00", "Australia Post Metro", "user1"),
            Acknowledgment("2025-01-20", "13:00", "DHL Express", "user2")
        ]
        self.mock_cache_manager.get_fast_cached.return_value = test_acks
        
        # Act
        result = self.repository.get_acknowledgment("07:00", "Australia Post Metro", "2025-01-20")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.manifest_time, "07:00")
        self.assertEqual(result.carrier, "Australia Post Metro")
    
    def test_get_acknowledgment_not_found(self):
        """Test retrieving non-existent acknowledgment."""
        # Arrange
        self.mock_cache_manager.get_fast_cached.return_value = []
        
        # Act
        result = self.repository.get_acknowledgment("99:99", "Nonexistent Carrier", "2025-01-20")
        
        # Assert
        self.assertIsNone(result)
    
    def test_clear_acknowledgments(self):
        """Test clearing acknowledgments for a date."""
        # Arrange
        all_acks = [
            Acknowledgment("2025-01-20", "07:00", "Carrier 1", "user1"),
            Acknowledgment("2025-01-21", "13:00", "Carrier 2", "user2")
        ]
        self.repository._load_all_acknowledgments = Mock(return_value=all_acks)
        self.repository._save_all_acknowledgments = Mock(return_value=True)
        
        # Act
        result = self.repository.clear_acknowledgments("2025-01-20")
        
        # Assert
        self.assertTrue(result)
        # Should save only the acknowledgment from 2025-01-21
        saved_acks = self.repository._save_all_acknowledgments.call_args[0][0]
        self.assertEqual(len(saved_acks), 1)
        self.assertEqual(saved_acks[0].date, "2025-01-21")
    
    def test_acknowledgment_summary(self):
        """Test getting acknowledgment summary statistics."""
        # Arrange
        test_acks = [
            Acknowledgment("2025-01-20", "07:00", "Carrier 1", "user1"),
            Acknowledgment("2025-01-20", "07:00", "Carrier 2", "user1"),
            Acknowledgment("2025-01-20", "13:00", "Carrier 1", "user2")
        ]
        self.mock_cache_manager.get_fast_cached.return_value = test_acks
        
        # Act
        result = self.repository.get_acknowledgment_summary("2025-01-20")
        
        # Assert
        self.assertEqual(result["total_count"], 3)
        self.assertEqual(result["unique_manifests"], 2)  # 07:00 and 13:00
        self.assertEqual(result["unique_carriers"], 2)   # Carrier 1 and Carrier 2
        self.assertEqual(result["acknowledgments_by_user"]["user1"], 2)
        self.assertEqual(result["acknowledgments_by_user"]["user2"], 1)


class TestConfigRepository(unittest.TestCase):
    """Test cases for FileConfigRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_network_service = Mock(spec=NetworkService)
        self.mock_cache_manager = Mock(spec=CacheManager)
        self.temp_dir = tempfile.mkdtemp()
        
        self.repository = FileConfigRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager,
            local_config_path=str(Path(self.temp_dir) / "config.json")
        )
    
    def test_load_config_from_cache(self):
        """Test loading configuration using cache."""
        # Arrange
        test_config = {
            "manifest_times": ["07:00", "13:00"],
            "carriers": ["Australia Post Metro"],
            "sound_enabled": True
        }
        self.mock_cache_manager.get_network_cached.return_value = test_config
        
        # Act
        result = self.repository.load_config()
        
        # Assert
        self.assertEqual(result["manifest_times"], ["07:00", "13:00"])
        self.mock_cache_manager.get_network_cached.assert_called_once()
    
    def test_save_config(self):
        """Test saving configuration."""
        # Arrange
        config = {"test_setting": "test_value"}
        self.mock_network_service.save_json_file.return_value = True
        
        # Act
        result = self.repository.save_config(config)
        
        # Assert
        self.assertTrue(result)
        self.mock_network_service.save_json_file.assert_called_once()
        self.mock_cache_manager.invalidate.assert_called_once_with("app_config")
    
    def test_get_setting(self):
        """Test getting specific configuration setting."""
        # Arrange
        test_config = {"sound_enabled": True, "volume": 75}
        self.mock_cache_manager.get_network_cached.return_value = test_config
        
        # Act
        sound_result = self.repository.get_setting("sound_enabled")
        volume_result = self.repository.get_setting("volume")
        missing_result = self.repository.get_setting("missing_setting", "default")
        
        # Assert
        self.assertTrue(sound_result)
        self.assertEqual(volume_result, 75)
        self.assertEqual(missing_result, "default")
    
    def test_fallback_to_default_config(self):
        """Test fallback to default configuration when loading fails."""
        # Arrange
        self.mock_cache_manager.get_network_cached.side_effect = Exception("Network failure")
        
        # Act
        result = self.repository.load_config()
        
        # Assert
        self.assertIn("manifest_times", result)
        self.assertIn("carriers", result)
        self.assertIn("version", result)
    
    def test_exists_check(self):
        """Test repository existence check."""
        # Arrange
        self.mock_network_service.file_exists.return_value = True
        
        # Act
        result = self.repository.exists()
        
        # Assert
        self.assertTrue(result)


class TestRepositoryErrorHandling(unittest.TestCase):
    """Test error handling across all repositories."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_network_service = Mock(spec=NetworkService)
        self.mock_cache_manager = Mock(spec=CacheManager)
        
        self.manifest_repo = FileManifestRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager
        )
        
        self.mute_repo = FileMuteRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager
        )
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        # Arrange
        self.mock_cache_manager.get_network_cached.side_effect = NetworkAccessException("Timeout")
        
        # Act & Assert
        with self.assertRaises(NetworkAccessException):
            self.manifest_repo.load_manifests()
    
    def test_data_validation_error_handling(self):
        """Test handling of data validation errors."""
        # Arrange
        self.mock_network_service.save_json_file.side_effect = DataValidationException("Invalid data")
        
        # Act & Assert
        with self.assertRaises(NetworkAccessException):
            self.mute_repo.save_mute_status(MuteStatus.create_unmuted())
    
    def test_error_tracking(self):
        """Test that repositories track last errors."""
        # Arrange
        error = NetworkAccessException("Test error")
        self.manifest_repo._set_error(error)
        
        # Act
        last_error = self.manifest_repo.get_last_error()
        
        # Assert
        self.assertEqual(last_error, error)


class TestRepositoryPerformance(unittest.TestCase):
    """Test performance-related functionality of repositories."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_network_service = Mock(spec=NetworkService)
        self.mock_cache_manager = Mock(spec=CacheManager)
        
        # Configure performance stats
        self.mock_network_service.get_performance_stats.return_value = {
            "total_operations": 100,
            "average_time_ms": 50.0,
            "timeout_count": 1,
            "cache_hit_rate": 0.95
        }
        
        self.mute_repo = FileMuteRepository(
            network_service=self.mock_network_service,
            cache_manager=self.mock_cache_manager
        )
    
    def test_performance_stats_collection(self):
        """Test collection of performance statistics."""
        # Act
        stats = self.mute_repo.get_performance_stats()
        
        # Assert
        self.assertIn("mute_repository", stats)
        self.assertIn("cache_hit_ratio", stats["mute_repository"])
        self.assertIn("network_stats", stats["mute_repository"])


if __name__ == '__main__':
    unittest.main()
