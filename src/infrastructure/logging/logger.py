"""
Logging Framework for Manifest Alert System

This module provides a centralized logging framework with file and console handlers,
performance logging for network operations, and structured logging with appropriate levels.
"""

import logging
import logging.handlers
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict


class ManifestLogger:
    """Centralized logging framework for the manifest alert system.
    
    Provides structured logging with file and console handlers, performance
    tracking for network operations, and proper log rotation.
    """
    
    def __init__(self, name: str, log_level: str = "INFO", log_dir: Optional[str] = None):
        """Initialize the logger.
        
        Args:
            name: Logger name (typically module name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (defaults to current directory)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.log_dir = Path(log_dir) if log_dir else Path.cwd()
        self.setup_logging(log_level)
    
    def setup_logging(self, log_level: str) -> None:
        """Configure file and console handlers.
        
        Args:
            log_level: The minimum logging level to capture
        """
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set the logger level
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        try:
            self.log_dir.mkdir(exist_ok=True)
            log_file = self.log_dir / "manifest_alerts.log"
            
            # Use RotatingFileHandler to prevent log files from growing too large
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        except (OSError, PermissionError) as e:
            # If file logging fails, log to console only
            self.logger.warning(f"Could not set up file logging: {e}")
    
    def log_network_operation(self, operation: str, path: str, success: bool, 
                             duration: float, details: Optional[Dict[str, Any]] = None) -> None:
        """Log network operations with performance metrics.
        
        Args:
            operation: The network operation performed (e.g., 'read_mute_status')
            path: The network path accessed
            success: Whether the operation succeeded
            duration: Operation duration in seconds
            details: Optional additional details about the operation
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Network operation {operation} on {path}: {status} (Duration: {duration:.3f}s)"
        
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" - {detail_str}"
        
        # Log based on performance and success
        if not success:
            self.logger.error(message)
        elif duration > 1.0:
            self.logger.warning(f"SLOW: {message}")
        elif duration > 0.5:
            self.logger.info(f"MODERATE: {message}")
        else:
            self.logger.debug(message)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message: The error message
            exception: Optional exception object for stack trace
        """
        if exception:
            self.logger.error(message, exc_info=exception, **kwargs)
        else:
            self.logger.error(message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message: The critical message
            exception: Optional exception object for stack trace
        """
        if exception:
            self.logger.critical(message, exc_info=exception, **kwargs)
        else:
            self.logger.critical(message, **kwargs)


# Global logger registry to ensure single instance per name
_logger_registry: Dict[str, ManifestLogger] = {}


def get_logger(name: str, log_level: str = "INFO", log_dir: Optional[str] = None) -> ManifestLogger:
    """Get or create a logger instance.
    
    This function ensures that only one logger instance exists per name,
    following the singleton pattern for loggers.
    
    Args:
        name: Logger name (typically module name)
        log_level: Logging level (only used for new loggers)
        log_dir: Directory for log files (only used for new loggers)
    
    Returns:
        ManifestLogger instance
    """
    if name not in _logger_registry:
        _logger_registry[name] = ManifestLogger(name, log_level, log_dir)
    return _logger_registry[name]


class PerformanceTimer:
    """Context manager for timing operations and automatic logging.
    
    Usage:
        logger = get_logger(__name__)
        with PerformanceTimer(logger, "network_read", "/path/to/file"):
            # perform operation
            result = network_operation()
    """
    
    def __init__(self, logger: ManifestLogger, operation: str, path: str, 
                 auto_log: bool = True, details: Optional[Dict[str, Any]] = None):
        """Initialize the performance timer.
        
        Args:
            logger: Logger instance to use
            operation: Name of the operation being timed
            path: Path or identifier of the resource
            auto_log: Whether to automatically log the result
            details: Optional additional details for logging
        """
        self.logger = logger
        self.operation = operation
        self.path = path
        self.auto_log = auto_log
        self.details = details or {}
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.success = False
    
    def __enter__(self) -> 'PerformanceTimer':
        """Start timing the operation."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End timing and optionally log the result."""
        if self.start_time is not None:
            self.duration = time.time() - self.start_time
            self.success = exc_type is None
            
            if self.auto_log:
                self.logger.log_network_operation(
                    self.operation, 
                    self.path, 
                    self.success, 
                    self.duration,
                    self.details
                )