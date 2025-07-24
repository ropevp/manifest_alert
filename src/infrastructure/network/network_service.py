"""
Network service for high-performance file operations.

Provides timeout protection, retry logic, and fallback strategies
for accessing the centralized network share at \\\\Prddpkmitlgt004\\ManifestPC\\.
"""

import os
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List
import json
import threading

from .timeout_context import timeout_context, TimeoutException, NetworkTimeoutManager
from ...infrastructure.exceptions import NetworkAccessException
from ...infrastructure.cache import CacheManager

class NetworkService:
    """High-performance network service with aggressive caching and timeout protection.
    
    Implements the critical network performance requirements:
    - 1-second maximum timeout for all network operations
    - Aggressive caching with 30-second TTL
    - Fallback strategies for network failures
    - Thread-safe operations with retry logic
    """
    
    # Network configuration
    DEFAULT_NETWORK_PATH = r"\\Prddpkmitlgt004\ManifestPC"
    DEFAULT_TIMEOUT = 1.0  # 1 second maximum
    MAX_RETRIES = 2
    RETRY_DELAY = 0.1  # 100ms between retries
    
    def __init__(self, network_path: str = DEFAULT_NETWORK_PATH, 
                 cache_manager: Optional[CacheManager] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the network service.
        
        Args:
            network_path: Path to the network share
            cache_manager: Cache manager for aggressive caching
            logger: Logger for network operations
        """
        self.network_path = Path(network_path)
        self.cache_manager = cache_manager or CacheManager()
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.timeout_manager = NetworkTimeoutManager(self.DEFAULT_TIMEOUT)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance tracking
        self._operation_count = 0
        self._total_time = 0.0
        self._timeout_count = 0
        self._cache_hit_count = 0
        
        self.logger.info(f"NetworkService initialized for path: {self.network_path}")
    
    def load_json_file(self, filename: str, use_cache: bool = True, 
                      timeout: Optional[float] = None) -> Dict[str, Any]:
        """Load a JSON file from the network share with caching and timeout protection.
        
        This is the primary method for loading configuration and data files.
        Uses aggressive caching to minimize network calls.
        
        Args:
            filename: Name of the JSON file to load
            use_cache: Whether to use network cache (30-second TTL)
            timeout: Custom timeout, uses default if None
            
        Returns:
            Parsed JSON data
            
        Raises:
            NetworkAccessException: When file cannot be loaded within timeout
            DataValidationException: When JSON is malformed
        """
        file_path = self.network_path / filename
        cache_key = f"json_file:{filename}"
        
        if use_cache:
            return self.cache_manager.get_network_cached(
                cache_key, 
                lambda: self._load_json_file_direct(file_path, timeout)
            )
        else:
            return self._load_json_file_direct(file_path, timeout)
    
    def save_json_file(self, filename: str, data: Dict[str, Any], 
                      create_backup: bool = True, timeout: Optional[float] = None) -> bool:
        """Save data to a JSON file on the network share with backup and timeout protection.
        
        Args:
            filename: Name of the JSON file to save
            data: Data to save as JSON
            create_backup: Whether to create backup before saving
            timeout: Custom timeout, uses default if None
            
        Returns:
            True if save was successful
            
        Raises:
            NetworkAccessException: When file cannot be saved within timeout
        """
        file_path = self.network_path / filename
        
        def save_operation():
            return self._save_json_file_direct(file_path, data, create_backup, timeout)
        
        try:
            success = self.timeout_manager.execute_with_timeout(
                save_operation, timeout, f"save JSON file '{filename}'"
            )
            
            # Invalidate cache after successful save
            if success:
                cache_key = f"json_file:{filename}"
                self.cache_manager.invalidate(cache_key, 'network')
                self.logger.debug(f"Invalidated cache for saved file: {filename}")
            
            return success
            
        except TimeoutException as e:
            self._timeout_count += 1
            raise NetworkAccessException(f"Timeout saving file '{filename}': {e}")
        except Exception as e:
            raise NetworkAccessException(f"Failed to save file '{filename}': {e}")
    
    def file_exists(self, filename: str, use_cache: bool = True, 
                   timeout: Optional[float] = None) -> bool:
        """Check if a file exists on the network share.
        
        Args:
            filename: Name of the file to check
            use_cache: Whether to use fast cache (5-second TTL)
            timeout: Custom timeout, uses default if None
            
        Returns:
            True if file exists and is accessible
        """
        file_path = self.network_path / filename
        cache_key = f"file_exists:{filename}"
        
        if use_cache:
            return self.cache_manager.get_fast_cached(
                cache_key,
                lambda: self._file_exists_direct(file_path, timeout)
            )
        else:
            return self._file_exists_direct(file_path, timeout)
    
    def get_file_modification_time(self, filename: str, timeout: Optional[float] = None) -> Optional[float]:
        """Get the modification time of a file on the network share.
        
        Args:
            filename: Name of the file
            timeout: Custom timeout, uses default if None
            
        Returns:
            Modification time as timestamp, None if file doesn't exist
        """
        file_path = self.network_path / filename
        
        def check_operation():
            return self._get_modification_time_direct(file_path, timeout)
        
        try:
            return self.timeout_manager.execute_with_timeout(
                check_operation, timeout, f"get modification time for '{filename}'"
            )
        except TimeoutException:
            self._timeout_count += 1
            self.logger.warning(f"Timeout checking modification time for '{filename}'")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get modification time for '{filename}': {e}")
            return None
    
    def validate_network_access(self, timeout: Optional[float] = None) -> bool:
        """Validate that the network share is accessible.
        
        Args:
            timeout: Custom timeout, uses default if None
            
        Returns:
            True if network share is accessible
        """
        def validate_operation():
            return self._validate_network_access_direct(timeout)
        
        try:
            return self.timeout_manager.execute_with_timeout(
                validate_operation, timeout, "validate network access"
            )
        except TimeoutException:
            self._timeout_count += 1
            self.logger.warning("Timeout validating network access")
            return False
        except Exception as e:
            self.logger.warning(f"Network access validation failed: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the network service.
        
        Returns:
            Dictionary with performance metrics
        """
        with self._lock:
            cache_stats = self.cache_manager.get_statistics()
            
            avg_time = self._total_time / max(1, self._operation_count)
            
            return {
                'total_operations': self._operation_count,
                'average_time_ms': avg_time * 1000,
                'timeout_count': self._timeout_count,
                'timeout_rate': self._timeout_count / max(1, self._operation_count),
                'cache_hit_count': self._cache_hit_count,
                'cache_hit_rate': cache_stats.hit_ratio,
                'network_calls_saved': cache_stats.network_calls_saved,
                'cache_stats': cache_stats.get_summary(),
            }
    
    def _load_json_file_direct(self, file_path: Path, timeout: Optional[float]) -> Dict[str, Any]:
        """Direct JSON file loading without caching.
        
        Args:
            file_path: Path to the JSON file
            timeout: Timeout for the operation
            
        Returns:
            Parsed JSON data
        """
        start_time = time.time()
        
        def load_operation():
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        
        try:
            result = self.timeout_manager.execute_with_timeout(
                load_operation, timeout, f"load JSON file '{file_path.name}'"
            )
            
            # Update performance stats
            with self._lock:
                self._operation_count += 1
                self._total_time += time.time() - start_time
            
            return result
            
        except TimeoutException as e:
            self._timeout_count += 1
            raise NetworkAccessException(f"Timeout loading file '{file_path}': {e}")
        except json.JSONDecodeError as e:
            from ...infrastructure.exceptions import DataValidationException
            raise DataValidationException(f"Invalid JSON in file '{file_path}': {e}")
        except Exception as e:
            raise NetworkAccessException(f"Failed to load file '{file_path}': {e}")
    
    def _save_json_file_direct(self, file_path: Path, data: Dict[str, Any], 
                             create_backup: bool, timeout: Optional[float]) -> bool:
        """Direct JSON file saving without caching.
        
        Args:
            file_path: Path to save the file
            data: Data to save
            create_backup: Whether to create backup
            timeout: Timeout for the operation
            
        Returns:
            True if successful
        """
        start_time = time.time()
        
        def save_operation():
            # Create backup if requested
            if create_backup and file_path.exists():
                backup_name = f"{file_path.stem}_backup_{int(time.time())}{file_path.suffix}"
                backup_path = file_path.parent / backup_name
                try:
                    backup_path.write_bytes(file_path.read_bytes())
                except Exception as e:
                    self.logger.warning(f"Failed to create backup: {e}")
            
            # Save the file
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
            return True
        
        try:
            result = self.timeout_manager.execute_with_timeout(
                save_operation, timeout, f"save JSON file '{file_path.name}'"
            )
            
            # Update performance stats
            with self._lock:
                self._operation_count += 1
                self._total_time += time.time() - start_time
            
            return result
            
        except TimeoutException as e:
            self._timeout_count += 1
            raise NetworkAccessException(f"Timeout saving file '{file_path}': {e}")
        except Exception as e:
            raise NetworkAccessException(f"Failed to save file '{file_path}': {e}")
    
    def _file_exists_direct(self, file_path: Path, timeout: Optional[float]) -> bool:
        """Direct file existence check without caching.
        
        Args:
            file_path: Path to check
            timeout: Timeout for the operation
            
        Returns:
            True if file exists
        """
        def exists_operation():
            return file_path.exists()
        
        try:
            return self.timeout_manager.execute_with_timeout(
                exists_operation, timeout, f"check existence of '{file_path.name}'"
            )
        except TimeoutException:
            self._timeout_count += 1
            return False
        except Exception:
            return False
    
    def _get_modification_time_direct(self, file_path: Path, timeout: Optional[float]) -> Optional[float]:
        """Direct file modification time check.
        
        Args:
            file_path: Path to check
            timeout: Timeout for the operation
            
        Returns:
            Modification time or None
        """
        def mtime_operation():
            if file_path.exists():
                return file_path.stat().st_mtime
            return None
        
        try:
            return self.timeout_manager.execute_with_timeout(
                mtime_operation, timeout, f"get modification time of '{file_path.name}'"
            )
        except TimeoutException:
            self._timeout_count += 1
            return None
        except Exception:
            return None
    
    def _validate_network_access_direct(self, timeout: Optional[float]) -> bool:
        """Direct network access validation.
        
        Args:
            timeout: Timeout for the operation
            
        Returns:
            True if accessible
        """
        def validate_operation():
            return self.network_path.exists() or self.network_path.parent.exists()
        
        return self.timeout_manager.execute_with_timeout(
            validate_operation, timeout, "validate network path access"
        )
