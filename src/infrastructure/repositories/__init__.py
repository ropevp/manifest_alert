"""
Repository package for data access patterns.

This package contains the repository implementations for accessing and persisting
domain data with proper caching and error handling.
"""

from .base_repository import BaseRepository
from .manifest_repository import ManifestRepository, FileManifestRepository
from .acknowledgment_repository import AcknowledgmentRepository, FileAcknowledgmentRepository
from .mute_repository import MuteRepository, FileMuteRepository
from .config_repository import ConfigRepository, FileConfigRepository

__all__ = [
    'BaseRepository',
    'ManifestRepository',
    'FileManifestRepository',
    'AcknowledgmentRepository',
    'FileAcknowledgmentRepository',
    'MuteRepository',
    'FileMuteRepository',
    'ConfigRepository',
    'FileConfigRepository',
]
