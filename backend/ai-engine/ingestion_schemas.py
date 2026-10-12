"""
backend/ai-engine/ingestion_schemas.py
Pydantic contracts for multi-modal ingestion (OCR memos and voice orders).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class IngestionItem(BaseModel):
    item_name: str = Field(description="Name or title of the product/item")
    quantity: float = Field(default=1.0, description="Quantity purchased or sold")
    unit: Optional[str] = Field(default="pcs", description="Unit of measure (e.g., kg, pcs, sack)")
    unit_price: float = Field(default=0.0, description="Price per unit in BDT/local currency")
    total_price: float = Field(default=0.0, description="Calculated total price for this line item")


class ExtractedTransactionPayload(BaseModel):
    transaction_type: str = Field(
        default="SALE",
        description="Type of transaction: SALE, PURCHASE, DEBT_COLLECTION, EXPENSE"
    )
    customer_or_vendor_name: Optional[str] = Field(
        default=None,
        description="Extracted party name from voice or memo"
    )
    phone_number: Optional[str] = Field(
        default=None,
        description="Extracted phone number if available"
    )
    items: List[IngestionItem] = Field(default_factory=list, description="Extracted line items")
    subtotal: float = Field(default=0.0, description="Sum of line item totals")
    discount: float = Field(default=0.0, description="Discount amount applied")
    grand_total: float = Field(default=0.0, description="Net total payable")
    paid_amount: float = Field(default=0.0, description="Amount paid immediately")
    due_amount: float = Field(default=0.0, description="Remaining balance/due (Baki)")
    confidence_score: float = Field(
        default=1.0,
        description="Extraction confidence level between 0.0 and 1.0"
    )
    raw_transcription_or_ocr: Optional[str] = Field(
        default=None,
        description="Underlying raw text extracted before normalization"
    )