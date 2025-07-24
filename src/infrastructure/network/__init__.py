"""
Network service package for high-performance network operations.

Provides timeout protection, retry logic, and fallback strategies
for accessing network shares and remote files.
"""

from .network_service import NetworkService
from .timeout_context import timeout_context, TimeoutException

__all__ = ['NetworkService', 'timeout_context', 'TimeoutException']
