# Phase 5: Integration & Performance Optimization

## Priority: HIGH
## Estimated Time: 3-4 hours
## Dependencies: Phases 1-4 (All previous phases)

## Objective
Integrate all components into a cohesive system and optimize performance to meet or exceed the current system's benchmarks. This phase includes dependency injection, configuration management, and performance validation.

## Background
With all individual components built, we need to wire them together using proper dependency injection and ensure the integrated system meets the strict performance requirements (30s cache, 1s timeouts, <100ms UI response).

## Acceptance Criteria

### ✅ System Integration
- [ ] Dependency injection container for all services
- [ ] Application startup and initialization sequence
- [ ] Configuration management and validation
- [ ] Error handling and logging integration
- [ ] Graceful shutdown and cleanup

### ✅ Performance Optimization
- [ ] Network cache effectiveness >90% hit rate
- [ ] UI response times <100ms for all interactions
- [ ] Memory usage <100MB total
- [ ] Network timeouts never exceed 1 second
- [ ] System startup time <5 seconds

### ✅ Configuration Management
- [ ] Centralized settings management
- [ ] Environment-specific configurations
- [ ] Configuration validation and defaults
- [ ] Runtime configuration updates
- [ ] Configuration backup and recovery

### ✅ Monitoring & Health Checks
- [ ] Performance metrics collection
- [ ] System health monitoring
- [ ] Network connectivity validation
- [ ] Cache performance tracking
- [ ] Error rate monitoring

## Implementation Details

### File Structure to Create
```
src/
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── dependency_injection.py
│   └── config_validator.py
├── utils/
│   ├── __init__.py
│   ├── file_utils.py
│   ├── time_utils.py
│   └── performance_monitor.py
└── tests/
    ├── integration/
    │   ├── test_full_system.py
    │   ├── test_performance.py
    │   └── test_cross_pc_sync.py
    └── fixtures/
        ├── test_config.json
        └── sample_manifests.csv
```

### Key Implementation Requirements

#### 1. Dependency Injection Container
```python
class DependencyContainer:
    def __init__(self):
        self._services = {}
        self._singletons = {}
        self.setup_dependencies()
    
    def setup_dependencies(self) -> None:
        """Configure all service dependencies"""
        # Infrastructure layer
        self.register_singleton(ManifestLogger, lambda: ManifestLogger("manifest_alerts"))
        self.register_singleton(CacheManager, lambda: CacheManager())
        self.register_singleton(NetworkService, lambda: NetworkService(timeout_seconds=1.0))
        
        # Repository layer
        self.register(ManifestRepository, lambda: FileManifestRepository(
            self.get(CacheManager), 
            self.get(ManifestLogger)
        ))
        
        # Service layer
        self.register(AlertService, lambda: AlertService(
            self.get(ManifestRepository),
            self.get(MuteService),
            self.get(LayoutService)
        ))
        
        # UI layer
        self.register(MainWindow, lambda: MainWindow(
            self.get(AlertService),
            self.get(MuteService),
            self.get(LayoutService)
        ))
    
    def register_singleton(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a singleton service"""
        self._singletons[interface] = factory
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance"""
        if interface in self._singletons:
            if interface not in self._services:
                self._services[interface] = self._singletons[interface]()
            return self._services[interface]
        
        raise ValueError(f"Service not registered: {interface}")
```

#### 2. Application Main Entry Point
```python
class ManifestAlertApplication:
    def __init__(self):
        self.container = DependencyContainer()
        self.logger = self.container.get(ManifestLogger)
        self.performance_monitor = PerformanceMonitor(self.logger)
        
    def run(self) -> int:
        """Run the manifest alert application"""
        try:
            self.logger.logger.info("Starting Manifest Alert System v3.3")
            
            # Initialize PyQt6 application
            app = QApplication(sys.argv)
            app.setApplicationName("Manifest Alerts")
            app.setApplicationVersion("3.3.0")
            
            # Validate system requirements
            if not self.validate_system_requirements():
                return 1
            
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            # Create and show main window
            main_window = self.container.get(MainWindow)
            main_window.show()
            
            # Run application event loop
            return app.exec()
            
        except Exception as e:
            self.logger.logger.error(f"Application startup failed: {e}")
            return 1
        finally:
            self.cleanup()
    
    def validate_system_requirements(self) -> bool:
        """Validate system meets requirements"""
        # Check network access
        network_service = self.container.get(NetworkService)
        if not network_service.test_network_access():
            self.logger.logger.error("Network drive not accessible")
            return False
        
        # Check memory availability
        import psutil
        if psutil.virtual_memory().available < 200 * 1024 * 1024:  # 200MB
            self.logger.logger.error("Insufficient memory available")
            return False
        
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self.performance_monitor.stop_monitoring()
        self.logger.logger.info("Application shutdown complete")

def main() -> int:
    """Application entry point"""
    app = ManifestAlertApplication()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
```

