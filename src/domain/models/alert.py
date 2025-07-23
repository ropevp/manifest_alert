"""
Alert domain model.

Represents an active alert with timing, status, and escalation information.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from ...infrastructure.exceptions.custom_exceptions import DataValidationException, BusinessLogicException


class AlertPriority(Enum):
    """Enumeration of alert priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Enumeration of alert statuses."""
    PENDING = "pending"
    ACTIVE = "active"
    ESCALATED = "escalated"
    ACKNOWLEDGED = "acknowledged"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"


@dataclass
class Alert:
    """
    Represents an active alert in the system.
    
    Tracks the alert status, timing, escalation, and provides
    logic for determining when alerts should be triggered,
    escalated, or dismissed.
    """
    
    manifest_name: str
    carrier_name: Optional[str] = None  # None for manifest-level alerts
    alert_time: datetime = None
    priority: AlertPriority = AlertPriority.NORMAL
    status: AlertStatus = AlertStatus.PENDING
    snooze_until: Optional[datetime] = None
    escalation_time: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    message: str = ""
    
    def __post_init__(self):
        """Initialize alert data after creation."""
        if self.alert_time is None:
            self.alert_time = datetime.now()
        self._validate()
    
    def _validate(self):
        """Validate alert data and raise exceptions for invalid data."""
        # Validate manifest_name
        if not self.manifest_name or not isinstance(self.manifest_name, str):
            raise DataValidationException(
                "Alert manifest name must be a non-empty string",
                field_name="manifest_name",
                invalid_value=self.manifest_name
            )
        
        # Validate carrier_name (can be None)
        if self.carrier_name is not None and not isinstance(self.carrier_name, str):
            raise DataValidationException(
                "Carrier name must be a string or None",
                field_name="carrier_name",
                invalid_value=type(self.carrier_name).__name__
            )
        
        # Validate alert_time
        if not isinstance(self.alert_time, datetime):
            raise DataValidationException(
                "Alert time must be a datetime object",
                field_name="alert_time",
                invalid_value=type(self.alert_time).__name__
            )
        
        # Validate priority
        if not isinstance(self.priority, AlertPriority):
            raise DataValidationException(
                "Priority must be an AlertPriority enum value",
                field_name="priority",
                invalid_value=self.priority
            )
        
        # Validate status
        if not isinstance(self.status, AlertStatus):
            raise DataValidationException(
                "Status must be an AlertStatus enum value",
                field_name="status",
                invalid_value=self.status
            )
        
        # Validate message
        if self.message is not None and not isinstance(self.message, str):
            raise DataValidationException(
                "Message must be a string",
                field_name="message",
                invalid_value=type(self.message).__name__
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """
        Create an Alert from dictionary data (e.g., from JSON).
        
        Args:
            data: Dictionary containing alert data
            
        Returns:
            Alert instance
            
        Raises:
            DataValidationException: If data is invalid
        """
        try:
            # Handle datetime conversions
            alert_time = cls._parse_datetime(data.get('alert_time'))
            snooze_until = cls._parse_datetime(data.get('snooze_until')) if data.get('snooze_until') else None
            escalation_time = cls._parse_datetime(data.get('escalation_time')) if data.get('escalation_time') else None
            acknowledged_at = cls._parse_datetime(data.get('acknowledged_at')) if data.get('acknowledged_at') else None
            
            # Handle enum conversions
            priority_value = data.get('priority', 'normal')
            if isinstance(priority_value, str):
                priority = AlertPriority(priority_value.lower())
            else:
                priority = priority_value
            
            status_value = data.get('status', 'pending')
            if isinstance(status_value, str):
                status = AlertStatus(status_value.lower())
            else:
                status = status_value
            
            return cls(
                manifest_name=data['manifest_name'],
                carrier_name=data.get('carrier_name'),
                alert_time=alert_time,
                priority=priority,
                status=status,
                snooze_until=snooze_until,
                escalation_time=escalation_time,
                acknowledged_by=data.get('acknowledged_by'),
                acknowledged_at=acknowledged_at,
                message=data.get('message', "")
            )
        except KeyError as e:
            raise DataValidationException(
                f"Missing required field: {e}",
                field_name=str(e),
                cause=e
            )
        except ValueError as e:
            raise DataValidationException(
                f"Invalid enum value: {e}",
                cause=e
            )
        except Exception as e:
            if isinstance(e, DataValidationException):
                raise
            raise DataValidationException(
                f"Failed to create alert from data: {e}",
                cause=e
            )
    
    @staticmethod
    def _parse_datetime(datetime_data: Any) -> datetime:
        """Parse datetime from various formats."""
        if isinstance(datetime_data, str):
            try:
                return datetime.fromisoformat(datetime_data.replace('Z', '+00:00'))
            except ValueError:
                try:
                    return datetime.strptime(datetime_data, "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    raise DataValidationException(
                        f"Invalid datetime format: {datetime_data}",
                        cause=e
                    )
        elif isinstance(datetime_data, datetime):
            return datetime_data
        else:
            raise DataValidationException(
                "Datetime must be a string or datetime object",
                invalid_value=type(datetime_data).__name__
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert alert to dictionary (for JSON serialization).
        
        Returns:
            Dictionary representation of the alert
        """
        return {
            'manifest_name': self.manifest_name,
            'carrier_name': self.carrier_name,
            'alert_time': self.alert_time.isoformat(),
            'priority': self.priority.value,
            'status': self.status.value,
            'snooze_until': self.snooze_until.isoformat() if self.snooze_until else None,
            'escalation_time': self.escalation_time.isoformat() if self.escalation_time else None,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'message': self.message
        }
    
    def activate(self) -> None:
        """Activate the alert."""
        if self.status not in [AlertStatus.PENDING, AlertStatus.SNOOZED]:
            raise BusinessLogicException(
                f"Cannot activate alert in status: {self.status.value}",
                entity_type="alert",
                entity_id=self.get_id()
            )
        
        self.status = AlertStatus.ACTIVE
        self.snooze_until = None
    
    def acknowledge(self, user: str, timestamp: Optional[datetime] = None) -> None:
        """
        Acknowledge the alert.
        
        Args:
            user: User acknowledging the alert
            timestamp: Optional timestamp (defaults to now)
        """
        if self.status == AlertStatus.ACKNOWLEDGED:
            raise BusinessLogicException(
                "Alert is already acknowledged",
                entity_type="alert",
                entity_id=self.get_id()
            )
        
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timestamp or datetime.now()
        self.snooze_until = None
    
    def snooze(self, duration_minutes: int = 5) -> None:
        """
        Snooze the alert for the specified duration.
        
        Args:
            duration_minutes: Minutes to snooze the alert
        """
        if self.status == AlertStatus.ACKNOWLEDGED:
            raise BusinessLogicException(
                "Cannot snooze acknowledged alert",
                entity_type="alert",
                entity_id=self.get_id()
            )
        
        self.status = AlertStatus.SNOOZED
        self.snooze_until = datetime.now() + timedelta(minutes=duration_minutes)
    
    def escalate(self) -> None:
        """Escalate the alert to higher priority."""
        if self.status not in [AlertStatus.ACTIVE, AlertStatus.ESCALATED]:
            raise BusinessLogicException(
                f"Cannot escalate alert in status: {self.status.value}",
                entity_type="alert",
                entity_id=self.get_id()
            )
        
        self.status = AlertStatus.ESCALATED
        self.escalation_time = datetime.now()
        
        # Increase priority if possible
        if self.priority == AlertPriority.LOW:
            self.priority = AlertPriority.NORMAL
        elif self.priority == AlertPriority.NORMAL:
            self.priority = AlertPriority.HIGH
        elif self.priority == AlertPriority.HIGH:
            self.priority = AlertPriority.CRITICAL
    
    def dismiss(self) -> None:
        """Dismiss the alert."""
        self.status = AlertStatus.DISMISSED
        self.snooze_until = None
    
    def is_active(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the alert is currently active.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if alert should be actively displayed/sounding
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if snoozed and snooze time has passed
        if self.status == AlertStatus.SNOOZED:
            if self.snooze_until and current_time >= self.snooze_until:
                self.status = AlertStatus.ACTIVE
                self.snooze_until = None
                return True
            else:
                return False
        
        return self.status in [AlertStatus.ACTIVE, AlertStatus.ESCALATED]
    
    def is_snoozed(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the alert is currently snoozed.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if alert is snoozed
        """
        if self.status != AlertStatus.SNOOZED:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        return self.snooze_until is None or current_time < self.snooze_until
    
    def is_acknowledged(self) -> bool:
        """Check if the alert is acknowledged."""
        return self.status == AlertStatus.ACKNOWLEDGED
    
    def is_escalated(self) -> bool:
        """Check if the alert is escalated."""
        return self.status == AlertStatus.ESCALATED
    
    def get_time_since_alert(self, current_time: Optional[datetime] = None) -> float:
        """
        Get time elapsed since alert started in seconds.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Seconds elapsed since alert
        """
        if current_time is None:
            current_time = datetime.now()
        
        return (current_time - self.alert_time).total_seconds()
    
    def get_snooze_remaining(self, current_time: Optional[datetime] = None) -> Optional[float]:
        """
        Get remaining snooze time in seconds.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Seconds remaining in snooze, None if not snoozed
        """
        if not self.is_snoozed(current_time) or self.snooze_until is None:
            return None
        
        if current_time is None:
            current_time = datetime.now()
        
        remaining = (self.snooze_until - current_time).total_seconds()
        return max(0, remaining)
    
    def should_escalate(self, escalation_threshold_minutes: int = 5, 
                       current_time: Optional[datetime] = None) -> bool:
        """
        Check if the alert should be escalated based on time.
        
        Args:
            escalation_threshold_minutes: Minutes after which to escalate
            current_time: Current time (defaults to now)
            
        Returns:
            True if alert should be escalated
        """
        if self.status != AlertStatus.ACTIVE:
            return False
        
        if self.escalation_time is not None:
            return False  # Already escalated
        
        elapsed_minutes = self.get_time_since_alert(current_time) / 60
        return elapsed_minutes >= escalation_threshold_minutes
    
    def get_id(self) -> str:
        """Get a unique identifier for the alert."""
        if self.carrier_name:
            return f"{self.manifest_name}:{self.carrier_name}"
        else:
            return self.manifest_name
    
    def get_display_title(self) -> str:
        """Get display title for the alert."""
        if self.carrier_name:
            return f"{self.manifest_name} - {self.carrier_name}"
        else:
            return self.manifest_name
    
    def get_priority_display(self) -> str:
        """Get display-friendly priority string."""
        priority_map = {
            AlertPriority.LOW: "Low",
            AlertPriority.NORMAL: "Normal",
            AlertPriority.HIGH: "High",
            AlertPriority.CRITICAL: "Critical"
        }
        return priority_map.get(self.priority, self.priority.value.title())
    
    def get_status_display(self) -> str:
        """Get display-friendly status string."""
        status_map = {
            AlertStatus.PENDING: "Pending",
            AlertStatus.ACTIVE: "Active",
            AlertStatus.ESCALATED: "Escalated",
            AlertStatus.ACKNOWLEDGED: "Acknowledged",
            AlertStatus.SNOOZED: "Snoozed",
            AlertStatus.DISMISSED: "Dismissed"
        }
        return status_map.get(self.status, self.status.value.title())
    
    def __str__(self) -> str:
        """Return string representation of the alert."""
        return f"Alert({self.get_id()}, {self.status.value}, {self.priority.value})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the alert."""
        return (f"Alert(manifest_name='{self.manifest_name}', "
                f"carrier_name='{self.carrier_name}', status={self.status}, "
                f"priority={self.priority})")
    
    def __eq__(self, other) -> bool:
        """Check equality based on manifest and carrier names."""
        if not isinstance(other, Alert):
            return False
        return (self.manifest_name == other.manifest_name and 
                self.carrier_name == other.carrier_name)
    
    def __hash__(self) -> int:
        """Return hash based on manifest and carrier names."""
        return hash((self.manifest_name, self.carrier_name))