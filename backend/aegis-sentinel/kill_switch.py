"""
backend/aegis-sentinel/kill_switch.py
Real-time Circuit Breaker and Global/Tenant-level Kill Switch.
Halts compromised or looping agents instantly.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional

logger = logging.getLogger("AegisKillSwitch")


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is blocked due to an open circuit breaker."""
    pass


class KillSwitchManager:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        # In-memory circuit state storage: {tenant_id: {"failures": int, "state": "CLOSED"|"OPEN", "tripped_at": float}}
        self._tenant_breakers: Dict[str, Dict[str, any]] = {}
        self._global_kill_active: bool = False

    def trigger_global_kill(self, reason: str) -> None:
        """Globally shuts down all AI processing across all tenants."""
        self._global_kill_active = True
        logger.critical("GLOBAL KILL-SWITCH ACTIVATED! Reason: %s", reason)

    def reset_global_kill(self) -> None:
        """Resets the global kill switch."""
        self._global_kill_active = False
        logger.warning("Global kill-switch deactivated. Normal operations resumed.")

    def is_globally_killed(self) -> bool:
        """Returns True if global kill switch is engaged."""
        return self._global_kill_active

    def record_failure(self, org_id: str, reason: str) -> None:
        """Records a security or execution failure for a tenant."""
        now = time.time()
        record = self._tenant_breakers.setdefault(
            org_id, {"failures": 0, "state": "CLOSED", "tripped_at": 0.0}
        )

        record["failures"] += 1
        logger.warning("Failure logged for org %s. Total: %d. Reason: %s", org_id, record["failures"], reason)

        if record["failures"] >= self.failure_threshold:
            record["state"] = "OPEN"
            record["tripped_at"] = now
            logger.error("Circuit breaker TRIPPED for org %s! Halting agent actions.", org_id)

    def record_success(self, org_id: str) -> None:
        """Resets tenant failure count on successful, safe run."""
        if org_id in self._tenant_breakers:
            if self._tenant_breakers[org_id]["state"] == "CLOSED":
                self._tenant_breakers[org_id]["failures"] = 0

    def verify_execution_permitted(self, org_id: str) -> None:
        """
        Validates if agent is permitted to run.
        Raises CircuitBreakerOpenException if blocked.
        """
        if self._global_kill_active:
            raise CircuitBreakerOpenException("Execution denied: Global Kill Switch is ACTIVE.")

        record = self._tenant_breakers.get(org_id)
        if not record:
            return

        if record["state"] == "OPEN":
            elapsed = time.time() - record["tripped_at"]
            if elapsed < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - elapsed)
                raise CircuitBreakerOpenException(
                    f"Execution blocked for org {org_id}: Circuit breaker is OPEN. Cooldown: {remaining}s."
                )
            else:
                # Half-open trial state
                logger.info("Circuit breaker cooldown expired for org %s. Entering HALF-OPEN state.", org_id)
                record["state"] = "HALF-OPEN"
                record["failures"] = 0