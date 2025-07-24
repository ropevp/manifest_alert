"""
Manifest Service - Business logic for manifest operations.

Handles manifest loading, validation, status updates, and coordination
with acknowledgment and alert systems.
"""

from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
import logging

from ...domain.models.manifest import Manifest, ManifestStatus
from ...domain.models.carrier import Carrier
from ...infrastructure.repositories.manifest_repository import ManifestRepository
from ...infrastructure.repositories.acknowledgment_repository import AcknowledgmentRepository
from ...infrastructure.repositories.config_repository import ConfigRepository
from ...infrastructure.exceptions import BusinessLogicException, DataValidationException


class ManifestService:
    """Service for managing manifest business logic.
    
    This service orchestrates manifest operations including:
    - Loading and validating manifest data
    - Coordinating with acknowledgment system
    - Status calculations and updates
    - Configuration management
    """
    
    def __init__(self,
                 manifest_repository: ManifestRepository,
                 acknowledgment_repository: AcknowledgmentRepository,
                 config_repository: ConfigRepository,
                 logger: Optional[logging.Logger] = None):
        """Initialize the manifest service.
        
        Args:
            manifest_repository: Repository for manifest data
            acknowledgment_repository: Repository for acknowledgments
            config_repository: Repository for configuration
            logger: Optional logger instance
        """
        self.manifest_repository = manifest_repository
        self.acknowledgment_repository = acknowledgment_repository
        self.config_repository = config_repository
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache for performance
        self._cached_manifests: Optional[List[Manifest]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 30  # 30 second cache TTL
        
        self.logger.info("ManifestService initialized")
    
    def get_manifests_for_date(self, date: Optional[str] = None, 
                              force_refresh: bool = False) -> List[Manifest]:
        """Get all manifests for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            force_refresh: Force reload from repository (bypass cache)
            
        Returns:
            List of manifest objects for the date
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Check cache first (unless force refresh)
            if not force_refresh and self._is_cache_valid(date):
                self.logger.debug(f"Returning cached manifests for {date}")
                return self._cached_manifests or []
            
            # Load from repository
            self.logger.debug(f"Loading manifests for {date} from repository")
            manifests = self.manifest_repository.load_manifests(date)
            
            # Apply acknowledgments to manifests
            self._apply_acknowledgments(manifests, date)
            
            # Update cache
            self._cached_manifests = manifests
            self._cache_timestamp = datetime.now()
            
            self.logger.info(f"Loaded {len(manifests)} manifests for {date}")
            return manifests
            
        except Exception as e:
            self.logger.error(f"Error loading manifests for {date}: {e}")
            raise BusinessLogicException(f"Failed to load manifests: {e}")
    
    def get_current_manifests(self, force_refresh: bool = False) -> List[Manifest]:
        """Get manifests for today.
        
        Args:
            force_refresh: Force reload from repository (bypass cache)
            
        Returns:
            List of today's manifest objects
        """
        return self.get_manifests_for_date(force_refresh=force_refresh)
    
    def get_manifest_by_time(self, time: str, date: Optional[str] = None) -> Optional[Manifest]:
        """Get a specific manifest by time.
        
        Args:
            time: Manifest time in HH:MM format
            date: Date string in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Manifest object if found, None otherwise
        """
        try:
            manifests = self.get_manifests_for_date(date)
            
            for manifest in manifests:
                if manifest.time == time:
                    return manifest
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding manifest for time {time}: {e}")
            return None
    
    def refresh_manifest_statuses(self, manifests: Optional[List[Manifest]] = None,
                                 current_time: Optional[datetime] = None) -> List[Manifest]:
        """Refresh status for all manifests based on current time.
        
        Args:
            manifests: Optional list of manifests (loads current if None)
            current_time: Current time for calculations (defaults to now)
            
        Returns:
            List of manifests with updated statuses
        """
        if manifests is None:
            manifests = self.get_current_manifests()
        
        if current_time is None:
            current_time = datetime.now()
        
        try:
            for manifest in manifests:
                # Status is automatically calculated by the domain model
                # but we can trigger recalculation by accessing it
                status = manifest.get_status(current_time)
                self.logger.debug(f"Manifest {manifest.time} status: {status.value}")
            
            self.logger.debug(f"Refreshed status for {len(manifests)} manifests")
            return manifests
            
        except Exception as e:
            self.logger.error(f"Error refreshing manifest statuses: {e}")
            return manifests
    
    def create_manifest(self, time: str, carrier_names: List[str], 
                       date: Optional[str] = None) -> Manifest:
        """Create a new manifest with carriers.
        
        Args:
            time: Manifest time in HH:MM format
            carrier_names: List of carrier names
            date: Optional date string (defaults to today)
            
        Returns:
            Created manifest object
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Create carriers
            carriers = []
            for name in carrier_names:
                if name and name.strip():
                    carriers.append(Carrier(name.strip()))
            
            # Create manifest
            manifest = Manifest(time=time, carriers=carriers, date=date)
            
            # Save to repository
            if not self.manifest_repository.save_manifest(manifest):
                raise BusinessLogicException("Failed to save manifest to repository")
            
            # Invalidate cache
            self._invalidate_cache()
            
            self.logger.info(f"Created manifest {time} with {len(carriers)} carriers")
            return manifest
            
        except Exception as e:
            self.logger.error(f"Error creating manifest {time}: {e}")
            raise BusinessLogicException(f"Failed to create manifest: {e}")
    
    def add_carrier_to_manifest(self, manifest_time: str, carrier_name: str,
                               date: Optional[str] = None) -> bool:
        """Add a carrier to an existing manifest.
        
        Args:
            manifest_time: Time of the manifest
            carrier_name: Name of carrier to add
            date: Optional date string (defaults to today)
            
        Returns:
            True if carrier was added successfully
        """
        try:
            manifest = self.get_manifest_by_time(manifest_time, date)
            if not manifest:
                self.logger.warning(f"Manifest not found for time {manifest_time}")
                return False
            
            # Add carrier to manifest
            manifest.add_carrier(carrier_name)
            
            # Save updated manifest
            if not self.manifest_repository.save_manifest(manifest):
                raise BusinessLogicException("Failed to save updated manifest")
            
            # Invalidate cache
            self._invalidate_cache()
            
            self.logger.info(f"Added carrier {carrier_name} to manifest {manifest_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding carrier {carrier_name} to manifest {manifest_time}: {e}")
            return False
    
    def remove_carrier_from_manifest(self, manifest_time: str, carrier_name: str,
                                   date: Optional[str] = None) -> bool:
        """Remove a carrier from an existing manifest.
        
        Args:
            manifest_time: Time of the manifest
            carrier_name: Name of carrier to remove
            date: Optional date string (defaults to today)
            
        Returns:
            True if carrier was removed successfully
        """
        try:
            manifest = self.get_manifest_by_time(manifest_time, date)
            if not manifest:
                self.logger.warning(f"Manifest not found for time {manifest_time}")
                return False
            
            # Remove carrier from manifest
            if not manifest.remove_carrier(carrier_name):
                self.logger.warning(f"Carrier {carrier_name} not found in manifest {manifest_time}")
                return False
            
            # Save updated manifest
            if not self.manifest_repository.save_manifest(manifest):
                raise BusinessLogicException("Failed to save updated manifest")
            
            # Invalidate cache
            self._invalidate_cache()
            
            self.logger.info(f"Removed carrier {carrier_name} from manifest {manifest_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing carrier {carrier_name} from manifest {manifest_time}: {e}")
            return False
    
    def get_manifest_statistics(self, date: Optional[str] = None) -> Dict:
        """Get statistics about manifests for a date.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary containing manifest statistics
        """
        try:
            manifests = self.get_manifests_for_date(date)
            current_time = datetime.now()
            
            stats = {
                'total_manifests': len(manifests),
                'total_carriers': sum(len(m.carriers) for m in manifests),
                'active_manifests': 0,
                'missed_manifests': 0,
                'pending_manifests': 0,
                'acknowledged_manifests': 0,
                'unacknowledged_carriers': 0,
                'acknowledged_carriers': 0,
                'acknowledgment_percentage': 0
            }
            
            for manifest in manifests:
                status = manifest.get_status(current_time)
                
                if status == ManifestStatus.ACTIVE:
                    stats['active_manifests'] += 1
                elif status == ManifestStatus.MISSED:
                    stats['missed_manifests'] += 1
                elif status == ManifestStatus.PENDING:
                    stats['pending_manifests'] += 1
                elif status == ManifestStatus.ACKNOWLEDGED:
                    stats['acknowledged_manifests'] += 1
                
                stats['unacknowledged_carriers'] += len(manifest.get_unacknowledged_carriers())
                stats['acknowledged_carriers'] += len(manifest.get_acknowledged_carriers())
            
            # Calculate acknowledgment percentage
            total_carriers = stats['acknowledged_carriers'] + stats['unacknowledged_carriers']
            if total_carriers > 0:
                stats['acknowledgment_percentage'] = round(
                    (stats['acknowledged_carriers'] / total_carriers) * 100, 1
                )
            
            self.logger.debug(f"Generated statistics: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating manifest statistics: {e}")
            return {
                'total_manifests': 0,
                'total_carriers': 0,
                'active_manifests': 0,
                'missed_manifests': 0,
                'pending_manifests': 0,
                'acknowledged_manifests': 0,
                'unacknowledged_carriers': 0,
                'acknowledged_carriers': 0,
                'acknowledgment_percentage': 0
            }
    
    def _apply_acknowledgments(self, manifests: List[Manifest], date: str) -> None:
        """Apply acknowledgment data to manifests.
        
        Args:
            manifests: List of manifests to update
            date: Date to load acknowledgments for
        """
        try:
            # Load acknowledgments for the date
            acknowledgments = self.acknowledgment_repository.get_acknowledgments_for_date(date)
            
            # Apply acknowledgments to corresponding carriers
            for ack in acknowledgments:
                # Find matching manifest
                manifest = None
                for m in manifests:
                    if m.time == ack.manifest_time and m.date == ack.date:
                        manifest = m
                        break
                
                if manifest:
                    # Find matching carrier
                    carrier = manifest.get_carrier(ack.carrier)
                    if carrier:
                        carrier.acknowledge(ack.user, ack.reason)
                        self.logger.debug(f"Applied acknowledgment: {ack.manifest_time} - {ack.carrier}")
            
            self.logger.debug(f"Applied {len(acknowledgments)} acknowledgments to manifests")
            
        except Exception as e:
            self.logger.warning(f"Error applying acknowledgments: {e}")
            # Don't fail the entire operation if acknowledgments fail
    
    def _is_cache_valid(self, date: str) -> bool:
        """Check if cached data is valid for the given date.
        
        Args:
            date: Date to check cache validity for
            
        Returns:
            True if cache is valid
        """
        if not self._cached_manifests or not self._cache_timestamp:
            return False
        
        # Check if cache has expired
        cache_age = datetime.now() - self._cache_timestamp
        if cache_age.total_seconds() > self._cache_ttl_seconds:
            return False
        
        # Check if cache is for today (simple check - could be enhanced)
        today = datetime.now().strftime("%Y-%m-%d")
        if date != today:
            return False
        
        return True
    
    def _invalidate_cache(self) -> None:
        """Invalidate the manifest cache."""
        self._cached_manifests = None
        self._cache_timestamp = None
        self.logger.debug("Manifest cache invalidated")
