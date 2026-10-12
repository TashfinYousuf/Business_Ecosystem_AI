"""
backend/tests/test_auth_middleware.py
Unit and integration tests for Multi-Tenant Auth Middleware and RLS injection.
"""

import os
import sys
import unittest
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_API_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "core-api"))
sys.path.insert(0, CORE_API_DIR)

from main import app
from middleware.auth_middleware import JWT_SECRET_KEY, JWT_ALGORITHM


class TestTenantAuthMiddleware(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.valid_org_id = str(uuid.uuid4())
        self.valid_user_id = str(uuid.uuid4())

    def _generate_token(self, org_id: str, user_id: str, expires_delta: timedelta = timedelta(hours=1)) -> str:
        """Helper to create signed test JWT."""
        payload = {
            "sub": user_id,
            "org_id": org_id,
            "role": "MERCHANT",
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def test_public_healthz_bypasses_auth(self):
        """Verify that public endpoints like /healthz do not require authentication."""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ONLINE")

    def test_missing_auth_rejected_on_protected_route(self):
        """Verify that protected business endpoints block requests lacking tenant credentials."""
        response = self.client.get("/api/v1/health-score")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data["error"], "UNAUTHORIZED_TENANT")

    def test_valid_jwt_sets_tenant_context(self):
        """Verify that valid JWT grants access and reflects tenant context in headers."""
        token = self._generate_token(self.valid_org_id, self.valid_user_id)
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.get("/api/v1/health-score", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-tenant-context"), self.valid_org_id)

    def test_expired_jwt_rejected(self):
        """Verify that expired tokens are immediately blocked with 401."""
        expired_token = self._generate_token(
            self.valid_org_id, self.valid_user_id, expires_delta=timedelta(seconds=-10)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = self.client.get("/api/v1/health-score", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "AUTH_EXPIRED")

    def test_explicit_valid_uuid_header_allowed_for_internal_worker(self):
        """Verify that backend worker calls using valid X-Org-ID UUID header pass safely."""
        headers = {"X-Org-ID": self.valid_org_id}
        response = self.client.get("/api/v1/ai-saved-you", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-tenant-context"), self.valid_org_id)

    def test_invalid_uuid_header_rejected(self):
        """Verify that malformed non-UUID tenant headers are rejected."""
        headers = {"X-Org-ID": "invalid-non-uuid-string"}
        response = self.client.get("/api/v1/ai-saved-you", headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "INVALID_ORG_ID")


if __name__ == "__main__":
    unittest.main(verbosity=2)