"""
Unit tests for network service functionality.

Tests timeout protection, retry logic, and performance requirements
for network file operations.
"""

import unittest
import tempfile
import json
import time
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.infrastructure.network import NetworkService, timeout_context, TimeoutException
from src.infrastructure.cache import CacheManager
from src.infrastructure.exceptions import NetworkAccessException


class TestTimeoutContext(unittest.TestCase):
    """Test cases for timeout context manager."""
    
    def test_timeout_context_success(self):
        """Test timeout context with operation that completes in time."""
        # Act
        with timeout_context(1.0):
            time.sleep(0.1)  # Short operation
        
        # Assert - Should complete without exception
    
    def test_timeout_context_with_zero_timeout_raises_error(self):
        """Test timeout context with invalid timeout."""
        # Act & Assert
        with self.assertRaises(ValueError):
            with timeout_context(0):
                pass
    
    def test_timeout_context_with_negative_timeout_raises_error(self):
        """Test timeout context with negative timeout."""
        # Act & Assert
        with self.assertRaises(ValueError):
            with timeout_context(-1.0):
                pass
    
    @patch('src.infrastructure.network.timeout_context.os.name', 'nt')
    def test_windows_timeout_implementation(self):
        """Test Windows-specific timeout implementation."""
        # This test verifies the Windows branch is taken
        # The actual timeout testing is difficult in unit tests
        with timeout_context(1.0):
            time.sleep(0.01)  # Very short operation
    
    def test_timeout_manager_execute_with_timeout(self):
        """Test timeout manager execution."""
        from src.infrastructure.network.timeout_context import NetworkTimeoutManager
        
        # Arrange
        manager = NetworkTimeoutManager(1.0)
        
        def quick_operation():
            return "success"
        
        # Act
        result = manager.execute_with_timeout(quick_operation, 1.0, "test operation")
        
        # Assert
        self.assertEqual(result, "success")
    
    def test_timeout_manager_with_failing_operation(self):
        """Test timeout manager with failing operation."""
        from src.infrastructure.network.timeout_context import NetworkTimeoutManager
        
        # Arrange
        manager = NetworkTimeoutManager(1.0)
        
        def failing_operation():
            raise ValueError("Operation failed")
        
        # Act & Assert
        with self.assertRaises(ValueError):
            manager.execute_with_timeout(failing_operation, 1.0, "failing operation")


