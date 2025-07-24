"""
Acknowledgment repository for managing manifest acknowledgments.

Handles loading and saving acknowledgment data with network synchronization
and local backup for reliability.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from .base_repository import BaseRepository
from ...domain.models.acknowledgment import Acknowledgment
from ...infrastructure.exceptions import DataValidationException, NetworkAccessException
from ...infrastructure.network import NetworkService
from ...infrastructure.cache import CacheManager


class AcknowledgmentRepository(BaseRepository[Acknowledgment]):
    """Abstract repository for acknowledgment data operations."""
    
    @abstractmethod
    def load_acknowledgments(self, date: Optional[str] = None) -> List[Acknowledgment]:
        """Load acknowledgments for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format, today if None
            
        Returns:
            List of acknowledgment objects
        """
        pass
    
    @abstractmethod
    def save_acknowledgment(self, acknowledgment: Acknowledgment) -> bool:
        """Save a single acknowledgment.
        
        Args:
            acknowledgment: Acknowledgment to save
            
        Returns:
            True if save was successful
        """
        pass
    
    @abstractmethod
    def get_acknowledgment(self, manifest_time: str, carrier_name: str, 
                          date: Optional[str] = None) -> Optional[Acknowledgment]:
        """Get specific acknowledgment by manifest and carrier.
        
        Args:
            manifest_time: Time of the manifest
            carrier_name: Name of the carrier
            date: Date string, today if None
            
        Returns:
            Acknowledgment object if found, None otherwise
        """
        pass


class FileAcknowledgmentRepository(AcknowledgmentRepository):
    """File-based acknowledgment repository with network and local storage.
    
    Stores acknowledgments in network-shared JSON file for cross-PC synchronization
    with local backup for reliability.
    """
    
    def __init__(self, network_service: Optional[NetworkService] = None,
                 cache_manager: Optional[CacheManager] = None,
                 local_data_path: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the acknowledgment repository.
        
        Args:
            network_service: Service for network file operations
            cache_manager: Cache manager for performance
            local_data_path: Local path for backup files
            logger: Logger for repository operations
        """
        super().__init__(logger)
        self.network_service = network_service or NetworkService()
        self.cache_manager = cache_manager or CacheManager()
        self.local_data_path = Path(local_data_path or "data")
        
        # File configuration
        self.ack_filename = "ack.json"
        self.local_backup_dir = self.local_data_path / "backup"
        
        # Ensure backup directory exists
        self.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"FileAcknowledgmentRepository initialized with local backup: {self.local_backup_dir}")
    
    def load(self) -> List[Acknowledgment]:
        """Load all acknowledgments for today."""
        return self.load_acknowledgments()
    
    def save(self, entities: List[Acknowledgment]) -> bool:
        """Save a list of acknowledgments."""
        try:
            success_count = 0
            for ack in entities:
                if self.save_acknowledgment(ack):
                    success_count += 1
            
            self.logger.info(f"Saved {success_count}/{len(entities)} acknowledgments")
            return success_count == len(entities)
            
        except Exception as e:
            self._set_error(e)
            return False
    
    def exists(self) -> bool:
        """Check if acknowledgment data sources are accessible."""
        try:
            # Check network file access
            network_exists = self.network_service.file_exists(self.ack_filename)
            
            # Check local backup
            local_exists = (self.local_backup_dir / self.ack_filename).exists()
            
            return network_exists or local_exists
            
        except Exception as e:
            self.logger.warning(f"Error checking acknowledgment repository existence: {e}")
            return False
    
    def load_acknowledgments(self, date: Optional[str] = None) -> List[Acknowledgment]:
        """Load acknowledgments for a specific date with caching.
        
        Args:
            date: Date string in YYYY-MM-DD format, today if None
            
        Returns:
            List of acknowledgment objects for the date
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"acknowledgments:{date}"
        
        try:
            return self.cache_manager.get_fast_cached(
                cache_key,
                lambda: self._load_acknowledgments_direct(date)
            )
        except Exception as e:
            error = NetworkAccessException(f"Failed to load acknowledgments for {date}: {e}")
            self._set_error(error)
            raise error
    
    def save_acknowledgment(self, acknowledgment: Acknowledgment) -> bool:
        """Save a single acknowledgment to network and local backup.
        
        Args:
            acknowledgment: Acknowledgment to save
            
        Returns:
            True if save was successful
        """
        try:
            # Load existing acknowledgments
            all_acks = self._load_all_acknowledgments()
            
            # Add or update the acknowledgment
            updated = False
            for i, existing_ack in enumerate(all_acks):
                if (existing_ack.manifest_time == acknowledgment.manifest_time and
                    existing_ack.carrier == acknowledgment.carrier and
                    existing_ack.date == acknowledgment.date):
                    all_acks[i] = acknowledgment
                    updated = True
                    break
            
            if not updated:
                all_acks.append(acknowledgment)
            
            # Save to network file
            success = self._save_all_acknowledgments(all_acks)
            
            if success:
                # Invalidate cache for the date
                cache_key = f"acknowledgments:{acknowledgment.date}"
                self.cache_manager.invalidate(cache_key, 'fast')
                
                self.logger.debug(f"Saved acknowledgment: {acknowledgment.get_manifest_key()} - {acknowledgment.carrier}")
            
            return success
            
        except Exception as e:
            error = NetworkAccessException(f"Failed to save acknowledgment: {e}")
            self._set_error(error)
            raise error
    
    def get_acknowledgment(self, manifest_time: str, carrier_name: str, 
                          date: Optional[str] = None) -> Optional[Acknowledgment]:
        """Get specific acknowledgment by manifest and carrier.
        
        Args:
            manifest_time: Time of the manifest
            carrier_name: Name of the carrier
            date: Date string, today if None
            
        Returns:
            Acknowledgment object if found, None otherwise
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            acknowledgments = self.load_acknowledgments(date)
            
            for ack in acknowledgments:
                if (ack.manifest_time == manifest_time and 
                    ack.carrier == carrier_name and 
                    ack.date == date):
                    return ack
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get acknowledgment for {manifest_time}, {carrier_name}: {e}")
            return None
    
    def clear_acknowledgments(self, date: Optional[str] = None) -> bool:
        """Clear acknowledgments for a specific date.
        
        Args:
            date: Date string, today if None
            
        Returns:
            True if successful
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Load all acknowledgments
            all_acks = self._load_all_acknowledgments()
            
            # Filter out acknowledgments for the specified date
            filtered_acks = [ack for ack in all_acks if ack.date != date]
            
            # Save filtered acknowledgments
            success = self._save_all_acknowledgments(filtered_acks)
            
            if success:
                # Invalidate cache
                cache_key = f"acknowledgments:{date}"
                self.cache_manager.invalidate(cache_key, 'fast')
                
                removed_count = len(all_acks) - len(filtered_acks)
                self.logger.info(f"Cleared {removed_count} acknowledgments for {date}")
            
            return success
            
        except Exception as e:
            error = NetworkAccessException(f"Failed to clear acknowledgments for {date}: {e}")
            self._set_error(error)
            raise error
    
    def get_acknowledgment_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for acknowledgments.
        
        Args:
            date: Date string, today if None
            
        Returns:
            Dictionary with acknowledgment statistics
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            acknowledgments = self.load_acknowledgments(date)
            
            summary = {
                "date": date,
                "total_count": len(acknowledgments),
                "unique_manifests": len(set(ack.manifest_time for ack in acknowledgments)),
                "unique_carriers": len(set(ack.carrier for ack in acknowledgments)),
                "acknowledgments_by_user": {},
                "acknowledgments_by_time": {},
            }
            
            # Group by user
            for ack in acknowledgments:
                user = ack.user
                if user not in summary["acknowledgments_by_user"]:
                    summary["acknowledgments_by_user"][user] = 0
                summary["acknowledgments_by_user"][user] += 1
            
            # Group by manifest time
            for ack in acknowledgments:
                time_key = ack.manifest_time
                if time_key not in summary["acknowledgments_by_time"]:
                    summary["acknowledgments_by_time"][time_key] = 0
                summary["acknowledgments_by_time"][time_key] += 1
            
            return summary
            
        except Exception as e:
            self.logger.warning(f"Failed to get acknowledgment summary for {date}: {e}")
            return {"date": date, "error": str(e)}
    
    def _load_acknowledgments_direct(self, date: str) -> List[Acknowledgment]:
        """Load acknowledgments directly from storage without caching.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of acknowledgment objects for the date
        """
        try:
            # Load all acknowledgments
            all_acks = self._load_all_acknowledgments()
            
            # Filter by date
            date_acks = [ack for ack in all_acks if ack.date == date]
            
            self.logger.debug(f"Loaded {len(date_acks)} acknowledgments for {date}")
            return date_acks
            
        except Exception as e:
            self.logger.warning(f"Failed to load acknowledgments for {date}: {e}")
            return []
    
    def _load_all_acknowledgments(self) -> List[Acknowledgment]:
        """Load all acknowledgments from network and local backup.
        
        Returns:
            List of all acknowledgment objects
        """
        acknowledgments = []
        
        # Try to load from network first
        try:
            network_data = self.network_service.load_json_file(self.ack_filename, use_cache=False)
            network_acks = self._parse_acknowledgment_data(network_data)
            acknowledgments.extend(network_acks)
            
            # Create local backup
            self._create_local_backup(network_data)
            
        except Exception as e:
            self.logger.warning(f"Could not load acknowledgments from network: {e}")
            
            # Try local backup
            try:
                backup_path = self.local_backup_dir / self.ack_filename
                if backup_path.exists():
                    with open(backup_path, 'r', encoding='utf-8') as file:
                        backup_data = json.load(file)
                    backup_acks = self._parse_acknowledgment_data(backup_data)
                    acknowledgments.extend(backup_acks)
                    self.logger.info(f"Loaded acknowledgments from local backup")
                
            except Exception as e2:
                self.logger.warning(f"Could not load acknowledgments from backup: {e2}")
        
        return acknowledgments
    
    def _save_all_acknowledgments(self, acknowledgments: List[Acknowledgment]) -> bool:
        """Save all acknowledgments to network and local backup.
        
        Args:
            acknowledgments: List of acknowledgments to save
            
        Returns:
            True if save was successful
        """
        try:
            # Convert to dictionary format
            ack_data = {
                "acknowledgments": [ack.to_dict() for ack in acknowledgments],
                "last_updated": datetime.now().isoformat(),
                "count": len(acknowledgments),
                "version": "1.0"
            }
            
            # Save to network
            network_success = self.network_service.save_json_file(
                self.ack_filename, ack_data, create_backup=True
            )
            
            # Always create local backup
            self._create_local_backup(ack_data)
            
            return network_success
            
        except Exception as e:
            self.logger.error(f"Failed to save acknowledgments: {e}")
            return False
    
    def _parse_acknowledgment_data(self, data: Dict[str, Any]) -> List[Acknowledgment]:
        """Parse acknowledgment data from dictionary format.
        
        Args:
            data: Dictionary containing acknowledgment data
            
        Returns:
            List of acknowledgment objects
        """
        acknowledgments = []
        
        try:
            ack_list = data.get("acknowledgments", [])
            
            for ack_dict in ack_list:
                try:
                    acknowledgment = Acknowledgment.from_dict(ack_dict)
                    acknowledgments.append(acknowledgment)
                except Exception as e:
                    self.logger.warning(f"Failed to parse acknowledgment: {e}")
                    continue
            
        except Exception as e:
            raise DataValidationException(f"Invalid acknowledgment data format: {e}")
        
        return acknowledgments
    
    def _create_local_backup(self, data: Dict[str, Any]) -> None:
        """Create local backup of acknowledgment data.
        
        Args:
            data: Dictionary data to backup
        """
        try:
            backup_path = self.local_backup_dir / self.ack_filename
            with open(backup_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Created local backup at {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create local backup: {e}")
    
    def cleanup_old_acknowledgments(self, days_to_keep: int = 30) -> int:
        """Clean up acknowledgments older than specified days.
        
        Args:
            days_to_keep: Number of days to keep acknowledgments
            
        Returns:
            Number of acknowledgments removed
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            # Load all acknowledgments
            all_acks = self._load_all_acknowledgments()
            
            # Filter out old acknowledgments
            kept_acks = [ack for ack in all_acks if ack.date >= cutoff_str]
            removed_count = len(all_acks) - len(kept_acks)
            
            if removed_count > 0:
                # Save filtered acknowledgments
                self._save_all_acknowledgments(kept_acks)
                self.logger.info(f"Cleaned up {removed_count} old acknowledgments (older than {cutoff_str})")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old acknowledgments: {e}")
            return 0
