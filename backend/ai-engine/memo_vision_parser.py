"""
backend/ai-engine/memo_vision_parser.py
Vision-based document parser for handwritten receipts, vouchers, and SME memos.
Uses Gemini 2.5 Flash multimodal capabilities.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Optional
import httpx

from config import gateway_settings
from ingestion_schemas import ExtractedTransactionPayload

logger = logging.getLogger("MemoVisionParser")

SYSTEM_VISION_PROMPT = """
You are Trade Wolf OS Memo OCR Engine. You specialize in analyzing SME handwritten memos, vouchers, and receipts from emerging markets (Bangladesh/South Asia).
Extract the transaction details into strict JSON adhering to this schema:
{
  "transaction_type": "SALE" | "PURCHASE" | "EXPENSE",
  "customer_or_vendor_name": string | null,
  "phone_number": string | null,
  "items": [
    {"item_name": string, "quantity": number, "unit": string, "unit_price": number, "total_price": number}
  ],
  "subtotal": number,
  "discount": number,
  "grand_total": number,
  "paid_amount": number,
  "due_amount": number,
  "confidence_score": number (0.0 to 1.0)
}
Calculate values strictly. Ensure (grand_total = subtotal - discount) and (due_amount = grand_total - paid_amount).
Respond ONLY with raw valid JSON without markdown fences.
"""


class MemoVisionParser:
    def __init__(self):
        self.settings = gateway_settings

    async def parse_memo_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> ExtractedTransactionPayload:
        """
        Submits image payload to Gemini 2.5 Flash for vision extraction.
        Returns parsed ExtractedTransactionPayload.
        """
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model_name}:generateContent?key={self.settings.gemini_api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": SYSTEM_VISION_PROMPT},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": encoded_image
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed_dict = json.loads(raw_json_str)
        parsed_dict["raw_transcription_or_ocr"] = "Extracted via Gemini Vision 2.5 Flash"

        return ExtractedTransactionPayload(**parsed_dict)