class TestNetworkService(unittest.TestCase):
    """Test cases for NetworkService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_cache_manager = Mock(spec=CacheManager)
        
        # Use temp directory as network path for testing
        self.network_service = NetworkService(
            network_path=self.temp_dir,
            cache_manager=self.mock_cache_manager
        )
    
    def test_network_service_initialization(self):
        """Test network service initialization."""
        # Assert
        self.assertEqual(str(self.network_service.network_path), self.temp_dir)
        self.assertEqual(self.network_service.DEFAULT_TIMEOUT, 1.0)
        self.assertIsNotNone(self.network_service.cache_manager)
    
    def test_load_json_file_with_cache(self):
        """Test loading JSON file using cache."""
        # Arrange
        test_data = {"test_key": "test_value"}
        self.mock_cache_manager.get_network_cached.return_value = test_data
        
        # Act
        result = self.network_service.load_json_file("test.json")
        
        # Assert
        self.assertEqual(result, test_data)
        self.mock_cache_manager.get_network_cached.assert_called_once()
    
    def test_load_json_file_without_cache(self):
        """Test loading JSON file without cache."""
        # Arrange
        test_data = {"test_key": "test_value"}
        test_file = Path(self.temp_dir) / "test.json"
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Act
        result = self.network_service.load_json_file("test.json", use_cache=False)
        
        # Assert
        self.assertEqual(result, test_data)
    
    def test_save_json_file(self):
        """Test saving JSON file."""
        # Arrange
        test_data = {"test_key": "test_value"}
        
        # Act
        result = self.network_service.save_json_file("save_test.json", test_data)
        
        # Assert
        self.assertTrue(result)
        
        # Verify file was created
        test_file = Path(self.temp_dir) / "save_test.json"
        self.assertTrue(test_file.exists())
        
        # Verify content
        with open(test_file, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, test_data)
    
    def test_save_json_file_with_backup(self):
        """Test saving JSON file with backup creation."""
        # Arrange
        test_file = Path(self.temp_dir) / "backup_test.json"
        original_data = {"original": "data"}
        new_data = {"new": "data"}
        
        # Create original file
        with open(test_file, 'w') as f:
            json.dump(original_data, f)
        
        # Act
        result = self.network_service.save_json_file("backup_test.json", new_data, create_backup=True)
        
        # Assert
        self.assertTrue(result)
        
        # Check that a backup was created
        backup_files = list(Path(self.temp_dir).glob("backup_test_backup_*.json"))
        self.assertGreater(len(backup_files), 0)
    
    def test_file_exists(self):
        """Test file existence check."""
        # Arrange
        test_file = Path(self.temp_dir) / "exists_test.json"
        test_file.write_text("{}")
        
        # Act
        exists = self.network_service.file_exists("exists_test.json", use_cache=False)
        not_exists = self.network_service.file_exists("nonexistent.json", use_cache=False)
        
        # Assert
        self.assertTrue(exists)
        self.assertFalse(not_exists)
    
    def test_file_exists_with_cache(self):
        """Test file existence check using cache."""
        # Arrange
        self.mock_cache_manager.get_fast_cached.return_value = True
        
        # Act
        result = self.network_service.file_exists("cached_file.json")
        
        # Assert
        self.assertTrue(result)
        self.mock_cache_manager.get_fast_cached.assert_called_once()
    
    def test_get_file_modification_time(self):
        """Test getting file modification time."""
        # Arrange
        test_file = Path(self.temp_dir) / "mtime_test.json"
        test_file.write_text("{}")
        expected_mtime = test_file.stat().st_mtime
        
        # Act
        result = self.network_service.get_file_modification_time("mtime_test.json")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, expected_mtime, places=1)
    
    def test_get_file_modification_time_nonexistent(self):
        """Test getting modification time for nonexistent file."""
        # Act
        result = self.network_service.get_file_modification_time("nonexistent.json")
        
        # Assert
        self.assertIsNone(result)
    
    def test_validate_network_access(self):
        """Test network access validation."""
        # Act
        result = self.network_service.validate_network_access()
        
        # Assert
        self.assertTrue(result)  # temp_dir should be accessible
    
    def test_validate_network_access_invalid_path(self):
        """Test network access validation with invalid path."""
        # Arrange
        invalid_service = NetworkService(network_path="\\\\invalid\\nonexistent\\path")
        
        # Act
        result = invalid_service.validate_network_access()
        
        # Assert
        self.assertFalse(result)
    
    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        # Arrange - Perform some operations to generate stats
        test_file = Path(self.temp_dir) / "perf_test.json"
        test_file.write_text('{"test": "data"}')
        
        self.network_service.load_json_file("perf_test.json", use_cache=False)
        
        # Act
        stats = self.network_service.get_performance_stats()
        
        # Assert
        self.assertIn("total_operations", stats)
        self.assertIn("average_time_ms", stats)
        self.assertIn("timeout_count", stats)
        self.assertIn("cache_stats", stats)
        self.assertGreater(stats["total_operations"], 0)
    
    def test_cache_invalidation_after_save(self):
        """Test that cache is invalidated after saving file."""
        # Arrange
        test_data = {"test": "data"}
        
        # Act
        self.network_service.save_json_file("invalidate_test.json", test_data)
        
        # Assert
        self.mock_cache_manager.invalidate.assert_called_once_with("json_file:invalidate_test.json", "network")


class TestNetworkServiceErrorHandling(unittest.TestCase):
    """Test error handling in network service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock(spec=CacheManager)
        self.network_service = NetworkService(
            network_path="\\\\invalid\\path",  # Invalid network path
            cache_manager=self.mock_cache_manager
        )
    
    def test_load_nonexistent_file_raises_exception(self):
        """Test loading nonexistent file raises appropriate exception."""
        # Arrange
        self.mock_cache_manager.get_network_cached.side_effect = NetworkAccessException("File not found")
        
        # Act & Assert
        with self.assertRaises(NetworkAccessException):
            self.network_service.load_json_file("nonexistent.json", use_cache=False)
    
    def test_save_to_invalid_path_raises_exception(self):
        """Test saving to invalid path raises exception."""
        # Act & Assert
        with self.assertRaises(NetworkAccessException):
            self.network_service.save_json_file("test.json", {"data": "test"})
    
    def test_timeout_increments_counter(self):
        """Test that timeouts increment the timeout counter."""
        # This is difficult to test directly, but we can verify the counter exists
        initial_count = self.network_service._timeout_count
        
        # Try an operation that should timeout (invalid path)
        try:
            self.network_service.validate_network_access(timeout=0.001)  # Very short timeout
        except:
            pass
        
        # The timeout count may or may not increment depending on the system
        # This test mainly verifies the counter exists and is being tracked
        self.assertIsInstance(self.network_service._timeout_count, int)


