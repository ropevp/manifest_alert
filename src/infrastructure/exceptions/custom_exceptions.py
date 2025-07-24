"""
Custom Exception Classes for Manifest Alert System

This module defines the exception hierarchy for the manifest alert system,
providing specific error types for different failure scenarios.
"""

from typing import Optional


class ManifestAlertException(Exception):
    """Base exception for all manifest alert system errors.
    
    This is the root exception class from which all other manifest alert
    exceptions inherit. It provides a consistent interface for error handling
    throughout the system.
    """
    
    def __init__(self, message: str, details: Optional[str] = None):
        """Initialize the exception.
        
        Args:
            message: The main error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return a string representation of the exception."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class NetworkAccessException(ManifestAlertException):
    """Raised when network file operations fail.
    
    This exception is used when the system cannot access network resources
    such as the centralized mute status file or shared configuration files.
    """
    
    def __init__(self, message: str, path: Optional[str] = None, operation: Optional[str] = None):
        """Initialize the network access exception.
        
        Args:
            message: The main error message
            path: The network path that failed
            operation: The operation that was being attempted
        """
        self.path = path
        self.operation = operation
        details = []
        if path:
            details.append(f"Path: {path}")
        if operation:
            details.append(f"Operation: {operation}")
        super().__init__(message, " | ".join(details) if details else None)


class DataValidationException(ManifestAlertException):
    """Raised when data validation fails.
    
    This exception is used when input data does not meet the required
    validation criteria, such as invalid time formats, missing required
    fields, or invalid data types.
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        """Initialize the data validation exception.
        
        Args:
            message: The main error message
            field: The field that failed validation
            value: The invalid value that was provided
        """
        self.field = field
        self.value = value
        details = []
        if field:
            details.append(f"Field: {field}")
        if value:
            details.append(f"Value: {value}")
        super().__init__(message, " | ".join(details) if details else None)


class ConfigurationException(ManifestAlertException):
    """Raised when configuration is invalid or missing.
    
    This exception is used when the system configuration is corrupted,
    missing required settings, or contains invalid configuration values.
    """
    
    def __init__(self, message: str, config_file: Optional[str] = None, setting: Optional[str] = None):
        """Initialize the configuration exception.
        
        Args:
            message: The main error message
            config_file: The configuration file that is problematic
            setting: The specific setting that is invalid
        """
        self.config_file = config_file
        self.setting = setting
        details = []
        if config_file:
            details.append(f"Config file: {config_file}")
        if setting:
            details.append(f"Setting: {setting}")
        super().__init__(message, " | ".join(details) if details else None)


class BusinessLogicException(ManifestAlertException):
    """Raised when business logic operations fail.
    
    This exception is used when business operations fail due to invalid
    states, constraint violations, or other business rule violations.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, context: Optional[str] = None):
        """Initialize the business logic exception.
        
        Args:
            message: The main error message
            operation: The business operation that failed
            context: Additional context about the failure
        """
        self.operation = operation
        self.context = context
        details = []
        if operation:
            details.append(f"Operation: {operation}")
        if context:
            details.append(f"Context: {context}")
        super().__init__(message, " | ".join(details) if details else None)