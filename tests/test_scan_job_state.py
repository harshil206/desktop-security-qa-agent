import os
import sys
from datetime import datetime, timedelta
import unittest
from starlette.testclient import TestClient

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.scanner.main import app
from services.scanner.db import init_db, create_scan_record, get_scan_record, update_scan_status, get_scan_history
from services.scanner.state_machine import validate_state_transition, InvalidStateTransitionError

class TestScanJobState(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = init_db(":memory:")
        self.client = TestClient(app)
        now = datetime.now()
        future = now + timedelta(hours=2)

        self.valid_policy = {
            "authorization": {
                "contact_email": "admin@example.com",
                "authorized_by": "System Admin",
                "owner_confirmed": True,
                "valid_from": now.isoformat(),
                "valid_until": future.isoformat(),
                "target_domains": ["example.com"]
            },
            "target_domains": ["example.com"],
            "allowed_url_prefixes": ["https://example.com/"],
            "max_depth": 3,
            "requests_per_minute": 60,
            "total_request_budget": 500,
            "max_duration_seconds": 1800,
            "scan_mode": "passive",
            "allowed_http_methods": ["GET", "HEAD"]
        }

    def test_state_machine_valid_transitions(self) -> None:
        """Should accept valid state transitions in sequence."""
        # draft -> scope_validated -> queued -> running -> completed
        validate_state_transition("draft", "scope_validated")
        validate_state_transition("scope_validated", "queued")
        validate_state_transition("queued", "running")
        validate_state_transition("running", "completed")

        # running -> blocked / failed / cancelled
        validate_state_transition("running", "blocked")
        validate_state_transition("running", "failed")
        validate_state_transition("running", "cancelled")

    def test_state_machine_invalid_transitions(self) -> None:
        """Should reject invalid state jumps."""
        with self.assertRaises(InvalidStateTransitionError):
            validate_state_transition("draft", "completed")

        with self.assertRaises(InvalidStateTransitionError):
            validate_state_transition("completed", "running")

        with self.assertRaises(InvalidStateTransitionError):
            validate_state_transition("failed", "queued")

    def test_db_scan_creation_and_history(self) -> None:
        """Should persist scan records and record state transition history in SQLite."""
        scan = create_scan_record(self.conn, "SCAN-TEST-01", ["example.com"], self.valid_policy)
        self.assertEqual(scan["scan_id"], "SCAN-TEST-01")
        self.assertEqual(scan["status"], "draft")

        # Transition draft -> scope_validated
        updated = update_scan_status(self.conn, "SCAN-TEST-01", "scope_validated", "Scope verified successfully")
        self.assertEqual(updated["status"], "scope_validated")

        history = get_scan_history(self.conn, "SCAN-TEST-01")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["from_status"], "draft")
        self.assertEqual(history[1]["to_status"], "scope_validated")
        self.assertEqual(history[1]["reason"], "Scope verified successfully")

    def test_scans_api_endpoints(self) -> None:
        """Should test scan creation, retrieval, and status PATCH endpoints."""
        # 1. Create scan job
        create_req = {
            "scan_id": "SCAN-API-01",
            "policy": self.valid_policy
        }
        res_create = self.client.post("/api/v1/scans", json=create_req)
        self.assertEqual(res_create.status_code, 201)
        self.assertEqual(res_create.json()["status"], "draft")

        # 2. Get scan job
        res_get = self.client.get("/api/v1/scans/SCAN-API-01")
        self.assertEqual(res_get.status_code, 200)
        self.assertIn("scan", res_get.json())
        self.assertIn("history", res_get.json())

        # 3. Patch status draft -> scope_validated (Valid)
        res_patch = self.client.patch("/api/v1/scans/SCAN-API-01/status", json={"status": "scope_validated", "reason": "Scope checked"})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()["status"], "scope_validated")

        # 4. Patch invalid status scope_validated -> completed (Invalid)
        res_invalid_patch = self.client.patch("/api/v1/scans/SCAN-API-01/status", json={"status": "completed"})
        self.assertEqual(res_invalid_patch.status_code, 400)
        self.assertIn("Invalid status transition", res_invalid_patch.json()["detail"])

if __name__ == "__main__":
    unittest.main()
