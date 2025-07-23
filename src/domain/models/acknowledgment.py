"""
Acknowledgment domain model.

Represents an acknowledgment record with user, timestamp, and reason information.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from ...infrastructure.exceptions.custom_exceptions import DataValidationException


@dataclass
class Acknowledgment:
    """
    Represents an acknowledgment record for a manifest or carrier.
    
    Tracks who acknowledged something, when it was acknowledged,
    and the reason for the acknowledgment.
    """
    
    user: str
    timestamp: datetime
    reason: str = ""
    entity_type: str = ""  # "manifest" or "carrier"
    entity_id: str = ""    # Name/ID of the acknowledged entity
    
    def __post_init__(self):
        """Validate the acknowledgment data after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate acknowledgment data and raise exceptions for invalid data."""
        # Validate user
        if not self.user or not isinstance(self.user, str):
            raise DataValidationException(
                "User must be a non-empty string",
                field_name="user",
                invalid_value=self.user
            )
        
        if not self.user.strip():
            raise DataValidationException(
                "User cannot be empty or whitespace only",
                field_name="user",
                invalid_value=self.user
            )
        
        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            raise DataValidationException(
                "Timestamp must be a datetime object",
                field_name="timestamp",
                invalid_value=type(self.timestamp).__name__
            )
        
        # Validate reason (can be empty)
        if self.reason is not None and not isinstance(self.reason, str):
            raise DataValidationException(
                "Reason must be a string",
                field_name="reason",
                invalid_value=type(self.reason).__name__
            )
        
        # Validate entity_type
        if self.entity_type is not None and not isinstance(self.entity_type, str):
            raise DataValidationException(
                "Entity type must be a string",
                field_name="entity_type",
                invalid_value=type(self.entity_type).__name__
            )
        
        # Validate entity_id
        if self.entity_id is not None and not isinstance(self.entity_id, str):
            raise DataValidationException(
                "Entity ID must be a string",
                field_name="entity_id",
                invalid_value=type(self.entity_id).__name__
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Acknowledgment':
        """
        Create an Acknowledgment from dictionary data (e.g., from JSON).
        
        Args:
            data: Dictionary containing acknowledgment data
            
        Returns:
            Acknowledgment instance
            
        Raises:
            DataValidationException: If data is invalid
        """
        try:
            # Handle timestamp conversion
            timestamp_data = data['timestamp']
            if isinstance(timestamp_data, str):
                try:
                    # Try ISO format first
                    timestamp = datetime.fromisoformat(timestamp_data.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        # Try common format
                        timestamp = datetime.strptime(timestamp_data, "%Y-%m-%d %H:%M:%S")
                    except ValueError as e:
                        raise DataValidationException(
                            f"Invalid timestamp format: {timestamp_data}",
                            field_name="timestamp",
                            invalid_value=timestamp_data,
                            cause=e
                        )
            elif isinstance(timestamp_data, datetime):
                timestamp = timestamp_data
            else:
                raise DataValidationException(
                    "Timestamp must be a string or datetime object",
                    field_name="timestamp",
                    invalid_value=type(timestamp_data).__name__
                )
            
            return cls(
                user=data['user'],
                timestamp=timestamp,
                reason=data.get('reason', ""),
                entity_type=data.get('entity_type', ""),
                entity_id=data.get('entity_id', "")
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
                f"Failed to create acknowledgment from data: {e}",
                cause=e
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert acknowledgment to dictionary (for JSON serialization).
        
        Returns:
            Dictionary representation of the acknowledgment
        """
        return {
            'user': self.user,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id
        }
    
    def get_formatted_timestamp(self, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Get formatted timestamp string.
        
        Args:
            format_string: strftime format string
            
        Returns:
            Formatted timestamp string
        """
        return self.timestamp.strftime(format_string)
    
    def get_time_since_acknowledgment(self, current_time: Optional[datetime] = None) -> float:
        """
        Get time elapsed since acknowledgment in seconds.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Seconds elapsed since acknowledgment
        """
        if current_time is None:
            current_time = datetime.now()
        
        return (current_time - self.timestamp).total_seconds()
    
    def is_recent(self, threshold_minutes: int = 5, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the acknowledgment is recent (within threshold).
        
        Args:
            threshold_minutes: Threshold in minutes for considering "recent"
            current_time: Current time (defaults to now)
            
        Returns:
            True if acknowledgment is recent
        """
        elapsed_seconds = self.get_time_since_acknowledgment(current_time)
        return elapsed_seconds <= (threshold_minutes * 60)
    
    def has_reason(self) -> bool:
        """Check if the acknowledgment has a reason."""
        return bool(self.reason and self.reason.strip())
    
    def get_display_reason(self) -> str:
        """Get display-friendly reason (or default text if no reason)."""
        if self.has_reason():
            return self.reason
        return "No reason provided"
    
    def get_summary(self) -> str:
        """Get a summary string of the acknowledgment."""
        time_str = self.get_formatted_timestamp("%m/%d %H:%M")
        if self.has_reason():
            return f"Acknowledged by {self.user} at {time_str}: {self.reason}"
        else:
            return f"Acknowledged by {self.user} at {time_str}"
    
    def matches_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Check if this acknowledgment matches the given entity.
        
        Args:
            entity_type: Type of entity to match
            entity_id: ID of entity to match
            
        Returns:
            True if acknowledgment matches the entity
        """
        return (self.entity_type == entity_type and 
                self.entity_id == entity_id)
    
    def __str__(self) -> str:
        """Return string representation of the acknowledgment."""
        return f"Acknowledgment({self.user}, {self.timestamp.strftime('%m/%d %H:%M')})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the acknowledgment."""
        return (f"Acknowledgment(user='{self.user}', "
                f"timestamp={self.timestamp}, reason='{self.reason}', "
                f"entity_type='{self.entity_type}', entity_id='{self.entity_id}')")
    
    def __eq__(self, other) -> bool:
        """Check equality based on all fields."""
        if not isinstance(other, Acknowledgment):
            return False
        return (self.user == other.user and 
                self.timestamp == other.timestamp and
                self.reason == other.reason and
                self.entity_type == other.entity_type and
                self.entity_id == other.entity_id)
    
    def __hash__(self) -> int:
        """Return hash based on user, timestamp, and entity."""
        return hash((self.user, self.timestamp, self.entity_type, self.entity_id))