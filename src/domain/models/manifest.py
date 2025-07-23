"""
Manifest Domain Model

Represents a manifest time slot with multiple carriers and acknowledgment tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from enum import Enum

from .carrier import Carrier
from .acknowledgment import Acknowledgment
from ...infrastructure.exceptions import DataValidationException


class ManifestStatus(Enum):
    """Enumeration of possible manifest statuses."""
    PENDING = "Pending"      # Manifest time hasn't arrived yet
    ACTIVE = "Active"        # Manifest time is current (within alert window)
    MISSED = "Missed"        # Manifest time has passed without acknowledgment
    ACKNOWLEDGED = "Acknowledged"  # All carriers acknowledged


@dataclass
class Manifest:
    """Represents a manifest time slot with carriers and acknowledgment status.
    
    A manifest represents a specific time when carriers need to be processed.
    It tracks multiple carriers and their individual acknowledgment status.
    
    Attributes:
        time: The manifest time in HH:MM format
        carriers: List of carriers for this manifest
        date: Optional specific date (defaults to today)
        acknowledged: Whether all carriers are acknowledged
        missed: Whether this manifest was missed (time passed without ack)
        acknowledgments: List of acknowledgment records
        alert_window_minutes: How many minutes before/after time to show alert
    """
    
    time: str
    carriers: List[Carrier] = field(default_factory=list)
    date: Optional[str] = None
    acknowledged: bool = False
    missed: bool = False
    acknowledgments: List[Acknowledgment] = field(default_factory=list)
    alert_window_minutes: int = 30
    
    def __post_init__(self) -> None:
        """Validate manifest data after initialization."""
        # Set date to today if not provided
        if self.date is None:
            self.date = datetime.now().strftime("%Y-%m-%d")
        
        self._validate()
        self._update_status()
    
    def _validate(self) -> None:
        """Validate manifest fields."""
        # Validate time format (HH:MM)
        if not self.time:
            raise DataValidationException(
                "Manifest time cannot be empty",
                field="time",
                value=str(self.time)
            )
        
        try:
            # Validate time format and range
            time_obj = datetime.strptime(self.time, "%H:%M")
            hour = time_obj.hour
            minute = time_obj.minute
            
            if not (0 <= hour <= 23):
                raise ValueError(f"Hour must be between 0-23, got {hour}")
            if not (0 <= minute <= 59):
                raise ValueError(f"Minute must be between 0-59, got {minute}")
                
        except ValueError as e:
            raise DataValidationException(
                f"Invalid time format. Expected HH:MM: {e}",
                field="time",
                value=self.time
            )
        
        # Validate date format if provided
        if self.date:
            try:
                datetime.strptime(self.date, "%Y-%m-%d")
            except ValueError as e:
                raise DataValidationException(
                    f"Invalid date format. Expected YYYY-MM-DD: {e}",
                    field="date",
                    value=self.date
                )
        
        # Validate carriers list
        if not isinstance(self.carriers, list):
            raise DataValidationException(
                "Carriers must be a list",
                field="carriers",
                value=str(type(self.carriers))
            )
        
        # Validate alert window
        if not isinstance(self.alert_window_minutes, int) or self.alert_window_minutes < 0:
            raise DataValidationException(
                "Alert window must be a non-negative integer",
                field="alert_window_minutes",
                value=str(self.alert_window_minutes)
            )
    
    def _update_status(self) -> None:
        """Update acknowledgment and missed status based on current state."""
        if not self.carriers:
            self.acknowledged = True
            return
        
        # Check if all carriers are acknowledged
        all_acknowledged = all(carrier.is_acknowledged() for carrier in self.carriers)
        self.acknowledged = all_acknowledged
        
        # Update missed status based on time and acknowledgment
        if not all_acknowledged and self._is_past_deadline():
            self.missed = True
        elif all_acknowledged:
            self.missed = False
    
    def _is_past_deadline(self) -> bool:
        """Check if the manifest deadline has passed."""
        now = datetime.now()
        manifest_datetime = self.get_manifest_datetime()
        deadline = manifest_datetime + timedelta(minutes=self.alert_window_minutes)
        return now > deadline
    
    def get_manifest_datetime(self) -> datetime:
        """Get the full datetime for this manifest.
        
        Returns:
            datetime object representing the manifest time
        """
        date_obj = datetime.strptime(self.date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(self.time, "%H:%M").time()
        return datetime.combine(date_obj, time_obj)
    
    def get_status(self, current_time: Optional[datetime] = None) -> ManifestStatus:
        """Get the current status of this manifest.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            ManifestStatus enum value
        """
        if current_time is None:
            current_time = datetime.now()
        
        # If all carriers acknowledged, status is acknowledged
        if self.acknowledged:
            return ManifestStatus.ACKNOWLEDGED
        
        manifest_datetime = self.get_manifest_datetime()
        
        # Check if we're within the alert window
        alert_start = manifest_datetime - timedelta(minutes=2)  # 2 minutes before
        alert_end = manifest_datetime + timedelta(minutes=self.alert_window_minutes)
        
        if current_time < alert_start:
            return ManifestStatus.PENDING
        elif alert_start <= current_time <= alert_end:
            return ManifestStatus.ACTIVE
        else:
            return ManifestStatus.MISSED
    
    def is_active(self, current_time: Optional[datetime] = None) -> bool:
        """Check if this manifest should trigger alerts.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            True if manifest should show alerts
        """
        status = self.get_status(current_time)
        return status in [ManifestStatus.ACTIVE, ManifestStatus.MISSED]
    
    def add_carrier(self, carrier_name: str) -> Carrier:
        """Add a new carrier to this manifest.
        
        Args:
            carrier_name: Name of the carrier to add
            
        Returns:
            The created Carrier object
            
        Raises:
            DataValidationException: If carrier name is invalid or already exists
        """
        if not carrier_name or not carrier_name.strip():
            raise DataValidationException(
                "Carrier name cannot be empty",
                field="carrier_name",
                value=carrier_name
            )
        
        carrier_name = carrier_name.strip()
        
        # Check if carrier already exists
        if any(c.name == carrier_name for c in self.carriers):
            raise DataValidationException(
                f"Carrier '{carrier_name}' already exists in this manifest",
                field="carrier_name",
                value=carrier_name
            )
        
        carrier = Carrier(name=carrier_name)
        self.carriers.append(carrier)
        self._update_status()
        return carrier
    
    def remove_carrier(self, carrier_name: str) -> bool:
        """Remove a carrier from this manifest.
        
        Args:
            carrier_name: Name of the carrier to remove
            
        Returns:
            True if carrier was removed, False if not found
        """
        for i, carrier in enumerate(self.carriers):
            if carrier.name == carrier_name:
                self.carriers.pop(i)
                self._update_status()
                return True
        return False
    
    def get_carrier(self, carrier_name: str) -> Optional[Carrier]:
        """Get a carrier by name.
        
        Args:
            carrier_name: Name of the carrier to find
            
        Returns:
            Carrier object if found, None otherwise
        """
        for carrier in self.carriers:
            if carrier.name == carrier_name:
                return carrier
        return None
    
    def acknowledge_carrier(self, carrier_name: str, user: str, reason: Optional[str] = None) -> bool:
        """Acknowledge a specific carrier.
        
        Args:
            carrier_name: Name of the carrier to acknowledge
            user: User making the acknowledgment
            reason: Optional reason for acknowledgment
            
        Returns:
            True if carrier was acknowledged, False if carrier not found
        """
        carrier = self.get_carrier(carrier_name)
        if carrier:
            carrier.acknowledge(user, reason)
            
            # Create acknowledgment record
            ack = Acknowledgment(
                date=self.date,
                manifest_time=self.time,
                carrier=carrier_name,
                user=user,
                reason=reason
            )
            self.acknowledgments.append(ack)
            
            self._update_status()
            return True
        return False
    
    def clear_carrier_acknowledgment(self, carrier_name: str) -> bool:
        """Clear acknowledgment for a specific carrier.
        
        Args:
            carrier_name: Name of the carrier to clear
            
        Returns:
            True if acknowledgment was cleared, False if carrier not found
        """
        carrier = self.get_carrier(carrier_name)
        if carrier:
            carrier.clear_acknowledgment()
            
            # Remove acknowledgment records for this carrier
            self.acknowledgments = [
                ack for ack in self.acknowledgments 
                if not ack.is_same_carrier(self.date, self.time, carrier_name)
            ]
            
            self._update_status()
            return True
        return False
    
    def acknowledge_all(self, user: str, reason: Optional[str] = None) -> None:
        """Acknowledge all carriers in this manifest.
        
        Args:
            user: User making the acknowledgment
            reason: Optional reason for acknowledgment
        """
        for carrier in self.carriers:
            if not carrier.is_acknowledged():
                self.acknowledge_carrier(carrier.name, user, reason)
    
    def get_unacknowledged_carriers(self) -> List[Carrier]:
        """Get list of carriers that haven't been acknowledged.
        
        Returns:
            List of unacknowledged Carrier objects
        """
        return [c for c in self.carriers if not c.is_acknowledged()]
    
    def get_acknowledged_carriers(self) -> List[Carrier]:
        """Get list of carriers that have been acknowledged.
        
        Returns:
            List of acknowledged Carrier objects
        """
        return [c for c in self.carriers if c.is_acknowledged()]
    
    def get_acknowledgment_summary(self) -> str:
        """Get a summary of acknowledgment status.
        
        Returns:
            String summary of acknowledged/total carriers
        """
        ack_count = len(self.get_acknowledged_carriers())
        total_count = len(self.carriers)
        return f"{ack_count}/{total_count} carriers acknowledged"
    
    def to_dict(self) -> dict:
        """Convert manifest to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "time": self.time,
            "date": self.date,
            "carriers": [carrier.to_dict() for carrier in self.carriers],
            "acknowledged": self.acknowledged,
            "missed": self.missed,
            "acknowledgments": [ack.to_dict() for ack in self.acknowledgments],
            "alert_window_minutes": self.alert_window_minutes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Manifest':
        """Create manifest from dictionary representation.
        
        Args:
            data: Dictionary containing manifest data
            
        Returns:
            Manifest instance
            
        Raises:
            DataValidationException: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise DataValidationException(
                "Manifest data must be a dictionary",
                field="data",
                value=str(type(data))
            )
        
        if "time" not in data:
            raise DataValidationException(
                "Manifest data must contain 'time' field",
                field="time",
                value="missing"
            )
        
        # Parse carriers
        carriers = []
        if "carriers" in data and data["carriers"]:
            for carrier_data in data["carriers"]:
                if isinstance(carrier_data, str):
                    # Handle simple string carrier format
                    carriers.append(Carrier(name=carrier_data))
                elif isinstance(carrier_data, dict):
                    # Handle full carrier object format
                    carriers.append(Carrier.from_dict(carrier_data))
                else:
                    raise DataValidationException(
                        "Carrier data must be string or dictionary",
                        field="carriers",
                        value=str(type(carrier_data))
                    )
        
        # Parse acknowledgments
        acknowledgments = []
        if "acknowledgments" in data and data["acknowledgments"]:
            for ack_data in data["acknowledgments"]:
                acknowledgments.append(Acknowledgment.from_dict(ack_data))
        
        return cls(
            time=data["time"],
            carriers=carriers,
            date=data.get("date"),
            acknowledged=data.get("acknowledged", False),
            missed=data.get("missed", False),
            acknowledgments=acknowledgments,
            alert_window_minutes=data.get("alert_window_minutes", 30)
        )
    
    @classmethod
    def from_config_format(cls, data: dict) -> 'Manifest':
        """Create manifest from config.json format.
        
        Args:
            data: Dictionary in config.json format (time + carriers list)
            
        Returns:
            Manifest instance
        """
        if not isinstance(data, dict) or "time" not in data:
            raise DataValidationException(
                "Config data must contain 'time' field",
                field="time",
                value="missing"
            )
        
        carriers = []
        if "carriers" in data and data["carriers"]:
            for carrier_name in data["carriers"]:
                carriers.append(Carrier(name=carrier_name))
        
        return cls(time=data["time"], carriers=carriers)
    
    def __str__(self) -> str:
        """String representation of the manifest."""
        status = self.get_status().value
        carrier_count = len(self.carriers)
        ack_summary = self.get_acknowledgment_summary()
        return f"{self.time} ({status}) - {ack_summary}"
    
    def __repr__(self) -> str:
        """Developer representation of the manifest."""
        return f"Manifest(time='{self.time}', carriers={len(self.carriers)}, status={self.get_status().value})"