"""
Mute Service - Business logic for mute system operations.

Handles global mute status, per-manifest muting, and coordination
with the centralized mute system across multiple PCs.
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

from ...domain.models.mute_status import MuteStatus
from ...infrastructure.repositories.mute_repository import MuteRepository
from ...infrastructure.exceptions import BusinessLogicException


class MuteService:
    """Service for managing mute system business logic.
    
    This service handles:
    - Global mute status management
    - Temporary mute operations
    - Centralized mute synchronization across PCs
    - Mute status validation and expiration
    """
    
    def __init__(self,
                 mute_repository: MuteRepository,
                 logger: Optional[logging.Logger] = None):
        """Initialize the mute service.
        
        Args:
            mute_repository: Repository for mute status data
            logger: Optional logger instance
        """
        self.mute_repository = mute_repository
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache for performance
        self._cached_status: Optional[MuteStatus] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 5  # 5 second cache TTL for mute status
        
        self.logger.info("MuteService initialized")
    
    def is_muted(self, force_refresh: bool = False) -> bool:
        """Check if the system is currently muted.
        
        Args:
            force_refresh: Force reload from repository (bypass cache)
            
        Returns:
            True if system is muted
        """
        try:
            status = self.get_current_status(force_refresh)
            return status.is_muted if status else False
            
        except Exception as e:
            self.logger.error(f"Error checking mute status: {e}")
            # Default to not muted on error for safety
            return False
    
    def get_current_status(self, force_refresh: bool = False) -> Optional[MuteStatus]:
        """Get the current mute status.
        
        Args:
            force_refresh: Force reload from repository (bypass cache)
            
        Returns:
            MuteStatus object or None if not available
        """
        try:
            # Check cache first (unless force refresh)
            if not force_refresh and self._is_cache_valid():
                self.logger.debug("Returning cached mute status")
                return self._cached_status
            
            # Load from repository
            status = self.mute_repository.get_current_status()
            
            # Update cache
            self._cached_status = status
            self._cache_timestamp = datetime.now()
            
            if status:
                self.logger.debug(f"Mute status: {status.is_muted}, expires: {status.mute_until}")
            else:
                self.logger.debug("No mute status found")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting current mute status: {e}")
            return None
    
    def mute_system(self, duration_minutes: Optional[int] = None, 
                   user: Optional[str] = None, reason: Optional[str] = None) -> bool:
        """Mute the system globally.
        
        Args:
            duration_minutes: Optional duration in minutes (None for indefinite)
            user: Optional user who initiated the mute
            reason: Optional reason for muting
            
        Returns:
            True if mute was successful
        """
        try:
            current_time = datetime.now()
            mute_until = None
            
            if duration_minutes:
                mute_until = current_time + timedelta(minutes=duration_minutes)
            
            # Create mute status
            mute_status = MuteStatus(
                is_muted=True,
                mute_timestamp=current_time,
                mute_until=mute_until,
                muted_by=user,
                reason=reason
            )
            
            # Save to repository
            if not self.mute_repository.save_status(mute_status):
                raise BusinessLogicException("Failed to save mute status")
            
            # Invalidate cache
            self._invalidate_cache()
            
            duration_str = f"{duration_minutes} minutes" if duration_minutes else "indefinitely"
            self.logger.info(f"System muted {duration_str} by {user or 'unknown'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error muting system: {e}")
            return False
    
    def unmute_system(self, user: Optional[str] = None) -> bool:
        """Unmute the system globally.
        
        Args:
            user: Optional user who initiated the unmute
            
        Returns:
            True if unmute was successful
        """
        try:
            current_time = datetime.now()
            
            # Create unmuted status
            mute_status = MuteStatus(
                is_muted=False,
                mute_timestamp=current_time,
                mute_until=None,
                muted_by=user,
                reason="Manual unmute"
            )
            
            # Save to repository
            if not self.mute_repository.save_status(mute_status):
                raise BusinessLogicException("Failed to save unmute status")
            
            # Invalidate cache
            self._invalidate_cache()
            
            self.logger.info(f"System unmuted by {user or 'unknown'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unmuting system: {e}")
            return False
    
    def mute_temporarily(self, minutes: int, user: Optional[str] = None, 
                        reason: Optional[str] = None) -> bool:
        """Mute the system for a specific duration.
        
        Args:
            minutes: Duration in minutes
            user: Optional user who initiated the mute
            reason: Optional reason for muting
            
        Returns:
            True if temporary mute was successful
        """
        if minutes <= 0:
            self.logger.warning(f"Invalid mute duration: {minutes} minutes")
            return False
        
        return self.mute_system(
            duration_minutes=minutes,
            user=user,
            reason=reason or f"Temporary mute for {minutes} minutes"
        )
    
    def extend_mute(self, additional_minutes: int, user: Optional[str] = None) -> bool:
        """Extend the current mute duration.
        
        Args:
            additional_minutes: Additional minutes to add to current mute
            user: Optional user who initiated the extension
            
        Returns:
            True if mute extension was successful
        """
        try:
            current_status = self.get_current_status(force_refresh=True)
            
            if not current_status or not current_status.is_muted:
                self.logger.warning("Cannot extend mute - system is not currently muted")
                return False
            
            # Calculate new mute end time
            current_time = datetime.now()
            
            if current_status.mute_until:
                # Extend from current end time
                new_mute_until = current_status.mute_until + timedelta(minutes=additional_minutes)
            else:
                # If indefinite mute, start from now
                new_mute_until = current_time + timedelta(minutes=additional_minutes)
            
            # Create updated mute status
            extended_status = MuteStatus(
                is_muted=True,
                mute_timestamp=current_status.mute_timestamp,  # Keep original mute time
                mute_until=new_mute_until,
                muted_by=user or current_status.muted_by,
                reason=f"Extended by {additional_minutes} minutes"
            )
            
            # Save to repository
            if not self.mute_repository.save_status(extended_status):
                raise BusinessLogicException("Failed to save extended mute status")
            
            # Invalidate cache
            self._invalidate_cache()
            
            self.logger.info(f"Mute extended by {additional_minutes} minutes until {new_mute_until}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extending mute: {e}")
            return False
    
    def check_mute_expiration(self) -> bool:
        """Check if current mute has expired and update status if needed.
        
        Returns:
            True if mute status was updated (expired)
        """
        try:
            current_status = self.get_current_status(force_refresh=True)
            
            if not current_status or not current_status.is_muted:
                return False
            
            # Check if mute has expiration time
            if not current_status.mute_until:
                return False  # Indefinite mute
            
            # Check if expired
            current_time = datetime.now()
            if current_time >= current_status.mute_until:
                # Mute has expired - unmute system
                self.logger.info(f"Mute expired at {current_status.mute_until}, unmuting system")
                return self.unmute_system("system")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking mute expiration: {e}")
            return False
    
    def get_mute_time_remaining(self) -> Optional[timedelta]:
        """Get time remaining on current mute.
        
        Returns:
            timedelta object with remaining time, None if not muted or indefinite
        """
        try:
            current_status = self.get_current_status()
            
            if not current_status or not current_status.is_muted:
                return None
            
            if not current_status.mute_until:
                return None  # Indefinite mute
            
            current_time = datetime.now()
            remaining = current_status.mute_until - current_time
            
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
            
        except Exception as e:
            self.logger.error(f"Error getting mute time remaining: {e}")
            return None
    
    def get_mute_history(self, days: int = 7) -> List[MuteStatus]:
        """Get mute status history for the specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of MuteStatus objects
        """
        try:
            since = datetime.now() - timedelta(days=days)
            return self.mute_repository.get_history(since)
            
        except Exception as e:
            self.logger.error(f"Error getting mute history: {e}")
            return []
    
    def get_mute_statistics(self, days: int = 7) -> Dict:
        """Get mute usage statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary containing mute statistics
        """
        try:
            history = self.get_mute_history(days)
            
            stats = {
                'total_mutes': 0,
                'total_mute_time_minutes': 0,
                'average_mute_duration_minutes': 0,
                'longest_mute_minutes': 0,
                'mutes_by_user': {},
                'mutes_by_day': {},
                'expired_mutes': 0,
                'manual_unmutes': 0
            }
            
            mute_durations = []
            
            for status in history:
                if status.is_muted:
                    stats['total_mutes'] += 1
                    
                    # Calculate duration if possible
                    duration_minutes = 0
                    if status.mute_until:
                        duration = status.mute_until - status.mute_timestamp
                        duration_minutes = duration.total_seconds() / 60
                        mute_durations.append(duration_minutes)
                        stats['total_mute_time_minutes'] += duration_minutes
                        stats['longest_mute_minutes'] = max(stats['longest_mute_minutes'], duration_minutes)
                    
                    # Group by user
                    user = status.muted_by or 'unknown'
                    if user not in stats['mutes_by_user']:
                        stats['mutes_by_user'][user] = 0
                    stats['mutes_by_user'][user] += 1
                    
                    # Group by day
                    day = status.mute_timestamp.strftime('%Y-%m-%d')
                    if day not in stats['mutes_by_day']:
                        stats['mutes_by_day'][day] = 0
                    stats['mutes_by_day'][day] += 1
                else:
                    # This is an unmute event
                    if "Manual unmute" in (status.reason or ""):
                        stats['manual_unmutes'] += 1
                    elif "expired" in (status.reason or "").lower():
                        stats['expired_mutes'] += 1
            
            # Calculate average
            if mute_durations:
                stats['average_mute_duration_minutes'] = sum(mute_durations) / len(mute_durations)
            
            self.logger.debug(f"Generated mute statistics: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating mute statistics: {e}")
            return {
                'total_mutes': 0,
                'total_mute_time_minutes': 0,
                'average_mute_duration_minutes': 0,
                'longest_mute_minutes': 0,
                'mutes_by_user': {},
                'mutes_by_day': {},
                'expired_mutes': 0,
                'manual_unmutes': 0
            }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached mute status is valid.
        
        Returns:
            True if cache is valid
        """
        if not self._cached_status or not self._cache_timestamp:
            return False
        
        # Check if cache has expired
        cache_age = datetime.now() - self._cache_timestamp
        return cache_age.total_seconds() <= self._cache_ttl_seconds
    
    def _invalidate_cache(self) -> None:
        """Invalidate the mute status cache."""
        self._cached_status = None
        self._cache_timestamp = None
        self.logger.debug("Mute status cache invalidated")
