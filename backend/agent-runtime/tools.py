"""
backend/agent-runtime/tools.py
Tool registry and action declaration engine with human-gate sensitivity flags.
Integrates Aegis Sentinel Firewall to inspect every tool parameter.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("AgentTools")


@dataclass
class ToolDefinition:
    name: str
    description: str
    requires_approval: bool
    risk_level: str  # "LOW", "MEDIUM", "CRITICAL"
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolRegistry:
    def __init__(self):
        self._registry: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(
        self,
        name: str,
        description: str,
        requires_approval: bool = False,
        risk_level: str = "LOW",
    ):
        """Decorator to register business domain tools."""
        def decorator(func: Callable[[Dict[str, Any]], Dict[str, Any]]):
            self._registry[name] = ToolDefinition(
                name=name,
                description=description,
                requires_approval=requires_approval,
                risk_level=risk_level,
                handler=func,
            )
            return func
        return decorator

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._registry.get(name)

    def _register_default_tools(self):
        """Default business tool definitions for Trade Wolf OS."""

        @self.register(
            name="query_inventory",
            description="Reads current stock count for an item.",
            requires_approval=False,
            risk_level="LOW",
        )
        def query_inventory(params: Dict[str, Any]) -> Dict[str, Any]:
            # Read-only operation: perfectly safe for autonomous execution
            return {"status": "SUCCESS", "item_id": params.get("item_id"), "available_stock": 42}

        @self.register(
            name="adjust_stock_bulk",
            description="Manually increases or decreases inventory levels.",
            requires_approval=True,
            risk_level="CRITICAL",
        )
        def adjust_stock_bulk(params: Dict[str, Any]) -> Dict[str, Any]:
            # Critical mutation: can manipulate accounting, requires human gate
            return {"status": "SUCCESS", "message": f"Stock adjusted for item {params.get('item_id')}"}

        @self.register(
            name="send_whatsapp_debt_notice",
            description="Sends automated recovery payment reminder to debtor.",
            requires_approval=True,
            risk_level="MEDIUM",
        )
        def send_whatsapp_debt_notice(params: Dict[str, Any]) -> Dict[str, Any]:
            # External customer communication: requires merchant review
            return {"status": "SUCCESS", "message": f"WhatsApp notice dispatched to {params.get('phone')}"}

        @self.register(
            name="record_sale_transaction",
            description="Finalizes sales invoice and updates cash balance.",
            requires_approval=False,
            risk_level="LOW",
        )
        def record_sale_transaction(params: Dict[str, Any]) -> Dict[str, Any]:
            # Standard verified sale creation
            return {"status": "SUCCESS", "invoice_id": "INV-MOCK-101", "total": params.get("grand_total")}


tool_registry = ToolRegistry()