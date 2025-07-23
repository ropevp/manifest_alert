# Phase 3: Application Services & Business Logic

## Priority: HIGH
## Estimated Time: 3-4 hours
## Dependencies: Phase 1 (Domain Models), Phase 2 (Repositories)

## Objective
Implement the core business logic services that orchestrate the application's behavior. This phase includes the critical single alert scaling feature and all alert management logic.

## Background
The current system has business logic scattered throughout the monolithic file. We need to extract this into dedicated service classes that handle alert triggering, layout decisions, acknowledgment processing, and the new single alert scaling feature.

## Acceptance Criteria

### ✅ Core Business Services
- [ ] `AlertService` for alert triggering and management
- [ ] `MuteService` for centralized mute operations
- [ ] `AcknowledgmentService` for tracking user acknowledgments
- [ ] `LayoutService` for dynamic layout management
- [ ] `ManifestService` for manifest data orchestration

### ✅ Single Alert Scaling Feature
- [ ] Detect when only one alert exists with no missed alerts
- [ ] Automatically switch to maximized single alert display
- [ ] Dynamic layout switching between grid and single modes
- [ ] Preserve all existing multi-alert functionality
- [ ] Handle transitions smoothly without UI flicker

### ✅ Event-Driven Architecture
- [ ] Domain events for alert state changes
- [ ] Event handlers for UI updates
- [ ] Observer pattern for loose coupling
- [ ] Event persistence for audit trails

### ✅ Business Logic Rules
- [ ] Alert triggering logic (time-based, acknowledgment status)
- [ ] Mute duration calculations and expiry
- [ ] Acknowledgment validation and persistence
- [ ] Layout mode determination algorithms

## Implementation Details

### File Structure to Create
```
src/
├── application/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_service.py
│   │   ├── mute_service.py
│   │   ├── acknowledgment_service.py
│   │   ├── layout_service.py
│   │   └── manifest_service.py
│   └── handlers/
│       ├── __init__.py
│       ├── alert_event_handler.py
│       └── layout_event_handler.py
├── domain/
│   └── events/
│       ├── alert_events.py
│       └── layout_events.py
└── tests/
    └── unit/
        ├── test_alert_service.py
        ├── test_mute_service.py
        ├── test_layout_service.py
        └── test_acknowledgment_service.py
```

### Key Implementation Requirements

#### 1. Alert Service with Single Alert Scaling
```python
class AlertService:
    def __init__(self, manifest_repo: ManifestRepository, 
                 mute_service: MuteService,
                 layout_service: LayoutService):
        self.manifest_repo = manifest_repo
        self.mute_service = mute_service
        self.layout_service = layout_service
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        manifests = self.manifest_repo.load_manifests()
        return [self.create_alert(m) for m in manifests if self.should_trigger_alert(m)]
    
    def should_trigger_alert(self, manifest: Manifest) -> bool:
        """Determine if manifest should trigger an alert"""
        if manifest.acknowledged:
            return False
        if self.mute_service.is_muted():
            return False
        # Additional business rules...
        
    def calculate_layout_mode(self, alerts: List[Alert]) -> LayoutMode:
        """CRITICAL: Single alert scaling logic"""
        missed_alerts = self.get_missed_alerts()
        
        # Single alert scaling: maximize when only one alert and no missed alerts
        if len(alerts) == 1 and len(missed_alerts) == 0:
            return LayoutMode.SINGLE_MAXIMIZED
        
        return LayoutMode.GRID
```

#### 2. Layout Service for Dynamic Switching
```python
class LayoutService:
    def __init__(self, event_dispatcher: EventDispatcher):
        self.event_dispatcher = event_dispatcher
        self.current_mode = LayoutMode.GRID
    
    def update_layout_mode(self, alerts: List[Alert], missed_alerts: List[Alert]) -> None:
        """Update layout mode based on current alert state"""
        new_mode = self.calculate_optimal_layout(alerts, missed_alerts)
        
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.event_dispatcher.dispatch(LayoutModeChangedEvent(new_mode))
    
    def calculate_optimal_layout(self, alerts: List[Alert], missed_alerts: List[Alert]) -> LayoutMode:
        """Calculate optimal layout mode"""
        # Single alert scaling logic
        if len(alerts) == 1 and len(missed_alerts) == 0:
            return LayoutMode.SINGLE_MAXIMIZED
        
        # Grid mode for multiple alerts or missed alerts
        return LayoutMode.GRID
```

