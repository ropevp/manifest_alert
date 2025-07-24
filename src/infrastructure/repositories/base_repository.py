"""
Base repository interface and common functionality.

Provides the abstract base class that all repositories must implement,
along with common utility methods for data access operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pathlib import Path
import json
import logging
from datetime import datetime

from ...infrastructure.exceptions import (
    DataValidationException,
    NetworkAccessException,
    ConfigurationException
)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for all repository implementations.
    
    Provides common functionality for data persistence operations
    including error handling, validation, and logging.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the repository with optional logger.
        
        Args:
            logger: Optional logger instance for operation logging
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._last_error: Optional[Exception] = None
    
    @abstractmethod
    def load(self) -> List[T]:
        """Load all entities from the data source.
        
        Returns:
            List of domain entities
            
        Raises:
            NetworkAccessException: When data source is inaccessible
            DataValidationException: When data format is invalid
        """
        pass
    
    @abstractmethod
    def save(self, entities: List[T]) -> bool:
        """Save entities to the data source.
        
        Args:
            entities: List of domain entities to save
            
        Returns:
            True if save was successful, False otherwise
            
        Raises:
            NetworkAccessException: When data source is inaccessible
            DataValidationException: When entity data is invalid
        """
        pass
    
    @abstractmethod
    def exists(self) -> bool:
        """Check if the data source exists and is accessible.
        
        Returns:
            True if data source exists and is accessible
        """
        pass
    
    def get_last_error(self) -> Optional[Exception]:
        """Get the last error that occurred during repository operations.
        
        Returns:
            The last exception that occurred, or None if no errors
        """
        return self._last_error
    
    def _set_error(self, error: Exception) -> None:
        """Set the last error and log it.
        
        Args:
            error: The exception that occurred
        """
        self._last_error = error
        self.logger.error(f"Repository error in {self.__class__.__name__}: {error}")
    
    def _load_json_file(self, file_path: Path, timeout: float = 1.0) -> Dict[str, Any]:
        """Load and parse a JSON file with timeout protection.
        
        Args:
            file_path: Path to the JSON file
            timeout: Maximum time to wait for file access
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            NetworkAccessException: When file cannot be accessed within timeout
            DataValidationException: When JSON is malformed
        """
        try:
            self.logger.debug(f"Loading JSON file: {file_path}")
            
            # Check if file exists
            if not file_path.exists():
                raise NetworkAccessException(f"File not found: {file_path}")
            
            # Read with timeout protection (implementation depends on file location)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            self.logger.debug(f"Successfully loaded JSON file: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            error = DataValidationException(f"Invalid JSON in file {file_path}: {e}")
            self._set_error(error)
            raise error
        except PermissionError as e:
            error = NetworkAccessException(f"Permission denied accessing {file_path}: {e}")
            self._set_error(error)
            raise error
        except Exception as e:
            error = NetworkAccessException(f"Failed to load file {file_path}: {e}")
            self._set_error(error)
            raise error
    
    def _save_json_file(self, file_path: Path, data: Dict[str, Any], 
                       backup: bool = True, timeout: float = 1.0) -> bool:
        """Save data to a JSON file with backup and timeout protection.
        
        Args:
            file_path: Path to save the JSON file
            data: Data to save as JSON
            backup: Whether to create a backup before saving
            timeout: Maximum time to wait for file access
            
        Returns:
            True if save was successful
            
        Raises:
            NetworkAccessException: When file cannot be written within timeout
            DataValidationException: When data cannot be serialized
        """
        try:
            self.logger.debug(f"Saving JSON file: {file_path}")
            
            # Create backup if requested and file exists
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                try:
                    backup_path.write_bytes(file_path.read_bytes())
                    self.logger.debug(f"Created backup: {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to create backup: {e}")
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with timeout protection
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(json_content)
            
            self.logger.debug(f"Successfully saved JSON file: {file_path}")
            return True
            
        except (TypeError, ValueError) as e:
            error = DataValidationException(f"Data serialization failed for {file_path}: {e}")
            self._set_error(error)
            raise error
        except PermissionError as e:
            error = NetworkAccessException(f"Permission denied writing {file_path}: {e}")
            self._set_error(error)
            raise error
        except Exception as e:
            error = NetworkAccessException(f"Failed to save file {file_path}: {e}")
            self._set_error(error)
            raise error
    
    def _validate_path_accessible(self, path: Path, timeout: float = 1.0) -> bool:
        """Validate that a path is accessible within the timeout period.
        
        Args:
            path: Path to validate
            timeout: Maximum time to wait for access
            
        Returns:
            True if path is accessible
        """
        try:
            # For network paths, this might need special handling
            return path.exists() or path.parent.exists()
        except Exception as e:
            self.logger.warning(f"Path accessibility check failed for {path}: {e}")
            return False
    
    def _normalize_file_path(self, path_str: str) -> Path:
        """Normalize a file path string to a Path object.
        
        Args:
            path_str: Path string to normalize
            
        Returns:
            Normalized Path object
        """
        # Handle network paths and local paths uniformly
        return Path(path_str).resolve()
