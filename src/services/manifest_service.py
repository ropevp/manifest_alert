"""
Manifest Service

Business logic service for managing manifest processing, validation,
and coordination with other services.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, time, timedelta
from enum import Enum

from ..domain.models import Manifest, Carrier, Alert, AlertPriority, AlertStatus
from ..infrastructure.repositories import ManifestRepository, AcknowledgmentRepository
from ..infrastructure.exceptions import (
    DataValidationException,
    NetworkAccessException,
    ManifestProcessingException
)


class ManifestStatus(Enum):
    """Status of manifest processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class ManifestProcessingResult:
    """Result of manifest processing operation."""
    success: bool
    manifests_processed: int
    alerts_generated: int
    errors: List[str]
    warnings: List[str]
    processing_time_ms: float
    
    def add_error(self, error: str) -> None:
        """Add a processing error."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a processing warning."""
        self.warnings.append(warning)


@dataclass
class ManifestSummary:
    """Summary of manifest data for a specific time period."""
    date: str
    total_manifests: int
    unique_times: Set[str]
    carriers_by_time: Dict[str, List[str]]
    acknowledged_count: int
    pending_count: int
    overdue_count: int
    last_updated: Optional[datetime] = None


class ManifestService:
    """Service for managing manifest processing and business logic.
    
    This service provides core manifest functionality including:
    - Loading and processing manifest data from CSV sources
    - Generating alerts based on manifest status and acknowledgments
    - Coordinating with acknowledgment tracking
    - Providing manifest summaries and statistics
    - Managing manifest validation and data integrity
    """
    
    def __init__(self, manifest_repository: ManifestRepository, 
                 acknowledgment_repository: AcknowledgmentRepository):
        """Initialize manifest service.
        
        Args:
            manifest_repository: Repository for manifest data persistence
            acknowledgment_repository: Repository for acknowledgment tracking
        """
        self.manifest_repository = manifest_repository
        self.acknowledgment_repository = acknowledgment_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("ManifestService initialized")
    
    def load_manifests(self, date: Optional[str] = None, 
                      force_refresh: bool = False) -> List[Manifest]:
        """Load manifests for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            force_refresh: Force reload from data source
            
        Returns:
            List of manifests for the specified date
            
        Raises:
            ManifestProcessingException: If manifests cannot be loaded
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            self.logger.debug(f"Loading manifests for {date}")
            
            # Load manifests from repository
            manifests = self.manifest_repository.load_manifests(date, force_refresh)
            
            # Validate loaded manifests
            validated_manifests = []
            for manifest in manifests:
                try:
                    self._validate_manifest(manifest)
                    validated_manifests.append(manifest)
                except DataValidationException as e:
                    self.logger.warning(f"Invalid manifest skipped: {e}")
            
            self.logger.info(f"Loaded {len(validated_manifests)} valid manifests for {date}")
            return validated_manifests
            
        except Exception as e:
            error_msg = f"Failed to load manifests for {date}: {e}"
            self.logger.error(error_msg)
            raise ManifestProcessingException(error_msg)
    
    def process_manifests(self, date: Optional[str] = None, 
                         configured_times: Optional[List[str]] = None,
                         configured_carriers: Optional[List[Carrier]] = None) -> ManifestProcessingResult:
        """Process manifests and generate alerts for missing carriers.
        
        Args:
            date: Date to process (defaults to today)
            configured_times: Expected manifest times
            configured_carriers: Expected carriers
            
        Returns:
            Processing result with statistics and any errors
        """
        start_time = datetime.now()
        result = ManifestProcessingResult(
            success=True,
            manifests_processed=0,
            alerts_generated=0,
            errors=[],
            warnings=[],
            processing_time_ms=0.0
        )
        
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            if configured_times is None:
                configured_times = ["07:00", "13:00", "19:00"]  # Default times
            
            if configured_carriers is None:
                # Default carriers if none provided
                default_carrier_names = [
                    "Australia Post Metro", "Australia Post Regular",
                    "DHL Express", "TNT Express",
                    "Startrack Premium", "Startrack Standard"
                ]
                configured_carriers = [Carrier(name) for name in default_carrier_names]
            
            self.logger.info(f"Processing manifests for {date}")
            
            # Load existing manifests
            manifests = self.load_manifests(date)
            result.manifests_processed = len(manifests)
            
            # Load acknowledgments for the date
            acknowledgments = self.acknowledgment_repository.load_acknowledgments(date)
            
            # Process each configured time
            for manifest_time in configured_times:
                time_manifests = [m for m in manifests if m.time == manifest_time]
                
                # Get carriers present in manifests for this time
                present_carriers = {m.get_primary_carrier().name for m in time_manifests}
                
                # Check for missing carriers
                for carrier in configured_carriers:
                    if carrier.name not in present_carriers:
                        # Check if this carrier is acknowledged
                        is_acknowledged = any(
                            ack.manifest_time == manifest_time and ack.carrier == carrier.name
                            for ack in acknowledgments
                        )
                        
                        if not is_acknowledged:
                            # Generate alert for missing carrier
                            alert = self._create_missing_carrier_alert(
                                date, manifest_time, carrier, datetime.now()
                            )
                            result.alerts_generated += 1
                            
                            self.logger.debug(f"Generated alert for missing {carrier.name} at {manifest_time}")
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            self.logger.info(f"Processed {result.manifests_processed} manifests, "
                           f"generated {result.alerts_generated} alerts in "
                           f"{result.processing_time_ms:.1f}ms")
            
            return result
            
        except Exception as e:
            result.add_error(f"Manifest processing failed: {e}")
            self.logger.error(f"Manifest processing failed: {e}")
            return result
    
    def get_manifest_summary(self, date: Optional[str] = None) -> ManifestSummary:
        """Get summary of manifest data for a date.
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Manifest summary with statistics
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Load manifests and acknowledgments
            manifests = self.load_manifests(date)
            acknowledgments = self.acknowledgment_repository.load_acknowledgments(date)
            
            # Build summary
            unique_times = {m.time for m in manifests}
            carriers_by_time = {}
            
            for time_str in unique_times:
                time_manifests = [m for m in manifests if m.time == time_str]
                carriers_by_time[time_str] = [m.get_primary_carrier().name for m in time_manifests]
            
            # Count acknowledgments
            acknowledged_count = len(acknowledgments)
            
            # Calculate pending/overdue counts (simplified logic)
            current_time = datetime.now()
            pending_count = 0
            overdue_count = 0
            
            # This would need more complex logic based on actual business rules
            for time_str in unique_times:
                try:
                    manifest_datetime = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
                    if manifest_datetime < current_time:
                        # Past manifest time - check if all carriers are acknowledged
                        time_acknowledgments = [a for a in acknowledgments if a.manifest_time == time_str]
                        if len(time_acknowledgments) < len(carriers_by_time.get(time_str, [])):
                            overdue_count += 1
                    else:
                        pending_count += 1
                except ValueError:
                    pass  # Skip invalid time formats
            
            return ManifestSummary(
                date=date,
                total_manifests=len(manifests),
                unique_times=unique_times,
                carriers_by_time=carriers_by_time,
                acknowledged_count=acknowledged_count,
                pending_count=pending_count,
                overdue_count=overdue_count,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate manifest summary for {date}: {e}")
            # Return empty summary on error
            return ManifestSummary(
                date=date,
                total_manifests=0,
                unique_times=set(),
                carriers_by_time={},
                acknowledged_count=0,
                pending_count=0,
                overdue_count=0
            )
    
    def get_missing_carriers(self, date: Optional[str] = None,
                           configured_times: Optional[List[str]] = None,
                           configured_carriers: Optional[List[Carrier]] = None) -> Dict[str, List[str]]:
        """Get missing carriers for each manifest time.
        
        Args:
            date: Date to check (defaults to today)
            configured_times: Expected manifest times
            configured_carriers: Expected carriers
            
        Returns:
            Dictionary mapping manifest times to lists of missing carrier names
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            if configured_times is None:
                configured_times = ["07:00", "13:00", "19:00"]
            
            if configured_carriers is None:
                default_carrier_names = [
                    "Australia Post Metro", "Australia Post Regular",
                    "DHL Express", "TNT Express",
                    "Startrack Premium", "Startrack Standard"
                ]
                configured_carriers = [Carrier(name) for name in default_carrier_names]
            
            # Load manifests and acknowledgments
            manifests = self.load_manifests(date)
            acknowledgments = self.acknowledgment_repository.load_acknowledgments(date)
            
            missing_by_time = {}
            
            for manifest_time in configured_times:
                # Get carriers present in manifests for this time
                time_manifests = [m for m in manifests if m.time == manifest_time]
                present_carriers = {m.get_primary_carrier().name for m in time_manifests}
                
                # Get acknowledged carriers for this time
                acknowledged_carriers = {
                    ack.carrier for ack in acknowledgments 
                    if ack.manifest_time == manifest_time
                }
                
                # Find missing carriers (not present and not acknowledged)
                missing_carriers = []
                for carrier in configured_carriers:
                    if (carrier.name not in present_carriers and 
                        carrier.name not in acknowledged_carriers):
                        missing_carriers.append(carrier.name)
                
                missing_by_time[manifest_time] = missing_carriers
            
            return missing_by_time
            
        except Exception as e:
            self.logger.error(f"Failed to get missing carriers for {date}: {e}")
            return {}
    
    def get_carrier_status(self, date: str, manifest_time: str, carrier_name: str) -> ManifestStatus:
        """Get the status of a specific carrier for a manifest time.
        
        Args:
            date: Date in YYYY-MM-DD format
            manifest_time: Time in HH:MM format
            carrier_name: Name of the carrier
            
        Returns:
            Status of the carrier
        """
        try:
            # Check if carrier has a manifest
            manifests = self.load_manifests(date)
            has_manifest = any(
                m.time == manifest_time and m.get_primary_carrier().name == carrier_name
                for m in manifests
            )
            
            if has_manifest:
                return ManifestStatus.COMPLETED
            
            # Check if carrier is acknowledged
            acknowledgments = self.acknowledgment_repository.load_acknowledgments(date)
            is_acknowledged = any(
                ack.manifest_time == manifest_time and ack.carrier == carrier_name
                for ack in acknowledgments
            )
            
            if is_acknowledged:
                return ManifestStatus.ACKNOWLEDGED
            
            # Check if manifest time has passed
            try:
                current_time = datetime.now()
                manifest_datetime = datetime.strptime(f"{date} {manifest_time}", "%Y-%m-%d %H:%M")
                
                if manifest_datetime < current_time:
                    return ManifestStatus.ERROR  # Overdue
                else:
                    return ManifestStatus.PENDING
            except ValueError:
                return ManifestStatus.ERROR
                
        except Exception as e:
            self.logger.error(f"Failed to get carrier status for {carrier_name}: {e}")
            return ManifestStatus.ERROR
    
    def validate_manifest_data(self, manifests: List[Manifest]) -> List[str]:
        """Validate a list of manifests and return any errors.
        
        Args:
            manifests: List of manifests to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for i, manifest in enumerate(manifests):
            try:
                self._validate_manifest(manifest)
            except DataValidationException as e:
                errors.append(f"Manifest {i}: {e}")
        
        return errors
    
    def deduplicate_manifests(self, manifests: List[Manifest]) -> List[Manifest]:
        """Remove duplicate manifests based on name and time.
        
        Args:
            manifests: List of manifests potentially containing duplicates
            
        Returns:
            List of unique manifests
        """
        seen = set()
        unique_manifests = []
        
        for manifest in manifests:
            # Create a key based on name and time
            key = (manifest.name, manifest.time)
            if key not in seen:
                seen.add(key)
                unique_manifests.append(manifest)
            else:
                self.logger.debug(f"Duplicate manifest removed: {manifest.name} at {manifest.time}")
        
        return unique_manifests
    
    def get_manifests_by_carrier(self, date: str, carrier_name: str) -> List[Manifest]:
        """Get all manifests for a specific carrier on a date.
        
        Args:
            date: Date in YYYY-MM-DD format
            carrier_name: Name of the carrier
            
        Returns:
            List of manifests for the carrier
        """
        try:
            manifests = self.load_manifests(date)
            return [
                m for m in manifests 
                if m.get_primary_carrier().name == carrier_name
            ]
        except Exception as e:
            self.logger.error(f"Failed to get manifests for carrier {carrier_name}: {e}")
            return []
    
    def get_manifests_by_time(self, date: str, manifest_time: str) -> List[Manifest]:
        """Get all manifests for a specific time on a date.
        
        Args:
            date: Date in YYYY-MM-DD format
            manifest_time: Time in HH:MM format
            
        Returns:
            List of manifests for the time
        """
        try:
            manifests = self.load_manifests(date)
            return [m for m in manifests if m.time == manifest_time]
        except Exception as e:
            self.logger.error(f"Failed to get manifests for time {manifest_time}: {e}")
            return []
    
    def _validate_manifest(self, manifest: Manifest) -> None:
        """Validate a single manifest.
        
        Args:
            manifest: Manifest to validate
            
        Raises:
            DataValidationException: If manifest is invalid
        """
        if not manifest.name or not manifest.name.strip():
            raise DataValidationException("Manifest name cannot be empty")
        
        if not manifest.time:
            raise DataValidationException("Manifest time cannot be empty")
        
        # Validate time format
        try:
            time.fromisoformat(manifest.time)
        except ValueError:
            raise DataValidationException(f"Invalid time format: {manifest.time}")
        
        # Validate carriers
        if not manifest.carriers or len(manifest.carriers) == 0:
            raise DataValidationException("Manifest must have at least one carrier")
        
        for carrier in manifest.carriers:
            if not carrier.name or not carrier.name.strip():
                raise DataValidationException("Carrier name cannot be empty")
    
    def _create_missing_carrier_alert(self, date: str, manifest_time: str, 
                                    carrier: Carrier, detected_at: datetime) -> Alert:
        """Create an alert for a missing carrier.
        
        Args:
            date: Date of the manifest
            manifest_time: Time of the manifest
            carrier: Missing carrier
            detected_at: When the missing carrier was detected
            
        Returns:
            Alert object for the missing carrier
        """
        return Alert(
            id=f"missing_{carrier.name}_{date}_{manifest_time}",
            title=f"Missing Manifest: {carrier.name}",
            message=f"{carrier.name} manifest is missing for {manifest_time} on {date}",
            priority=AlertPriority.HIGH,
            status=AlertStatus.ACTIVE,
            created_at=detected_at,
            manifest_date=date,
            manifest_time=manifest_time,
            carrier_name=carrier.name,
            requires_acknowledgment=True
        )
