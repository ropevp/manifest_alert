# Phase 2: Service Layer & Repository Implementation

## Priority: HIGH
## Estimated Time: 3-4 hours
## Dependencies: Phase 1 (Domain Models)

## Objective
Implement the data access layer and service infrastructure. This phase creates the repositories for data persistence and the caching system that enables the high-performance network operations required by the system.

## Background
The current system directly accesses files and network shares with custom caching logic scattered throughout. We need to centralize this into proper repository patterns with aggressive caching to maintain the 30-second network cache and 1-second timeout requirements.

## Acceptance Criteria

### ✅ Repository Pattern Implementation
- [ ] `ManifestRepository` for manifest data access
- [ ] `AcknowledgmentRepository` for acknowledgment persistence
- [ ] `MuteRepository` for centralized mute state
- [ ] `ConfigRepository` for configuration management
- [ ] Abstract base classes with concrete file-based implementations

### ✅ Caching Infrastructure
- [ ] `CacheManager` with 30-second network cache
- [ ] Fast cache layer with 5-second TTL
- [ ] Cache invalidation and refresh logic
- [ ] Memory-efficient cache storage
- [ ] Cache hit/miss metrics and logging

### ✅ Network Services
- [ ] `NetworkService` with 1-second timeout protection
- [ ] Retry logic for failed network operations
- [ ] Fallback strategies for network failures
- [ ] Network path validation and error handling

### ✅ Performance Requirements Met
- [ ] Network calls cached for 30 seconds minimum
- [ ] UI updates use fast cache (5-second TTL)
- [ ] Network timeouts never exceed 1 second
- [ ] Fallback to cached data when network unavailable

## Implementation Details

### File Structure to Create
```
src/
├── infrastructure/
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── manifest_repository.py
│   │   ├── acknowledgment_repository.py
│   │   ├── mute_repository.py
│   │   └── config_repository.py
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── cache_manager.py
│   │   └── cache_entry.py
│   └── network/
│       ├── __init__.py
│       ├── network_service.py
│       └── timeout_context.py
└── tests/
    └── unit/
        ├── test_repositories.py
        ├── test_cache_manager.py
        └── test_network_service.py
```

### Key Implementation Requirements

#### 1. Repository Pattern
```python
class ManifestRepository(ABC):
    @abstractmethod
    def load_manifests(self) -> List[Manifest]:
        pass
        
    @abstractmethod
    def save_manifest(self, manifest: Manifest) -> bool:
        pass

class FileManifestRepository(ManifestRepository):
    def __init__(self, cache_manager: CacheManager, logger: ManifestLogger):
        self.cache_manager = cache_manager
        self.logger = logger
    
    def load_manifests(self) -> List[Manifest]:
        # Implementation with caching and error handling
```

#### 2. Cache Manager with Aggressive Caching
```python
@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)

class CacheManager:
    def __init__(self):
        self.network_cache = {}  # 30-second TTL
        self.fast_cache = {}     # 5-second TTL
        
    def get_network_cached(self, key: str, fetch_func: Callable) -> Any:
        # 30-second cache for network operations
        
    def get_fast_cached(self, key: str, fetch_func: Callable) -> Any:
        # 5-second cache for UI updates
```

#### 3. Network Service with Timeout Protection
```python
class NetworkService:
    def __init__(self, timeout_seconds: float = 1.0):
        self.timeout_seconds = timeout_seconds
        
    def read_network_file(self, path: str) -> str:
        with timeout_context(self.timeout_seconds):
            # Network file operation with timeout
            
    def write_network_file(self, path: str, content: str) -> bool:
        with timeout_context(self.timeout_seconds):
            # Network write with timeout protection
```

## Critical Network Paths
- **Production Path**: `\\Prddpkmitlgt004\ManifestPC\`
- **Config File**: `\\Prddpkmitlgt004\ManifestPC\config.json`
- **Mute Status**: `\\Prddpkmitlgt004\ManifestPC\mute_status.json`
- **Acknowledgments**: `\\Prddpkmitlgt004\ManifestPC\ack.json`

## Performance Requirements
- **Network Cache**: 30-second TTL minimum
- **Fast Cache**: 5-second TTL for UI responsiveness
- **Timeout Protection**: 1-second maximum for any network call
- **Fallback Strategy**: Use cached data when network fails
- **Memory Efficiency**: Cache should not exceed 50MB

## Testing Requirements

### Unit Tests Must Cover
- [ ] Repository CRUD operations with mock data
- [ ] Cache hit/miss scenarios with TTL expiration
- [ ] Network timeout simulation and handling
- [ ] Fallback behavior when network unavailable
- [ ] Error conditions and exception handling
- [ ] Performance benchmarks against current system

### Integration Tests
- [ ] End-to-end data flow from network to cache to repository
- [ ] Cross-PC mute synchronization via network share
- [ ] Configuration changes propagated across system
- [ ] Network failure recovery scenarios

## Migration Strategy
- [ ] Repositories must work with existing file formats
- [ ] Cache must improve performance over current system
- [ ] Network operations must maintain existing synchronization
- [ ] No changes to shared network file structure

## Success Criteria
- [ ] All repositories implemented and tested
- [ ] Cache system operational with required TTLs
- [ ] Network operations never block longer than 1 second
- [ ] Performance equal or better than current system
- [ ] Unit tests pass with >90% coverage
- [ ] Integration tests validate cross-PC synchronization

## Risk Mitigation
- **Network Risk**: Comprehensive timeout and fallback handling
- **Performance Risk**: Benchmark cache effectiveness
- **Data Risk**: Validate repository operations preserve data integrity
- **Compatibility Risk**: Test with existing configuration files

## Reference Files
- Current caching logic: `alert_display.py` (search for cache-related functions)
- Network operations: `alert_display.py` (network file access patterns)
- Architecture spec: `OOP_REWRITE_SPECIFICATION.md` (Infrastructure Layer)

## Definition of Done
- All acceptance criteria completed
- Performance benchmarks meet or exceed current system
- Unit and integration tests passing
- Code reviewed for quality and performance
- Cache metrics demonstrate effectiveness
- Ready for Phase 3 integration
