"""
backend/tests/test_digital_invoice.py
Validates Bengali WhatsApp text receipt formatting and dynamic QR generation.
"""

import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_API_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "core-api"))
sys.path.insert(0, CORE_API_DIR)

from domain.invoice_generator import SmartInvoiceEngine, DigitalInvoicePayload


class TestDigitalInvoiceEngine(unittest.TestCase):

    def setUp(self):
        self.invoice_data = DigitalInvoicePayload(
            invoice_number="INV-TEST-001",
            merchant_name="মোল্লা ব্রাদার্স",
            merchant_phone="01700112233",
            customer_name="করিম স্টোর",
            customer_phone="01911223344",
            items=[
                {"product_name": "চিনি ৫০ কেজি", "quantity": 1, "unit_price": 6200.0, "total_price": 6200.0}
            ],
            subtotal=6200.0,
            discount=200.0,
            grand_total=6000.0,
            paid_amount=3000.0,
            due_amount=3000.0,
            payment_method="BKASH",
            date_str="12/10/2026",
        )

    def test_whatsapp_receipt_generation(self):
        """Verify that the generated WhatsApp message has correct Bengali tags and arithmetic."""
        receipt = SmartInvoiceEngine.generate_whatsapp_receipt(self.invoice_data)
        
        self.assertIn("মোল্লা ব্রাদার্স", receipt)
        self.assertIn("করিম স্টোর", receipt)
        self.assertIn("৳৬,০০০", receipt)
        self.assertIn("অবশিষ্ট বকেয়া", receipt)
        self.assertIn("৳৩,০০০", receipt)

    def test_qr_code_generation(self):
        """Verify Base64 image string generation for payment QR."""
        pay_url = "https://pay.tradewolf.os/test"
        qr_code = SmartInvoiceEngine.generate_payment_qr_base64(pay_url)
        
        self.assertTrue(qr_code.startswith("data:image/png;base64,"))
        self.assertGreater(len(qr_code), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)