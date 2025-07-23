# GitHub Copilot Instructions - Manifest Alerts System

## Project Overview

This is a **production manifest alert system** written in Python with PyQt6. The system displays real-time alerts for manifest carriers across multiple PCs with centralized mute synchronization via network share.

**CRITICAL**: This is a working production system. Any changes must preserve ALL existing functionality.

## Current Architecture

- **Monolithic Design**: Single `alert_display.py` file (2965 lines) containing all functionality
- **Network Synchronization**: Uses `\\Prddpkmitlgt004\ManifestPC\` for shared mute state
- **Performance Optimizations**: 30s network cache, 5s fast cache, 1s timeout protection
- **UI Framework**: PyQt6 with custom styling and multi-monitor support

## Key Features to Preserve

### Core Functionality
- Real-time manifest alert display with carrier-specific information
- Audio alerts with volume control and visual flashing
- Centralized mute system synchronized across multiple PCs
- Single alert scaling (maximizes single alerts when no missed alerts exist)
- CSV data import and configuration management
- Multi-monitor support with fullscreen capabilities

### Performance Requirements
- Network cache TTL: 30 seconds
- Fast cache TTL: 5 seconds  
- Network timeout: 1 second maximum
- UI responsiveness: <100ms for button clicks
- Memory usage: <100MB total

### Data Protection
- Backup/restore for critical data files
- Input validation for CSV imports
- Acknowledgment data integrity protection
- Configuration corruption recovery

## Current OOP Rewrite Project

We are implementing a complete OOP rewrite while preserving all functionality. Reference:
- **Implementation Guide**: `promptv4.md`
- **Architecture Specification**: `OOP_REWRITE_SPECIFICATION.md` (1750+ lines)
- **Current Working System**: `alert_display.py`

### Target Architecture
- **Domain Layer**: Models (Manifest, Carrier, Alert, Acknowledgment)
- **Infrastructure Layer**: Repositories, caching, network services
- **Application Layer**: Business logic services
- **Presentation Layer**: UI components and windows

## Coding Guidelines

### Code Quality Standards
```python
# Always use type hints
def process_manifest(manifest: Manifest) -> bool:
    """Process manifest with proper error handling."""
    
# Use dataclasses for models
@dataclass
class Manifest:
    name: str
    time: datetime
    carriers: List[Carrier]
    
# Implement proper error handling
try:
    result = network_operation()
except NetworkAccessException as e:
    logger.error(f"Network operation failed: {e}")
    return fallback_strategy()
```

### Performance Patterns
```python
# Use aggressive caching for network operations
@cached(ttl=30)  # 30 second cache for network calls
def load_mute_status() -> MuteStatus:
    return network_service.get_mute_status()

# Implement timeout protection
def network_call_with_timeout(path: str, timeout: float = 1.0):
    with timeout_context(timeout):
        return perform_network_operation(path)

# Use threading for non-blocking operations
def async_toggle_mute():
    threading.Thread(target=toggle_mute_operation, daemon=True).start()
```

### Error Handling Patterns
```python
# Comprehensive exception hierarchy
class ManifestAlertException(Exception): pass
class NetworkAccessException(ManifestAlertException): pass
class DataValidationException(ManifestAlertException): pass

# Fallback strategies for network failures
def load_data_with_fallbacks():
    try:
        return load_from_network()
    except NetworkAccessException:
        cached_data = cache_manager.get_cached_data()
        if cached_data:
            return cached_data
        return load_default_data()
