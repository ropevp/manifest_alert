"""
Mute Service

Business logic service for managing centralized mute/snooze functionality
with cross-PC synchronization and performance optimization.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

from ..domain.models import MuteStatus, MuteType
from ..infrastructure.repositories import MuteRepository
from ..infrastructure.exceptions import NetworkAccessException, MuteOperationException


class MuteReason(Enum):
    """Common reasons for muting alerts."""
    MANUAL = "manual"
    SCHEDULED_BREAK = "scheduled_break"
    SYSTEM_MAINTENANCE = "system_maintenance"
    CARRIER_ISSUE = "carrier_issue"
    TEMPORARY_ABSENCE = "temporary_absence"
    OTHER = "other"


@dataclass
class MuteOperationResult:
    """Result of a mute operation."""
    success: bool
    previous_status: Optional[MuteStatus]
    new_status: Optional[MuteStatus]
    error_message: Optional[str] = None
    operation_time_ms: Optional[float] = None


@dataclass
class MuteStatistics:
    """Statistics about mute operations."""
    total_mute_operations: int = 0
    total_snooze_operations: int = 0
    total_unmute_operations: int = 0
    average_mute_duration_minutes: float = 0.0
    most_common_reason: Optional[str] = None
    cache_hit_rate: float = 0.0
    network_timeout_count: int = 0


class MuteService:
    """Service for managing centralized mute/snooze functionality.
    
    This service provides business logic for mute operations including:
    - High-performance mute/unmute/snooze with aggressive caching
    - Cross-PC synchronization via network share
    - Thread-safe operations with timeout protection
    - Mute status monitoring and statistics
    - Automatic snooze expiration handling
    - Integration with alert and UI services
    """
    
    def __init__(self, mute_repository: MuteRepository):
        """Initialize mute service.
        
        Args:
            mute_repository: Repository for mute status persistence
        """
        self.mute_repository = mute_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread safety
        self._operation_lock = threading.Lock()
        
        # Statistics tracking
        self._statistics = MuteStatistics()
        
        # Cache for last known status to improve UI responsiveness
        self._last_known_status: Optional[MuteStatus] = None
        self._last_status_check: Optional[datetime] = None
        
        self.logger.info("MuteService initialized with high-performance caching")
    
    def get_mute_status(self, use_cache: bool = True) -> MuteStatus:
        """Get current mute status with aggressive caching.
        
        Args:
            use_cache: Whether to use cached status for performance
            
        Returns:
            Current mute status
            
        Raises:
            MuteOperationException: If status cannot be retrieved
        """
        try:
            current_time = datetime.now()
            
            # Use cached status if available and recent (for UI responsiveness)
            if (use_cache and self._last_known_status is not None and 
                self._last_status_check is not None):
                
                cache_age = (current_time - self._last_status_check).total_seconds()
                if cache_age < 5.0:  # 5-second cache for UI responsiveness
                    return self._last_known_status
            
            # Load from repository (which has its own 30s network cache)
            status = self.mute_repository.load_mute_status()
            
            # Update local cache
            self._last_known_status = status
            self._last_status_check = current_time
            
            return status
            
        except Exception as e:
            error_msg = f"Failed to get mute status: {e}"
            self.logger.error(error_msg)
            
            # Return cached status as fallback
            if self._last_known_status is not None:
                self.logger.warning("Using cached mute status due to error")
                return self._last_known_status
            
            # Final fallback to unmuted
            from ..domain.models import MuteStatus
            return MuteStatus.create_unmuted()
    
    def toggle_mute(self, duration_minutes: Optional[int] = None, 
                   user: Optional[str] = None, reason: Optional[str] = None) -> MuteOperationResult:
        """Toggle mute status with thread safety and performance optimization.
        
        Args:
            duration_minutes: Duration for snooze if toggling to muted
            user: User performing the operation
            reason: Reason for the mute operation
            
        Returns:
            Result of the toggle operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                # Get current status
                current_status = self.get_mute_status(use_cache=False)  # Force fresh load
                previous_status = current_status
                
                # Perform toggle operation
                new_status = self.mute_repository.toggle_mute(duration_minutes)
                
                # Update local cache immediately
                self._last_known_status = new_status
                self._last_status_check = datetime.now()
                
                # Update statistics
                if new_status.is_currently_muted():
                    self._statistics.total_mute_operations += 1
                    if new_status.mute_type == MuteType.SNOOZE:
                        self._statistics.total_snooze_operations += 1
                else:
                    self._statistics.total_unmute_operations += 1
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                result = MuteOperationResult(
                    success=True,
                    previous_status=previous_status,
                    new_status=new_status,
                    operation_time_ms=operation_time
                )
                
                self.logger.info(f"Mute toggled: {'muted' if new_status.is_currently_muted() else 'unmuted'} "
                               f"in {operation_time:.1f}ms")
                
                return result
                
            except Exception as e:
                error_msg = f"Failed to toggle mute: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return MuteOperationResult(
                    success=False,
                    previous_status=None,
                    new_status=None,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def mute_alerts(self, duration_minutes: Optional[int] = None, 
                   user: Optional[str] = None, reason: Optional[str] = None) -> MuteOperationResult:
        """Mute alerts for a specific duration or indefinitely.
        
        Args:
            duration_minutes: Duration in minutes (None for indefinite)
            user: User performing the operation
            reason: Reason for muting
            
        Returns:
            Result of the mute operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                current_status = self.get_mute_status(use_cache=False)
                
                # Create new muted status
                new_status = MuteStatus.create_muted(duration_minutes, user, reason)
                
                # Save to repository
                success = self.mute_repository.save_mute_status(new_status)
                
                if success:
                    # Update local cache
                    self._last_known_status = new_status
                    self._last_status_check = datetime.now()
                    
                    # Update statistics
                    self._statistics.total_mute_operations += 1
                    if duration_minutes is not None:
                        self._statistics.total_snooze_operations += 1
                    
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"Alerts muted for {duration_minutes or 'indefinite'} minutes")
                    
                    return MuteOperationResult(
                        success=True,
                        previous_status=current_status,
                        new_status=new_status,
                        operation_time_ms=operation_time
                    )
                else:
                    raise MuteOperationException("Failed to save mute status")
                    
            except Exception as e:
                error_msg = f"Failed to mute alerts: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return MuteOperationResult(
                    success=False,
                    previous_status=None,
                    new_status=None,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def snooze_alerts(self, duration_minutes: int = 30, 
                     user: Optional[str] = None, reason: Optional[str] = None) -> MuteOperationResult:
        """Snooze alerts for a specific duration.
        
        Args:
            duration_minutes: Snooze duration in minutes
            user: User performing the operation
            reason: Reason for snoozing
            
        Returns:
            Result of the snooze operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                current_status = self.get_mute_status(use_cache=False)
                
                # Use repository snooze method
                new_status = self.mute_repository.snooze(duration_minutes)
                
                # Update local cache
                self._last_known_status = new_status
                self._last_status_check = datetime.now()
                
                # Update statistics
                self._statistics.total_snooze_operations += 1
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self.logger.info(f"Alerts snoozed for {duration_minutes} minutes")
                
                return MuteOperationResult(
                    success=True,
                    previous_status=current_status,
                    new_status=new_status,
                    operation_time_ms=operation_time
                )
                
            except Exception as e:
                error_msg = f"Failed to snooze alerts: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return MuteOperationResult(
                    success=False,
                    previous_status=None,
                    new_status=None,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def unmute_alerts(self, user: Optional[str] = None) -> MuteOperationResult:
        """Unmute all alerts.
        
        Args:
            user: User performing the operation
            
        Returns:
            Result of the unmute operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                current_status = self.get_mute_status(use_cache=False)
                
                # Use repository unmute method
                new_status = self.mute_repository.unmute()
                
                # Update local cache
                self._last_known_status = new_status
                self._last_status_check = datetime.now()
                
                # Update statistics
                self._statistics.total_unmute_operations += 1
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self.logger.info("Alerts unmuted")
                
                return MuteOperationResult(
                    success=True,
                    previous_status=current_status,
                    new_status=new_status,
                    operation_time_ms=operation_time
                )
                
            except Exception as e:
                error_msg = f"Failed to unmute alerts: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return MuteOperationResult(
                    success=False,
                    previous_status=None,
                    new_status=None,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def extend_snooze(self, additional_minutes: int, 
                     user: Optional[str] = None) -> MuteOperationResult:
        """Extend current snooze duration.
        
        Args:
            additional_minutes: Additional minutes to add
            user: User performing the operation
            
        Returns:
            Result of the extend operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                current_status = self.get_mute_status(use_cache=False)
                
                if not current_status.is_currently_muted():
                    raise MuteOperationException("Cannot extend snooze when not muted")
                
                if current_status.mute_type != MuteType.SNOOZE:
                    raise MuteOperationException("Cannot extend non-snooze mute")
                
                # Extend the snooze
                current_status.extend_snooze(additional_minutes, user)
                
                # Save updated status
                success = self.mute_repository.save_mute_status(current_status)
                
                if success:
                    # Update local cache
                    self._last_known_status = current_status
                    self._last_status_check = datetime.now()
                    
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"Snooze extended by {additional_minutes} minutes")
                    
                    return MuteOperationResult(
                        success=True,
                        previous_status=current_status,
                        new_status=current_status,
                        operation_time_ms=operation_time
                    )
                else:
                    raise MuteOperationException("Failed to save extended snooze")
                    
            except Exception as e:
                error_msg = f"Failed to extend snooze: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return MuteOperationResult(
                    success=False,
                    previous_status=None,
                    new_status=None,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def is_muted(self, use_cache: bool = True) -> bool:
        """Check if alerts are currently muted.
        
        Args:
            use_cache: Whether to use cached status
            
        Returns:
            True if alerts are muted
        """
        try:
            status = self.get_mute_status(use_cache)
            return status.is_currently_muted()
        except Exception as e:
            self.logger.warning(f"Mute status check failed: {e}")
            return False
    
    def get_remaining_time(self, use_cache: bool = True) -> Optional[timedelta]:
        """Get remaining time for current mute/snooze.
        
        Args:
            use_cache: Whether to use cached status
            
        Returns:
            Remaining time as timedelta, or None if not muted or indefinite
        """
        try:
            status = self.get_mute_status(use_cache)
            return status.get_remaining_time()
        except Exception as e:
            self.logger.warning(f"Remaining time check failed: {e}")
            return None
    
    def get_remaining_minutes(self, use_cache: bool = True) -> Optional[int]:
        """Get remaining time in minutes.
        
        Args:
            use_cache: Whether to use cached status
            
        Returns:
            Remaining minutes, or None if not muted or indefinite
        """
        try:
            status = self.get_mute_status(use_cache)
            return status.get_remaining_minutes()
        except Exception as e:
            self.logger.warning(f"Remaining minutes check failed: {e}")
            return None
    
    def get_mute_summary(self, use_cache: bool = True) -> str:
        """Get human-readable mute status summary.
        
        Args:
            use_cache: Whether to use cached status
            
        Returns:
            Human-readable mute status
        """
        try:
            status = self.get_mute_status(use_cache)
            return status.get_mute_summary()
        except Exception as e:
            self.logger.warning(f"Mute summary failed: {e}")
            return "Status unknown"
    
    def get_mute_statistics(self) -> MuteStatistics:
        """Get mute operation statistics.
        
        Returns:
            Statistics about mute operations
        """
        # Update cache hit rate from repository
        try:
            repo_stats = self.mute_repository.get_performance_stats()
            self._statistics.cache_hit_rate = repo_stats.get("cache_hit_rate", 0.0)
            self._statistics.network_timeout_count = repo_stats.get("timeout_count", 0)
        except Exception as e:
            self.logger.debug(f"Could not get repository stats: {e}")
        
        return self._statistics
    
    def clear_statistics(self) -> None:
        """Clear mute operation statistics."""
        self._statistics = MuteStatistics()
        self.logger.info("Mute statistics cleared")
    
    def validate_network_connectivity(self) -> bool:
        """Validate network connectivity to mute status storage.
        
        Returns:
            True if network is accessible
        """
        try:
            # Try to load mute status without cache to test network
            self.mute_repository.load_mute_status()
            return True
        except NetworkAccessException:
            return False
        except Exception as e:
            self.logger.warning(f"Network validation failed: {e}")
            return False
    
    def force_cache_refresh(self) -> bool:
        """Force refresh of all mute status caches.
        
        Returns:
            True if refresh was successful
        """
        try:
            # Clear local cache
            self._last_known_status = None
            self._last_status_check = None
            
            # Force fresh load from repository
            status = self.get_mute_status(use_cache=False)
            
            self.logger.info("Mute status cache refreshed")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache refresh failed: {e}")
            return False
    
    def get_mute_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent mute status changes.
        
        Args:
            limit: Maximum number of history entries
            
        Returns:
            List of mute status history entries
        """
        try:
            return self.mute_repository.get_mute_history(limit)
        except Exception as e:
            self.logger.warning(f"Failed to get mute history: {e}")
            return []
    
    def schedule_snooze_check(self) -> None:
        """Schedule automatic snooze expiration check.
        
        This method can be called periodically to check for expired snoozes
        and automatically unmute when the snooze period ends.
        """
        try:
            status = self.get_mute_status(use_cache=False)
            
            if (status.is_currently_muted() and 
                status.mute_type == MuteType.SNOOZE):
                
                remaining = status.get_remaining_time()
                if remaining is None or remaining.total_seconds() <= 0:
                    # Snooze has expired, automatically unmute
                    self.unmute_alerts(user="system")
                    self.logger.info("Snooze automatically expired and unmuted")
                    
        except Exception as e:
            self.logger.debug(f"Snooze check failed: {e}")
    
    def async_toggle_mute(self, duration_minutes: Optional[int] = None,
                         user: Optional[str] = None, 
                         callback: Optional[callable] = None) -> None:
        """Perform mute toggle asynchronously for UI responsiveness.
        
        Args:
            duration_minutes: Duration for snooze if toggling to muted
            user: User performing the operation
            callback: Optional callback function for result
        """
        def async_operation():
            try:
                result = self.toggle_mute(duration_minutes, user)
                if callback:
                    callback(result)
            except Exception as e:
                self.logger.error(f"Async mute toggle failed: {e}")
                if callback:
                    callback(MuteOperationResult(
                        success=False,
                        previous_status=None,
                        new_status=None,
                        error_message=str(e)
                    ))
        
        thread = threading.Thread(target=async_operation, daemon=True)
        thread.start()
