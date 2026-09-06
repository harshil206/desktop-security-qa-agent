import os
import sys
import unittest
from pydantic import ValidationError
from starlette.testclient import TestClient

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.scanner.config import ScannerConfig
from services.scanner.main import app

class TestScannerService(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        """Should return 200 OK and health status JSON payload."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "scanner"})

    def test_version_endpoint(self) -> None:
        """Should return 200 OK and version JSON payload."""
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "0.1.0"})

    def test_valid_loopback_hosts(self) -> None:
        """Should accept valid loopback hosts."""
        for host in ["127.0.0.1", "localhost", "::1"]:
            cfg = ScannerConfig(host=host)
            self.assertIn(cfg.host, ["127.0.0.1", "localhost", "::1"])

    def test_reject_external_hosts(self) -> None:
        """Should reject non-loopback hosts (0.0.0.0, LAN IPs)."""
        invalid_hosts = ["0.0.0.0", "192.168.1.1", "10.0.0.1", "0.0.0.0:8000", "external.example.com"]
        for host in invalid_hosts:
            with self.assertRaises(ValidationError, msg=f"Should have rejected host: {host}"):
                ScannerConfig(host=host)

if __name__ == "__main__":
    unittest.main()