```

## File Structure (Target)

```
src/
├── domain/
│   ├── models/         # Domain models (Manifest, Carrier, etc.)
│   └── events/         # Domain events
├── infrastructure/
│   ├── repositories/   # Data access layer
│   ├── cache/          # Caching implementation
│   ├── network/        # Network operations
│   └── logging/        # Logging framework
├── application/
│   ├── services/       # Business logic services
│   └── handlers/       # Event handlers
├── presentation/
│   ├── components/     # UI components
│   ├── windows/        # Main windows
│   └── styles/         # Theme management
└── config/             # Configuration management
```

## Testing Requirements

### Unit Testing
- Test all domain models with edge cases
- Mock external dependencies (network, files)
- Achieve >90% code coverage
- Test error conditions and recovery scenarios

### Integration Testing
- Test full workflows end-to-end
- Verify network synchronization across PCs
- Test UI responsiveness under load
- Validate data persistence and recovery

### Performance Testing
- Benchmark against current system performance
- Test with large datasets (1000+ manifests)
- Measure memory usage over time
- Validate cache effectiveness

## Common Patterns

### Repository Pattern
```python
class ManifestRepository(ABC):
    @abstractmethod
    def load_manifests(self) -> List[Manifest]:
        pass
        
    @abstractmethod
    def save_manifest(self, manifest: Manifest) -> bool:
        pass

class FileManifestRepository(ManifestRepository):
    def load_manifests(self) -> List[Manifest]:
        # Implementation with error handling and caching
```

### Service Pattern
```python
class AlertService:
    def __init__(self, manifest_repo: ManifestRepository, 
                 mute_service: MuteService):
        self.manifest_repo = manifest_repo
        self.mute_service = mute_service
    
    def calculate_layout_mode(self, manifests: List[Manifest]) -> LayoutMode:
        # Single alert scaling logic
        if len(manifests) == 1 and not self.has_missed_alerts():
            return LayoutMode.SINGLE_MAXIMIZED
        return LayoutMode.GRID
```

### UI Component Pattern
```python
class StatusCard(QWidget):
    def __init__(self, manifest: Manifest):
        super().__init__()
        self.manifest = manifest
        self.setup_ui()
    
    def set_maximized_mode(self, maximized: bool) -> None:
        # Dynamic layout switching for single alert scaling
        if maximized:
            self.apply_maximized_styling()
        else:
            self.apply_normal_styling()
```

## Network Path Configuration

**Production Network Path**: `\\Prddpkmitlgt004\ManifestPC\`

Critical files on network share:
- `config.json` - Global configuration
- `mute_status.json` - Centralized mute state
- `ack.json` - Acknowledgment data

## Dependencies

Core dependencies to maintain:
- **PyQt6**: GUI framework (v6.5.0+)
- **pygame**: Audio handling (v2.5.0+)
- **psutil**: System monitoring (v5.9.0+)

## Debugging Guidelines

### Performance Issues
1. Check network cache effectiveness (should hit cache 90%+ of time)
2. Monitor network timeout occurrences (should be <1% of calls)
3. Measure UI response times (should be <100ms)
4. Check memory usage patterns

### Network Issues
1. Verify network path accessibility: `\\Prddpkmitlgt004\ManifestPC\`
2. Check cache fallback behavior
3. Validate timeout protection is working
4. Test offline scenario handling

### UI Issues
1. Test single alert scaling behavior
2. Verify multi-monitor support
3. Check layout switching responsiveness
4. Validate audio/visual alert synchronization

## Migration Strategy

When implementing the OOP rewrite:
1. **Shadow Mode**: Run new system alongside current system
2. **Component Replacement**: Replace one component at a time
3. **Validation**: Ensure identical behavior at each step
4. **Rollback Plan**: Maintain ability to revert to current system

## Success Criteria

The rewrite is successful when:
- ✅ All current features work identically
- ✅ Performance equals or exceeds current system
- ✅ Code is maintainable and well-documented
- ✅ System is more testable and extensible
- ✅ No regressions in user experience

## Emergency Procedures

If the system breaks:
1. **Immediate**: Revert to `alert_display.py` (known working version)
2. **Investigation**: Check logs in `manifest_alerts.log`
3. **Network Issues**: Verify `\\Prddpkmitlgt004\ManifestPC\` accessibility
4. **Data Corruption**: Restore from backup in `backup/` directory

## Notes for AI Assistance

- Always preserve existing functionality when making changes
- Reference `OOP_REWRITE_SPECIFICATION.md` for architectural decisions
- Test changes against current system behavior
- Implement comprehensive error handling and logging
- Maintain performance standards (30s cache, 1s timeouts)
- Focus on incremental improvements rather than breaking changes