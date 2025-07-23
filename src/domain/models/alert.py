"""
Alert Domain Model

Represents an active alert state with timing and display information.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from .manifest import Manifest
from ...infrastructure.exceptions import DataValidationException


class AlertType(Enum):
    """Enumeration of alert types."""
    MANIFEST_ACTIVE = "manifest_active"    # Manifest time has arrived
    MANIFEST_MISSED = "manifest_missed"    # Manifest time was missed
    SYSTEM_ERROR = "system_error"          # System error alert


class AlertPriority(Enum):
    """Enumeration of alert priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents an active alert state.
    
    An alert represents a condition that requires user attention, such as
    an active manifest time or a missed manifest. It tracks timing, display
    state, and user interaction.
    
    Attributes:
        alert_id: Unique identifier for this alert
        alert_type: Type of alert (manifest_active, manifest_missed, etc.)
        priority: Priority level of the alert
        manifest: Associated manifest (if applicable)
        title: Alert title/header
        message: Alert message content
        created_at: When the alert was created
        acknowledged_at: When the alert was acknowledged (if applicable)
        auto_dismiss_after: Auto-dismiss after this many seconds (None = no auto-dismiss)
        flash_enabled: Whether visual flashing is enabled
        sound_enabled: Whether audio alerts are enabled
        display_duration: How long alert has been displayed (updated externally)
    """
    
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    manifest: Optional[Manifest] = None
    created_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    auto_dismiss_after: Optional[int] = None
    flash_enabled: bool = True
    sound_enabled: bool = True
    display_duration: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate alert data after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate alert fields."""
        if not self.alert_id or not self.alert_id.strip():
            raise DataValidationException(
                "Alert ID cannot be empty",
                field="alert_id",
                value=str(self.alert_id)
            )
        
        if not self.title or not self.title.strip():
            raise DataValidationException(
                "Alert title cannot be empty",
                field="title",
                value=str(self.title)
            )
        
        if not self.message or not self.message.strip():
            raise DataValidationException(
                "Alert message cannot be empty",
                field="message",
                value=str(self.message)
            )
        
        # Normalize strings
        self.alert_id = self.alert_id.strip()
        self.title = self.title.strip()
        self.message = self.message.strip()
        
        # Validate auto_dismiss_after
        if self.auto_dismiss_after is not None and self.auto_dismiss_after <= 0:
            raise DataValidationException(
                "Auto dismiss duration must be positive",
                field="auto_dismiss_after",
                value=str(self.auto_dismiss_after)
            )
    
    def is_acknowledged(self) -> bool:
        """Check if this alert has been acknowledged.
        
        Returns:
            True if the alert has been acknowledged
        """
        return self.acknowledged_at is not None
    
    def acknowledge(self) -> None:
        """Acknowledge this alert."""
        if not self.is_acknowledged():
            self.acknowledged_at = datetime.now()
    
    def get_age_seconds(self, current_time: Optional[datetime] = None) -> float:
        """Get the age of this alert in seconds.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            Age in seconds since the alert was created
        """
        if current_time is None:
            current_time = datetime.now()
        
        if self.created_at:
            return (current_time - self.created_at).total_seconds()
        return 0.0
    
    def should_auto_dismiss(self, current_time: Optional[datetime] = None) -> bool:
        """Check if this alert should be auto-dismissed.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            True if alert should be auto-dismissed
        """
        if self.auto_dismiss_after is None:
            return False
        
        age = self.get_age_seconds(current_time)
        return age >= self.auto_dismiss_after
    
    def should_flash(self) -> bool:
        """Check if visual flashing should be active.
        
        Returns:
            True if visual flashing should be enabled
        """
        return self.flash_enabled and not self.is_acknowledged()
    
    def should_play_sound(self) -> bool:
        """Check if audio alerts should be active.
        
        Returns:
            True if audio alerts should be enabled
        """
        return self.sound_enabled and not self.is_acknowledged()
    
    def get_display_info(self) -> dict:
        """Get information for displaying this alert.
        
        Returns:
            Dictionary with display information
        """
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "acknowledged": self.is_acknowledged(),
            "should_flash": self.should_flash(),
            "should_play_sound": self.should_play_sound(),
            "age_seconds": self.get_age_seconds(),
            "display_duration": self.display_duration,
            "manifest_info": self.get_manifest_info() if self.manifest else None
        }
    
    def get_manifest_info(self) -> Optional[dict]:
        """Get manifest information if this is a manifest-related alert.
        
        Returns:
            Dictionary with manifest information, or None if no manifest
        """
        if not self.manifest:
            return None
        
        return {
            "time": self.manifest.time,
            "date": self.manifest.date,
            "status": self.manifest.get_status().value,
            "carriers": [carrier.name for carrier in self.manifest.carriers],
            "acknowledged_carriers": [c.name for c in self.manifest.get_acknowledged_carriers()],
            "unacknowledged_carriers": [c.name for c in self.manifest.get_unacknowledged_carriers()],
            "acknowledgment_summary": self.manifest.get_acknowledgment_summary()
        }
    
    def update_from_manifest(self) -> None:
        """Update alert state based on associated manifest.
        
        This should be called periodically to keep the alert in sync
        with the manifest state.
        """
        if not self.manifest:
            return
        
        # Update title and message based on manifest status
        status = self.manifest.get_status()
        unack_carriers = self.manifest.get_unacknowledged_carriers()
        
        if status.value == "Active":
            self.title = f"Manifest Alert - {self.manifest.time}"
            if unack_carriers:
                carrier_list = ", ".join(c.name for c in unack_carriers)
                self.message = f"Manifest time reached. Pending carriers: {carrier_list}"
            else:
                self.message = "All carriers acknowledged"
                
        elif status.value == "Missed":
            self.title = f"Missed Manifest - {self.manifest.time}"
            if unack_carriers:
                carrier_list = ", ".join(c.name for c in unack_carriers)
                self.message = f"Manifest missed! Unacknowledged carriers: {carrier_list}"
                self.priority = AlertPriority.CRITICAL
            else:
                self.message = "Manifest was missed but all carriers are now acknowledged"
        
        # Auto-acknowledge if all carriers are acknowledged
        if self.manifest.acknowledged and not self.is_acknowledged():
            self.acknowledge()
    
    def to_dict(self) -> dict:
        """Convert alert to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "auto_dismiss_after": self.auto_dismiss_after,
            "flash_enabled": self.flash_enabled,
            "sound_enabled": self.sound_enabled,
            "display_duration": self.display_duration
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Alert':
        """Create alert from dictionary representation.
        
        Args:
            data: Dictionary containing alert data
            
        Returns:
            Alert instance
            
        Raises:
            DataValidationException: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise DataValidationException(
                "Alert data must be a dictionary",
                field="data",
                value=str(type(data))
            )
        
        # Check required fields
        required_fields = ["alert_id", "alert_type", "priority", "title", "message"]
        for field in required_fields:
            if field not in data:
                raise DataValidationException(
                    f"Alert data must contain '{field}' field",
                    field=field,
                    value="missing"
                )
        
        # Parse enums
        try:
            alert_type = AlertType(data["alert_type"])
        except ValueError as e:
            raise DataValidationException(
                f"Invalid alert type: {e}",
                field="alert_type",
                value=data["alert_type"]
            )
        
        try:
            priority = AlertPriority(data["priority"])
        except ValueError as e:
            raise DataValidationException(
                f"Invalid priority: {e}",
                field="priority",
                value=data["priority"]
            )
        
        # Parse timestamps
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError) as e:
                raise DataValidationException(
                    f"Invalid created_at timestamp: {e}",
                    field="created_at",
                    value=str(data.get("created_at"))
                )
        
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
        
        # Parse manifest
        manifest = None
        if data.get("manifest"):
            from .manifest import Manifest  # Import here to avoid circular import
            manifest = Manifest.from_dict(data["manifest"])
        
        return cls(
            alert_id=data["alert_id"],
            alert_type=alert_type,
            priority=priority,
            title=data["title"],
            message=data["message"],
            manifest=manifest,
            created_at=created_at,
            acknowledged_at=acknowledged_at,
            auto_dismiss_after=data.get("auto_dismiss_after"),
            flash_enabled=data.get("flash_enabled", True),
            sound_enabled=data.get("sound_enabled", True),
            display_duration=data.get("display_duration", 0.0)
        )
    
    @classmethod
    def create_manifest_alert(cls, manifest: Manifest, alert_id: Optional[str] = None) -> 'Alert':
        """Create an alert for a manifest.
        
        Args:
            manifest: The manifest to create an alert for
            alert_id: Optional custom alert ID (auto-generated if not provided)
            
        Returns:
            Alert instance for the manifest
        """
        if alert_id is None:
            alert_id = f"manifest_{manifest.date}_{manifest.time}".replace(":", "")
        
        status = manifest.get_status()
        
        if status.value == "Active":
            alert_type = AlertType.MANIFEST_ACTIVE
            priority = AlertPriority.HIGH
            title = f"Manifest Alert - {manifest.time}"
            unack_carriers = manifest.get_unacknowledged_carriers()
            if unack_carriers:
                carrier_list = ", ".join(c.name for c in unack_carriers)
                message = f"Manifest time reached. Pending carriers: {carrier_list}"
            else:
                message = "All carriers acknowledged"
                
        elif status.value == "Missed":
            alert_type = AlertType.MANIFEST_MISSED
            priority = AlertPriority.CRITICAL
            title = f"Missed Manifest - {manifest.time}"
            unack_carriers = manifest.get_unacknowledged_carriers()
            if unack_carriers:
                carrier_list = ", ".join(c.name for c in unack_carriers)
                message = f"Manifest missed! Unacknowledged carriers: {carrier_list}"
            else:
                message = "Manifest was missed but all carriers are now acknowledged"
        else:
            # Should not create alerts for pending or acknowledged manifests
            raise DataValidationException(
                f"Cannot create alert for manifest with status {status.value}",
                field="status",
                value=status.value
            )
        
        return cls(
            alert_id=alert_id,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            manifest=manifest
        )
    
    def __str__(self) -> str:
        """String representation of the alert."""
        status = "✓" if self.is_acknowledged() else "!"
        return f"{status} [{self.priority.value.upper()}] {self.title}"
    
    def __repr__(self) -> str:
        """Developer representation of the alert."""
        return f"Alert(id='{self.alert_id}', type={self.alert_type.value}, priority={self.priority.value})"