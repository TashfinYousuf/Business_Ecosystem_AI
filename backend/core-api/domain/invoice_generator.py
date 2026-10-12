"""
backend/core-api/domain/invoice_generator.py
Generates bilingual WhatsApp-shareable receipts and dynamic payment QR codes for SME invoices.
Includes authentic Bengali numeral conversion for local merchant readability.
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import qrcode

logger = logging.getLogger("InvoiceGenerator")

# Bengali numeral translation map
BENGALI_DIGITS = {
    "0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
    "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯",
}


def to_bengali_digits(text: str) -> str:
    """Converts ASCII numeric digits in a string to authentic Bengali digits."""
    return "".join(BENGALI_DIGITS.get(char, char) for char in str(text))


def format_bengali_amount(amount: float, include_decimals: bool = False) -> str:
    """Formats monetary amounts into Bengali currency notation (e.g., ৳৬,০০০)."""
    if include_decimals:
        formatted_ascii = f"{amount:,.2f}"
    else:
        formatted_ascii = f"{amount:,.0f}"
    return f"৳{to_bengali_digits(formatted_ascii)}"


@dataclass
class DigitalInvoicePayload:
    invoice_number: str
    merchant_name: str
    merchant_phone: str
    customer_name: str
    customer_phone: Optional[str]
    items: List[Dict[str, Any]]
    subtotal: float
    discount: float
    grand_total: float
    paid_amount: float
    due_amount: float
    payment_method: str
    date_str: str


class SmartInvoiceEngine:
    @staticmethod
    def generate_whatsapp_receipt(invoice: DigitalInvoicePayload) -> str:
        """
        Formats clean, culturally professional Bengali text receipt for 1-click WhatsApp dispatch.
        """
        lines = [
            f"🧾 *ক্যাশ মেমো / চালানের কপি*",
            f"দোকান: *{invoice.merchant_name}*",
            f"মোবাইল: {to_bengali_digits(invoice.merchant_phone)}",
            f"তারিখ: {to_bengali_digits(invoice.date_str)}",
            f"চালান নং: `{invoice.invoice_number}`",
            "--------------------------------",
            f"ক্রেতা: *{invoice.customer_name}*",
        ]

        if invoice.customer_phone:
            lines.append(f"ফোন: {to_bengali_digits(invoice.customer_phone)}")

        lines.append("--------------------------------")
        lines.append("*পণ্যের বিবরণ:*")

        for idx, item in enumerate(invoice.items, start=1):
            name = item.get("product_name") or item.get("item_name", "পণ্য")
            qty = item.get("quantity", 1)
            rate = item.get("unit_price", 0.0)
            total = item.get("total_price", 0.0)
            b_idx = to_bengali_digits(idx)
            b_qty = to_bengali_digits(qty)
            b_rate = format_bengali_amount(rate)
            b_total = format_bengali_amount(total)
            lines.append(f"{b_idx}. {name} ({b_qty} × {b_rate}) = {b_total}")

        lines.append("--------------------------------")
        lines.append(f"মোট মূল্য: {format_bengali_amount(invoice.subtotal)}")
        if invoice.discount > 0:
            lines.append(f"ছাড় (ডিসকাউন্ট): -{format_bengali_amount(invoice.discount)}")
        lines.append(f"*সর্বমোট প্রদেয়:* *{format_bengali_amount(invoice.grand_total)}*")
        lines.append(f"নগদ পরিশোধ: {format_bengali_amount(invoice.paid_amount)} ({invoice.payment_method})")

        if invoice.due_amount > 0:
            lines.append(f"⚠️ *অবশিষ্ট বকেয়া:* *{format_bengali_amount(invoice.due_amount)}*")
            lines.append("\nবকেয়া দ্রুত পরিশোধের অনুরোধ রইল। ধন্যবাদ!")
        else:
            lines.append("\n✅ *পরিশোধিত (PAID)* - আপনার ব্যবসার জন্য ধন্যবাদ!")

        return "\n".join(lines)

    @staticmethod
    def generate_payment_qr_base64(payment_url: str) -> str:
        """Encodes payment or invoice URL into a compact Base64 PNG QR image."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#0b0e11", back_color="#ffffff")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"