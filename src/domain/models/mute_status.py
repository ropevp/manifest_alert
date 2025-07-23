"""
MuteStatus Domain Model

Represents the centralized mute state for the manifest alert system.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from ...infrastructure.exceptions import DataValidationException


class MuteType(Enum):
    """Enumeration of mute types."""
    MANUAL = "manual"        # Manually muted indefinitely
    SNOOZE = "snooze"       # Temporary snooze with auto-resume
    DISABLED = "disabled"    # Muting is disabled


@dataclass
class MuteStatus:
    """Represents the centralized mute state for alerts.
    
    This model manages the mute/snooze functionality that is synchronized
    across multiple PCs via network share. It tracks whether alerts are
    currently muted and when they should resume.
    
    Attributes:
        is_muted: Whether alerts are currently muted
        mute_type: Type of mute (manual, snooze, disabled)
        muted_at: When the mute was activated
        mute_end_time: When the mute should end (None for indefinite)
        muted_by: User who activated the mute
        reason: Optional reason for muting
        snooze_duration_minutes: Duration for snooze mode
    """
    
    is_muted: bool = False
    mute_type: MuteType = MuteType.DISABLED
    muted_at: Optional[datetime] = None
    mute_end_time: Optional[datetime] = None
    muted_by: Optional[str] = None
    reason: Optional[str] = None
    snooze_duration_minutes: int = 5
    
    def __post_init__(self) -> None:
        """Validate mute status after initialization."""
        self._validate()
        self._update_status()
    
    def _validate(self) -> None:
        """Validate mute status fields."""
        # Validate snooze duration
        if self.snooze_duration_minutes <= 0:
            raise DataValidationException(
                "Snooze duration must be positive",
                field="snooze_duration_minutes",
                value=str(self.snooze_duration_minutes)
            )
        
        # Validate consistency of mute state
        if self.is_muted:
            if self.mute_type == MuteType.DISABLED:
                raise DataValidationException(
                    "Cannot be muted when mute type is disabled",
                    field="mute_type",
                    value=self.mute_type.value
                )
            
            if not self.muted_at:
                # Set muted_at to now if not provided
                self.muted_at = datetime.now()
        else:
            # If not muted, clear mute-related fields
            if self.mute_type != MuteType.DISABLED:
                self.mute_type = MuteType.DISABLED
    
    def _update_status(self) -> None:
        """Update mute status based on current time."""
        if not self.is_muted:
            return
        
        current_time = datetime.now()
        
        # Check if snooze period has expired
        if (self.mute_type == MuteType.SNOOZE and 
            self.mute_end_time and 
            current_time >= self.mute_end_time):
            self.unmute()
    
    def mute(self, duration_minutes: Optional[int] = None, user: Optional[str] = None, 
             reason: Optional[str] = None) -> None:
        """Activate mute mode.
        
        Args:
            duration_minutes: Duration in minutes (None for indefinite)
            user: User activating the mute
            reason: Optional reason for muting
        """
        current_time = datetime.now()
        
        self.is_muted = True
        self.muted_at = current_time
        self.muted_by = user
        self.reason = reason
        
        if duration_minutes is not None:
            if duration_minutes <= 0:
                raise DataValidationException(
                    "Mute duration must be positive",
                    field="duration_minutes",
                    value=str(duration_minutes)
                )
            
            self.mute_type = MuteType.SNOOZE
            self.mute_end_time = current_time + timedelta(minutes=duration_minutes)
        else:
            self.mute_type = MuteType.MANUAL
            self.mute_end_time = None
    
    def snooze(self, duration_minutes: Optional[int] = None, user: Optional[str] = None,
               reason: Optional[str] = None) -> None:
        """Activate snooze mode (temporary mute).
        
        Args:
            duration_minutes: Duration in minutes (defaults to snooze_duration_minutes)
            user: User activating the snooze
            reason: Optional reason for snoozing
        """
        if duration_minutes is None:
            duration_minutes = self.snooze_duration_minutes
        
        self.mute(duration_minutes, user, reason or "Snoozed")
    
    def unmute(self, user: Optional[str] = None) -> None:
        """Deactivate mute mode.
        
        Args:
            user: User deactivating the mute
        """
        self.is_muted = False
        self.mute_type = MuteType.DISABLED
        self.muted_at = None
        self.mute_end_time = None
        self.muted_by = user if user else self.muted_by
        self.reason = None
    
    def toggle_mute(self, duration_minutes: Optional[int] = None, user: Optional[str] = None) -> bool:
        """Toggle mute state.
        
        Args:
            duration_minutes: Duration for mute (if toggling to muted)
            user: User performing the toggle
            
        Returns:
            True if now muted, False if now unmuted
        """
        if self.is_currently_muted():
            self.unmute(user)
            return False
        else:
            self.mute(duration_minutes, user, "Toggled")
            return True
    
    def is_currently_muted(self, current_time: Optional[datetime] = None) -> bool:
        """Check if alerts are currently muted.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            True if alerts are currently muted
        """
        if not self.is_muted:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        # Check if snooze period has expired
        if (self.mute_type == MuteType.SNOOZE and 
            self.mute_end_time and 
            current_time >= self.mute_end_time):
            # Auto-unmute expired snooze
            self.unmute()
            return False
        
        return True
    
    def get_remaining_time(self, current_time: Optional[datetime] = None) -> Optional[timedelta]:
        """Get remaining time for mute/snooze.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            Remaining time as timedelta, or None if indefinite/not muted
        """
        if not self.is_currently_muted(current_time) or not self.mute_end_time:
            return None
        
        if current_time is None:
            current_time = datetime.now()
        
        remaining = self.mute_end_time - current_time
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def get_remaining_minutes(self, current_time: Optional[datetime] = None) -> Optional[int]:
        """Get remaining time in minutes.
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            Remaining minutes, or None if indefinite/not muted
        """
        remaining = self.get_remaining_time(current_time)
        if remaining is None:
            return None
        
        return max(0, int(remaining.total_seconds() / 60))
    
    def get_mute_summary(self) -> str:
        """Get a human-readable summary of mute status.
        
        Returns:
            String summary of current mute state
        """
        if not self.is_currently_muted():
            return "Alerts active"
        
        if self.mute_type == MuteType.MANUAL:
            summary = "Muted indefinitely"
        elif self.mute_type == MuteType.SNOOZE:
            remaining = self.get_remaining_minutes()
            if remaining is not None and remaining > 0:
                summary = f"Snoozed for {remaining} more minutes"
            else:
                summary = "Snooze expired"
        else:
            summary = "Muted"
        
        if self.muted_by:
            summary += f" by {self.muted_by}"
        
        if self.reason:
            summary += f" ({self.reason})"
        
        return summary
    
    def extend_snooze(self, additional_minutes: int, user: Optional[str] = None) -> None:
        """Extend current snooze duration.
        
        Args:
            additional_minutes: Additional minutes to add
            user: User extending the snooze
            
        Raises:
            DataValidationException: If not currently snoozed or invalid duration
        """
        if not self.is_currently_muted():
            raise DataValidationException(
                "Cannot extend snooze when not muted",
                field="is_muted",
                value=str(self.is_muted)
            )
        
        if self.mute_type != MuteType.SNOOZE:
            raise DataValidationException(
                "Cannot extend snooze for non-snooze mute",
                field="mute_type",
                value=self.mute_type.value
            )
        
        if additional_minutes <= 0:
            raise DataValidationException(
                "Additional minutes must be positive",
                field="additional_minutes",
                value=str(additional_minutes)
            )
        
        if self.mute_end_time:
            self.mute_end_time += timedelta(minutes=additional_minutes)
        else:
            # Convert to snooze if it wasn't already
            current_time = datetime.now()
            self.mute_end_time = current_time + timedelta(minutes=additional_minutes)
        
        if user:
            self.muted_by = user
    
    def to_dict(self) -> dict:
        """Convert mute status to dictionary representation.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "is_muted": self.is_muted,
            "mute_type": self.mute_type.value,
            "muted_at": self.muted_at.isoformat() if self.muted_at else None,
            "mute_end_time": self.mute_end_time.isoformat() if self.mute_end_time else None,
            "muted_by": self.muted_by,
            "reason": self.reason,
            "snooze_duration_minutes": self.snooze_duration_minutes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MuteStatus':
        """Create mute status from dictionary representation.
        
        Args:
            data: Dictionary containing mute status data
            
        Returns:
            MuteStatus instance
            
        Raises:
            DataValidationException: If data is invalid
        """
        if not isinstance(data, dict):
            raise DataValidationException(
                "Mute status data must be a dictionary",
                field="data",
                value=str(type(data))
            )
        
        # Parse mute type
        mute_type = MuteType.DISABLED
        if "mute_type" in data:
            try:
                mute_type = MuteType(data["mute_type"])
            except ValueError as e:
                raise DataValidationException(
                    f"Invalid mute type: {e}",
                    field="mute_type",
                    value=str(data["mute_type"])
                )
        
        # Parse timestamps
        muted_at = None
        if data.get("muted_at"):
            try:
                muted_at = datetime.fromisoformat(data["muted_at"])
            except (ValueError, TypeError) as e:
                raise DataValidationException(
                    f"Invalid muted_at timestamp: {e}",
                    field="muted_at",
                    value=str(data.get("muted_at"))
                )
        
        mute_end_time = None
        if data.get("mute_end_time"):
            try:
                mute_end_time = datetime.fromisoformat(data["mute_end_time"])
            except (ValueError, TypeError) as e:
                raise DataValidationException(
                    f"Invalid mute_end_time timestamp: {e}",
                    field="mute_end_time",
                    value=str(data.get("mute_end_time"))
                )
        
        return cls(
            is_muted=data.get("is_muted", False),
            mute_type=mute_type,
            muted_at=muted_at,
            mute_end_time=mute_end_time,
            muted_by=data.get("muted_by"),
            reason=data.get("reason"),
            snooze_duration_minutes=data.get("snooze_duration_minutes", 5)
        )
    
    @classmethod
    def create_unmuted(cls) -> 'MuteStatus':
        """Create an unmuted status.
        
        Returns:
            MuteStatus instance in unmuted state
        """
        return cls(is_muted=False, mute_type=MuteType.DISABLED)
    
    @classmethod
    def create_muted(cls, duration_minutes: Optional[int] = None, user: Optional[str] = None,
                     reason: Optional[str] = None) -> 'MuteStatus':
        """Create a muted status.
        
        Args:
            duration_minutes: Duration in minutes (None for indefinite)
            user: User activating the mute
            reason: Optional reason for muting
            
        Returns:
            MuteStatus instance in muted state
        """
        status = cls()
        status.mute(duration_minutes, user, reason)
        return status
    
    @classmethod
    def create_snoozed(cls, duration_minutes: int = 5, user: Optional[str] = None) -> 'MuteStatus':
        """Create a snoozed status.
        
        Args:
            duration_minutes: Snooze duration in minutes
            user: User activating the snooze
            
        Returns:
            MuteStatus instance in snoozed state
        """
        status = cls(snooze_duration_minutes=duration_minutes)
        status.snooze(duration_minutes, user)
        return status
    
    def __str__(self) -> str:
        """String representation of mute status."""
        return self.get_mute_summary()
    
    def __repr__(self) -> str:
        """Developer representation of mute status."""
        return f"MuteStatus(is_muted={self.is_muted}, type={self.mute_type.value})"