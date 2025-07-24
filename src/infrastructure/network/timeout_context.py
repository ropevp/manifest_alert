"""
Timeout context manager for network operations.

Provides timeout protection for network file operations to prevent
the application from hanging when network shares are slow or unavailable.
"""

import threading
import time
import signal
import os
from contextlib import contextmanager
from typing import Optional, Any, Generator
import logging


class TimeoutException(Exception):
    """Exception raised when an operation times out."""
    pass


@contextmanager
def timeout_context(timeout_seconds: float) -> Generator[None, None, None]:
    """Context manager that enforces a timeout on operations.
    
    This implementation works on Windows by using threading to interrupt
    long-running operations that might hang on network file access.
    
    Args:
        timeout_seconds: Maximum time to allow for the operation
        
    Raises:
        TimeoutException: If the operation exceeds the timeout
        
    Example:
        with timeout_context(1.0):
            # This operation will be interrupted if it takes > 1 second
            data = load_network_file()
    """
    if timeout_seconds <= 0:
        raise ValueError("Timeout must be positive")
    
    logger = logging.getLogger(__name__)
    
    # For Windows, we need to use threading-based timeout
    if os.name == 'nt':
        yield from _windows_timeout_context(timeout_seconds, logger)
    else:
        yield from _unix_timeout_context(timeout_seconds, logger)


def _windows_timeout_context(timeout_seconds: float, logger: logging.Logger) -> Generator[None, None, None]:
    """Windows-specific timeout implementation using threading.
    
    Args:
        timeout_seconds: Timeout in seconds
        logger: Logger for timeout events
    """
    timeout_occurred = threading.Event()
    
    def timeout_handler():
        """Handler that sets timeout flag after delay."""
        time.sleep(timeout_seconds)
        timeout_occurred.set()
    
    # Start timeout thread
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    try:
        yield
        
        # Check if timeout occurred during operation
        if timeout_occurred.is_set():
            raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds")
            
    except Exception as e:
        if timeout_occurred.is_set():
            logger.warning(f"Operation interrupted by timeout: {e}")
            raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds")
        raise


def _unix_timeout_context(timeout_seconds: float, logger: logging.Logger) -> Generator[None, None, None]:
    """Unix-specific timeout implementation using signals.
    
    Args:
        timeout_seconds: Timeout in seconds
        logger: Logger for timeout events
    """
    def timeout_handler(signum, frame):
        """Signal handler for timeout."""
        raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds")
    
    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout_seconds))
    
    try:
        yield
    finally:
        # Clean up signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class NetworkTimeoutManager:
    """Manager for handling network operation timeouts.
    
    Provides additional utilities for managing timeouts across
    multiple network operations with consistent behavior.
    """
    
    DEFAULT_TIMEOUT = 1.0  # 1 second default timeout
    
    def __init__(self, default_timeout: float = DEFAULT_TIMEOUT):
        """Initialize timeout manager.
        
        Args:
            default_timeout: Default timeout for operations
        """
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute_with_timeout(self, operation, timeout: Optional[float] = None, 
                           operation_name: str = "network operation") -> Any:
        """Execute an operation with timeout protection.
        
        Args:
            operation: Callable to execute
            timeout: Timeout in seconds, uses default if None
            operation_name: Description of operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            TimeoutException: If operation times out
        """
        effective_timeout = timeout or self.default_timeout
        
        self.logger.debug(f"Executing {operation_name} with {effective_timeout}s timeout")
        
        start_time = time.time()
        try:
            with timeout_context(effective_timeout):
                result = operation()
            
            duration = time.time() - start_time
            self.logger.debug(f"{operation_name} completed in {duration:.3f}s")
            return result
            
        except TimeoutException:
            duration = time.time() - start_time
            self.logger.warning(f"{operation_name} timed out after {duration:.3f}s")
            raise
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
            raise
