"""
Service Layer Package

This package contains the business logic services that orchestrate domain models
and infrastructure components to provide the core functionality of the manifest
alert system.

The service layer sits between the domain models and infrastructure, implementing
complex business rules and coordinating multiple repositories and external systems.

Services:
- ManifestService: Core manifest processing and scheduling logic
- AlertService: Alert generation, timing, and state management
- AcknowledgmentService: User acknowledgment processing and tracking
- MuteService: Centralized mute/snooze management with network synchronization
- ConfigService: Configuration management, validation, and defaults
"""

from .config_service import ConfigService, ConfigValidationResult
from .manifest_service import ManifestService, ManifestProcessingResult
from .alert_service import AlertService, LayoutMode, AlertFilter
from .mute_service import MuteService, MuteOperationResult, MuteStatistics
from .acknowledgment_service import AcknowledgmentService, AcknowledgmentResult, ManifestAckSummary

__all__ = [
    # Services
    'ConfigService',
    'ManifestService',
    'AlertService', 
    'MuteService',
    'AcknowledgmentService',
    
    # Data structures and results
    'ConfigValidationResult',
    'ManifestProcessingResult',
    'LayoutMode',
    'AlertFilter',
    'MuteOperationResult',
    'MuteStatistics',
    'AcknowledgmentResult',
    'ManifestAckSummary',
]
