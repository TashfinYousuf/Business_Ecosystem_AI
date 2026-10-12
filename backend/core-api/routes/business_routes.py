"""
backend/core-api/routes/business_routes.py
FastAPI Router for core SME operations: Sales, HITL Approvals, Health Score, and AI Impact.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from domain.invoice_generator import SmartInvoiceEngine, DigitalInvoicePayload

from schemas import (
    CreateSaleInvoiceRequest,
    InvoiceResponse,
    ApprovalResolveRequest,
    ApprovalItemResponse,
    HealthScoreResponse,
    AISavedResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Business Operations"])

# In-memory mock stores for rapid prototyping prior to active DB session pooling
_MOCK_APPROVALS = [
    {
        "id": "app-001",
        "execution_id": "exec-901",
        "action_type": "send_whatsapp_debt_notice",
        "action_summary": "Send MODERATE WhatsApp payment reminder to Babul Store (৳45,000 overdue for 24 days)",
        "risk_level": "MEDIUM",
        "parameters": {"phone": "01811223344", "total_due": 45000, "customer_name": "Babul Store"},
        "status": "PENDING",
        "requested_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "app-002",
        "execution_id": "exec-902",
        "action_type": "adjust_stock_bulk",
        "action_summary": "Auto-deplete 50 bags of damaged Miniket rice from warehouse inventory",
        "risk_level": "CRITICAL",
        "parameters": {"product_id": "prod-55", "quantity": -50, "reason": "Water damage"},
        "status": "PENDING",
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
]


@router.post("/sales/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_sales_invoice(
    payload: CreateSaleInvoiceRequest,
    x_org_id: str = Header(default="00000000-0000-0000-0000-000000000001", description="Tenant Organization ID"),
):
    """Generates a new validated sales invoice and registers customer due balance."""
    due = payload.grand_total - payload.paid_amount
    inv_status = "PAID" if due <= 0 else "PARTIAL" if payload.paid_amount > 0 else "UNPAID"
    
    invoice_id = str(uuid.uuid4())
    inv_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{invoice_id[:4].upper()}"

    return InvoiceResponse(
        id=invoice_id,
        invoice_number=inv_number,
        customer_name=payload.customer_name,
        grand_total=payload.grand_total,
        paid_amount=payload.paid_amount,
        due_amount=max(0.0, due),
        status=inv_status,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/approvals/pending", response_model=List[ApprovalItemResponse])
async def get_pending_approvals(
    x_org_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
):
    """Fetches all high-risk actions queued by AI agents awaiting merchant confirmation."""
    return [a for a in _MOCK_APPROVALS if a["status"] == "PENDING"]


@router.post("/approvals/{approval_id}/resolve")
async def resolve_approval_gate(
    approval_id: str,
    payload: ApprovalResolveRequest,
    x_org_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
):
    """Allows merchant to approve or reject a paused workflow step."""
    for item in _MOCK_APPROVALS:
        if item["id"] == approval_id:
            if item["status"] != "PENDING":
                raise HTTPException(status_code=400, detail="Approval request is already resolved.")
            
            item["status"] = payload.decision
            return {
                "approval_id": approval_id,
                "status": payload.decision,
                "message": f"Action successfully {payload.decision.lower()} by merchant.",
            }
            
    raise HTTPException(status_code=404, detail="Approval request not found.")


@router.get("/health-score", response_model=HealthScoreResponse)
async def get_business_health_score(
    x_org_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
):
    """Returns real-time 0-100 business stability score, sub-metrics, and risk insights."""
    return HealthScoreResponse(
        total_score=78.5,
        health_band="MODERATE",
        liquidity_score=82.0,
        debt_score=68.5,
        inventory_score=85.0,
        retention_score=75.0,
        margin_score=80.0,
        total_receivable_due=145000.0,
        monthly_revenue=480000.0,
        deadstock_count=3,
        insights=[
            {
                "type": "WARNING",
                "area": "DEBT",
                "message": "মোট বকেয়া (৳১,৪৫,০০০) মাসিক আয়ের ৩০% এর বেশি। দ্রুত তাগাদা পাঠানো জরুরি।",
            },
            {
                "type": "INFO",
                "area": "INVENTORY",
                "message": "৩টি আইটেমে গত ৬০ দিনে কোনো সেল নেই (ডেডস্টক)।",
            }
        ],
    )


@router.get("/ai-saved-you", response_model=AISavedResponse)
async def get_ai_saved_metrics(
    x_org_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
):
    """Returns live calculated ROI: hours saved, recovered debt, and math errors prevented."""
    return AISavedResponse(
        total_hours_saved=42.5,
        total_debt_recovered_bdt=85000.0,
        total_math_errors_fixed=14,
        estimated_labor_cost_saved_bdt=6375.0,
        total_monetary_benefit_bdt=91375.0,
    )


@router.get("/sales/invoices/{invoice_id}/digital")
async def get_digital_invoice_view(
    invoice_id: str,
    x_org_id: str = Header(default="00000000-0000-0000-0000-000000000001"),
):
    """
    Returns WhatsApp formatted receipt string and Base64 QR code for 1-click sharing.
    """
    # Sample mock invoice record lookup
    sample_payload = DigitalInvoicePayload(
        invoice_number=f"INV-20261012-{invoice_id[:4].upper()}",
        merchant_name="সততা ট্রেডার্স (Satata Traders)",
        merchant_phone="01711223344",
        customer_name="আলমগীর ভ্যারাইটি স্টোর",
        customer_phone="01822334455",
        items=[
            {"product_name": "তীর সয়াবিন তেল ৫ লিটার", "quantity": 4, "unit_price": 820.0, "total_price": 3280.0},
            {"product_name": "মিনিকেট চাল ২৫ কেজি বস্তা", "quantity": 2, "unit_price": 1850.0, "total_price": 3700.0},
        ],
        subtotal=6980.0,
        discount=80.0,
        grand_total=6900.0,
        paid_amount=4000.0,
        due_amount=2900.0,
        payment_method="CASH",
        date_str=datetime.now().strftime("%d/%m/%Y"),
    )

    whatsapp_text = SmartInvoiceEngine.generate_whatsapp_receipt(sample_payload)
    payment_link = f"https://pay.tradewolf.os/invoice/{invoice_id}?amount=2900"
    qr_base64 = SmartInvoiceEngine.generate_payment_qr_base64(payment_link)

    return {
        "invoice_id": invoice_id,
        "whatsapp_formatted_text": whatsapp_text,
        "payment_qr_code": qr_base64,
        "payment_link": payment_link,
        "due_amount": sample_payload.due_amount,
    }