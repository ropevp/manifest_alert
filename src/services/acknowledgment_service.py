"""
Acknowledgment Service

Business logic service for managing manifest acknowledgments with individual
carrier-level tracking, performance optimization, and data integrity protection.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..domain.models import Acknowledgment, AckType, Manifest, Carrier
from ..infrastructure.repositories import AcknowledgmentRepository, ManifestRepository
from ..infrastructure.exceptions import (
    AcknowledgmentException, 
    DataValidationException,
    NetworkAccessException
)


class AckOperation(Enum):
    """Types of acknowledgment operations."""
    ACKNOWLEDGE = "acknowledge"
    UNACKNOWLEDGE = "unacknowledge" 
    BULK_ACKNOWLEDGE = "bulk_acknowledge"
    BULK_UNACKNOWLEDGE = "bulk_unacknowledge"
    CLEAR_ALL = "clear_all"


@dataclass
class AcknowledgmentResult:
    """Result of an acknowledgment operation."""
    success: bool
    operation: AckOperation
    acknowledged_count: int = 0
    unacknowledged_count: int = 0
    failed_count: int = 0
    failed_items: List[str] = None
    error_message: Optional[str] = None
    operation_time_ms: Optional[float] = None
    
    def __post_init__(self):
        if self.failed_items is None:
            self.failed_items = []


@dataclass
class AckStatistics:
    """Statistics about acknowledgment operations."""
    total_acknowledgments: int = 0
    total_unacknowledgments: int = 0
    bulk_operations: int = 0
    average_operation_time_ms: float = 0.0
    most_acked_manifest: Optional[str] = None
    most_acked_carrier: Optional[str] = None
    cache_hit_rate: float = 0.0
    data_corruption_recoveries: int = 0


@dataclass
class ManifestAckSummary:
    """Summary of acknowledgment status for a manifest."""
    manifest_name: str
    total_carriers: int
    acknowledged_carriers: int
    unacknowledged_carriers: int
    ack_percentage: float
    last_ack_time: Optional[datetime] = None
    last_ack_user: Optional[str] = None


class AcknowledgmentService:
    """Service for managing manifest acknowledgments.
    
    This service provides business logic for acknowledgment operations including:
    - Individual carrier-level acknowledgment tracking
    - High-performance bulk operations with caching
    - Data integrity protection and corruption recovery
    - Cross-PC synchronization via network share
    - Acknowledgment status analysis and reporting
    - Integration with manifest and alert services
    """
    
    def __init__(self, acknowledgment_repository: AcknowledgmentRepository,
                 manifest_repository: Optional[ManifestRepository] = None):
        """Initialize acknowledgment service.
        
        Args:
            acknowledgment_repository: Repository for acknowledgment persistence
            manifest_repository: Optional manifest repository for validation
        """
        self.acknowledgment_repository = acknowledgment_repository
        self.manifest_repository = manifest_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread safety
        self._operation_lock = threading.Lock()
        
        # Statistics tracking
        self._statistics = AckStatistics()
        
        # Performance optimization - cache recent manifest summaries
        self._manifest_summary_cache: Dict[str, ManifestAckSummary] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # 5-minute cache for summaries
        
        self.logger.info("AcknowledgmentService initialized with performance optimization")
    
    def acknowledge_carrier(self, manifest_name: str, carrier_name: str,
                          user: Optional[str] = None, reason: Optional[str] = None) -> AcknowledgmentResult:
        """Acknowledge a specific carrier for a manifest.
        
        Args:
            manifest_name: Name of the manifest
            carrier_name: Name of the carrier to acknowledge
            user: User performing the acknowledgment
            reason: Optional reason for acknowledgment
            
        Returns:
            Result of the acknowledgment operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                # Create acknowledgment
                acknowledgment = Acknowledgment.create(
                    manifest_name=manifest_name,
                    carrier_name=carrier_name,
                    ack_type=AckType.ACKNOWLEDGED,
                    user=user,
                    reason=reason
                )
                
                # Validate acknowledgment if manifest repository available
                if self.manifest_repository:
                    self._validate_acknowledgment(acknowledgment)
                
                # Save acknowledgment
                success = self.acknowledgment_repository.save_acknowledgment(acknowledgment)
                
                if success:
                    # Clear relevant cache entries
                    self._invalidate_cache(manifest_name)
                    
                    # Update statistics
                    self._statistics.total_acknowledgments += 1
                    
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"Acknowledged {carrier_name} for {manifest_name}")
                    
                    return AcknowledgmentResult(
                        success=True,
                        operation=AckOperation.ACKNOWLEDGE,
                        acknowledged_count=1,
                        operation_time_ms=operation_time
                    )
                else:
                    raise AcknowledgmentException("Failed to save acknowledgment")
                    
            except Exception as e:
                error_msg = f"Failed to acknowledge {carrier_name} for {manifest_name}: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return AcknowledgmentResult(
                    success=False,
                    operation=AckOperation.ACKNOWLEDGE,
                    failed_count=1,
                    failed_items=[f"{manifest_name}:{carrier_name}"],
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def unacknowledge_carrier(self, manifest_name: str, carrier_name: str,
                            user: Optional[str] = None) -> AcknowledgmentResult:
        """Remove acknowledgment for a specific carrier.
        
        Args:
            manifest_name: Name of the manifest
            carrier_name: Name of the carrier to unacknowledge
            user: User performing the operation
            
        Returns:
            Result of the unacknowledgment operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                # Remove acknowledgment
                success = self.acknowledgment_repository.remove_acknowledgment(
                    manifest_name, carrier_name
                )
                
                if success:
                    # Clear relevant cache entries
                    self._invalidate_cache(manifest_name)
                    
                    # Update statistics
                    self._statistics.total_unacknowledgments += 1
                    
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"Unacknowledged {carrier_name} for {manifest_name}")
                    
                    return AcknowledgmentResult(
                        success=True,
                        operation=AckOperation.UNACKNOWLEDGE,
                        unacknowledged_count=1,
                        operation_time_ms=operation_time
                    )
                else:
                    # Not an error if acknowledgment didn't exist
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    return AcknowledgmentResult(
                        success=True,
                        operation=AckOperation.UNACKNOWLEDGE,
                        unacknowledged_count=0,
                        operation_time_ms=operation_time
                    )
                    
            except Exception as e:
                error_msg = f"Failed to unacknowledge {carrier_name} for {manifest_name}: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return AcknowledgmentResult(
                    success=False,
                    operation=AckOperation.UNACKNOWLEDGE,
                    failed_count=1,
                    failed_items=[f"{manifest_name}:{carrier_name}"],
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def bulk_acknowledge_manifest(self, manifest_name: str, 
                                carrier_names: Optional[List[str]] = None,
                                user: Optional[str] = None, 
                                reason: Optional[str] = None) -> AcknowledgmentResult:
        """Acknowledge multiple carriers for a manifest.
        
        Args:
            manifest_name: Name of the manifest
            carrier_names: List of carrier names (None for all carriers)
            user: User performing the operation
            reason: Optional reason for acknowledgment
            
        Returns:
            Result of the bulk acknowledgment operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                # Get carrier list if not provided
                if carrier_names is None:
                    if self.manifest_repository:
                        manifest = self.manifest_repository.get_manifest_by_name(manifest_name)
                        if manifest:
                            carrier_names = [c.name for c in manifest.carriers]
                        else:
                            raise AcknowledgmentException(f"Manifest not found: {manifest_name}")
                    else:
                        raise AcknowledgmentException("Cannot bulk acknowledge without carrier list or manifest repository")
                
                # Perform bulk acknowledgment
                acknowledged_count = 0
                failed_count = 0
                failed_items = []
                
                for carrier_name in carrier_names:
                    try:
                        acknowledgment = Acknowledgment.create(
                            manifest_name=manifest_name,
                            carrier_name=carrier_name,
                            ack_type=AckType.ACKNOWLEDGED,
                            user=user,
                            reason=reason
                        )
                        
                        success = self.acknowledgment_repository.save_acknowledgment(acknowledgment)
                        if success:
                            acknowledged_count += 1
                        else:
                            failed_count += 1
                            failed_items.append(f"{manifest_name}:{carrier_name}")
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to acknowledge {carrier_name}: {e}")
                        failed_count += 1
                        failed_items.append(f"{manifest_name}:{carrier_name}")
                
                # Clear cache
                self._invalidate_cache(manifest_name)
                
                # Update statistics
                self._statistics.total_acknowledgments += acknowledged_count
                self._statistics.bulk_operations += 1
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self.logger.info(f"Bulk acknowledged {acknowledged_count} carriers for {manifest_name}")
                
                return AcknowledgmentResult(
                    success=failed_count == 0,
                    operation=AckOperation.BULK_ACKNOWLEDGE,
                    acknowledged_count=acknowledged_count,
                    failed_count=failed_count,
                    failed_items=failed_items,
                    operation_time_ms=operation_time
                )
                
            except Exception as e:
                error_msg = f"Failed bulk acknowledge for {manifest_name}: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return AcknowledgmentResult(
                    success=False,
                    operation=AckOperation.BULK_ACKNOWLEDGE,
                    failed_count=len(carrier_names or []),
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def bulk_unacknowledge_manifest(self, manifest_name: str) -> AcknowledgmentResult:
        """Remove all acknowledgments for a manifest.
        
        Args:
            manifest_name: Name of the manifest
            
        Returns:
            Result of the bulk unacknowledgment operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                # Get current acknowledgments for the manifest
                acknowledgments = self.acknowledgment_repository.get_acknowledgments_for_manifest(manifest_name)
                initial_count = len(acknowledgments)
                
                # Remove all acknowledgments for the manifest
                success = self.acknowledgment_repository.clear_manifest_acknowledgments(manifest_name)
                
                if success:
                    # Clear cache
                    self._invalidate_cache(manifest_name)
                    
                    # Update statistics
                    self._statistics.total_unacknowledgments += initial_count
                    self._statistics.bulk_operations += 1
                    
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"Bulk unacknowledged {initial_count} carriers for {manifest_name}")
                    
                    return AcknowledgmentResult(
                        success=True,
                        operation=AckOperation.BULK_UNACKNOWLEDGE,
                        unacknowledged_count=initial_count,
                        operation_time_ms=operation_time
                    )
                else:
                    raise AcknowledgmentException("Failed to clear manifest acknowledgments")
                    
            except Exception as e:
                error_msg = f"Failed bulk unacknowledge for {manifest_name}: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return AcknowledgmentResult(
                    success=False,
                    operation=AckOperation.BULK_UNACKNOWLEDGE,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def is_carrier_acknowledged(self, manifest_name: str, carrier_name: str) -> bool:
        """Check if a specific carrier is acknowledged.
        
        Args:
            manifest_name: Name of the manifest
            carrier_name: Name of the carrier
            
        Returns:
            True if carrier is acknowledged
        """
        try:
            acknowledgment = self.acknowledgment_repository.get_acknowledgment(
                manifest_name, carrier_name
            )
            return acknowledgment is not None and acknowledgment.is_acknowledged()
        except Exception as e:
            self.logger.warning(f"Failed to check acknowledgment status: {e}")
            return False
    
    def get_manifest_acknowledgment_summary(self, manifest_name: str, 
                                          use_cache: bool = True) -> Optional[ManifestAckSummary]:
        """Get acknowledgment summary for a manifest.
        
        Args:
            manifest_name: Name of the manifest
            use_cache: Whether to use cached summary
            
        Returns:
            Acknowledgment summary or None if manifest not found
        """
        try:
            # Check cache first
            if use_cache and manifest_name in self._manifest_summary_cache:
                cache_time = self._cache_expiry.get(manifest_name)
                if cache_time and datetime.now() < cache_time:
                    return self._manifest_summary_cache[manifest_name]
            
            # Get manifest information
            if not self.manifest_repository:
                return None
                
            manifest = self.manifest_repository.get_manifest_by_name(manifest_name)
            if not manifest:
                return None
            
            # Get acknowledgments for the manifest
            acknowledgments = self.acknowledgment_repository.get_acknowledgments_for_manifest(manifest_name)
            acknowledged_carriers = {ack.carrier_name for ack in acknowledgments if ack.is_acknowledged()}
            
            # Calculate summary
            total_carriers = len(manifest.carriers)
            acknowledged_count = len(acknowledged_carriers)
            unacknowledged_count = total_carriers - acknowledged_count
            ack_percentage = (acknowledged_count / total_carriers * 100) if total_carriers > 0 else 0.0
            
            # Find latest acknowledgment
            latest_ack = None
            for ack in acknowledgments:
                if ack.is_acknowledged() and (latest_ack is None or ack.timestamp > latest_ack.timestamp):
                    latest_ack = ack
            
            summary = ManifestAckSummary(
                manifest_name=manifest_name,
                total_carriers=total_carriers,
                acknowledged_carriers=acknowledged_count,
                unacknowledged_carriers=unacknowledged_count,
                ack_percentage=ack_percentage,
                last_ack_time=latest_ack.timestamp if latest_ack else None,
                last_ack_user=latest_ack.user if latest_ack else None
            )
            
            # Cache the summary
            self._manifest_summary_cache[manifest_name] = summary
            self._cache_expiry[manifest_name] = datetime.now() + self._cache_ttl
            
            return summary
            
        except Exception as e:
            self.logger.warning(f"Failed to get acknowledgment summary for {manifest_name}: {e}")
            return None
    
    def get_unacknowledged_carriers(self, manifest_name: str) -> List[str]:
        """Get list of unacknowledged carriers for a manifest.
        
        Args:
            manifest_name: Name of the manifest
            
        Returns:
            List of unacknowledged carrier names
        """
        try:
            if not self.manifest_repository:
                return []
                
            manifest = self.manifest_repository.get_manifest_by_name(manifest_name)
            if not manifest:
                return []
            
            # Get acknowledged carriers
            acknowledgments = self.acknowledgment_repository.get_acknowledgments_for_manifest(manifest_name)
            acknowledged_carriers = {ack.carrier_name for ack in acknowledgments if ack.is_acknowledged()}
            
            # Return unacknowledged carriers
            all_carriers = {c.name for c in manifest.carriers}
            unacknowledged = list(all_carriers - acknowledged_carriers)
            
            return sorted(unacknowledged)
            
        except Exception as e:
            self.logger.warning(f"Failed to get unacknowledged carriers for {manifest_name}: {e}")
            return []
    
    def get_acknowledged_carriers(self, manifest_name: str) -> List[str]:
        """Get list of acknowledged carriers for a manifest.
        
        Args:
            manifest_name: Name of the manifest
            
        Returns:
            List of acknowledged carrier names
        """
        try:
            acknowledgments = self.acknowledgment_repository.get_acknowledgments_for_manifest(manifest_name)
            acknowledged_carriers = [ack.carrier_name for ack in acknowledgments if ack.is_acknowledged()]
            
            return sorted(acknowledged_carriers)
            
        except Exception as e:
            self.logger.warning(f"Failed to get acknowledged carriers for {manifest_name}: {e}")
            return []
    
    def get_all_acknowledgment_summaries(self) -> List[ManifestAckSummary]:
        """Get acknowledgment summaries for all manifests.
        
        Returns:
            List of acknowledgment summaries
        """
        summaries = []
        
        try:
            if not self.manifest_repository:
                return summaries
                
            manifests = self.manifest_repository.get_all_manifests()
            
            for manifest in manifests:
                summary = self.get_manifest_acknowledgment_summary(manifest.name)
                if summary:
                    summaries.append(summary)
                    
        except Exception as e:
            self.logger.warning(f"Failed to get all acknowledgment summaries: {e}")
        
        return summaries
    
    def clear_all_acknowledgments(self, user: Optional[str] = None) -> AcknowledgmentResult:
        """Clear all acknowledgments in the system.
        
        Args:
            user: User performing the operation
            
        Returns:
            Result of the clear operation
        """
        start_time = datetime.now()
        
        with self._operation_lock:
            try:
                # Get count of existing acknowledgments
                initial_count = len(self.acknowledgment_repository.get_all_acknowledgments())
                
                # Clear all acknowledgments
                success = self.acknowledgment_repository.clear_all_acknowledgments()
                
                if success:
                    # Clear all caches
                    self._manifest_summary_cache.clear()
                    self._cache_expiry.clear()
                    
                    # Update statistics
                    self._statistics.total_unacknowledgments += initial_count
                    self._statistics.bulk_operations += 1
                    
                    operation_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"Cleared all {initial_count} acknowledgments")
                    
                    return AcknowledgmentResult(
                        success=True,
                        operation=AckOperation.CLEAR_ALL,
                        unacknowledged_count=initial_count,
                        operation_time_ms=operation_time
                    )
                else:
                    raise AcknowledgmentException("Failed to clear all acknowledgments")
                    
            except Exception as e:
                error_msg = f"Failed to clear all acknowledgments: {e}"
                self.logger.error(error_msg)
                
                operation_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return AcknowledgmentResult(
                    success=False,
                    operation=AckOperation.CLEAR_ALL,
                    error_message=error_msg,
                    operation_time_ms=operation_time
                )
    
    def get_acknowledgment_statistics(self) -> AckStatistics:
        """Get acknowledgment operation statistics.
        
        Returns:
            Statistics about acknowledgment operations
        """
        # Update cache hit rate from repository
        try:
            repo_stats = self.acknowledgment_repository.get_performance_stats()
            self._statistics.cache_hit_rate = repo_stats.get("cache_hit_rate", 0.0)
        except Exception as e:
            self.logger.debug(f"Could not get repository stats: {e}")
        
        return self._statistics
    
    def clear_statistics(self) -> None:
        """Clear acknowledgment operation statistics."""
        self._statistics = AckStatistics()
        self.logger.info("Acknowledgment statistics cleared")
    
    def validate_data_integrity(self) -> Tuple[bool, List[str]]:
        """Validate acknowledgment data integrity.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Get all acknowledgments
            acknowledgments = self.acknowledgment_repository.get_all_acknowledgments()
            
            # Check for duplicate acknowledgments
            seen_keys = set()
            for ack in acknowledgments:
                key = f"{ack.manifest_name}:{ack.carrier_name}"
                if key in seen_keys:
                    issues.append(f"Duplicate acknowledgment: {key}")
                seen_keys.add(key)
            
            # Validate acknowledgment data
            for ack in acknowledgments:
                if not ack.manifest_name or not ack.manifest_name.strip():
                    issues.append(f"Invalid manifest name in acknowledgment: '{ack.manifest_name}'")
                
                if not ack.carrier_name or not ack.carrier_name.strip():
                    issues.append(f"Invalid carrier name in acknowledgment: '{ack.carrier_name}'")
                
                if ack.timestamp > datetime.now() + timedelta(hours=1):
                    issues.append(f"Future timestamp in acknowledgment: {ack.timestamp}")
            
            # Cross-reference with manifests if repository available
            if self.manifest_repository:
                manifests = self.manifest_repository.get_all_manifests()
                manifest_carriers = {}
                
                for manifest in manifests:
                    manifest_carriers[manifest.name] = {c.name for c in manifest.carriers}
                
                for ack in acknowledgments:
                    if ack.manifest_name in manifest_carriers:
                        if ack.carrier_name not in manifest_carriers[ack.manifest_name]:
                            issues.append(f"Acknowledgment for unknown carrier: {ack.manifest_name}:{ack.carrier_name}")
                    else:
                        issues.append(f"Acknowledgment for unknown manifest: {ack.manifest_name}")
            
            self.logger.info(f"Data integrity check completed: {len(issues)} issues found")
            
        except Exception as e:
            issues.append(f"Data integrity check failed: {e}")
            self.logger.error(f"Data integrity validation failed: {e}")
        
        return len(issues) == 0, issues
    
    def repair_data_integrity(self) -> bool:
        """Attempt to repair acknowledgment data integrity issues.
        
        Returns:
            True if repair was successful
        """
        try:
            is_valid, issues = self.validate_data_integrity()
            
            if is_valid:
                self.logger.info("No data integrity issues to repair")
                return True
            
            # Backup current data
            backup_success = self.acknowledgment_repository.backup_data()
            if not backup_success:
                self.logger.warning("Failed to backup data before repair")
            
            # Remove duplicate acknowledgments
            acknowledgments = self.acknowledgment_repository.get_all_acknowledgments()
            seen_keys = set()
            valid_acknowledgments = []
            
            for ack in acknowledgments:
                key = f"{ack.manifest_name}:{ack.carrier_name}"
                
                # Skip duplicates and invalid acknowledgments
                if (key not in seen_keys and 
                    ack.manifest_name and ack.manifest_name.strip() and
                    ack.carrier_name and ack.carrier_name.strip() and
                    ack.timestamp <= datetime.now() + timedelta(hours=1)):
                    
                    seen_keys.add(key)
                    valid_acknowledgments.append(ack)
            
            # Clear all acknowledgments and save valid ones
            self.acknowledgment_repository.clear_all_acknowledgments()
            
            for ack in valid_acknowledgments:
                self.acknowledgment_repository.save_acknowledgment(ack)
            
            # Clear caches
            self._manifest_summary_cache.clear()
            self._cache_expiry.clear()
            
            # Update statistics
            self._statistics.data_corruption_recoveries += 1
            
            self.logger.info(f"Data integrity repaired: {len(valid_acknowledgments)} valid acknowledgments restored")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data integrity repair failed: {e}")
            return False
    
    def _validate_acknowledgment(self, acknowledgment: Acknowledgment) -> None:
        """Validate an acknowledgment against manifest data.
        
        Args:
            acknowledgment: Acknowledgment to validate
            
        Raises:
            DataValidationException: If acknowledgment is invalid
        """
        if not self.manifest_repository:
            return  # Skip validation if no manifest repository
        
        manifest = self.manifest_repository.get_manifest_by_name(acknowledgment.manifest_name)
        if not manifest:
            raise DataValidationException(f"Unknown manifest: {acknowledgment.manifest_name}")
        
        carrier_names = {c.name for c in manifest.carriers}
        if acknowledgment.carrier_name not in carrier_names:
            raise DataValidationException(
                f"Unknown carrier '{acknowledgment.carrier_name}' for manifest '{acknowledgment.manifest_name}'"
            )
    
    def _invalidate_cache(self, manifest_name: str) -> None:
        """Invalidate cache entries for a manifest.
        
        Args:
            manifest_name: Name of the manifest to invalidate
        """
        if manifest_name in self._manifest_summary_cache:
            del self._manifest_summary_cache[manifest_name]
        if manifest_name in self._cache_expiry:
            del self._cache_expiry[manifest_name]
    
    def force_cache_refresh(self) -> None:
        """Force refresh of all acknowledgment caches."""
        self._manifest_summary_cache.clear()
        self._cache_expiry.clear()
        self.logger.info("Acknowledgment caches refreshed")
    
    def get_recent_acknowledgments(self, limit: int = 10) -> List[Acknowledgment]:
        """Get recent acknowledgments ordered by timestamp.
        
        Args:
            limit: Maximum number of acknowledgments to return
            
        Returns:
            List of recent acknowledgments
        """
        try:
            acknowledgments = self.acknowledgment_repository.get_all_acknowledgments()
            
            # Sort by timestamp (newest first)
            acknowledgments.sort(key=lambda x: x.timestamp, reverse=True)
            
            return acknowledgments[:limit]
            
        except Exception as e:
            self.logger.warning(f"Failed to get recent acknowledgments: {e}")
            return []
