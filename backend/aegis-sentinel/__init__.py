"""
backend/aegis-sentinel/__init__.py
AEGIS Sentinel defense module exports.
"""

from .firewall import AegisSentinelFirewall, InspectionResult
from .kill_switch import KillSwitchManager, CircuitBreakerOpenException

__all__ = [
    "AegisSentinelFirewall",
    "InspectionResult",
    "KillSwitchManager",
    "CircuitBreakerOpenException",
]