"""
Carrier domain model.

Represents an individual carrier with name, status, and acknowledgment information.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .acknowledgment import Acknowledgment

from ...infrastructure.exceptions.custom_exceptions import DataValidationException, BusinessLogicException


class CarrierStatus(Enum):
    """Enumeration of possible carrier statuses."""
    PENDING = "pending"
    READY = "ready"
    ACKNOWLEDGED = "acknowledged"
    DELAYED = "delayed"


@dataclass
class Carrier:
    """
    Represents an individual carrier within a manifest.
    
    A carrier is responsible for pickup/delivery and can be individually
    acknowledged with specific user and reason information.
    """
    
    name: str
    status: CarrierStatus = CarrierStatus.PENDING
    acknowledged: bool = False
    acknowledgment_details: Optional['Acknowledgment'] = None
    notes: str = ""
    
    def __post_init__(self):
        """Validate the carrier data after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate carrier data and raise exceptions for invalid data."""
        # Validate name
        if not self.name or not isinstance(self.name, str):
            raise DataValidationException(
                "Carrier name must be a non-empty string",
                field_name="name",
                invalid_value=self.name
            )
        
        if not self.name.strip():
            raise DataValidationException(
                "Carrier name cannot be empty or whitespace only",
                field_name="name",
                invalid_value=self.name
            )
        
        # Validate status
        if not isinstance(self.status, CarrierStatus):
            raise DataValidationException(
                "Carrier status must be a CarrierStatus enum value",
                field_name="status",
                invalid_value=self.status
            )
        
        # Validate acknowledgment consistency
        if self.acknowledged and self.acknowledgment_details is None:
            raise DataValidationException(
                "Acknowledged carrier must have acknowledgment details",
                field_name="acknowledgment_details",
                invalid_value=None
            )
        
        if not self.acknowledged and self.acknowledgment_details is not None:
            raise DataValidationException(
                "Non-acknowledged carrier cannot have acknowledgment details",
                field_name="acknowledged",
                invalid_value=False
            )
        
        # Validate notes
        if self.notes is not None and not isinstance(self.notes, str):
            raise DataValidationException(
                "Carrier notes must be a string",
                field_name="notes",
                invalid_value=type(self.notes).__name__
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Carrier':
        """
        Create a Carrier from dictionary data (e.g., from JSON).
        
        Args:
            data: Dictionary containing carrier data
            
        Returns:
            Carrier instance
            
        Raises:
            DataValidationException: If data is invalid
        """
        try:
            # Handle status conversion
            status_value = data.get('status', 'pending')
            if isinstance(status_value, str):
                try:
                    status = CarrierStatus(status_value.lower())
                except ValueError as e:
                    raise DataValidationException(
                        f"Invalid carrier status: {status_value}",
                        field_name="status",
                        invalid_value=status_value,
                        cause=e
                    )
            else:
                status = status_value
            
            # Handle acknowledgment details
            from .acknowledgment import Acknowledgment
            ack_details = None
            ack_data = data.get('acknowledgment_details')
            if ack_data and isinstance(ack_data, dict):
                ack_details = Acknowledgment.from_dict(ack_data)
            elif ack_data:
                ack_details = ack_data  # Assume it's already an Acknowledgment
            
            return cls(
                name=data['name'],
                status=status,
                acknowledged=data.get('acknowledged', False),
                acknowledgment_details=ack_details,
                notes=data.get('notes', "")
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
                f"Failed to create carrier from data: {e}",
                cause=e
            )
    
    @classmethod
    def from_name(cls, name: str) -> 'Carrier':
        """
        Create a Carrier with just a name (convenience method).
        
        Args:
            name: Carrier name
            
        Returns:
            Carrier instance with default values
        """
        return cls(name=name)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert carrier to dictionary (for JSON serialization).
        
        Returns:
            Dictionary representation of the carrier
        """
        return {
            'name': self.name,
            'status': self.status.value,
            'acknowledged': self.acknowledged,
            'acknowledgment_details': self.acknowledgment_details.to_dict() if self.acknowledgment_details else None,
            'notes': self.notes
        }
    
    def acknowledge(self, user: str, reason: str = "", timestamp: Optional[datetime] = None) -> None:
        """
        Acknowledge the carrier.
        
        Args:
            user: User performing the acknowledgment
            reason: Optional reason for acknowledgment
            timestamp: Optional custom timestamp (defaults to now)
            
        Raises:
            BusinessLogicException: If carrier is already acknowledged
        """
        if self.acknowledged:
            raise BusinessLogicException(
                f"Carrier '{self.name}' is already acknowledged",
                entity_type="carrier",
                entity_id=self.name
            )
        
        from .acknowledgment import Acknowledgment
        self.acknowledged = True
        self.status = CarrierStatus.ACKNOWLEDGED
        self.acknowledgment_details = Acknowledgment(
            user=user,
            timestamp=timestamp or datetime.now(),
            reason=reason,
            entity_type="carrier",
            entity_id=self.name
        )
    
    def unacknowledge(self) -> None:
        """Remove acknowledgment from the carrier."""
        self.acknowledged = False
        self.acknowledgment_details = None
        # Reset status to pending unless it was specifically set to something else
        if self.status == CarrierStatus.ACKNOWLEDGED:
            self.status = CarrierStatus.PENDING
    
    def set_status(self, status: CarrierStatus) -> None:
        """
        Set the carrier status.
        
        Args:
            status: New status for the carrier
            
        Raises:
            DataValidationException: If status is invalid
            BusinessLogicException: If status change is not allowed
        """
        if not isinstance(status, CarrierStatus):
            raise DataValidationException(
                "Status must be a CarrierStatus enum value",
                field_name="status",
                invalid_value=status
            )
        
        # Check for invalid status transitions
        if self.acknowledged and status != CarrierStatus.ACKNOWLEDGED:
            raise BusinessLogicException(
                "Cannot change status of acknowledged carrier (unacknowledge first)",
                entity_type="carrier",
                entity_id=self.name
            )
        
        self.status = status
    
    def add_note(self, note: str) -> None:
        """
        Add a note to the carrier.
        
        Args:
            note: Note to add
        """
        if not isinstance(note, str):
            raise DataValidationException(
                "Note must be a string",
                field_name="note",
                invalid_value=type(note).__name__
            )
        
        if self.notes:
            self.notes += f"\n{note}"
        else:
            self.notes = note
    
    def clear_notes(self) -> None:
        """Clear all notes from the carrier."""
        self.notes = ""
    
    def is_ready(self) -> bool:
        """Check if the carrier is ready for pickup."""
        return self.status in [CarrierStatus.READY, CarrierStatus.ACKNOWLEDGED]
    
    def is_delayed(self) -> bool:
        """Check if the carrier is delayed."""
        return self.status == CarrierStatus.DELAYED
    
    def is_pending(self) -> bool:
        """Check if the carrier is still pending."""
        return self.status == CarrierStatus.PENDING
    
    def get_display_name(self) -> str:
        """Get a display-friendly name for the carrier."""
        return self.name
    
    def get_status_display(self) -> str:
        """Get a display-friendly status string."""
        status_map = {
            CarrierStatus.PENDING: "Pending",
            CarrierStatus.READY: "Ready",
            CarrierStatus.ACKNOWLEDGED: "Acknowledged",
            CarrierStatus.DELAYED: "Delayed"
        }
        return status_map.get(self.status, self.status.value.title())
    
    def __str__(self) -> str:
        """Return string representation of the carrier."""
        return f"Carrier({self.name}, {self.status.value})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the carrier."""
        return (f"Carrier(name='{self.name}', status={self.status}, "
                f"acknowledged={self.acknowledged})")
    
    def __eq__(self, other) -> bool:
        """Check equality based on carrier name."""
        if not isinstance(other, Carrier):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        """Return hash based on carrier name."""
        return hash(self.name)