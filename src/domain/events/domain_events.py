"""
Domain Events for Manifest Alert System

Domain events represent important business occurrences that other parts of the system
may need to react to.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from abc import ABC


class DomainEvent(ABC):
    """Base class for all domain events."""
    
    def __init__(self):
        self.occurred_at = datetime.now()
        self.event_id = f"{self.__class__.__name__}_{self.occurred_at.strftime('%Y%m%d_%H%M%S_%f')}"


@dataclass
class ManifestCreatedEvent(DomainEvent):
    """Event raised when a new manifest is created."""
    
    def __init__(self, manifest_time: str, carrier_count: int, date: Optional[str] = None):
        super().__init__()
        self.manifest_time = manifest_time
        self.carrier_count = carrier_count
        self.date = date or datetime.now().strftime("%Y-%m-%d")


@dataclass
class CarrierAcknowledgedEvent(DomainEvent):
    """Event raised when a carrier is acknowledged."""
    
    def __init__(self, manifest_time: str, carrier_name: str, user: str, 
                 reason: Optional[str] = None, date: Optional[str] = None):
        super().__init__()
        self.manifest_time = manifest_time
        self.carrier_name = carrier_name
        self.user = user
        self.reason = reason
        self.date = date or datetime.now().strftime("%Y-%m-%d")


@dataclass
class ManifestFullyAcknowledgedEvent(DomainEvent):
    """Event raised when all carriers in a manifest are acknowledged."""
    
    def __init__(self, manifest_time: str, total_carriers: int, date: Optional[str] = None):
        super().__init__()
        self.manifest_time = manifest_time
        self.total_carriers = total_carriers
        self.date = date or datetime.now().strftime("%Y-%m-%d")


@dataclass
class AlertCreatedEvent(DomainEvent):
    """Event raised when an alert is created."""
    
    def __init__(self, alert_id: str, alert_type: str, priority: str, 
                 manifest_time: Optional[str] = None):
        super().__init__()
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.priority = priority
        self.manifest_time = manifest_time


@dataclass
class AlertAcknowledgedEvent(DomainEvent):
    """Event raised when an alert is acknowledged."""
    
    def __init__(self, alert_id: str, alert_type: str, 
                 manifest_time: Optional[str] = None):
        super().__init__()
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.manifest_time = manifest_time


@dataclass
class MuteStatusChangedEvent(DomainEvent):
    """Event raised when mute status changes."""
    
    def __init__(self, is_muted: bool, mute_type: str, user: Optional[str] = None,
                 duration_minutes: Optional[int] = None):
        super().__init__()
        self.is_muted = is_muted
        self.mute_type = mute_type
        self.user = user
        self.duration_minutes = duration_minutes


@dataclass
class ManifestMissedEvent(DomainEvent):
    """Event raised when a manifest time is missed."""
    
    def __init__(self, manifest_time: str, unacknowledged_carriers: list, 
                 date: Optional[str] = None):
        super().__init__()
        self.manifest_time = manifest_time
        self.unacknowledged_carriers = unacknowledged_carriers
        self.date = date or datetime.now().strftime("%Y-%m-%d")


@dataclass
class CarrierAddedEvent(DomainEvent):
    """Event raised when a carrier is added to a manifest."""
    
    def __init__(self, manifest_time: str, carrier_name: str, date: Optional[str] = None):
        super().__init__()
        self.manifest_time = manifest_time
        self.carrier_name = carrier_name
        self.date = date or datetime.now().strftime("%Y-%m-%d")


@dataclass
class CarrierRemovedEvent(DomainEvent):
    """Event raised when a carrier is removed from a manifest."""
    
    def __init__(self, manifest_time: str, carrier_name: str, date: Optional[str] = None):
        super().__init__()
        self.manifest_time = manifest_time
        self.carrier_name = carrier_name
        self.date = date or datetime.now().strftime("%Y-%m-%d")


# Event registry for tracking and handling domain events
class DomainEventRegistry:
    """Registry for managing domain events and their handlers."""
    
    def __init__(self):
        self._events: list = []
        self._handlers: Dict[type, list] = {}
    
    def register_handler(self, event_type: type, handler: callable):
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def raise_event(self, event: DomainEvent):
        """Raise a domain event and notify all registered handlers."""
        self._events.append(event)
        
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't let it stop other handlers
                    print(f"Error in event handler for {event_type.__name__}: {e}")
    
    def get_events(self, event_type: Optional[type] = None) -> list:
        """Get events from the registry, optionally filtered by type."""
        if event_type is None:
            return self._events.copy()
        return [event for event in self._events if isinstance(event, event_type)]
    
    def clear_events(self):
        """Clear all events from the registry."""
        self._events.clear()


# Global event registry instance
_global_event_registry = DomainEventRegistry()


def get_event_registry() -> DomainEventRegistry:
    """Get the global event registry."""
    return _global_event_registry


def raise_domain_event(event: DomainEvent):
    """Convenience function to raise a domain event."""
    _global_event_registry.raise_event(event)