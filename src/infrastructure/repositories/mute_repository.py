"""
Mute repository for centralized mute state management.

Handles loading and saving mute status with aggressive caching
for the cross-PC mute synchronization system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime

from .base_repository import BaseRepository
from ...domain.models.mute_status import MuteStatus, MuteType
from ...infrastructure.exceptions import DataValidationException, NetworkAccessException
from ...infrastructure.network import NetworkService
from ...infrastructure.cache import CacheManager


class MuteRepository(BaseRepository[MuteStatus]):
    """Abstract repository for mute status operations."""
    
    @abstractmethod
    def load_mute_status(self) -> MuteStatus:
        """Load the current centralized mute status.
        
        Returns:
            Current mute status object
        """
        pass
    
    @abstractmethod
    def save_mute_status(self, mute_status: MuteStatus) -> bool:
        """Save mute status to centralized storage.
        
        Args:
            mute_status: Mute status to save
            
        Returns:
            True if save was successful
        """
        pass
    
    @abstractmethod
    def toggle_mute(self, duration_minutes: Optional[int] = None) -> MuteStatus:
        """Toggle the mute status.
        
        Args:
            duration_minutes: Duration for snooze, indefinite if None
            
        Returns:
            New mute status after toggle
        """
        pass


class FileMuteRepository(MuteRepository):
    """File-based mute repository with network synchronization.
    
    Stores mute status in network-shared JSON file for cross-PC synchronization.
    Uses aggressive caching to meet performance requirements.
    """
    
    def __init__(self, network_service: Optional[NetworkService] = None,
                 cache_manager: Optional[CacheManager] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the mute repository.
        
        Args:
            network_service: Service for network file operations
            cache_manager: Cache manager for performance
            logger: Logger for repository operations
        """
        super().__init__(logger)
        self.network_service = network_service or NetworkService()
        self.cache_manager = cache_manager or CacheManager()
        
        # File configuration
        self.mute_filename = "mute_status.json"
        
        self.logger.info("FileMuteRepository initialized for centralized mute state")
    
    def load(self) -> List[MuteStatus]:
        """Load method for base repository compatibility."""
        return [self.load_mute_status()]
    
    def save(self, entities: List[MuteStatus]) -> bool:
        """Save method for base repository compatibility."""
        if not entities:
            return False
        return self.save_mute_status(entities[0])
    
    def exists(self) -> bool:
        """Check if mute status file is accessible."""
        try:
            return self.network_service.file_exists(self.mute_filename)
        except Exception as e:
            self.logger.warning(f"Error checking mute status file existence: {e}")
            return False
    
    def load_mute_status(self) -> MuteStatus:
        """Load the current centralized mute status with caching.
        
        This method uses fast cache (5-second TTL) for UI responsiveness
        while falling back to network cache for reliability.
        
        Returns:
            Current mute status object
        """
        cache_key = "mute_status"
        
        try:
            # Use fast cache for UI responsiveness
            return self.cache_manager.get_fast_cached(
                cache_key,
                lambda: self._load_mute_status_from_network()
            )
        except Exception as e:
            # Try network cache as fallback
            try:
                return self.cache_manager.get_network_cached(
                    cache_key,
                    lambda: self._load_mute_status_from_network()
                )
            except Exception as e2:
                self.logger.warning(f"Failed to load mute status, using default: {e2}")
                return MuteStatus.create_unmuted()
    
    def save_mute_status(self, mute_status: MuteStatus) -> bool:
        """Save mute status to centralized network file.
        
        Args:
            mute_status: Mute status to save
            
        Returns:
            True if save was successful
        """
        try:
            # Convert to dictionary format
            mute_data = mute_status.to_dict()
            
            # Add metadata
            save_data = {
                "mute_status": mute_data,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Save to network file
            success = self.network_service.save_json_file(
                self.mute_filename, save_data, create_backup=True
            )
            
            if success:
                # Invalidate all caches to ensure immediate update
                cache_key = "mute_status"
                self.cache_manager.invalidate(cache_key, 'fast')
                self.cache_manager.invalidate(cache_key, 'network')
                
                self.logger.debug(f"Saved mute status: {mute_status.get_mute_summary()}")
            
            return success
            
        except Exception as e:
            error = NetworkAccessException(f"Failed to save mute status: {e}")
            self._set_error(error)
            raise error
    
    def toggle_mute(self, duration_minutes: Optional[int] = None) -> MuteStatus:
        """Toggle the mute status with optional snooze duration.
        
        Args:
            duration_minutes: Duration for snooze, indefinite if None
            
        Returns:
            New mute status after toggle
        """
        try:
            # Load current status
            current_status = self.load_mute_status()
            
            # Toggle the status
            is_now_muted = current_status.toggle_mute(duration_minutes)
            
            # Get the updated status after toggle
            new_status = current_status  # The toggle method modifies the object in place
            
            # Save the new status
            success = self.save_mute_status(new_status)
            
            if success:
                self.logger.info(f"Mute toggled: now {'muted' if is_now_muted else 'unmuted'}")
                return new_status
            else:
                self.logger.error("Failed to save mute status after toggle")
                return current_status
                
        except Exception as e:
            error = NetworkAccessException(f"Failed to toggle mute: {e}")
            self._set_error(error)
            raise error
    
    def snooze(self, duration_minutes: int = 30) -> MuteStatus:
        """Snooze alerts for a specific duration.
        
        Args:
            duration_minutes: Duration to snooze in minutes
            
        Returns:
            New mute status with snooze
        """
        try:
            snooze_status = MuteStatus.create_snoozed(duration_minutes)
            success = self.save_mute_status(snooze_status)
            
            if success:
                self.logger.info(f"Snoozed for {duration_minutes} minutes")
                return snooze_status
            else:
                raise NetworkAccessException("Failed to save snooze status")
                
        except Exception as e:
            error = NetworkAccessException(f"Failed to snooze: {e}")
            self._set_error(error)
            raise error
    
    def unmute(self) -> MuteStatus:
        """Unmute all alerts.
        
        Returns:
            Unmuted status
        """
        try:
            unmute_status = MuteStatus.create_unmuted()
            success = self.save_mute_status(unmute_status)
            
            if success:
                self.logger.info("Alerts unmuted")
                return unmute_status
            else:
                raise NetworkAccessException("Failed to save unmute status")
                
        except Exception as e:
            error = NetworkAccessException(f"Failed to unmute: {e}")
            self._set_error(error)
            raise error
    
    def _load_mute_status_from_network(self) -> MuteStatus:
        """Load mute status directly from network file.
        
        Returns:
            Mute status object from network file
        """
        try:
            # Load data from network file
            data = self.network_service.load_json_file(self.mute_filename, use_cache=False)
            
            # Extract mute status data
            mute_data = data.get("mute_status", {})
            
            if not mute_data:
                self.logger.info("No mute status found in file, using default unmuted")
                return MuteStatus.create_unmuted()
            
            # Parse mute status from dictionary
            mute_status = MuteStatus.from_dict(mute_data)
            
            self.logger.debug(f"Loaded mute status from network: {mute_status.get_mute_summary()}")
            return mute_status
            
        except FileNotFoundError:
            self.logger.info("Mute status file not found, creating default unmuted status")
            default_status = MuteStatus.create_unmuted()
            self.save_mute_status(default_status)
            return default_status
            
        except DataValidationException as e:
            self.logger.error(f"Invalid mute status data format: {e}")
            return MuteStatus.create_unmuted()
            
        except Exception as e:
            self.logger.warning(f"Failed to load mute status from network: {e}")
            return MuteStatus.create_unmuted()
    
    def get_mute_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent mute status changes (if history tracking is implemented).
        
        Args:
            limit: Maximum number of history entries
            
        Returns:
            List of mute status history entries
        """
        # This could be extended to track mute history
        # For now, return empty list
        return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for mute operations.
        
        Returns:
            Dictionary with performance metrics
        """
        cache_stats = self.cache_manager.get_statistics()
        network_stats = self.network_service.get_performance_stats()
        
        return {
            "mute_repository": {
                "cache_hit_ratio": cache_stats.hit_ratio,
                "network_calls_saved": cache_stats.network_calls_saved,
                "network_stats": network_stats,
            }
        }
