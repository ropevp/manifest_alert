# Phase 1: Domain Models & Core Infrastructure

## Priority: CRITICAL
## Estimated Time: 2-3 hours
## Dependencies: None

## Objective
Create the foundational domain models and core infrastructure for the OOP rewrite. This phase establishes the data structures and basic framework that all other phases will build upon.

## Background
The current `alert_display.py` system works with raw dictionaries and loosely structured data. We need to create strongly-typed domain models that represent the core business concepts while preserving all existing functionality.

## Acceptance Criteria

### ✅ Domain Models Created
- [ ] `Manifest` model with time, carriers, acknowledgment status
- [ ] `Carrier` model with name and status information  
- [ ] `Acknowledgment` model with user, timestamp, reason
- [ ] `Alert` model representing active alerts
- [ ] `MuteStatus` model for centralized mute state

### ✅ Core Infrastructure
- [ ] Exception hierarchy with base `ManifestAlertException`
- [ ] Logging framework with file and console handlers
- [ ] Type definitions and enums for common values
- [ ] Validation logic for all domain models

### ✅ Quality Standards
- [ ] All models use dataclasses with type hints
- [ ] Comprehensive docstrings for all classes and methods
- [ ] Input validation with proper error messages
- [ ] Unit tests for all domain models (>90% coverage)

## Implementation Details

### File Structure to Create
```
src/
├── __init__.py
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
└── tests/
    ├── __init__.py
    └── unit/
        ├── __init__.py
        ├── test_manifest.py
        ├── test_carrier.py
        ├── test_acknowledgment.py
        ├── test_alert.py
        └── test_mute_status.py
```

### Key Implementation Requirements

#### 1. Manifest Model
```python
@dataclass
class Manifest:
    name: str
    time: datetime
    carriers: List[Carrier]
    acknowledged: bool = False
    missed: bool = False
    acknowledgment_details: Optional[Acknowledgment] = None
    
    def __post_init__(self):
        # Validation logic
        
    def acknowledge(self, user: str, reason: str = "") -> None:
        # Business logic for acknowledgment
        
    def is_active(self) -> bool:
        # Determine if manifest should trigger alerts
```

#### 2. Exception Hierarchy
```python
class ManifestAlertException(Exception):
    """Base exception for all manifest alert system errors"""
    pass

class NetworkAccessException(ManifestAlertException):
    """Raised when network file operations fail"""
    pass

class DataValidationException(ManifestAlertException):
    """Raised when data validation fails"""
    pass

class ConfigurationException(ManifestAlertException):
    """Raised when configuration is invalid or missing"""
    pass
```

#### 3. Logging Framework
```python
class ManifestLogger:
    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.setup_logging(log_level)
    
    def setup_logging(self, log_level: str):
        # Configure file and console handlers
        
    def log_network_operation(self, operation: str, path: str, success: bool, duration: float):
        # Log network operations with performance metrics
```

## Testing Requirements

### Unit Tests Must Cover
- [ ] Model validation with valid and invalid data
- [ ] Business logic methods (acknowledge, is_active, etc.)
- [ ] Edge cases (empty carriers, invalid times, etc.)
- [ ] Error conditions and exception handling
- [ ] Data serialization/deserialization if implemented

### Test Data Examples
```python
# Valid test cases
valid_manifest = Manifest(
    name="Test Manifest",
    time=datetime.now(),
    carriers=[Carrier("Test Carrier")]
)

# Invalid test cases
invalid_manifest_empty_name = Manifest(
    name="",  # Should fail validation
    time=datetime.now(),
    carriers=[]
)
```

## Performance Considerations
- Models should be lightweight and fast to construct
- Validation should be efficient (avoid expensive operations)
- Consider lazy loading for large carrier lists
- Memory usage should be minimal

## Integration Points
- Models must be compatible with current CSV data format
- Must support serialization to/from JSON for network storage
- Should integrate with existing configuration structure
- Must preserve all current data fields and behaviors

## Success Criteria
- [ ] All domain models created and tested
- [ ] Exception hierarchy fully implemented
- [ ] Logging framework operational
- [ ] Unit tests pass with >90% coverage
- [ ] No regressions in data handling compared to current system
- [ ] Models can represent all current system data accurately

## Risk Mitigation
- **Data Loss Risk**: Ensure models can represent all existing data
- **Performance Risk**: Benchmark model creation against current system
- **Integration Risk**: Validate models work with existing CSV files
- **Validation Risk**: Test edge cases thoroughly

## Reference Files
- Current implementation: `alert_display.py` (lines with data structures)
- Architecture spec: `OOP_REWRITE_SPECIFICATION.md` (Domain Models section)
- Performance requirements: `promptv4.md` (Performance Requirements)

## Definition of Done
- All acceptance criteria checked off
- Unit tests passing with >90% coverage
- Code reviewed for quality and consistency
- Documentation complete with examples
- Performance validated against current system
- Ready for Phase 2 integration