#### 3. Performance Monitor
```python
class PerformanceMonitor:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "network_timeouts": 0,
            "ui_response_times": [],
            "memory_usage": []
        }
        self.monitoring_active = False
        
    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        self.monitoring_active = True
        
        # Start metrics collection thread
        def monitor_loop():
            while self.monitoring_active:
                self.collect_metrics()
                time.sleep(30)  # Collect metrics every 30 seconds
        
        threading.Thread(target=monitor_loop, daemon=True).start()
    
    def collect_metrics(self) -> None:
        """Collect system performance metrics"""
        import psutil
        
        # Memory usage
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.metrics["memory_usage"].append(memory_mb)
        
        # Keep only last 100 measurements
        if len(self.metrics["memory_usage"]) > 100:
            self.metrics["memory_usage"] = self.metrics["memory_usage"][-100:]
        
        # Log if memory usage exceeds threshold
        if memory_mb > 100:
            self.logger.logger.warning(f"High memory usage: {memory_mb:.1f}MB")
    
    def record_cache_hit(self) -> None:
        """Record cache hit"""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self) -> None:
        """Record cache miss"""
        self.metrics["cache_misses"] += 1
    
    def record_network_timeout(self) -> None:
        """Record network timeout"""
        self.metrics["network_timeouts"] += 1
        self.logger.logger.warning("Network timeout occurred")
    
    def record_ui_response_time(self, response_time_ms: float) -> None:
        """Record UI response time"""
        self.metrics["ui_response_times"].append(response_time_ms)
        
        # Keep only last 100 measurements
        if len(self.metrics["ui_response_times"]) > 100:
            self.metrics["ui_response_times"] = self.metrics["ui_response_times"][-100:]
        
        # Alert if response time exceeds threshold
        if response_time_ms > 100:
            self.logger.logger.warning(f"Slow UI response: {response_time_ms:.1f}ms")
    
    def get_performance_report(self) -> dict:
        """Generate performance report"""
        total_cache_ops = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        avg_response_time = sum(self.metrics["ui_response_times"]) / len(self.metrics["ui_response_times"]) if self.metrics["ui_response_times"] else 0
        
        avg_memory = sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0
        
        return {
            "cache_hit_rate_percent": cache_hit_rate,
            "average_ui_response_ms": avg_response_time,
            "average_memory_mb": avg_memory,
            "network_timeouts": self.metrics["network_timeouts"]
        }
```

#### 4. Configuration Management
```python
class ConfigurationManager:
    def __init__(self, logger: ManifestLogger):
        self.logger = logger
        self.config = {}
        self.config_path = "config.json"
        self.network_config_path = r"\\Prddpkmitlgt004\ManifestPC\config.json"
        
    def load_configuration(self) -> dict:
        """Load configuration with fallback strategy"""
        # Try network configuration first
        try:
            if os.path.exists(self.network_config_path):
                with open(self.network_config_path, 'r') as f:
                    network_config = json.load(f)
                self.logger.logger.info("Loaded configuration from network")
                return network_config
        except Exception as e:
            self.logger.logger.warning(f"Failed to load network config: {e}")
        
        # Fallback to local configuration
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    local_config = json.load(f)
                self.logger.logger.info("Loaded configuration from local file")
                return local_config
        except Exception as e:
            self.logger.logger.warning(f"Failed to load local config: {e}")
        
        # Ultimate fallback to default configuration
        self.logger.logger.warning("Using default configuration")
        return self.get_default_configuration()
    
    def get_default_configuration(self) -> dict:
        """Get default configuration"""
        return {
            "manifests": [],
            "settings": {
                "volume": 0.5,
                "flash_interval": 500,
                "flash_cycles": 3,
                "pause_between_cycles": 2000,
                "default_monitor": 0,
                "fullscreen_mode": False,
                "tv_fullscreen_timeout": 30,
                "mute_duration_minutes": 5,
                "theme": "default",
                "data_folder": ""
            }
        }
    
    def validate_configuration(self, config: dict) -> bool:
        """Validate configuration structure"""
        required_keys = ["manifests", "settings"]
        if not all(key in config for key in required_keys):
            return False
        
        settings = config["settings"]
        required_settings = ["volume", "flash_interval", "mute_duration_minutes"]
        if not all(key in settings for key in required_settings):
            return False
        
        # Validate value ranges
        if not (0.0 <= settings["volume"] <= 1.0):
            return False
        
        if settings["flash_interval"] < 100 or settings["flash_interval"] > 2000:
            return False
        
        return True
```

## Performance Benchmarks

### Required Performance Metrics
- **Cache Hit Rate**: >90% for network operations
- **UI Response Time**: <100ms for button clicks and layout changes
- **Memory Usage**: <100MB total application memory
- **Network Timeouts**: <1% of all network operations
- **Startup Time**: <5 seconds from launch to ready

### Performance Test Cases
```python
def test_cache_performance():
    """Test cache hit rate and effectiveness"""
    cache_manager = CacheManager()
    
    # Simulate 100 operations
    for i in range(100):
        # First call should miss cache
        data = cache_manager.get_network_cached("test_key", lambda: fetch_test_data())
        
        # Subsequent calls within TTL should hit cache
        for j in range(9):
            cached_data = cache_manager.get_network_cached("test_key", lambda: fetch_test_data())
            assert cached_data == data  # Should be same cached data
    
    # Verify cache hit rate >90%
    hit_rate = cache_manager.get_hit_rate()
    assert hit_rate > 0.9

def test_ui_response_time():
    """Test UI responsiveness"""
    start_time = time.time()
    
    # Simulate button click
    button.click()
    
    response_time = (time.time() - start_time) * 1000  # Convert to ms
    assert response_time < 100  # Must be under 100ms
```

## Success Criteria
- [ ] All components integrated successfully
- [ ] Performance benchmarks met or exceeded
- [ ] Configuration management operational
- [ ] Monitoring and logging functional
- [ ] System startup and shutdown working
- [ ] Integration tests pass >95%

## Risk Mitigation
- **Integration Risk**: Comprehensive integration testing
- **Performance Risk**: Continuous performance monitoring
- **Configuration Risk**: Multiple fallback strategies
- **Stability Risk**: Extensive error handling and recovery

## Definition of Done
- All integration components implemented
- Performance benchmarks validated
- Configuration management working
- System ready for Phase 6 testing and migration
- All integration tests passing
