# Manifest Alerts OOP Rewrite Implementation Prompt v4

## Context & Objective

You are implementing a complete Object-Oriented Programming (OOP) rewrite of a working manifest alert system. The current system is a 2965-line monolithic Python application that works perfectly but needs architectural improvements for maintainability and extensibility.

**CRITICAL**: This is a working production system. The rewrite must preserve ALL existing functionality while improving code architecture.

## Current System Overview

The existing system (`alert_display.py`) provides:
- Real-time manifest alert display with carrier-specific alerts
- Centralized mute system synchronized across multiple PCs via network share
- Single alert scaling feature (maximizes single alerts when no missed alerts exist)
- Audio alerts with volume control and visual flashing
- CSV data import and configuration management
- Performance optimizations (30s network cache, 1s timeout protection)
- Multi-monitor support with fullscreen capabilities

## Implementation Strategy

### Phase-Based Approach
Implement in phases to minimize bugs and enable incremental testing:

1. **Phase 1**: Domain Models & Core Infrastructure
2. **Phase 2**: Service Layer & Repository Implementation  
3. **Phase 3**: Application Services & Business Logic
4. **Phase 4**: UI Components & Presentation Layer
5. **Phase 5**: Integration & Performance Optimization
6. **Phase 6**: Testing & Migration

### Quality Assurance
- Create comprehensive test files for each component
- Maintain backward compatibility throughout
- Implement error handling and logging from the start
- Use the existing system as reference for expected behavior

## Detailed Implementation Instructions

### Phase 1: Domain Models & Core Infrastructure

**Files to Create:**
```
src/
├── domain/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── manifest.py
│   │   ├── carrier.py
│   │   ├── acknowledgment.py
│   │   ├── alert.py
│   │   └── mute_status.py
│   └── events/
│       ├── __init__.py
│       └── domain_events.py
├── infrastructure/
│   ├── __init__.py
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py
│   └── exceptions/
│       ├── __init__.py
│       └── custom_exceptions.py
└── __init__.py
```

**Implementation Requirements:**

1. **Domain Models** - Create dataclasses with validation:
```python
# Example structure for manifest.py
@dataclass
class Manifest:
    name: str
    time: datetime
    carriers: List[Carrier]
    acknowledged: bool = False
    missed: bool = False
    
    def __post_init__(self):
        # Validation logic
        
    def acknowledge(self, user: str) -> None:
        # Business logic
```

2. **Exception Hierarchy** - Implement from specification:
```python
class ManifestAlertException(Exception): pass
class NetworkAccessException(ManifestAlertException): pass
class DataValidationException(ManifestAlertException): pass
# ... etc
```

3. **Logging Framework** - Create ManifestLogger class with file/console handlers

### Phase 2: Service Layer & Repository Implementation

**Files to Create:**
```
src/
├── infrastructure/
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── manifest_repository.py
│   │   ├── acknowledgment_repository.py
│   │   ├── mute_repository.py
│   │   └── config_repository.py
│   ├── cache/
│   │   ├── __init__.py
│   │   └── cache_manager.py
│   └── network/
│       ├── __init__.py
│       └── network_service.py
```

**Implementation Requirements:**

1. **Repository Pattern** - Abstract data access:
```python
class ManifestRepository(ABC):
    @abstractmethod
    def load_manifests(self) -> List[Manifest]: pass
    
    @abstractmethod
    def save_manifest(self, manifest: Manifest) -> bool: pass
```

2. **Cache Manager** - Implement aggressive caching (30s network, 5s fast):
```python
class CacheManager:
    def __init__(self):
        self.network_cache = {}  # 30s TTL
        self.fast_cache = {}     # 5s TTL
```

3. **Network Service** - Handle timeout protection and failure recovery

### Phase 3: Application Services & Business Logic

**Files to Create:**
```
src/
├── application/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── manifest_service.py
│   │   ├── alert_service.py
│   │   ├── mute_service.py
│   │   ├── acknowledgment_service.py
│   │   └── layout_service.py
│   └── handlers/
│       ├── __init__.py
│       └── event_handlers.py
```

**Implementation Requirements:**

1. **Business Logic Services**:
```python
class AlertService:
    def calculate_layout_mode(self, manifests: List[Manifest]) -> LayoutMode:
        # Single alert scaling logic
        
    def should_trigger_alert(self, manifest: Manifest) -> bool:
        # Alert triggering logic
```

2. **Event Handling** - Implement observer pattern for UI updates

### Phase 4: UI Components & Presentation Layer

