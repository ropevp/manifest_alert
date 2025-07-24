"""
Acknowledgment Service - Business logic for acknowledgment operations.

Handles carrier and manifest acknowledgments, validation, and coordination
with repository layer for persistence.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from ...domain.models.manifest import Manifest
from ...domain.models.carrier import Carrier
from ...domain.models.acknowledgment import Acknowledgment
from ...infrastructure.repositories.acknowledgment_repository import AcknowledgmentRepository
from ...infrastructure.exceptions import BusinessLogicException, DataValidationException


class AcknowledgmentService:
    """Service for managing acknowledgment business logic.
    
    This service handles:
    - Single carrier acknowledgments
    - Full manifest acknowledgments
    - Acknowledgment validation and persistence
    - Acknowledgment history and reporting
    """
    
    def __init__(self,
                 acknowledgment_repository: AcknowledgmentRepository,
                 logger: Optional[logging.Logger] = None):
        """Initialize the acknowledgment service.
        
        Args:
            acknowledgment_repository: Repository for acknowledgment data
            logger: Optional logger instance
        """
        self.acknowledgment_repository = acknowledgment_repository
        self.logger = logger or logging.getLogger(__name__)
        
        self.logger.info("AcknowledgmentService initialized")
    
    def acknowledge_carrier(self, manifest: Manifest, carrier_name: str, 
                          user: str, reason: Optional[str] = None,
                          timestamp: Optional[datetime] = None) -> bool:
        """Acknowledge a specific carrier in a manifest.
        
        Args:
            manifest: Manifest containing the carrier
            carrier_name: Name of carrier to acknowledge
            user: User making the acknowledgment
            reason: Optional reason for acknowledgment
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            True if acknowledgment was successful
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # Validate inputs
            self._validate_acknowledgment_inputs(manifest, user, carrier_name)
            
            # Find the carrier
            carrier = manifest.get_carrier(carrier_name)
            if not carrier:
                raise DataValidationException(
                    f"Carrier '{carrier_name}' not found in manifest {manifest.time}",
                    field="carrier_name",
                    value=carrier_name
                )
            
            # Check if already acknowledged
            if carrier.is_acknowledged():
                self.logger.warning(f"Carrier {carrier_name} in {manifest.time} already acknowledged")
                return True  # Consider this success
            
            # Create acknowledgment record
            acknowledgment = Acknowledgment(
                date=manifest.date,
                manifest_time=manifest.time,
                carrier=carrier_name,
                user=user,
                reason=reason,
                timestamp=timestamp
            )
            
            # Save acknowledgment to repository
            if not self.acknowledgment_repository.save_acknowledgment(acknowledgment):
                raise BusinessLogicException("Failed to save acknowledgment to repository")
            
            # Update the carrier in the manifest
            carrier.acknowledge(user, reason, timestamp)
            
            # Add acknowledgment to manifest's acknowledgment list
            manifest.acknowledgments.append(acknowledgment)
            
            self.logger.info(f"Acknowledged carrier {carrier_name} in {manifest.time} by {user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error acknowledging carrier {carrier_name}: {e}")
            raise BusinessLogicException(f"Failed to acknowledge carrier: {e}")
    
    def acknowledge_manifest(self, manifest: Manifest, user: str, 
                           reason: Optional[str] = None,
                           timestamp: Optional[datetime] = None) -> bool:
        """Acknowledge all carriers in a manifest.
        
        Args:
            manifest: Manifest to acknowledge
            user: User making the acknowledgment
            reason: Optional reason for acknowledgment
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            True if all carriers were acknowledged successfully
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # Validate inputs
            self._validate_acknowledgment_inputs(manifest, user)
            
            if not manifest.carriers:
                self.logger.warning(f"No carriers to acknowledge in manifest {manifest.time}")
                return True
            
            # Get unacknowledged carriers
            unacknowledged = manifest.get_unacknowledged_carriers()
            if not unacknowledged:
                self.logger.info(f"All carriers already acknowledged in manifest {manifest.time}")
                return True
            
            # Acknowledge each unacknowledged carrier
            success_count = 0
            for carrier in unacknowledged:
                try:
                    if self.acknowledge_carrier(manifest, carrier.name, user, reason, timestamp):
                        success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to acknowledge carrier {carrier.name}: {e}")
                    # Continue with other carriers
            
            # Check if all were acknowledged
            all_acknowledged = success_count == len(unacknowledged)
            
            if all_acknowledged:
                self.logger.info(f"Successfully acknowledged all {success_count} carriers in manifest {manifest.time}")
            else:
                self.logger.warning(f"Only acknowledged {success_count}/{len(unacknowledged)} carriers in manifest {manifest.time}")
            
            return all_acknowledged
            
        except Exception as e:
            self.logger.error(f"Error acknowledging manifest {manifest.time}: {e}")
            raise BusinessLogicException(f"Failed to acknowledge manifest: {e}")
    
    def clear_carrier_acknowledgment(self, manifest: Manifest, carrier_name: str) -> bool:
        """Clear acknowledgment for a specific carrier.
        
        Args:
            manifest: Manifest containing the carrier
            carrier_name: Name of carrier to clear acknowledgment
            
        Returns:
            True if acknowledgment was cleared successfully
        """
        try:
            # Find the carrier
            carrier = manifest.get_carrier(carrier_name)
            if not carrier:
                self.logger.warning(f"Carrier {carrier_name} not found in manifest {manifest.time}")
                return False
            
            if not carrier.is_acknowledged():
                self.logger.info(f"Carrier {carrier_name} in {manifest.time} not acknowledged")
                return True
            
            # Remove acknowledgment from repository
            removed_count = self.acknowledgment_repository.remove_acknowledgment(
                manifest.date, manifest.time, carrier_name
            )
            
            if removed_count > 0:
                # Clear acknowledgment in the carrier
                carrier.clear_acknowledgment()
                
                # Remove from manifest's acknowledgment list
                manifest.acknowledgments = [
                    ack for ack in manifest.acknowledgments
                    if not ack.is_same_carrier(manifest.date, manifest.time, carrier_name)
                ]
                
                self.logger.info(f"Cleared acknowledgment for carrier {carrier_name} in {manifest.time}")
                return True
            else:
                self.logger.warning(f"No acknowledgment found to clear for {carrier_name} in {manifest.time}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error clearing acknowledgment for carrier {carrier_name}: {e}")
            return False
    
    def clear_manifest_acknowledgments(self, manifest: Manifest) -> bool:
        """Clear all acknowledgments for a manifest.
        
        Args:
            manifest: Manifest to clear acknowledgments for
            
        Returns:
            True if acknowledgments were cleared successfully
        """
        try:
            acknowledged_carriers = manifest.get_acknowledged_carriers()
            if not acknowledged_carriers:
                self.logger.info(f"No acknowledgments to clear in manifest {manifest.time}")
                return True
            
            # Clear each acknowledged carrier
            success_count = 0
            for carrier in acknowledged_carriers:
                if self.clear_carrier_acknowledgment(manifest, carrier.name):
                    success_count += 1
            
            all_cleared = success_count == len(acknowledged_carriers)
            
            if all_cleared:
                self.logger.info(f"Cleared all {success_count} acknowledgments in manifest {manifest.time}")
            else:
                self.logger.warning(f"Only cleared {success_count}/{len(acknowledged_carriers)} acknowledgments in manifest {manifest.time}")
            
            return all_cleared
            
        except Exception as e:
            self.logger.error(f"Error clearing acknowledgments for manifest {manifest.time}: {e}")
            return False
    
    def get_acknowledgment_history(self, date: Optional[str] = None, 
                                 manifest_time: Optional[str] = None,
                                 carrier: Optional[str] = None,
                                 user: Optional[str] = None) -> List[Acknowledgment]:
        """Get acknowledgment history with optional filters.
        
        Args:
            date: Optional date filter (YYYY-MM-DD)
            manifest_time: Optional manifest time filter (HH:MM)
            carrier: Optional carrier name filter
            user: Optional user name filter
            
        Returns:
            List of acknowledgment records matching filters
        """
        try:
            if date:
                acknowledgments = self.acknowledgment_repository.get_acknowledgments_for_date(date)
            else:
                acknowledgments = self.acknowledgment_repository.get_all_acknowledgments()
            
            # Apply additional filters
            if manifest_time:
                acknowledgments = [ack for ack in acknowledgments if ack.manifest_time == manifest_time]
            
            if carrier:
                acknowledgments = [ack for ack in acknowledgments if ack.carrier == carrier]
            
            if user:
                acknowledgments = [ack for ack in acknowledgments if ack.user == user]
            
            self.logger.debug(f"Retrieved {len(acknowledgments)} acknowledgments with filters")
            return acknowledgments
            
        except Exception as e:
            self.logger.error(f"Error retrieving acknowledgment history: {e}")
            return []
    
    def get_acknowledgment_statistics(self, date: Optional[str] = None) -> Dict:
        """Get acknowledgment statistics for a date.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary containing acknowledgment statistics
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            acknowledgments = self.get_acknowledgment_history(date=date)
            
            stats = {
                'total_acknowledgments': len(acknowledgments),
                'unique_manifests': len(set(ack.manifest_time for ack in acknowledgments)),
                'unique_carriers': len(set(ack.carrier for ack in acknowledgments)),
                'unique_users': len(set(ack.user for ack in acknowledgments)),
                'acknowledgments_by_user': {},
                'acknowledgments_by_hour': {},
                'late_acknowledgments': 0
            }
            
            # Group by user
            for ack in acknowledgments:
                user = ack.user
                if user not in stats['acknowledgments_by_user']:
                    stats['acknowledgments_by_user'][user] = 0
                stats['acknowledgments_by_user'][user] += 1
            
            # Group by hour
            for ack in acknowledgments:
                hour = ack.timestamp.hour
                if hour not in stats['acknowledgments_by_hour']:
                    stats['acknowledgments_by_hour'][hour] = 0
                stats['acknowledgments_by_hour'][hour] += 1
            
            # Count late acknowledgments (acknowledged after manifest time + 30 minutes)
            for ack in acknowledgments:
                try:
                    manifest_datetime = datetime.strptime(f"{ack.date} {ack.manifest_time}", "%Y-%m-%d %H:%M")
                    deadline = manifest_datetime + timedelta(minutes=30)
                    if ack.timestamp > deadline:
                        stats['late_acknowledgments'] += 1
                except:
                    pass
            
            self.logger.debug(f"Generated acknowledgment statistics: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating acknowledgment statistics: {e}")
            return {
                'total_acknowledgments': 0,
                'unique_manifests': 0,
                'unique_carriers': 0,
                'unique_users': 0,
                'acknowledgments_by_user': {},
                'acknowledgments_by_hour': {},
                'late_acknowledgments': 0
            }
    
    def is_acknowledgment_late(self, acknowledgment: Acknowledgment) -> bool:
        """Check if an acknowledgment was made late (after deadline).
        
        Args:
            acknowledgment: Acknowledgment to check
            
        Returns:
            True if acknowledgment was late
        """
        try:
            # Calculate manifest deadline (manifest time + 30 minutes)
            manifest_datetime = datetime.strptime(
                f"{acknowledgment.date} {acknowledgment.manifest_time}", 
                "%Y-%m-%d %H:%M"
            )
            deadline = manifest_datetime + timedelta(minutes=30)
            
            return acknowledgment.timestamp > deadline
            
        except Exception as e:
            self.logger.warning(f"Error checking if acknowledgment is late: {e}")
            return False
    
    def _validate_acknowledgment_inputs(self, manifest: Manifest, user: str, 
                                      carrier_name: Optional[str] = None) -> None:
        """Validate inputs for acknowledgment operations.
        
        Args:
            manifest: Manifest to validate
            user: User name to validate
            carrier_name: Optional carrier name to validate
            
        Raises:
            DataValidationException: If validation fails
        """
        if not manifest:
            raise DataValidationException(
                "Manifest cannot be None",
                field="manifest",
                value="None"
            )
        
        if not user or not user.strip():
            raise DataValidationException(
                "User name cannot be empty",
                field="user",
                value=user
            )
        
        if carrier_name is not None and (not carrier_name or not carrier_name.strip()):
            raise DataValidationException(
                "Carrier name cannot be empty when specified",
                field="carrier_name",
                value=carrier_name
            )
