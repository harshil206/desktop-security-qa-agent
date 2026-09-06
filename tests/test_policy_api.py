import os
import sys
from datetime import datetime, timedelta
import unittest
from starlette.testclient import TestClient

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.scanner.main import app

class TestPolicyAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        now = datetime.now()
        future = now + timedelta(hours=2)

        self.valid_payload = {
            "authorization": {
                "contact_email": "security@example.com",
                "authorized_by": "Jane Doe",
                "owner_confirmed": True,
                "valid_from": now.isoformat(),
                "valid_until": future.isoformat(),
                "target_domains": ["example.com"]
            },
            "target_domains": ["example.com"],
            "allowed_url_prefixes": ["https://example.com/api"],
            "max_depth": 3,
            "requests_per_minute": 60,
            "total_request_budget": 500,
            "max_duration_seconds": 1800,
            "scan_mode": "passive",
            "allowed_http_methods": ["GET", "HEAD"]
        }

    def test_validate_valid_policy(self) -> None:
        """Should return valid=true for a compliant scan policy."""
        response = self.client.post("/api/v1/policies/validate", json=self.valid_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertIn("policy", data)

    def test_validate_unconfirmed_owner(self) -> None:
        """Should return valid=false when owner_confirmed is false."""
        payload = dict(self.valid_payload)
        payload["authorization"] = dict(payload["authorization"])
        payload["authorization"]["owner_confirmed"] = False

        response = self.client.post("/api/v1/policies/validate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertIn("errors", data)

    def test_validate_unauthorized_domain(self) -> None:
        """Should return valid=false when policy target domain is not in authorization record."""
        payload = dict(self.valid_payload)
        payload["target_domains"] = ["unauthorized-domain.com"]
        payload["allowed_url_prefixes"] = ["https://unauthorized-domain.com/"]

        response = self.client.post("/api/v1/policies/validate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["valid"])

    def test_validate_unsafe_budget(self) -> None:
        """Should return valid=false when budget limits are exceeded."""
        payload = dict(self.valid_payload)
        payload["max_depth"] = 10  # max allowed is 5

        response = self.client.post("/api/v1/policies/validate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["valid"])

    def test_validate_active_mode_rejection(self) -> None:
        """Should return valid=false when scan_mode is active."""
        payload = dict(self.valid_payload)
        payload["scan_mode"] = "active"

        response = self.client.post("/api/v1/policies/validate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["valid"])

    def test_create_policy_endpoint(self) -> None:
        """Should return 200 OK and status=validated for valid POST /api/v1/policies."""
        response = self.client.post("/api/v1/policies", json=self.valid_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "validated")

    def test_create_policy_invalid_payload(self) -> None:
        """Should return HTTP 422 for malformed policy creation request."""
        invalid_payload = {"invalid": "data"}
        response = self.client.post("/api/v1/policies", json=invalid_payload)
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
