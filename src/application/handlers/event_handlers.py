"""
Event handlers for domain and application events.

Implements the observer pattern to coordinate between services
and handle events like manifest updates, acknowledgments, and mute changes.
"""

from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from ...domain.events.domain_events import DomainEvent
from ...infrastructure.exceptions import BusinessLogicException


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Handle a domain event.
        
        Args:
            event: Domain event to handle
        """
        pass
    
    @abstractmethod
    def can_handle(self, event_type: type) -> bool:
        """Check if this handler can handle the given event type.
        
        Args:
            event_type: Type of event to check
            
        Returns:
            True if this handler can handle the event type
        """
        pass


class EventBus:
    """Event bus for coordinating application events.
    
    Implements the observer pattern to allow services to communicate
    through events rather than direct coupling.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the event bus.
        
        Args:
            logger: Optional logger instance
        """
        self.handlers: Dict[type, List[EventHandler]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logger or logging.getLogger(__name__)
        
        self.logger.info("EventBus initialized")
    
    def register_handler(self, event_type: type, handler: EventHandler) -> None:
        """Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Handler instance
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for {event_type.__name__}")
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to events by name.
        
        Args:
            event_name: Name of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        
        self.subscribers[event_name].append(callback)
        self.logger.debug(f"Subscribed to event: {event_name}")
    
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered handlers.
        
        Args:
            event: Domain event to publish
        """
        try:
            event_type = type(event)
            
            # Handle with registered handlers
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    try:
                        handler.handle(event)
                    except Exception as e:
                        self.logger.error(f"Error in event handler {handler.__class__.__name__}: {e}")
            
            # Notify subscribers
            event_name = event.__class__.__name__
            if event_name in self.subscribers:
                for callback in self.subscribers[event_name]:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"Error in event subscriber callback: {e}")
            
            self.logger.debug(f"Published event: {event_name}")
            
        except Exception as e:
            self.logger.error(f"Error publishing event {event.__class__.__name__}: {e}")
    
    def emit(self, event_name: str, data: Dict[str, Any]) -> None:
        """Emit a simple event by name.
        
        Args:
            event_name: Name of event to emit
            data: Event data dictionary
        """
        try:
            if event_name in self.subscribers:
                for callback in self.subscribers[event_name]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.error(f"Error in event callback for {event_name}: {e}")
            
            self.logger.debug(f"Emitted event: {event_name}")
            
        except Exception as e:
            self.logger.error(f"Error emitting event {event_name}: {e}")


class ManifestUpdatedHandler(EventHandler):
    """Handler for manifest update events."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """Initialize the handler.
        
        Args:
            event_bus: Event bus for emitting UI update events
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, event_type: type) -> bool:
        """Check if this handler can handle the event type."""
        from ...domain.events.domain_events import ManifestUpdatedEvent
        return issubclass(event_type, ManifestUpdatedEvent)
    
    def handle(self, event: DomainEvent) -> None:
        """Handle manifest updated event.
        
        Args:
            event: ManifestUpdatedEvent
        """
        try:
            self.logger.debug(f"Handling manifest update for {event.data.get('manifest_time')}")
            
            # Emit UI refresh event
            self.event_bus.emit('ui_refresh_needed', {
                'manifest_time': event.data.get('manifest_time'),
                'change_type': 'manifest_updated',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling manifest updated event: {e}")


class CarrierAcknowledgedHandler(EventHandler):
    """Handler for carrier acknowledgment events."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """Initialize the handler.
        
        Args:
            event_bus: Event bus for emitting UI update events
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, event_type: type) -> bool:
        """Check if this handler can handle the event type."""
        from ...domain.events.domain_events import CarrierAcknowledgedEvent
        return issubclass(event_type, CarrierAcknowledgedEvent)
    
    def handle(self, event: DomainEvent) -> None:
        """Handle carrier acknowledged event.
        
        Args:
            event: CarrierAcknowledgedEvent
        """
        try:
            manifest_time = event.data.get('manifest_time')
            carrier = event.data.get('carrier')
            user = event.data.get('user')
            
            self.logger.debug(f"Handling carrier acknowledgment: {carrier} in {manifest_time} by {user}")
            
            # Emit UI update event
            self.event_bus.emit('carrier_acknowledged', {
                'manifest_time': manifest_time,
                'carrier': carrier,
                'user': user,
                'timestamp': datetime.now().isoformat()
            })
            
            # Emit layout recalculation event
            self.event_bus.emit('layout_recalculation_needed', {
                'reason': 'carrier_acknowledged',
                'manifest_time': manifest_time,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling carrier acknowledged event: {e}")


class MuteStatusChangedHandler(EventHandler):
    """Handler for mute status change events."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """Initialize the handler.
        
        Args:
            event_bus: Event bus for emitting UI update events
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, event_type: type) -> bool:
        """Check if this handler can handle the event type."""
        from ...domain.events.domain_events import MuteStatusChangedEvent
        return issubclass(event_type, MuteStatusChangedEvent)
    
    def handle(self, event: DomainEvent) -> None:
        """Handle mute status changed event.
        
        Args:
            event: MuteStatusChangedEvent
        """
        try:
            is_muted = event.data.get('is_muted')
            muted_by = event.data.get('muted_by')
            
            self.logger.debug(f"Handling mute status change: muted={is_muted} by {muted_by}")
            
            # Emit UI update event
            self.event_bus.emit('mute_status_changed', {
                'is_muted': is_muted,
                'muted_by': muted_by,
                'timestamp': datetime.now().isoformat()
            })
            
            # Emit alert system update event
            self.event_bus.emit('alert_system_update', {
                'reason': 'mute_status_changed',
                'is_muted': is_muted,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling mute status changed event: {e}")


class AlertTriggeredHandler(EventHandler):
    """Handler for alert triggered events."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """Initialize the handler.
        
        Args:
            event_bus: Event bus for emitting UI update events
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, event_type: type) -> bool:
        """Check if this handler can handle the event type."""
        from ...domain.events.domain_events import AlertTriggeredEvent
        return issubclass(event_type, AlertTriggeredEvent)
    
    def handle(self, event: DomainEvent) -> None:
        """Handle alert triggered event.
        
        Args:
            event: AlertTriggeredEvent
        """
        try:
            manifest_time = event.data.get('manifest_time')
            alert_type = event.data.get('alert_type')
            priority = event.data.get('priority')
            
            self.logger.debug(f"Handling alert trigger: {alert_type} for {manifest_time} (priority: {priority})")
            
            # Emit audio alert event if needed
            if alert_type == 'audio':
                self.event_bus.emit('play_audio_alert', {
                    'manifest_time': manifest_time,
                    'priority': priority,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Emit visual alert event
            self.event_bus.emit('visual_alert_triggered', {
                'manifest_time': manifest_time,
                'alert_type': alert_type,
                'priority': priority,
                'timestamp': datetime.now().isoformat()
            })
            
            # Emit layout update for single card mode
            self.event_bus.emit('layout_recalculation_needed', {
                'reason': 'alert_triggered',
                'manifest_time': manifest_time,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error handling alert triggered event: {e}")


class EventHandlerRegistry:
    """Registry for managing event handlers.
    
    Provides a centralized way to register and configure all event handlers.
    """
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        """Initialize the registry.
        
        Args:
            event_bus: Event bus to register handlers with
            logger: Optional logger instance
        """
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)
        
        self._handlers: List[EventHandler] = []
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Set up all default event handlers."""
        try:
            # Create handlers
            manifest_handler = ManifestUpdatedHandler(self.event_bus, self.logger)
            acknowledgment_handler = CarrierAcknowledgedHandler(self.event_bus, self.logger)
            mute_handler = MuteStatusChangedHandler(self.event_bus, self.logger)
            alert_handler = AlertTriggeredHandler(self.event_bus, self.logger)
            
            self._handlers = [
                manifest_handler,
                acknowledgment_handler, 
                mute_handler,
                alert_handler
            ]
            
            # Register handlers with event bus
            from ...domain.events.domain_events import (
                ManifestUpdatedEvent, CarrierAcknowledgedEvent,
                MuteStatusChangedEvent, AlertTriggeredEvent
            )
            
            self.event_bus.register_handler(ManifestUpdatedEvent, manifest_handler)
            self.event_bus.register_handler(CarrierAcknowledgedEvent, acknowledgment_handler)
            self.event_bus.register_handler(MuteStatusChangedEvent, mute_handler)
            self.event_bus.register_handler(AlertTriggeredEvent, alert_handler)
            
            self.logger.info(f"Registered {len(self._handlers)} event handlers")
            
        except Exception as e:
            self.logger.error(f"Error setting up event handlers: {e}")
    
    def get_handlers(self) -> List[EventHandler]:
        """Get all registered handlers.
        
        Returns:
            List of event handler instances
        """
        return self._handlers.copy()
    
    def add_handler(self, event_type: type, handler: EventHandler) -> None:
        """Add a custom event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Handler instance
        """
        self.event_bus.register_handler(event_type, handler)
        self._handlers.append(handler)
        self.logger.debug(f"Added custom handler for {event_type.__name__}")


def create_default_event_system(logger: Optional[logging.Logger] = None) -> tuple:
    """Create a default event system with all handlers.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        Tuple of (event_bus, handler_registry)
    """
    event_bus = EventBus(logger)
    handler_registry = EventHandlerRegistry(event_bus, logger)
    
    return event_bus, handler_registry