**Files to Create:**
```
src/
├── presentation/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── status_card.py
│   │   ├── control_panel.py
│   │   ├── countdown_display.py
│   │   └── layout_manager.py
│   ├── windows/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   └── config_dialog.py
│   └── styles/
│       ├── __init__.py
│       └── theme_manager.py
```

**Implementation Requirements:**

1. **Component Architecture** - Separate UI components with clear responsibilities
2. **Layout Management** - Implement dynamic layout switching for single alert scaling
3. **Theme System** - Extract styling into theme manager

### Phase 5: Integration & Performance Optimization

**Files to Create:**
```
src/
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── dependency_injection.py
└── utils/
    ├── __init__.py
    ├── file_utils.py
    └── time_utils.py
```

**Implementation Requirements:**

1. **Dependency Injection** - Wire all components together
2. **Configuration Management** - Centralized settings
3. **Performance Monitoring** - Implement health checks and monitoring

### Phase 6: Testing & Migration

**Files to Create:**
```
tests/
├── __init__.py
├── unit/
│   ├── test_domain_models.py
│   ├── test_services.py
│   └── test_repositories.py
├── integration/
│   ├── test_ui_components.py
│   └── test_end_to_end.py
└── fixtures/
    ├── sample_config.json
    └── test_data.csv
```

## Critical Implementation Guidelines

### 1. **Preserve Existing Functionality**
- Study `alert_display.py` thoroughly before implementing each component
- Maintain exact same user experience and behavior
- Test against current system continuously

### 2. **Performance Requirements**
- Network cache: 30 seconds TTL
- Fast cache: 5 seconds TTL
- Network timeout: 1 second maximum
- UI responsiveness: <100ms for button clicks
- Memory usage: <100MB total

### 3. **Error Handling Strategy**
- Implement comprehensive exception handling from start
- Use fallback strategies for network failures
- Log all errors with context
- Never crash - always provide graceful degradation

### 4. **Data Protection**
- Implement backup/restore for critical data
- Validate all input data (especially CSV imports)
- Protect acknowledgment data integrity
- Handle configuration corruption gracefully

### 5. **Network Reliability**
- Use `\\Prddpkmitlgt004\ManifestPC\` path for shared files
- Implement aggressive caching to minimize network calls
- Provide offline fallback capabilities
- Handle network drive disconnections

## Testing Strategy

### Unit Testing Requirements
- Test all domain models with edge cases
- Mock external dependencies (network, files)
- Achieve >90% code coverage
- Test error conditions and recovery

### Integration Testing
- Test full workflows end-to-end
- Verify network synchronization across PCs
- Test UI responsiveness under load
- Validate data persistence and recovery

### Performance Testing
- Benchmark against current system
- Test with large datasets (1000+ manifests)
- Measure memory usage over time
- Validate cache effectiveness

## Migration Strategy

### Incremental Migration
1. **Shadow Mode**: Run new system alongside old system
2. **Component Replacement**: Replace components one at a time
3. **Validation**: Ensure identical behavior at each step
4. **Rollback Plan**: Maintain ability to revert to old system

### Data Migration
- Preserve existing configuration files
- Maintain backward compatibility with current data formats
- Migrate acknowledgment history
- Backup all data before migration

## Success Criteria

### Functional Requirements ✅
- All current features work identically
- Single alert scaling functions correctly
- Mute synchronization works across PCs
- Performance equal or better than current system
- No regressions in user experience

### Technical Requirements ✅
- Clean OOP architecture with separation of concerns
- Comprehensive test coverage (>90%)
- Proper error handling and logging
- Maintainable and extensible codebase
- Documentation for all components

### Quality Requirements ✅
- Code is readable and well-documented
- Easy to add new features
- Deployment is automated
- System is reliable and stable

## File References

**Current Implementation**: `alert_display.py` (2965 lines)
**Architecture Specification**: `OOP_REWRITE_SPECIFICATION.md` (1750+ lines)
**Performance Baseline**: Existing system with 30s cache, 1s timeouts

## Implementation Notes

- **Start with Phase 1** and complete each phase fully before moving to next
- **Create test files** for each component as you build it
- **Refer to specification** for detailed class designs and interactions
- **Test frequently** against the current working system
- **Maintain performance** - the system must be as fast or faster than current
- **Document as you go** - include docstrings and type hints
- **Use existing patterns** from current codebase where they work well

## Final Reminders

This is a **production system rewrite** - treat it with appropriate care and attention to detail. The goal is not just to make it work, but to make it maintainable, extensible, and robust for future development while preserving all current functionality perfectly.

Every component should be built with error handling, logging, and testing in mind from the start. The new system should feel identical to users while being much easier for developers to work with.

**Begin with Phase 1: Domain Models & Core Infrastructure**
