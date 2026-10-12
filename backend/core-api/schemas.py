"""
backend/core-api/schemas.py
Pydantic Request & Response Data Transfer Objects (DTO) for FastAPI endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Sales & Invoicing Schemas ---
class InvoiceItemCreate(BaseModel):
    product_name: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    total_price: float = Field(ge=0)


class CreateSaleInvoiceRequest(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[InvoiceItemCreate]
    subtotal: float = Field(ge=0)
    discount: float = Field(default=0.0, ge=0)
    grand_total: float = Field(ge=0)
    paid_amount: float = Field(default=0.0, ge=0)
    payment_method: str = Field(default="CASH")  # CASH, BKASH, NAGAD, BANK


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    customer_name: str
    grand_total: float
    paid_amount: float
    due_amount: float
    status: str
    created_at: str


# --- Human Approval Gate Schemas ---
class ApprovalResolveRequest(BaseModel):
    decision: str = Field(description="'APPROVED' or 'REJECTED'")
    resolution_note: Optional[str] = None


class ApprovalItemResponse(BaseModel):
    id: str
    execution_id: str
    action_type: str
    action_summary: str
    risk_level: str
    parameters: Dict[str, Any]
    status: str
    requested_at: str


# --- Business Intelligence Schemas ---
class HealthScoreResponse(BaseModel):
    total_score: float
    health_band: str
    liquidity_score: float
    debt_score: float
    inventory_score: float
    retention_score: float
    margin_score: float
    total_receivable_due: float
    monthly_revenue: float
    deadstock_count: int
    insights: List[Dict[str, str]]


class AISavedResponse(BaseModel):
    total_hours_saved: float
    total_debt_recovered_bdt: float
    total_math_errors_fixed: int
    estimated_labor_cost_saved_bdt: float
    total_monetary_benefit_bdt: float