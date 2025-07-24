"""
Manifest repository for loading and saving manifest data.

Handles CSV and JSON manifest data with caching and validation.
Provides the data access layer for manifest domain objects.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
import json
import logging
from datetime import datetime

from .base_repository import BaseRepository
from ...domain.models.manifest import Manifest
from ...domain.models.carrier import Carrier
from ...infrastructure.exceptions import DataValidationException, NetworkAccessException
from ...infrastructure.network import NetworkService
from ...infrastructure.cache import CacheManager


class ManifestRepository(BaseRepository[Manifest]):
    """Abstract repository for manifest data operations."""
    
    @abstractmethod
    def load_manifests(self, date: Optional[str] = None) -> List[Manifest]:
        """Load manifests for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format, today if None
            
        Returns:
            List of manifest objects for the date
        """
        pass
    
    @abstractmethod
    def save_manifest(self, manifest: Manifest) -> bool:
        """Save a single manifest.
        
        Args:
            manifest: Manifest to save
            
        Returns:
            True if save was successful
        """
        pass
    
    @abstractmethod
    def load_manifest_config(self) -> Dict[str, Any]:
        """Load manifest configuration data.
        
        Returns:
            Configuration dictionary
        """
        pass


class FileManifestRepository(ManifestRepository):
    """File-based manifest repository with network and local file support.
    
    Loads manifests from CSV files and configuration from JSON files.
    Implements aggressive caching for performance.
    """
    
    def __init__(self, network_service: Optional[NetworkService] = None,
                 cache_manager: Optional[CacheManager] = None,
                 local_data_path: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the manifest repository.
        
        Args:
            network_service: Service for network file operations
            cache_manager: Cache manager for performance
            local_data_path: Local path for data files
            logger: Logger for repository operations
        """
        super().__init__(logger)
        self.network_service = network_service or NetworkService()
        self.cache_manager = cache_manager or CacheManager()
        self.local_data_path = Path(local_data_path or "data")
        
        # File configuration
        self.config_filename = "config.json"
        self.csv_path = "csv"
        
        self.logger.info(f"FileManifestRepository initialized with local path: {self.local_data_path}")
    
    def load(self) -> List[Manifest]:
        """Load all manifests for today."""
        return self.load_manifests()
    
    def save(self, entities: List[Manifest]) -> bool:
        """Save a list of manifests."""
        try:
            success_count = 0
            for manifest in entities:
                if self.save_manifest(manifest):
                    success_count += 1
            
            self.logger.info(f"Saved {success_count}/{len(entities)} manifests")
            return success_count == len(entities)
            
        except Exception as e:
            self._set_error(e)
            return False
    
    def exists(self) -> bool:
        """Check if manifest data sources are accessible."""
        try:
            # Check network configuration access
            config_exists = self.network_service.file_exists(self.config_filename)
            
            # Check local CSV directory
            csv_dir = self.local_data_path / self.csv_path
            local_exists = csv_dir.exists()
            
            return config_exists or local_exists
            
        except Exception as e:
            self.logger.warning(f"Error checking manifest repository existence: {e}")
            return False
    
    def load_manifests(self, date: Optional[str] = None) -> List[Manifest]:
        """Load manifests for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format, today if None
            
        Returns:
            List of manifest objects for the date
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"manifests:{date}"
        
        try:
            return self.cache_manager.get_network_cached(
                cache_key,
                lambda: self._load_manifests_direct(date)
            )
        except Exception as e:
            error = NetworkAccessException(f"Failed to load manifests for {date}: {e}")
            self._set_error(error)
            raise error
    
    def save_manifest(self, manifest: Manifest) -> bool:
        """Save a single manifest to CSV file.
        
        Args:
            manifest: Manifest to save
            
        Returns:
            True if save was successful
        """
        try:
            # Generate CSV filename
            date_str = manifest.date.replace("-", "")
            csv_filename = f"manifest_config-{date_str}.csv"
            csv_path = self.local_data_path / self.csv_path / csv_filename
            
            # Ensure directory exists
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert manifest to CSV row format
            csv_data = self._manifest_to_csv_rows([manifest])
            
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                for row in csv_data:
                    writer.writerow(row)
            
            # Invalidate cache
            cache_key = f"manifests:{manifest.date}"
            self.cache_manager.invalidate(cache_key)
            
            self.logger.debug(f"Saved manifest to {csv_filename}")
            return True
            
        except Exception as e:
            error = NetworkAccessException(f"Failed to save manifest: {e}")
            self._set_error(error)
            raise error
    
    def load_manifest_config(self) -> Dict[str, Any]:
        """Load manifest configuration from network config.json.
        
        Returns:
            Configuration dictionary with manifest settings
        """
        cache_key = "manifest_config"
        
        try:
            return self.cache_manager.get_network_cached(
                cache_key,
                lambda: self.network_service.load_json_file(self.config_filename)
            )
        except Exception as e:
            error = NetworkAccessException(f"Failed to load manifest config: {e}")
            self._set_error(error)
            raise error
    
    def _load_manifests_direct(self, date: str) -> List[Manifest]:
        """Load manifests directly from files without caching.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of manifest objects
        """
        manifests = []
        
        try:
            # Load from network config first
            config_data = self.network_service.load_json_file(self.config_filename, use_cache=False)
            network_manifests = self._parse_config_manifests(config_data, date)
            manifests.extend(network_manifests)
            
        except Exception as e:
            self.logger.warning(f"Could not load manifests from network config: {e}")
        
        try:
            # Load from local CSV files as backup/supplement
            csv_manifests = self._load_csv_manifests(date)
            manifests.extend(csv_manifests)
            
        except Exception as e:
            self.logger.warning(f"Could not load manifests from CSV files: {e}")
        
        if not manifests:
            self.logger.warning(f"No manifests found for date {date}")
        
        # Remove duplicates based on time
        unique_manifests = self._deduplicate_manifests(manifests)
        
        self.logger.info(f"Loaded {len(unique_manifests)} manifests for {date}")
        return unique_manifests
    
    def _parse_config_manifests(self, config_data: Dict[str, Any], date: str) -> List[Manifest]:
        """Parse manifests from network configuration data.
        
        Args:
            config_data: Configuration dictionary
            date: Target date for manifests
            
        Returns:
            List of parsed manifest objects
        """
        manifests = []
        
        try:
            # Look for manifest times in config
            manifest_times = config_data.get("manifest_times", [])
            carriers_config = config_data.get("carriers", [])
            
            for time_str in manifest_times:
                try:
                    # Create carriers from config
                    carriers = []
                    for carrier_name in carriers_config:
                        if carrier_name and carrier_name.strip():
                            carriers.append(Carrier(carrier_name.strip()))
                    
                    # Create manifest
                    manifest = Manifest(
                        time=time_str,
                        carriers=carriers,
                        date=date
                    )
                    manifests.append(manifest)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse manifest for time {time_str}: {e}")
                    continue
            
        except Exception as e:
            raise DataValidationException(f"Invalid manifest configuration format: {e}")
        
        return manifests
    
    def _load_csv_manifests(self, date: str) -> List[Manifest]:
        """Load manifests from local CSV files.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of manifest objects from CSV
        """
        manifests = []
        
        # Generate possible CSV filenames for the date
        date_str = date.replace("-", "")
        csv_patterns = [
            f"manifest_config-{date_str}.csv",
            f"manifest-{date_str}.csv",
            "manifest_config.csv",
        ]
        
        csv_dir = self.local_data_path / self.csv_path
        
        for pattern in csv_patterns:
            csv_path = csv_dir / pattern
            if csv_path.exists():
                try:
                    file_manifests = self._parse_csv_file(csv_path, date)
                    manifests.extend(file_manifests)
                    self.logger.debug(f"Loaded {len(file_manifests)} manifests from {pattern}")
                except Exception as e:
                    self.logger.warning(f"Failed to parse CSV file {pattern}: {e}")
        
        return manifests
    
    def _parse_csv_file(self, csv_path: Path, date: str) -> List[Manifest]:
        """Parse a CSV file to extract manifest data.
        
        Args:
            csv_path: Path to the CSV file
            date: Target date for manifests
            
        Returns:
            List of manifest objects
        """
        manifests = []
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            for row_num, row in enumerate(reader, 1):
                if not row or len(row) < 2:
                    continue
                
                try:
                    # Assume format: [time, carrier1, carrier2, ...]
                    time_str = row[0].strip()
                    carrier_names = [name.strip() for name in row[1:] if name.strip()]
                    
                    if not time_str or not carrier_names:
                        continue
                    
                    # Create carriers
                    carriers = [Carrier(name) for name in carrier_names]
                    
                    # Create manifest
                    manifest = Manifest(
                        time=time_str,
                        carriers=carriers,
                        date=date
                    )
                    manifests.append(manifest)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse CSV row {row_num}: {e}")
                    continue
        
        return manifests
    
    def _manifest_to_csv_rows(self, manifests: List[Manifest]) -> List[List[str]]:
        """Convert manifests to CSV row format.
        
        Args:
            manifests: List of manifest objects
            
        Returns:
            List of CSV rows
        """
        rows = []
        
        for manifest in manifests:
            # Format: [time, carrier1, carrier2, ...]
            row = [manifest.time]
            row.extend([carrier.name for carrier in manifest.carriers])
            rows.append(row)
        
        return rows
    
    def _deduplicate_manifests(self, manifests: List[Manifest]) -> List[Manifest]:
        """Remove duplicate manifests based on time and date.
        
        Args:
            manifests: List of manifest objects
            
        Returns:
            List with duplicates removed
        """
        seen = set()
        unique_manifests = []
        
        for manifest in manifests:
            key = (manifest.time, manifest.date)
            if key not in seen:
                seen.add(key)
                unique_manifests.append(manifest)
        
        return unique_manifests
