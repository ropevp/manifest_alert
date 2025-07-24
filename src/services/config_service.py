"""
Configuration Service

Business logic service for managing application configuration,
validation, and dynamic settings management.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, time

from ..domain.models import Carrier
from ..infrastructure.repositories import ConfigRepository
from ..infrastructure.exceptions import (
    DataValidationException, 
    NetworkAccessException,
    ConfigurationException
)


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_config: Optional[Dict[str, Any]] = None
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are validation warnings."""
        return len(self.warnings) > 0


class ConfigService:
    """Service for managing application configuration.
    
    This service provides business logic for configuration management including:
    - Loading and validating configuration from multiple sources
    - Providing default values and fallbacks
    - Dynamic configuration updates with validation
    - Configuration schema validation and type checking
    - Performance optimization through caching
    """
    
    DEFAULT_CONFIG = {
        "manifest_times": ["07:00", "13:00", "19:00"],
        "carriers": [
            "Australia Post Metro",
            "Australia Post Regular", 
            "DHL Express",
            "TNT Express",
            "Startrack Premium",
            "Startrack Standard"
        ],
        "alert_settings": {
            "sound_enabled": True,
            "sound_file": "alert.wav",
            "repeat_interval_minutes": 5,
            "auto_acknowledge_timeout_minutes": 30,
            "max_alerts_per_manifest": 10
        },
        "ui_settings": {
            "window_width": 800,
            "window_height": 600,
            "always_on_top": True,
            "minimize_to_tray": True,
            "startup_with_windows": False,
            "theme": "light"
        },
        "network_settings": {
            "timeout_seconds": 1.0,
            "max_retries": 2,
            "retry_delay_seconds": 0.1,
            "cache_ttl_seconds": 30,
            "fast_cache_ttl_seconds": 5
        },
        "logging": {
            "level": "INFO",
            "max_log_files": 10,
            "max_log_size_mb": 10,
            "console_logging": True,
            "file_logging": True
        },
        "version": "3.3.0",
        "last_updated": None,
        "updated_by": None
    }
    
    def __init__(self, config_repository: ConfigRepository):
        """Initialize configuration service.
        
        Args:
            config_repository: Repository for configuration persistence
        """
        self.config_repository = config_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cached_config: Optional[Dict[str, Any]] = None
        self._last_load_time: Optional[datetime] = None
        
        self.logger.info("ConfigService initialized")
    
    def load_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Load configuration with caching and fallbacks.
        
        Args:
            force_refresh: Force reload from repository
            
        Returns:
            Complete configuration dictionary
            
        Raises:
            ConfigurationException: If configuration cannot be loaded or validated
        """
        try:
            # Use cached config if available and not forcing refresh
            if not force_refresh and self._cached_config is not None:
                return self._cached_config.copy()
            
            # Load from repository
            config = self.config_repository.load_config()
            
            # Validate configuration
            validation_result = self.validate_config(config)
            if validation_result.has_errors():
                self.logger.error(f"Configuration validation failed: {validation_result.errors}")
                # Fall back to default config with warnings
                config = self.DEFAULT_CONFIG.copy()
                self.logger.warning("Using default configuration due to validation errors")
            elif validation_result.has_warnings():
                self.logger.warning(f"Configuration warnings: {validation_result.warnings}")
            
            # Merge with defaults to ensure all required keys exist
            config = self._merge_with_defaults(config)
            
            # Cache the validated configuration
            self._cached_config = config.copy()
            self._last_load_time = datetime.now()
            
            self.logger.info("Configuration loaded successfully")
            return config.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Fall back to default configuration
            fallback_config = self.DEFAULT_CONFIG.copy()
            self._cached_config = fallback_config.copy()
            self.logger.warning("Using default configuration due to load error")
            return fallback_config.copy()
    
    def save_config(self, config: Dict[str, Any], user: Optional[str] = None) -> bool:
        """Save configuration with validation.
        
        Args:
            config: Configuration to save
            user: User making the change
            
        Returns:
            True if save was successful
            
        Raises:
            ConfigurationException: If configuration is invalid
        """
        try:
            # Validate the configuration
            validation_result = self.validate_config(config)
            if validation_result.has_errors():
                raise ConfigurationException(
                    f"Configuration validation failed: {', '.join(validation_result.errors)}"
                )
            
            # Add metadata
            config_to_save = config.copy()
            config_to_save["last_updated"] = datetime.now().isoformat()
            config_to_save["updated_by"] = user or "system"
            
            # Save to repository
            success = self.config_repository.save_config(config_to_save)
            
            if success:
                # Update cache
                merged_config = self._merge_with_defaults(config_to_save)
                self._cached_config = merged_config.copy()
                self._last_load_time = datetime.now()
                
                self.logger.info(f"Configuration saved successfully by {user or 'system'}")
                
                # Log warnings if any
                if validation_result.has_warnings():
                    self.logger.warning(f"Configuration saved with warnings: {validation_result.warnings}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationException(f"Failed to save configuration: {e}")
    
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate configuration structure and values.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = ConfigValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not isinstance(config, dict):
            result.add_error("Configuration must be a dictionary")
            return result
        
        # Validate manifest times
        self._validate_manifest_times(config.get("manifest_times", []), result)
        
        # Validate carriers
        self._validate_carriers(config.get("carriers", []), result)
        
        # Validate alert settings
        self._validate_alert_settings(config.get("alert_settings", {}), result)
        
        # Validate UI settings
        self._validate_ui_settings(config.get("ui_settings", {}), result)
        
        # Validate network settings
        self._validate_network_settings(config.get("network_settings", {}), result)
        
        # Validate logging settings
        self._validate_logging_settings(config.get("logging", {}), result)
        
        # Store validated config
        if result.is_valid:
            result.validated_config = config.copy()
        
        return result
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """Get a specific setting using dot notation.
        
        Args:
            key_path: Setting path (e.g., "alert_settings.sound_enabled")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            config = self.load_config()
            
            # Navigate through nested keys
            value = config
            for key in key_path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Failed to get setting '{key_path}': {e}")
            return default
    
    def set_setting(self, key_path: str, value: Any, user: Optional[str] = None) -> bool:
        """Set a specific setting using dot notation.
        
        Args:
            key_path: Setting path (e.g., "alert_settings.sound_enabled")
            value: New value
            user: User making the change
            
        Returns:
            True if setting was updated successfully
        """
        try:
            config = self.load_config()
            
            # Navigate to parent and set value
            keys = key_path.split('.')
            current = config
            
            # Navigate to parent
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save the updated configuration
            return self.save_config(config, user)
            
        except Exception as e:
            self.logger.error(f"Failed to set setting '{key_path}': {e}")
            return False
    
    def get_manifest_times(self) -> List[str]:
        """Get configured manifest times.
        
        Returns:
            List of manifest times in HH:MM format
        """
        return self.get_setting("manifest_times", self.DEFAULT_CONFIG["manifest_times"])
    
    def get_carriers(self) -> List[Carrier]:
        """Get configured carriers as domain objects.
        
        Returns:
            List of Carrier domain objects
        """
        carrier_names = self.get_setting("carriers", self.DEFAULT_CONFIG["carriers"])
        return [Carrier(name) for name in carrier_names]
    
    def get_alert_settings(self) -> Dict[str, Any]:
        """Get alert configuration settings.
        
        Returns:
            Alert settings dictionary
        """
        return self.get_setting("alert_settings", self.DEFAULT_CONFIG["alert_settings"])
    
    def is_sound_enabled(self) -> bool:
        """Check if sound alerts are enabled.
        
        Returns:
            True if sound is enabled
        """
        return self.get_setting("alert_settings.sound_enabled", True)
    
    def get_repeat_interval(self) -> int:
        """Get alert repeat interval in minutes.
        
        Returns:
            Repeat interval in minutes
        """
        return self.get_setting("alert_settings.repeat_interval_minutes", 5)
    
    def reset_to_defaults(self, user: Optional[str] = None) -> bool:
        """Reset configuration to default values.
        
        Args:
            user: User performing the reset
            
        Returns:
            True if reset was successful
        """
        try:
            default_config = self.DEFAULT_CONFIG.copy()
            return self.save_config(default_config, user)
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration for backup.
        
        Returns:
            Complete configuration with metadata
        """
        config = self.load_config()
        config["exported_at"] = datetime.now().isoformat()
        config["exported_by"] = "system"
        return config
    
    def import_config(self, config: Dict[str, Any], user: Optional[str] = None) -> ConfigValidationResult:
        """Import configuration from external source.
        
        Args:
            config: Configuration to import
            user: User performing the import
            
        Returns:
            Validation result indicating success/failure
        """
        try:
            # Remove export metadata
            clean_config = {k: v for k, v in config.items() 
                          if k not in ["exported_at", "exported_by"]}
            
            # Validate the configuration
            validation_result = self.validate_config(clean_config)
            
            if not validation_result.has_errors():
                # Save the validated configuration
                success = self.save_config(clean_config, user)
                if not success:
                    validation_result.add_error("Failed to save imported configuration")
            
            return validation_result
            
        except Exception as e:
            result = ConfigValidationResult(is_valid=False, errors=[], warnings=[])
            result.add_error(f"Failed to import configuration: {e}")
            return result
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration with defaults to ensure all keys exist.
        
        Args:
            config: Configuration to merge
            
        Returns:
            Merged configuration with all default keys
        """
        def deep_merge(default: dict, override: dict) -> dict:
            result = default.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(self.DEFAULT_CONFIG, config)
    
    def _validate_manifest_times(self, manifest_times: Any, result: ConfigValidationResult) -> None:
        """Validate manifest times configuration."""
        if not isinstance(manifest_times, list):
            result.add_error("manifest_times must be a list")
            return
        
        if len(manifest_times) == 0:
            result.add_warning("No manifest times configured")
            return
        
        for i, time_str in enumerate(manifest_times):
            if not isinstance(time_str, str):
                result.add_error(f"manifest_times[{i}] must be a string")
                continue
            
            try:
                time.fromisoformat(time_str)
            except ValueError:
                result.add_error(f"manifest_times[{i}] '{time_str}' is not a valid time format (HH:MM)")
    
    def _validate_carriers(self, carriers: Any, result: ConfigValidationResult) -> None:
        """Validate carriers configuration."""
        if not isinstance(carriers, list):
            result.add_error("carriers must be a list")
            return
        
        if len(carriers) == 0:
            result.add_warning("No carriers configured")
            return
        
        for i, carrier_name in enumerate(carriers):
            if not isinstance(carrier_name, str):
                result.add_error(f"carriers[{i}] must be a string")
                continue
            
            if not carrier_name.strip():
                result.add_error(f"carriers[{i}] cannot be empty")
    
    def _validate_alert_settings(self, alert_settings: Any, result: ConfigValidationResult) -> None:
        """Validate alert settings configuration."""
        if not isinstance(alert_settings, dict):
            result.add_warning("alert_settings should be a dictionary, using defaults")
            return
        
        # Validate sound_enabled
        if "sound_enabled" in alert_settings:
            if not isinstance(alert_settings["sound_enabled"], bool):
                result.add_error("alert_settings.sound_enabled must be a boolean")
        
        # Validate repeat_interval_minutes
        if "repeat_interval_minutes" in alert_settings:
            interval = alert_settings["repeat_interval_minutes"]
            if not isinstance(interval, int) or interval <= 0:
                result.add_error("alert_settings.repeat_interval_minutes must be a positive integer")
        
        # Validate auto_acknowledge_timeout_minutes
        if "auto_acknowledge_timeout_minutes" in alert_settings:
            timeout = alert_settings["auto_acknowledge_timeout_minutes"]
            if not isinstance(timeout, int) or timeout <= 0:
                result.add_error("alert_settings.auto_acknowledge_timeout_minutes must be a positive integer")
    
    def _validate_ui_settings(self, ui_settings: Any, result: ConfigValidationResult) -> None:
        """Validate UI settings configuration."""
        if not isinstance(ui_settings, dict):
            result.add_warning("ui_settings should be a dictionary, using defaults")
            return
        
        # Validate window dimensions
        for dimension in ["window_width", "window_height"]:
            if dimension in ui_settings:
                value = ui_settings[dimension]
                if not isinstance(value, int) or value <= 0:
                    result.add_error(f"ui_settings.{dimension} must be a positive integer")
        
        # Validate boolean settings
        bool_settings = ["always_on_top", "minimize_to_tray", "startup_with_windows"]
        for setting in bool_settings:
            if setting in ui_settings:
                if not isinstance(ui_settings[setting], bool):
                    result.add_error(f"ui_settings.{setting} must be a boolean")
    
    def _validate_network_settings(self, network_settings: Any, result: ConfigValidationResult) -> None:
        """Validate network settings configuration."""
        if not isinstance(network_settings, dict):
            result.add_warning("network_settings should be a dictionary, using defaults")
            return
        
        # Validate timeout_seconds
        if "timeout_seconds" in network_settings:
            timeout = network_settings["timeout_seconds"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                result.add_error("network_settings.timeout_seconds must be a positive number")
        
        # Validate max_retries
        if "max_retries" in network_settings:
            retries = network_settings["max_retries"]
            if not isinstance(retries, int) or retries < 0:
                result.add_error("network_settings.max_retries must be a non-negative integer")
    
    def _validate_logging_settings(self, logging_settings: Any, result: ConfigValidationResult) -> None:
        """Validate logging settings configuration."""
        if not isinstance(logging_settings, dict):
            result.add_warning("logging should be a dictionary, using defaults")
            return
        
        # Validate log level
        if "level" in logging_settings:
            level = logging_settings["level"]
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level not in valid_levels:
                result.add_error(f"logging.level must be one of {valid_levels}")
        
        # Validate numeric settings
        numeric_settings = {
            "max_log_files": "positive integer",
            "max_log_size_mb": "positive number"
        }
        
        for setting, description in numeric_settings.items():
            if setting in logging_settings:
                value = logging_settings[setting]
                if not isinstance(value, (int, float)) or value <= 0:
                    result.add_error(f"logging.{setting} must be a {description}")
