"""
Custom exception hierarchy for the Manifest Alert System.

This module defines a comprehensive exception hierarchy that covers all
error conditions in the manifest alert system, from network failures to
data validation errors.
"""

from typing import Optional, Any


class ManifestAlertException(Exception):
    """
    Base exception for all manifest alert system errors.
    
    All custom exceptions in the system should inherit from this base class
    to provide consistent error handling and logging capabilities.
    """
    
    def __init__(self, message: str, details: Optional[dict] = None, cause: Optional[Exception] = None):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """Return a detailed string representation of the exception."""
        result = self.message
        if self.details:
            result += f" (Details: {self.details})"
        if self.cause:
            result += f" (Caused by: {self.cause})"
        return result


class NetworkAccessException(ManifestAlertException):
    """
    Raised when network file operations fail.
    
    This exception is used for failures in accessing shared network folders,
    timeouts, permission errors, or connectivity issues.
    """
    
    def __init__(self, message: str, network_path: Optional[str] = None, 
                 timeout: Optional[float] = None, cause: Optional[Exception] = None):
        """
        Initialize the network access exception.
        
        Args:
            message: Error message
            network_path: The network path that failed to access
            timeout: Timeout value if operation timed out
            cause: Underlying exception
        """
        details = {}
        if network_path:
            details['network_path'] = network_path
        if timeout:
            details['timeout'] = timeout
        
        super().__init__(message, details, cause)
        self.network_path = network_path
        self.timeout = timeout


class DataValidationException(ManifestAlertException):
    """
    Raised when data validation fails.
    
    This exception is used when input data doesn't meet validation criteria,
    such as invalid time formats, missing required fields, or invalid values.
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 invalid_value: Optional[Any] = None, cause: Optional[Exception] = None):
        """
        Initialize the data validation exception.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            invalid_value: The invalid value that caused the error
            cause: Underlying exception
        """
        details = {}
        if field_name:
            details['field_name'] = field_name
        if invalid_value is not None:
            details['invalid_value'] = invalid_value
        
        super().__init__(message, details, cause)
        self.field_name = field_name
        self.invalid_value = invalid_value


class ConfigurationException(ManifestAlertException):
    """
    Raised when configuration is invalid or missing.
    
    This exception is used for missing configuration files, invalid
    configuration data, or corrupted settings.
    """
    
    def __init__(self, message: str, config_path: Optional[str] = None, 
                 config_key: Optional[str] = None, cause: Optional[Exception] = None):
        """
        Initialize the configuration exception.
        
        Args:
            message: Error message
            config_path: Path to the configuration file
            config_key: Specific configuration key that failed
            cause: Underlying exception
        """
        details = {}
        if config_path:
            details['config_path'] = config_path
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(message, details, cause)
        self.config_path = config_path
        self.config_key = config_key


class FileOperationException(ManifestAlertException):
    """
    Raised when file operations fail.
    
    This exception is used for file system errors, permission issues,
    or corruption in local files.
    """
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 operation: Optional[str] = None, cause: Optional[Exception] = None):
        """
        Initialize the file operation exception.
        
        Args:
            message: Error message
            file_path: Path to the file that failed
            operation: The operation that failed (read, write, delete, etc.)
            cause: Underlying exception
        """
        details = {}
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        
        super().__init__(message, details, cause)
        self.file_path = file_path
        self.operation = operation


class AudioException(ManifestAlertException):
    """
    Raised when audio operations fail.
    
    This exception is used for audio playback failures, missing audio files,
    or audio system initialization errors.
    """
    
    def __init__(self, message: str, audio_file: Optional[str] = None, 
                 cause: Optional[Exception] = None):
        """
        Initialize the audio exception.
        
        Args:
            message: Error message
            audio_file: Path to the audio file that failed
            cause: Underlying exception
        """
        details = {}
        if audio_file:
            details['audio_file'] = audio_file
        
        super().__init__(message, details, cause)
        self.audio_file = audio_file


class BusinessLogicException(ManifestAlertException):
    """
    Raised when business logic constraints are violated.
    
    This exception is used when operations violate business rules,
    such as attempting to acknowledge an already acknowledged manifest.
    """
    
    def __init__(self, message: str, entity_type: Optional[str] = None, 
                 entity_id: Optional[str] = None, cause: Optional[Exception] = None):
        """
        Initialize the business logic exception.
        
        Args:
            message: Error message
            entity_type: Type of entity involved (manifest, carrier, etc.)
            entity_id: ID of the specific entity
            cause: Underlying exception
        """
        details = {}
        if entity_type:
            details['entity_type'] = entity_type
        if entity_id:
            details['entity_id'] = entity_id
        
        super().__init__(message, details, cause)
        self.entity_type = entity_type
        self.entity_id = entity_id