"""
backend/tests/test_api_endpoints.py
Unit & integration tests for FastAPI Business Endpoints.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_API_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "core-api"))
sys.path.insert(0, CORE_API_DIR)

from main import app


class TestFastAPIBusinessEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_healthz_endpoint(self):
        """Test system heartbeat."""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ONLINE")

    def test_create_sales_invoice_success(self):
        """Test sales invoice generation with accurate due calculation."""
        payload = {
            "customer_name": "Karim Enterprise",
            "customer_phone": "01999887766",
            "items": [
                {"product_name": "Sugar 50kg Sack", "quantity": 2, "unit_price": 6000, "total_price": 12000}
            ],
            "subtotal": 12000.0,
            "discount": 500.0,
            "grand_total": 11500.0,
            "paid_amount": 5000.0,
            "payment_method": "BKASH",
        }

        response = self.client.post("/api/v1/sales/invoices", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["customer_name"], "Karim Enterprise")
        self.assertEqual(data["grand_total"], 11500.0)
        self.assertEqual(data["due_amount"], 6500.0)  # 11500 - 5000 = 6500
        self.assertEqual(data["status"], "PARTIAL")

    def test_get_pending_approvals(self):
        """Test fetching human approval requests."""
        response = self.client.get("/api/v1/approvals/pending")
        self.assertEqual(response.status_code, 200)
        approvals = response.json()
        self.assertIsInstance(approvals, list)
        self.assertGreaterEqual(len(approvals), 1)

    def test_resolve_approval_request(self):
        """Test merchant resolving an approval gate."""
        payload = {"decision": "APPROVED", "resolution_note": "Verified customer balance over phone."}
        response = self.client.post("/api/v1/approvals/app-001/resolve", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "APPROVED")

    def test_get_business_health_score(self):
        """Test business health score endpoint."""
        response = self.client.get("/api/v1/health-score")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["health_band"], "MODERATE")
        self.assertIn("insights", data)

    def test_get_ai_saved_metrics(self):
        """Test AI Saved You metric endpoint."""
        response = self.client.get("/api/v1/ai-saved-you")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total_hours_saved"], 0)
        self.assertGreater(data["total_monetary_benefit_bdt"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)