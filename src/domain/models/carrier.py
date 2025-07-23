"""
Carrier Domain Model

Represents an individual carrier within a manifest time slot.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from ...infrastructure.exceptions import DataValidationException


@dataclass
class Carrier:
    """Represents an individual carrier within a manifest.
    
    A carrier is a shipping company or service (e.g., "Australia Post Metro",
    "DHL Express") that needs to be tracked for a specific manifest time.
    
    Attributes:
        name: The carrier name (e.g., "Australia Post Metro")
        acknowledged: Whether this carrier has been acknowledged
        acknowledged_by: User who acknowledged this carrier
        acknowledged_at: Timestamp when carrier was acknowledged
        acknowledgment_reason: Reason for acknowledgment (optional)
    """
    
    name: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledgment_reason: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate carrier data after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate carrier fields."""
        if not self.name or not self.name.strip():
            raise DataValidationException(
                "Carrier name cannot be empty",
                field="name",
                value=str(self.name)
            )
        
        # Normalize the name
        self.name = self.name.strip()
        
        # Validate acknowledgment consistency
        if self.acknowledged:
            if not self.acknowledged_by:
                raise DataValidationException(
                    "Acknowledged carrier must have acknowledged_by field",
                    field="acknowledged_by",
                    value=None
                )
            if not self.acknowledged_at:
                raise DataValidationException(
                    "Acknowledged carrier must have acknowledged_at timestamp",
                    field="acknowledged_at", 
                    value=None
                )
        else:
            # If not acknowledged, clear acknowledgment fields
            self.acknowledged_by = None
            self.acknowledged_at = None
            self.acknowledgment_reason = None
    
    def acknowledge(self, user: str, reason: Optional[str] = None) -> None:
        """Acknowledge this carrier.
        
        Args:
            user: The user acknowledging the carrier
            reason: Optional reason for acknowledgment
            
        Raises:
            DataValidationException: If user is empty
        """
        if not user or not user.strip():
            raise DataValidationException(
                "User cannot be empty for acknowledgment",
                field="user",
                value=str(user)
            )
        
        self.acknowledged = True
        self.acknowledged_by = user.strip()
        self.acknowledged_at = datetime.now()
        self.acknowledgment_reason = reason.strip() if reason else None
    
    def clear_acknowledgment(self) -> None:
        """Clear the acknowledgment for this carrier."""
        self.acknowledged = False
        self.acknowledged_by = None
        self.acknowledged_at = None
        self.acknowledgment_reason = None
    
    def is_acknowledged(self) -> bool:
        """Check if this carrier is acknowledged.
        
        Returns:
            True if the carrier has been acknowledged
        """
        return self.acknowledged
    
    def get_acknowledgment_summary(self) -> Optional[str]:
        """Get a summary of the acknowledgment details.
        
        Returns:
            String summary of acknowledgment, or None if not acknowledged
        """
        if not self.acknowledged:
            return None
        
        summary = f"Acknowledged by {self.acknowledged_by}"
        if self.acknowledged_at:
            summary += f" at {self.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S')}"
        if self.acknowledgment_reason:
            summary += f" (Reason: {self.acknowledgment_reason})"
        
        return summary
    
    def to_dict(self) -> dict:
        """Convert carrier to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "name": self.name,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledgment_reason": self.acknowledgment_reason
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Carrier':
        """Create carrier from dictionary representation.
        
        Args:
            data: Dictionary containing carrier data
            
        Returns:
            Carrier instance
            
        Raises:
            DataValidationException: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise DataValidationException(
                "Carrier data must be a dictionary",
                field="data",
                value=str(type(data))
            )
        
        if "name" not in data:
            raise DataValidationException(
                "Carrier data must contain 'name' field",
                field="name",
                value="missing"
            )
        
        # Parse acknowledged_at timestamp if present
        acknowledged_at = None
        if data.get("acknowledged_at"):
            try:
                acknowledged_at = datetime.fromisoformat(data["acknowledged_at"])
            except (ValueError, TypeError) as e:
                raise DataValidationException(
                    f"Invalid acknowledged_at timestamp: {e}",
                    field="acknowledged_at",
                    value=str(data.get("acknowledged_at"))
                )
        
        return cls(
            name=data["name"],
            acknowledged=data.get("acknowledged", False),
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=acknowledged_at,
            acknowledgment_reason=data.get("acknowledgment_reason")
        )
    
    def __str__(self) -> str:
        """String representation of the carrier."""
        status = "✓" if self.acknowledged else "○"
        return f"{status} {self.name}"
    
    def __repr__(self) -> str:
        """Developer representation of the carrier."""
        return f"Carrier(name='{self.name}', acknowledged={self.acknowledged})"