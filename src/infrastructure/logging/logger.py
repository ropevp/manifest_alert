"""
Logging framework for the Manifest Alert System.

This module provides a comprehensive logging framework with file and console
handlers, performance monitoring, and structured logging capabilities.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ManifestLogger:
    """
    Centralized logging framework for the Manifest Alert System.
    
    Provides structured logging with file rotation, console output,
    and performance monitoring capabilities.
    """
    
    _instances: Dict[str, 'ManifestLogger'] = {}
    
    def __init__(self, name: str, log_level: str = "INFO", log_dir: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            name: Logger name (typically module or component name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (defaults to current directory)
        """
        self.name = name
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir) if log_dir else Path.cwd()
        
        # Create the logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    @classmethod
    def get_logger(cls, name: str, log_level: str = "INFO", log_dir: Optional[str] = None) -> 'ManifestLogger':
        """
        Get or create a logger instance (singleton pattern per name).
        
        Args:
            name: Logger name
            log_level: Logging level
            log_dir: Directory for log files
            
        Returns:
            ManifestLogger instance
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, log_level, log_dir)
        return cls._instances[name]
    
    def _setup_handlers(self):
        """Setup file and console handlers for the logger."""
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        log_file = self.log_dir / "manifest_alerts.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))
        
        # Formatter with timestamp, level, name, and message
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context."""
        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {context_str}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def log_network_operation(self, operation: str, path: str, success: bool, 
                            duration: float, error: Optional[Exception] = None):
        """
        Log network operations with performance metrics.
        
        Args:
            operation: Type of operation (read, write, check, etc.)
            path: Network path accessed
            success: Whether operation succeeded
            duration: Operation duration in seconds
            error: Exception if operation failed
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Network operation {operation} on {path}: {status} in {duration:.3f}s"
        
        context = {
            'operation': operation,
            'path': path,
            'duration': duration,
            'success': success
        }
        
        if error:
            context['error'] = str(error)
            self.error(message, **context)
        elif duration > 1.0:  # Log slow operations as warnings
            self.warning(f"{message} (SLOW)", **context)
        else:
            self.info(message, **context)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """
        Log performance metrics.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
        """
        self.info(f"Performance metric: {metric_name}={value}{unit}")
    
    def log_user_action(self, user: str, action: str, target: str, success: bool = True):
        """
        Log user actions for audit trail.
        
        Args:
            user: Username or identifier
            action: Action performed (acknowledge, mute, etc.)
            target: Target of the action (manifest, carrier, etc.)
            success: Whether action succeeded
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"User action: {user} {action} {target}: {status}"
        
        context = {
            'user': user,
            'action': action,
            'target': target,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.info(message, **context)
        else:
            self.warning(message, **context)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log system events (startup, shutdown, configuration changes, etc.).
        
        Args:
            event_type: Type of system event
            details: Additional event details
        """
        message = f"System event: {event_type}"
        self.info(message, **details)
    
    def log_data_operation(self, operation: str, entity_type: str, entity_id: str, 
                          success: bool, error: Optional[Exception] = None):
        """
        Log data operations (create, read, update, delete).
        
        Args:
            operation: Type of operation (create, read, update, delete)
            entity_type: Type of entity (manifest, carrier, acknowledgment, etc.)
            entity_id: Identifier of the entity
            success: Whether operation succeeded
            error: Exception if operation failed
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Data operation {operation} on {entity_type}[{entity_id}]: {status}"
        
        context = {
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'success': success
        }
        
        if error:
            context['error'] = str(error)
            self.error(message, **context)
        else:
            self.debug(message, **context)


# Global logger instances for common components
def get_domain_logger() -> ManifestLogger:
    """Get logger for domain layer."""
    return ManifestLogger.get_logger("domain")


def get_infrastructure_logger() -> ManifestLogger:
    """Get logger for infrastructure layer."""
    return ManifestLogger.get_logger("infrastructure")


def get_application_logger() -> ManifestLogger:
    """Get logger for application layer."""
    return ManifestLogger.get_logger("application")


def get_presentation_logger() -> ManifestLogger:
    """Get logger for presentation layer."""
    return ManifestLogger.get_logger("presentation")


# Convenience function for getting any logger
def get_logger(name: str, log_level: str = "INFO", log_dir: Optional[str] = None) -> ManifestLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        log_level: Logging level
        log_dir: Directory for log files
        
    Returns:
        ManifestLogger instance
    """
    return ManifestLogger.get_logger(name, log_level, log_dir)