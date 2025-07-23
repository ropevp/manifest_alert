"""
Acknowledgment Domain Model

Represents an individual acknowledgment record for tracking user actions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ...infrastructure.exceptions import DataValidationException


@dataclass
class Acknowledgment:
    """Represents an individual acknowledgment record.
    
    This model tracks when a user acknowledges a specific carrier for a
    specific manifest time, including the user, timestamp, and reason.
    
    Attributes:
        date: The date of the manifest (YYYY-MM-DD format)
        manifest_time: The time of the manifest (HH:MM format)
        carrier: The name of the carrier being acknowledged
        user: The user who made the acknowledgment
        reason: Optional reason for the acknowledgment
        timestamp: Precise timestamp when acknowledgment was made
    """
    
    date: str
    manifest_time: str
    carrier: str
    user: str
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate acknowledgment data after initialization."""
        # Set timestamp if not provided
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate acknowledgment fields."""
        # Validate date format (YYYY-MM-DD)
        if not self.date:
            raise DataValidationException(
                "Date cannot be empty",
                field="date",
                value=str(self.date)
            )
        
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError as e:
            raise DataValidationException(
                f"Invalid date format. Expected YYYY-MM-DD: {e}",
                field="date",
                value=self.date
            )
        
        # Validate manifest_time format (HH:MM)
        if not self.manifest_time:
            raise DataValidationException(
                "Manifest time cannot be empty",
                field="manifest_time",
                value=str(self.manifest_time)
            )
        
        try:
            # Validate time format and range
            time_obj = datetime.strptime(self.manifest_time, "%H:%M")
            hour = time_obj.hour
            minute = time_obj.minute
            
            if not (0 <= hour <= 23):
                raise ValueError(f"Hour must be between 0-23, got {hour}")
            if not (0 <= minute <= 59):
                raise ValueError(f"Minute must be between 0-59, got {minute}")
                
        except ValueError as e:
            raise DataValidationException(
                f"Invalid manifest time format. Expected HH:MM: {e}",
                field="manifest_time",
                value=self.manifest_time
            )
        
        # Validate carrier name
        if not self.carrier or not self.carrier.strip():
            raise DataValidationException(
                "Carrier name cannot be empty",
                field="carrier",
                value=str(self.carrier)
            )
        
        # Validate user
        if not self.user or not self.user.strip():
            raise DataValidationException(
                "User cannot be empty",
                field="user", 
                value=str(self.user)
            )
        
        # Normalize fields
        self.carrier = self.carrier.strip()
        self.user = self.user.strip()
        if self.reason:
            self.reason = self.reason.strip() or None
    
    def get_manifest_key(self) -> str:
        """Get a unique key identifying the manifest this acknowledgment belongs to.
        
        Returns:
            String key in format "YYYY-MM-DD_HH:MM"
        """
        return f"{self.date}_{self.manifest_time}"
    
    def get_carrier_key(self) -> str:
        """Get a unique key identifying the specific carrier acknowledgment.
        
        Returns:
            String key in format "YYYY-MM-DD_HH:MM_CarrierName"
        """
        return f"{self.get_manifest_key()}_{self.carrier}"
    
    def is_same_manifest(self, other_date: str, other_time: str) -> bool:
        """Check if this acknowledgment is for the same manifest.
        
        Args:
            other_date: Date to compare (YYYY-MM-DD)
            other_time: Time to compare (HH:MM)
            
        Returns:
            True if this acknowledgment is for the same manifest
        """
        return self.date == other_date and self.manifest_time == other_time
    
    def is_same_carrier(self, other_date: str, other_time: str, other_carrier: str) -> bool:
        """Check if this acknowledgment is for the same carrier.
        
        Args:
            other_date: Date to compare (YYYY-MM-DD)
            other_time: Time to compare (HH:MM)
            other_carrier: Carrier name to compare
            
        Returns:
            True if this acknowledgment is for the same carrier
        """
        return (self.is_same_manifest(other_date, other_time) and 
                self.carrier == other_carrier)
    
    def get_formatted_timestamp(self) -> str:
        """Get formatted timestamp string.
        
        Returns:
            Formatted timestamp string (YYYY-MM-DD HH:MM:SS)
        """
        if self.timestamp:
            return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return "Unknown"
    
    def to_dict(self) -> dict:
        """Convert acknowledgment to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "date": self.date,
            "manifest_time": self.manifest_time,
            "carrier": self.carrier,
            "user": self.user,
            "reason": self.reason or "",
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Acknowledgment':
        """Create acknowledgment from dictionary representation.
        
        Args:
            data: Dictionary containing acknowledgment data
            
        Returns:
            Acknowledgment instance
            
        Raises:
            DataValidationException: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise DataValidationException(
                "Acknowledgment data must be a dictionary",
                field="data",
                value=str(type(data))
            )
        
        # Check required fields
        required_fields = ["date", "manifest_time", "carrier", "user"]
        for field in required_fields:
            if field not in data:
                raise DataValidationException(
                    f"Acknowledgment data must contain '{field}' field",
                    field=field,
                    value="missing"
                )
        
        # Parse timestamp if present
        timestamp = None
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError) as e:
                raise DataValidationException(
                    f"Invalid timestamp format: {e}",
                    field="timestamp",
                    value=str(data.get("timestamp"))
                )
        
        return cls(
            date=data["date"],
            manifest_time=data["manifest_time"],
            carrier=data["carrier"],
            user=data["user"],
            reason=data.get("reason") or None,
            timestamp=timestamp
        )
    
    def __str__(self) -> str:
        """String representation of the acknowledgment."""
        reason_part = f" ({self.reason})" if self.reason else ""
        return f"{self.carrier} acknowledged by {self.user}{reason_part}"
    
    def __repr__(self) -> str:
        """Developer representation of the acknowledgment."""
        return (f"Acknowledgment(date='{self.date}', manifest_time='{self.manifest_time}', "
                f"carrier='{self.carrier}', user='{self.user}')")
    
    def __eq__(self, other) -> bool:
        """Check equality with another acknowledgment."""
        if not isinstance(other, Acknowledgment):
            return False
        return (self.date == other.date and 
                self.manifest_time == other.manifest_time and
                self.carrier == other.carrier and
                self.user == other.user)
    
    def __hash__(self) -> int:
        """Generate hash for acknowledgment (for use in sets/dicts)."""
        return hash((self.date, self.manifest_time, self.carrier, self.user))