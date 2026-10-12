"""
backend/tests/test_legacy_ecosystem.py
Comprehensive test suite verifying all 9 modules + Auth + Bilingual Dictionary
merged from legacy-streamlit-mvp into the decoupled FastAPI backend.
"""

import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_API_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "core-api"))
if CORE_API_DIR not in sys.path:
    sys.path.insert(0, CORE_API_DIR)

from main import app


class TestLegacyEcosystemIntegration(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.org_id = "00000000-0000-0000-0000-000000000001"
        self.headers = {"X-Org-ID": self.org_id}

    def test_01_ui_dictionary_bilingual(self):
        """Verify EN and BN UI dictionaries are returned."""
        resp = self.client.get("/api/v1/ui/dictionary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("EN", data)
        self.assertIn("BN", data)
        self.assertEqual(data["EN"]["menu_terminal"], "Live Market 🔴")
        self.assertEqual(data["BN"]["menu_terminal"], "লাইভ মার্কেট 🔴")

    def test_02_auth_register_verify_otp_and_login(self):
        """Verify user registration, 4-digit OTP ('1234') verification, and login."""
        unique_email = f"merchant_{uuid.uuid4().hex[:6]}@tradewolf.com"
        reg_resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test Merchant",
                "email": unique_email,
                "phone": "+8801711000000",
                "password": "secretpassword123",
            },
        )
        self.assertEqual(reg_resp.status_code, 201)
        self.assertTrue(reg_resp.json()["show_verification"])

        # Verify with OTP 1234
        otp_resp = self.client.post(
            "/api/v1/auth/verify-otp",
            json={"email": unique_email, "otp": "1234"},
        )
        self.assertEqual(otp_resp.status_code, 200)
        self.assertIn("access_token", otp_resp.json())

        # Login with registered credentials
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "secretpassword123"},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertEqual(login_resp.json()["username"], "Test Merchant")

    def test_03_live_market_terminal_and_arbitrage_scan(self):
        """Verify Live Market Terminal gainers/losers and StarTech AI Quant Arbitrage."""
        term_resp = self.client.get("/api/v1/market/terminal", headers=self.headers)
        self.assertEqual(term_resp.status_code, 200)
        term_data = term_resp.json()
        self.assertEqual(len(term_data["gainers"]), 4)
        self.assertEqual(len(term_data["losers"]), 4)
        self.assertEqual(term_data["metrics"]["market_heat"]["value"], "৳ 1.2B")

        arb_resp = self.client.post(
            "/api/v1/market/arbitrage-scan",
            json={"category": "smart-watch", "assumed_wholesale_discount": 0.65, "attempt_network": False},
            headers=self.headers,
        )
        self.assertEqual(arb_resp.status_code, 200)
        arb_data = arb_resp.json()
        self.assertEqual(arb_data["status"], "success")
        self.assertGreaterEqual(len(arb_data["opportunities"]), 3)
        self.assertIn("Gross Margin:", arb_data["opportunities"][0]["analysis_markdown"])

    def test_04_market_overview_and_wallet(self):
        """Verify National Sector Pulse, USD/BDT rate, Global Indicators, and Private Wallet."""
        resp = self.client.get("/api/v1/market/overview", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("national_pulse", data)
        self.assertIn("usd_rate", data)
        self.assertIn("Gold", data["global_indicators"])
        self.assertIn("Oil", data["global_indicators"])
        self.assertIn("SP500", data["global_indicators"])
        self.assertIn("private_wallet", data)

    def test_05_supplier_trust_radar(self):
        """Verify Supplier Trust Radar Titans and Red Flag Scam Alerts."""
        resp = self.client.get("/api/v1/suppliers/trust-radar", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data["verified_titans"]), 1)
        self.assertGreaterEqual(len(data["red_flag_alerts"]), 1)

    def test_06_flywheel_analytics_and_insights(self):
        """Verify Personal Ledger Analytics, Community Price Benchmark, and Proactive AI Alerts."""
        resp = self.client.get("/api/v1/analytics/flywheel", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("personal_ledger", data)
        self.assertIn("community_trends", data)
        self.assertIn("proactive_alerts", data)
        self.assertGreaterEqual(len(data["community_trends"]["benchmark_table"]), 1)

        m_resp = self.client.post(
            "/api/v1/analytics/market-insight",
            json={"product_name": "AirPods Pro 2", "current_price": 1350, "usd_rate": 118.50, "preferred_model": "groq"},
            headers=self.headers,
        )
        self.assertEqual(m_resp.status_code, 200)
        self.assertTrue(len(m_resp.json()["insight_markdown"]) > 20)

    def test_07_risk_simulator_and_capital_shield(self):
        """Verify AI Capital Shield context and interactive risk simulation."""
        ctx_resp = self.client.get("/api/v1/risk/context", headers=self.headers)
        self.assertEqual(ctx_resp.status_code, 200)
        self.assertIn("available_assets", ctx_resp.json())

        sim_resp = self.client.post(
            "/api/v1/risk/simulate",
            json={
                "capital": 100000,
                "selected_asset": "AirPods Pro 2",
                "capital_usage_pct": 50,
                "markup_pct": 25,
                "price_change_pct": -10,
            },
            headers=self.headers,
        )
        self.assertEqual(sim_resp.status_code, 200)
        sim_data = sim_resp.json()
        self.assertEqual(sim_data["max_units"], 40)  # 50,000 // 1,250 = 40
        self.assertIn("risk_score", sim_data)
        self.assertIn("portfolio_allocation", sim_data)
        self.assertIn("guard_alert", sim_data)

    def test_08_business_idea_validator(self):
        """Verify Business Idea Validator feasibility report."""
        resp = self.client.post(
            "/api/v1/validator/idea",
            json={
                "location": "Dhaka",
                "category": "TWS / Earbuds",
                "business_model": "Local Wholesale & Retail",
                "budget": 30000,
                "margin": 20,
                "risk": "Medium (Balanced)",
            },
            headers=self.headers,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Market Feasibility Score", data["report_markdown"])

    def test_09_smart_memo_scanner_and_inventory_commit(self):
        """Verify Image/Voice/Text purchase extraction and committing stock to memo_tracker."""
        ext_resp = self.client.post(
            "/api/v1/scanner/extract-text",
            json={"text": "Bought 8 AirPods Pro 2 at 1200 tk wholesale"},
            headers=self.headers,
        )
        self.assertEqual(ext_resp.status_code, 200)
        p_data = ext_resp.json()["temp_purchase"]
        self.assertEqual(p_data["quantity"], 8)

        commit_resp = self.client.post(
            "/api/v1/scanner/commit-inventory",
            json={
                "items": [
                    {"product_name": "AirPods Pro 2", "unit_price": 1200.0, "quantity": 3}
                ]
            },
            headers=self.headers,
        )
        self.assertEqual(commit_resp.status_code, 200)
        self.assertEqual(commit_resp.json()["total_units_added"], 3)

    def test_10_order_inbox_ledger_and_due_recovery(self):
        """Verify WhatsApp Order extraction, confirm & save to ledger, smart receipt, and due reminder."""
        ext_resp = self.client.post(
            "/api/v1/orders/extract-text",
            json={"text": "Sold 5 AirPods to Tuhin Bhai at 600 tk paid 1000"},
            headers=self.headers,
        )
        self.assertEqual(ext_resp.status_code, 200)
        temp_order = ext_resp.json()["temp_order"]
        self.assertEqual(temp_order["quantity"], 5)

        conf_resp = self.client.post(
            "/api/v1/orders/confirm",
            json={
                "customer_name": "Tuhin Bhai",
                "item_name": "AirPods Pro 2",
                "quantity": 5,
                "unit_price": 600.0,
                "paid_amount": 1000.0,
            },
            headers=self.headers,
        )
        self.assertEqual(conf_resp.status_code, 201)
        conf_data = conf_resp.json()
        self.assertEqual(conf_data["total_bill"], 3000.0)
        self.assertEqual(conf_data["due_amount"], 2000.0)
        self.assertIn("TRADE WOLF SMART RECEIPT", conf_data["smart_receipt"])

        ledger_resp = self.client.get("/api/v1/orders/ledger", headers=self.headers)
        self.assertEqual(ledger_resp.status_code, 200)
        self.assertGreater(ledger_resp.json()["total_dues"], 0)

        rem_resp = self.client.post(
            "/api/v1/orders/draft-reminder",
            json={"customer_name": "Tuhin Bhai"},
            headers=self.headers,
        )
        self.assertEqual(rem_resp.status_code, 200)
        self.assertIn("https://wa.me/?text=", rem_resp.json()["whatsapp_link"])

    def test_11_document_rag_upload_and_chat(self):
        """Verify Document AI (RAG) indexing and Q&A chat."""
        proc_resp = self.client.post(
            "/api/v1/rag/process-document",
            json={
                "filename": "Q3_Dhaka_Gadget_Survey.csv",
                "raw_text": "Product,Units_Sold,Avg_Price,Region\nAirPods Pro 2,450,1350,Dhaka\nLenovo LP40,620,600,Chattogram\n",
            },
            headers=self.headers,
        )
        self.assertEqual(proc_resp.status_code, 200)
        self.assertEqual(proc_resp.json()["status"], "PROCESSED")

        chat_resp = self.client.post(
            "/api/v1/rag/chat",
            json={"query": "How many AirPods Pro 2 were sold in Dhaka?", "model_choice": "groq"},
            headers=self.headers,
        )
        self.assertEqual(chat_resp.status_code, 200)
        self.assertTrue(len(chat_resp.json()["answer"]) > 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)

