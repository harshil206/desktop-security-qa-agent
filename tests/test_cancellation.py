import os
import sys
from datetime import datetime, timedelta
import unittest
from starlette.testclient import TestClient

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.scanner.main import app
from services.scanner.db import (
    init_db,
    create_scan_record,
    update_scan_status,
    cancel_scan_job,
    emergency_stop_scan_job,
    is_scan_active,
    get_scan_history
)

class TestScanCancellationAndEmergencyStop(unittest.TestCase):
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

    def test_cancel_scan_job(self) -> None:
        """Should transition scan from queued/running to cancelled and log history."""
        scan = create_scan_record(self.conn, "SCAN-CANCEL-01", ["example.com"], self.valid_policy)
        update_scan_status(self.conn, "SCAN-CANCEL-01", "scope_validated")
        update_scan_status(self.conn, "SCAN-CANCEL-01", "queued")
        
        self.assertTrue(is_scan_active(self.conn, "SCAN-CANCEL-01"))

        # Cancel scan job
        cancelled = cancel_scan_job(self.conn, "SCAN-CANCEL-01", "User clicked cancel button")
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertFalse(is_scan_active(self.conn, "SCAN-CANCEL-01"))

        history = get_scan_history(self.conn, "SCAN-CANCEL-01")
        self.assertEqual(history[-1]["to_status"], "cancelled")
        self.assertEqual(history[-1]["reason"], "User clicked cancel button")

    def test_emergency_stop_scan_job(self) -> None:
        """Should transition running scan to blocked instantly on emergency stop."""
        create_scan_record(self.conn, "SCAN-STOP-01", ["example.com"], self.valid_policy)
        update_scan_status(self.conn, "SCAN-STOP-01", "scope_validated")
        update_scan_status(self.conn, "SCAN-STOP-01", "queued")
        update_scan_status(self.conn, "SCAN-STOP-01", "running")

        self.assertTrue(is_scan_active(self.conn, "SCAN-STOP-01"))

        # Emergency stop
        stopped = emergency_stop_scan_job(self.conn, "SCAN-STOP-01", "Emergency stop key pressed")
        self.assertEqual(stopped["status"], "blocked")
        self.assertFalse(is_scan_active(self.conn, "SCAN-STOP-01"))

    def test_cancellation_api_endpoints(self) -> None:
        """Should test API POST /api/v1/scans/{scan_id}/cancel and emergency-stop."""
        # 1. Create scan job via API
        create_req = {
            "scan_id": "SCAN-API-CANCEL",
            "policy": self.valid_policy
        }
        res = self.client.post("/api/v1/scans", json=create_req)
        self.assertEqual(res.status_code, 201)

        # 2. Cancel scan job via API
        res_cancel = self.client.post(
            "/api/v1/scans/SCAN-API-CANCEL/cancel",
            json={"reason": "Testing cancel endpoint"}
        )
        self.assertEqual(res_cancel.status_code, 200)
        self.assertEqual(res_cancel.json()["status"], "cancelled")

        # 3. Create second scan job and trigger emergency stop via API
        create_req_2 = {
            "scan_id": "SCAN-API-STOP",
            "policy": self.valid_policy
        }
        self.client.post("/api/v1/scans", json=create_req_2)
        self.client.patch("/api/v1/scans/SCAN-API-STOP/status", json={"status": "scope_validated"})
        self.client.patch("/api/v1/scans/SCAN-API-STOP/status", json={"status": "queued"})
        self.client.patch("/api/v1/scans/SCAN-API-STOP/status", json={"status": "running"})

        res_stop = self.client.post(
            "/api/v1/scans/SCAN-API-STOP/emergency-stop",
            json={"reason": "Emergency stop test"}
        )
        self.assertEqual(res_stop.status_code, 200)
        self.assertEqual(res_stop.json()["status"], "blocked")

if __name__ == "__main__":
    unittest.main()
