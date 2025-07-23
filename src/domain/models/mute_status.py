"""
MuteStatus domain model.

Represents the centralized mute state for the alert system.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ...infrastructure.exceptions.custom_exceptions import DataValidationException, BusinessLogicException


@dataclass
class MuteStatus:
    """
    Represents the centralized mute status for the alert system.
    
    Manages both permanent mute and temporary snooze functionality
    with synchronization across multiple PCs via network share.
    """
    
    is_muted: bool = False
    muted_by: Optional[str] = None
    muted_at: Optional[datetime] = None
    snooze_until: Optional[datetime] = None
    reason: str = ""
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize mute status after creation."""
        if self.last_updated is None:
            self.last_updated = datetime.now()
        self._validate()
    
    def _validate(self):
        """Validate mute status data and raise exceptions for invalid data."""
        # Validate is_muted
        if not isinstance(self.is_muted, bool):
            raise DataValidationException(
                "is_muted must be a boolean",
                field_name="is_muted",
                invalid_value=type(self.is_muted).__name__
            )
        
        # Validate muted_by (can be None)
        if self.muted_by is not None and not isinstance(self.muted_by, str):
            raise DataValidationException(
                "muted_by must be a string or None",
                field_name="muted_by",
                invalid_value=type(self.muted_by).__name__
            )
        
        # Validate muted_at (can be None)
        if self.muted_at is not None and not isinstance(self.muted_at, datetime):
            raise DataValidationException(
                "muted_at must be a datetime object or None",
                field_name="muted_at",
                invalid_value=type(self.muted_at).__name__
            )
        
        # Validate snooze_until (can be None)
        if self.snooze_until is not None and not isinstance(self.snooze_until, datetime):
            raise DataValidationException(
                "snooze_until must be a datetime object or None",
                field_name="snooze_until",
                invalid_value=type(self.snooze_until).__name__
            )
        
        # Validate reason
        if self.reason is not None and not isinstance(self.reason, str):
            raise DataValidationException(
                "reason must be a string",
                field_name="reason",
                invalid_value=type(self.reason).__name__
            )
        
        # Validate last_updated
        if self.last_updated is not None and not isinstance(self.last_updated, datetime):
            raise DataValidationException(
                "last_updated must be a datetime object or None",
                field_name="last_updated",
                invalid_value=type(self.last_updated).__name__
            )
        
        # Validate consistency
        if self.is_muted and self.muted_by is None:
            raise DataValidationException(
                "Muted status must have muted_by specified",
                field_name="muted_by",
                invalid_value=None
            )
        
        if self.is_muted and self.muted_at is None:
            raise DataValidationException(
                "Muted status must have muted_at timestamp",
                field_name="muted_at",
                invalid_value=None
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MuteStatus':
        """
        Create a MuteStatus from dictionary data (e.g., from JSON).
        
        Args:
            data: Dictionary containing mute status data
            
        Returns:
            MuteStatus instance
            
        Raises:
            DataValidationException: If data is invalid
        """
        try:
            # Handle datetime conversions
            muted_at = cls._parse_datetime(data.get('muted_at')) if data.get('muted_at') else None
            snooze_until = cls._parse_datetime(data.get('snooze_until')) if data.get('snooze_until') else None
            last_updated = cls._parse_datetime(data.get('last_updated')) if data.get('last_updated') else None
            
            return cls(
                is_muted=data.get('is_muted', False),
                muted_by=data.get('muted_by'),
                muted_at=muted_at,
                snooze_until=snooze_until,
                reason=data.get('reason', ""),
                last_updated=last_updated
            )
        except Exception as e:
            if isinstance(e, DataValidationException):
                raise
            raise DataValidationException(
                f"Failed to create mute status from data: {e}",
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
        Convert mute status to dictionary (for JSON serialization).
        
        Returns:
            Dictionary representation of the mute status
        """
        return {
            'is_muted': self.is_muted,
            'muted_by': self.muted_by,
            'muted_at': self.muted_at.isoformat() if self.muted_at else None,
            'snooze_until': self.snooze_until.isoformat() if self.snooze_until else None,
            'reason': self.reason,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def create_unmuted(cls) -> 'MuteStatus':
        """Create a default unmuted status."""
        return cls(is_muted=False)
    
    def mute(self, user: str, reason: str = "", timestamp: Optional[datetime] = None) -> None:
        """
        Mute the alerts.
        
        Args:
            user: User performing the mute
            reason: Optional reason for muting
            timestamp: Optional timestamp (defaults to now)
        """
        if self.is_muted:
            raise BusinessLogicException(
                "System is already muted",
                entity_type="mute_status",
                entity_id="global"
            )
        
        now = timestamp or datetime.now()
        self.is_muted = True
        self.muted_by = user
        self.muted_at = now
        self.reason = reason
        self.last_updated = now
        self.snooze_until = None  # Clear any existing snooze
    
    def unmute(self, timestamp: Optional[datetime] = None) -> None:
        """
        Unmute the alerts.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.is_muted and self.snooze_until is None:
            raise BusinessLogicException(
                "System is not muted or snoozed",
                entity_type="mute_status",
                entity_id="global"
            )
        
        now = timestamp or datetime.now()
        self.is_muted = False
        self.muted_by = None
        self.muted_at = None
        self.reason = ""
        self.snooze_until = None
        self.last_updated = now
    
    def snooze(self, duration_minutes: int = 5, user: Optional[str] = None, 
              timestamp: Optional[datetime] = None) -> None:
        """
        Snooze alerts for the specified duration.
        
        Args:
            duration_minutes: Minutes to snooze alerts
            user: User performing the snooze (optional)
            timestamp: Optional timestamp (defaults to now)
        """
        now = timestamp or datetime.now()
        self.snooze_until = now + timedelta(minutes=duration_minutes)
        self.last_updated = now
        
        # If not already muted, track who snoozed
        if not self.is_muted and user:
            self.muted_by = user
            self.muted_at = now
            self.reason = f"Snoozed for {duration_minutes} minutes"
    
    def is_currently_muted(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if alerts are currently muted (including snooze).
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if alerts should be muted
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check permanent mute
        if self.is_muted:
            return True
        
        # Check snooze
        if self.snooze_until and current_time < self.snooze_until:
            return True
        
        # If snooze has expired, clear it
        if self.snooze_until and current_time >= self.snooze_until:
            self.snooze_until = None
            self.last_updated = current_time
        
        return False
    
    def is_snoozed(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if alerts are currently snoozed.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            True if alerts are snoozed
        """
        if self.snooze_until is None:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        return current_time < self.snooze_until
    
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
    
    def get_mute_duration(self, current_time: Optional[datetime] = None) -> Optional[float]:
        """
        Get duration alerts have been muted in seconds.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Seconds alerts have been muted, None if not muted
        """
        if not self.is_muted or self.muted_at is None:
            return None
        
        if current_time is None:
            current_time = datetime.now()
        
        return (current_time - self.muted_at).total_seconds()
    
    def get_status_summary(self, current_time: Optional[datetime] = None) -> str:
        """
        Get a human-readable status summary.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Status summary string
        """
        if self.is_currently_muted(current_time):
            if self.is_muted:
                muted_by = self.muted_by or "Unknown"
                if self.reason:
                    return f"Muted by {muted_by}: {self.reason}"
                else:
                    return f"Muted by {muted_by}"
            elif self.is_snoozed(current_time):
                remaining = self.get_snooze_remaining(current_time)
                if remaining:
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    return f"Snoozed for {minutes}:{seconds:02d}"
                else:
                    return "Snoozed"
        
        return "Active"
    
    def touch(self, timestamp: Optional[datetime] = None) -> None:
        """
        Update the last_updated timestamp.
        
        Args:
            timestamp: Optional timestamp (defaults to now)
        """
        self.last_updated = timestamp or datetime.now()
    
    def __str__(self) -> str:
        """Return string representation of the mute status."""
        if self.is_muted:
            return f"MuteStatus(muted by {self.muted_by})"
        elif self.snooze_until:
            return f"MuteStatus(snoozed until {self.snooze_until.strftime('%H:%M:%S')})"
        else:
            return "MuteStatus(active)"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the mute status."""
        return (f"MuteStatus(is_muted={self.is_muted}, muted_by='{self.muted_by}', "
                f"snooze_until={self.snooze_until})")
    
    def __eq__(self, other) -> bool:
        """Check equality based on all relevant fields."""
        if not isinstance(other, MuteStatus):
            return False
        return (self.is_muted == other.is_muted and 
                self.muted_by == other.muted_by and
                self.snooze_until == other.snooze_until)
    
    def __hash__(self) -> int:
        """Return hash based on key fields."""
        return hash((self.is_muted, self.muted_by, self.snooze_until))