#### 3. Mute Service with Cross-PC Synchronization
```python
class MuteService:
    def __init__(self, mute_repo: MuteRepository, cache_manager: CacheManager):
        self.mute_repo = mute_repo
        self.cache_manager = cache_manager
    
    def is_muted(self) -> bool:
        """Check if system is currently muted (uses fast cache)"""
        return self.cache_manager.get_fast_cached(
            "mute_status",
            lambda: self.mute_repo.load_mute_status().muted
        )
    
    def toggle_mute(self, duration_minutes: int = 5) -> bool:
        """Toggle mute state with cross-PC synchronization"""
        try:
            current_status = self.mute_repo.load_mute_status()
            
            if current_status.muted:
                new_status = MuteStatus(muted=False, until=None)
            else:
                until_time = datetime.now() + timedelta(minutes=duration_minutes)
                new_status = MuteStatus(muted=True, until=until_time)
            
            success = self.mute_repo.save_mute_status(new_status)
            if success:
                self.cache_manager.invalidate_cache("mute_status")
            
            return success
        except Exception as e:
            self.logger.error(f"Mute toggle failed: {e}")
            return False
```

#### 4. Acknowledgment Service
```python
class AcknowledgmentService:
    def __init__(self, ack_repo: AcknowledgmentRepository, 
                 event_dispatcher: EventDispatcher):
        self.ack_repo = ack_repo
        self.event_dispatcher = event_dispatcher
    
    def acknowledge_manifest(self, manifest_name: str, user: str, reason: str = "") -> bool:
        """Acknowledge a manifest"""
        acknowledgment = Acknowledgment(
            manifest_name=manifest_name,
            user=user,
            timestamp=datetime.now(),
            reason=reason
        )
        
        success = self.ack_repo.save_acknowledgment(acknowledgment)
        if success:
            self.event_dispatcher.dispatch(ManifestAcknowledgedEvent(acknowledgment))
        
        return success
```

## Single Alert Scaling Requirements

### Critical Behavior
- **Detection Logic**: Exactly one active alert AND zero missed alerts
- **Layout Switching**: Automatic transition to maximized single alert display
- **Responsive Transitions**: Smooth switching without UI flicker
- **Fallback Behavior**: Return to grid mode when conditions not met
- **Performance**: Layout calculations must complete in <10ms

### Test Scenarios
```python
def test_single_alert_scaling_scenarios():
    # Test case 1: Single alert, no missed alerts → SINGLE_MAXIMIZED
    alerts = [create_test_alert("Manifest A")]
    missed_alerts = []
    assert layout_service.calculate_optimal_layout(alerts, missed_alerts) == LayoutMode.SINGLE_MAXIMIZED
    
    # Test case 2: Single alert, with missed alerts → GRID
    alerts = [create_test_alert("Manifest A")]
    missed_alerts = [create_test_alert("Missed Manifest")]
    assert layout_service.calculate_optimal_layout(alerts, missed_alerts) == LayoutMode.GRID
    
    # Test case 3: Multiple alerts → GRID
    alerts = [create_test_alert("Manifest A"), create_test_alert("Manifest B")]
    missed_alerts = []
    assert layout_service.calculate_optimal_layout(alerts, missed_alerts) == LayoutMode.GRID
```

## Performance Requirements
- **Service calls**: <10ms for all business logic operations
- **Layout calculations**: <5ms for mode determination
- **Event processing**: <1ms for event dispatch
- **Memory usage**: <20MB for all service instances

## Testing Requirements

### Unit Tests Must Cover
- [ ] Alert triggering logic with various manifest states
- [ ] Single alert scaling detection and mode switching
- [ ] Mute service operations with network caching
- [ ] Acknowledgment processing and validation
- [ ] Event handling and dispatch mechanisms
- [ ] Error conditions and fallback behaviors

### Integration Tests
- [ ] End-to-end alert workflow from detection to acknowledgment
- [ ] Cross-PC mute synchronization
- [ ] Layout mode transitions in real UI scenarios
- [ ] Performance under load (100+ manifests)

## Success Criteria
- [ ] All business services implemented and tested
- [ ] Single alert scaling feature working correctly
- [ ] Event-driven architecture operational
- [ ] Cross-PC mute synchronization maintained
- [ ] Performance requirements met
- [ ] Unit tests pass with >90% coverage

## Risk Mitigation
- **Logic Risk**: Extensive testing of single alert scaling edge cases
- **Performance Risk**: Benchmark service operations
- **Synchronization Risk**: Test cross-PC mute scenarios thoroughly
- **Event Risk**: Validate event ordering and reliability

## Reference Files
- Current business logic: `alert_display.py` (alert triggering and layout logic)
- Single alert scaling: `alert_display.py` (search for scaling/maximized patterns)
- Architecture spec: `OOP_REWRITE_SPECIFICATION.md` (Application Layer)

## Definition of Done
- All acceptance criteria completed
- Single alert scaling feature fully implemented and tested
- Business logic extracted from monolithic system
- Event-driven architecture operational
- Performance benchmarks meet requirements
- Ready for Phase 4 UI integration