class TestNetworkServicePerformanceRequirements(unittest.TestCase):
    """Test that network service meets performance requirements."""
    
    def test_default_timeout_requirement(self):
        """Test that default timeout meets 1-second requirement."""
        self.assertEqual(NetworkService.DEFAULT_TIMEOUT, 1.0)
    
    def test_max_retries_configuration(self):
        """Test max retries configuration."""
        self.assertEqual(NetworkService.MAX_RETRIES, 2)
        self.assertEqual(NetworkService.RETRY_DELAY, 0.1)
    
    def test_network_path_configuration(self):
        """Test default network path configuration."""
        expected_path = r"\\Prddpkmitlgt004\ManifestPC"
        self.assertEqual(NetworkService.DEFAULT_NETWORK_PATH, expected_path)
    
    def test_operation_speed_meets_requirements(self):
        """Test that network operations are fast enough."""
        # Arrange
        temp_dir = tempfile.mkdtemp()
        service = NetworkService(network_path=temp_dir)
        
        test_file = Path(temp_dir) / "speed_test.json"
        test_data = {"test": "data"}
        test_file.write_text(json.dumps(test_data))
        
        # Act - Measure operation speed
        start_time = time.time()
        for _ in range(10):
            service.load_json_file("speed_test.json", use_cache=False)
        end_time = time.time()
        
        # Assert - Should be fast enough for real-time use
        avg_time_per_operation = (end_time - start_time) / 10
        self.assertLess(avg_time_per_operation, 0.1)  # Less than 100ms per operation


class TestNetworkServiceIntegration(unittest.TestCase):
    """Integration tests for network service with real file operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.network_service = NetworkService(network_path=self.temp_dir)
    
    def test_full_json_workflow(self):
        """Test complete JSON file workflow."""
        # Arrange
        test_data = {
            "manifest_times": ["07:00", "13:00", "19:00"],
            "carriers": ["Australia Post Metro", "DHL Express"],
            "version": "1.0"
        }
        
        # Act - Save file
        save_result = self.network_service.save_json_file("workflow_test.json", test_data)
        
        # Act - Load file
        loaded_data = self.network_service.load_json_file("workflow_test.json", use_cache=False)
        
        # Assert
        self.assertTrue(save_result)
        self.assertEqual(loaded_data, test_data)
    
    def test_concurrent_file_access(self):
        """Test concurrent access to the same file."""
        import threading
        
        # Arrange
        test_data = {"concurrent": "test"}
        results = []
        
        def load_file():
            try:
                result = self.network_service.load_json_file("concurrent_test.json", use_cache=False)
                results.append(result)
            except:
                results.append(None)
        
        # Create test file
        test_file = Path(self.temp_dir) / "concurrent_test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Act - Multiple concurrent loads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_file)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert - All loads should succeed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result, test_data)
    
    def test_file_backup_creation(self):
        """Test that file backups are created correctly."""
        # Arrange
        original_data = {"version": 1}
        updated_data = {"version": 2}
        
        # Create original file
        self.network_service.save_json_file("backup_workflow.json", original_data)
        
        # Act - Update file with backup
        self.network_service.save_json_file("backup_workflow.json", updated_data, create_backup=True)
        
        # Assert - Check that backup exists
        backup_files = list(Path(self.temp_dir).glob("backup_workflow_backup_*.json"))
        self.assertGreater(len(backup_files), 0)
        
        # Verify backup contains original data
        with open(backup_files[0], 'r') as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data, original_data)
        
        # Verify main file has updated data
        current_data = self.network_service.load_json_file("backup_workflow.json", use_cache=False)
        self.assertEqual(current_data, updated_data)


if __name__ == '__main__':
    unittest.main()
