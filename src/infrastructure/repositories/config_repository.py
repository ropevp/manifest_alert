"""
Configuration repository for application settings.

Handles loading and saving configuration data with validation
and fallback to default settings.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import logging
from pathlib import Path

from .base_repository import BaseRepository
from ...infrastructure.exceptions import DataValidationException, NetworkAccessException
from ...infrastructure.network import NetworkService
from ...infrastructure.cache import CacheManager


class ConfigRepository(BaseRepository[Dict[str, Any]]):
    """Abstract repository for configuration operations."""
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration.
        
        Returns:
            Configuration dictionary
        """
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save application configuration.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            True if save was successful
        """
        pass
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration setting.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        pass


class FileConfigRepository(ConfigRepository):
    """File-based configuration repository with network and local storage."""
    
    def __init__(self, network_service: Optional[NetworkService] = None,
                 cache_manager: Optional[CacheManager] = None,
                 local_config_path: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the configuration repository."""
        super().__init__(logger)
        self.network_service = network_service or NetworkService()
        self.cache_manager = cache_manager or CacheManager()
        self.local_config_path = Path(local_config_path or "config.json")
        
        self.config_filename = "config.json"
        
        self.logger.info("FileConfigRepository initialized")
    
    def load(self) -> List[Dict[str, Any]]:
        """Load method for base repository compatibility."""
        return [self.load_config()]
    
    def save(self, entities: List[Dict[str, Any]]) -> bool:
        """Save method for base repository compatibility."""
        if not entities:
            return False
        return self.save_config(entities[0])
    
    def exists(self) -> bool:
        """Check if configuration sources are accessible."""
        try:
            network_exists = self.network_service.file_exists(self.config_filename)
            local_exists = self.local_config_path.exists()
            return network_exists or local_exists
        except Exception:
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration with caching and fallback."""
        cache_key = "app_config"
        
        try:
            return self.cache_manager.get_network_cached(
                cache_key,
                lambda: self._load_config_direct()
            )
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to network and local backup."""
        try:
            # Save to network
            network_success = self.network_service.save_json_file(
                self.config_filename, config, create_backup=True
            )
            
            # Save local backup
            try:
                with open(self.local_config_path, 'w', encoding='utf-8') as file:
                    json.dump(config, file, indent=2, ensure_ascii=False)
            except Exception as e:
                self.logger.warning(f"Failed to save local config backup: {e}")
            
            # Invalidate cache
            if network_success:
                self.cache_manager.invalidate("app_config")
            
            return network_success
            
        except Exception as e:
            error = NetworkAccessException(f"Failed to save config: {e}")
            self._set_error(error)
            raise error
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration setting."""
        try:
            config = self.load_config()
            return config.get(key, default)
        except Exception:
            return default
    
    def _load_config_direct(self) -> Dict[str, Any]:
        """Load configuration directly from sources."""
        # Try network first
        try:
            return self.network_service.load_json_file(self.config_filename, use_cache=False)
        except Exception as e:
            self.logger.warning(f"Could not load config from network: {e}")
            
            # Try local backup
            try:
                if self.local_config_path.exists():
                    with open(self.local_config_path, 'r', encoding='utf-8') as file:
                        return json.load(file)
            except Exception as e2:
                self.logger.warning(f"Could not load local config: {e2}")
            
            # Return default
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "manifest_times": ["07:00", "13:00", "19:00"],
            "carriers": ["Australia Post Metro", "DHL Express", "TNT Express"],
            "alert_window_minutes": 30,
            "sound_enabled": True,
            "volume": 50,
            "flash_enabled": True,
            "version": "1.0"
        }
