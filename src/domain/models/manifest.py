"""
Manifest domain model.

Represents a manifest time slot with multiple carriers and acknowledgment status.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .acknowledgment import Acknowledgment
    from .carrier import Carrier

from ...infrastructure.exceptions.custom_exceptions import DataValidationException, BusinessLogicException


class ManifestStatus(Enum):
    """Enumeration of possible manifest statuses."""
    PENDING = "pending"
    ACTIVE = "active"
    MISSED = "missed"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Manifest:
    """
    Represents a manifest time slot with carriers and acknowledgment status.
    
    A manifest defines a specific time when carriers need to be ready for pickup.
    It tracks the acknowledgment status and can determine if it should trigger alerts.
    """
    
    name: str
    time: time
    carriers: List['Carrier'] = field(default_factory=list)
    acknowledged: bool = False
    missed: bool = False
    acknowledgment_details: Optional['Acknowledgment'] = None
    
    def __post_init__(self):
        """Validate the manifest data after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate manifest data and raise exceptions for invalid data."""
        # Validate name
        if not self.name or not isinstance(self.name, str):
            raise DataValidationException(
                "Manifest name must be a non-empty string",
                field_name="name",
                invalid_value=self.name
            )
        
        if not self.name.strip():
            raise DataValidationException(
                "Manifest name cannot be empty or whitespace only",
                field_name="name",
                invalid_value=self.name
            )
        
        # Validate time
        if not isinstance(self.time, time):
            raise DataValidationException(
                "Manifest time must be a datetime.time object",
                field_name="time",
                invalid_value=self.time
            )
        
        # Validate carriers
        if not isinstance(self.carriers, list):
            raise DataValidationException(
                "Carriers must be a list",
                field_name="carriers",
                invalid_value=type(self.carriers).__name__
            )
        
        # Validate each carrier
        from .carrier import Carrier
        for i, carrier in enumerate(self.carriers):
            if not isinstance(carrier, Carrier):
                raise DataValidationException(
                    f"Carrier at index {i} must be a Carrier instance",
                    field_name=f"carriers[{i}]",
                    invalid_value=type(carrier).__name__
                )
        
        # Validate acknowledgment consistency
        if self.acknowledged and self.acknowledgment_details is None:
            raise DataValidationException(
                "Acknowledged manifest must have acknowledgment details",
                field_name="acknowledgment_details",
                invalid_value=None
            )
        
        if not self.acknowledged and self.acknowledgment_details is not None:
            raise DataValidationException(
                "Non-acknowledged manifest cannot have acknowledgment details",
                field_name="acknowledged",
                invalid_value=False
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Manifest':
        """
        Create a Manifest from dictionary data (e.g., from JSON).
        
        Args:
            data: Dictionary containing manifest data
            
        Returns:
            Manifest instance
            
        Raises:
            DataValidationException: If data is invalid
        """
        try:
            # Parse time string to time object
            time_str = data.get('time', '')
            if isinstance(time_str, str):
                try:
                    time_obj = datetime.strptime(time_str, "%H:%M").time()
                except ValueError as e:
                    raise DataValidationException(
                        f"Invalid time format: {time_str}. Expected HH:MM format",
                        field_name="time",
                        invalid_value=time_str,
                        cause=e
                    )
            else:
                time_obj = time_str
            
            # Create carrier objects
            from .carrier import Carrier
            carriers_data = data.get('carriers', [])
            carriers = []
            for carrier_name in carriers_data:
                if isinstance(carrier_name, str):
                    carriers.append(Carrier(name=carrier_name))
                elif isinstance(carrier_name, dict):
                    carriers.append(Carrier.from_dict(carrier_name))
                else:
                    carriers.append(carrier_name)  # Assume it's already a Carrier
            
            # Handle acknowledgment details
            from .acknowledgment import Acknowledgment
            ack_details = None
            ack_data = data.get('acknowledgment_details')
            if ack_data and isinstance(ack_data, dict):
                ack_details = Acknowledgment.from_dict(ack_data)
            elif ack_data:
                ack_details = ack_data  # Assume it's already an Acknowledgment
            
            return cls(
                name=data.get('name', f"Manifest {time_str}"),
                time=time_obj,
                carriers=carriers,
                acknowledged=data.get('acknowledged', False),
                missed=data.get('missed', False),
                acknowledgment_details=ack_details
            )
        except KeyError as e:
            raise DataValidationException(
                f"Missing required field: {e}",
                field_name=str(e),
                cause=e
            )
        except Exception as e:
            if isinstance(e, DataValidationException):
                raise
            raise DataValidationException(
                f"Failed to create manifest from data: {e}",
                cause=e
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert manifest to dictionary (for JSON serialization).
        
        Returns:
            Dictionary representation of the manifest
        """
        return {
            'name': self.name,
            'time': self.time.strftime("%H:%M"),
            'carriers': [carrier.to_dict() for carrier in self.carriers],
            'acknowledged': self.acknowledged,
            'missed': self.missed,
            'acknowledgment_details': self.acknowledgment_details.to_dict() if self.acknowledgment_details else None
        }
    
    def acknowledge(self, user: str, reason: str = "", timestamp: Optional[datetime] = None) -> None:
        """
        Acknowledge the manifest.
        
        Args:
            user: User performing the acknowledgment
            reason: Optional reason for acknowledgment
            timestamp: Optional custom timestamp (defaults to now)
            
        Raises:
            BusinessLogicException: If manifest is already acknowledged
        """
        if self.acknowledged:
            raise BusinessLogicException(
                "Manifest is already acknowledged",
                entity_type="manifest",
                entity_id=self.name
            )
        
        from .acknowledgment import Acknowledgment
        self.acknowledged = True
        self.acknowledgment_details = Acknowledgment(
            user=user,
            timestamp=timestamp or datetime.now(),
            reason=reason,
            entity_type="manifest",
            entity_id=self.name
        )
    
    def unacknowledge(self) -> None:
        """Remove acknowledgment from the manifest."""
        self.acknowledged = False
        self.acknowledgment_details = None
    
    def get_status(self, current_time: Optional[datetime] = None) -> ManifestStatus:
        """
        Determine the current status of the manifest.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            ManifestStatus indicating current state
        """
        if self.acknowledged:
            return ManifestStatus.ACKNOWLEDGED
        
        if self.missed:
            return ManifestStatus.MISSED
        
        if current_time is None:
            current_time = datetime.now()
        
        # Convert manifest time to today's datetime for comparison
        today = current_time.date()
        manifest_datetime = datetime.combine(today, self.time)
        
        # Check if it's currently active (within 2 minutes before to 30 minutes after)
        time_diff = (current_time - manifest_datetime).total_seconds() / 60  # minutes
        
        if -2 <= time_diff <= 30:
            return ManifestStatus.ACTIVE
        elif time_diff > 30:
            return ManifestStatus.MISSED
        else:
            return ManifestStatus.PENDING
    
    def is_active(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the manifest should trigger alerts.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if manifest should trigger alerts
        """
        return self.get_status(current_time) == ManifestStatus.ACTIVE
    
    def is_overdue(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the manifest is overdue (missed and not acknowledged).
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if manifest is overdue
        """
        status = self.get_status(current_time)
        return status == ManifestStatus.MISSED and not self.acknowledged
    
    def add_carrier(self, carrier: 'Carrier') -> None:
        """
        Add a carrier to the manifest.
        
        Args:
            carrier: Carrier to add
            
        Raises:
            DataValidationException: If carrier is invalid
            BusinessLogicException: If carrier already exists
        """
        from .carrier import Carrier
        if not isinstance(carrier, Carrier):
            raise DataValidationException(
                "Must provide a Carrier instance",
                field_name="carrier",
                invalid_value=type(carrier).__name__
            )
        
        # Check for duplicate carrier names
        existing_names = [c.name for c in self.carriers]
        if carrier.name in existing_names:
            raise BusinessLogicException(
                f"Carrier '{carrier.name}' already exists in manifest",
                entity_type="carrier",
                entity_id=carrier.name
            )
        
        self.carriers.append(carrier)
    
    def remove_carrier(self, carrier_name: str) -> bool:
        """
        Remove a carrier from the manifest.
        
        Args:
            carrier_name: Name of carrier to remove
            
        Returns:
            True if carrier was removed, False if not found
        """
        original_length = len(self.carriers)
        self.carriers = [c for c in self.carriers if c.name != carrier_name]
        return len(self.carriers) < original_length
    
    def get_carrier(self, carrier_name: str) -> Optional['Carrier']:
        """
        Get a carrier by name.
        
        Args:
            carrier_name: Name of carrier to find
            
        Returns:
            Carrier if found, None otherwise
        """
        for carrier in self.carriers:
            if carrier.name == carrier_name:
                return carrier
        return None
    
    def get_acknowledged_carriers(self) -> List['Carrier']:
        """Get list of acknowledged carriers."""
        return [carrier for carrier in self.carriers if carrier.acknowledged]
    
    def get_unacknowledged_carriers(self) -> List['Carrier']:
        """Get list of unacknowledged carriers."""
        return [carrier for carrier in self.carriers if not carrier.acknowledged]
    
    def has_any_acknowledged_carriers(self) -> bool:
        """Check if any carriers are acknowledged."""
        return any(carrier.acknowledged for carrier in self.carriers)
    
    def has_all_carriers_acknowledged(self) -> bool:
        """Check if all carriers are acknowledged."""
        return len(self.carriers) > 0 and all(carrier.acknowledged for carrier in self.carriers)
    
    def __str__(self) -> str:
        """Return string representation of the manifest."""
        return f"Manifest({self.name} at {self.time.strftime('%H:%M')}, {len(self.carriers)} carriers)"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the manifest."""
        return (f"Manifest(name='{self.name}', time={self.time}, "
                f"carriers={len(self.carriers)}, acknowledged={self.acknowledged}, "
                f"missed={self.missed})")