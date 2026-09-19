import os
import sys
from datetime import datetime, timedelta
import unittest
from starlette.testclient import TestClient

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import (
    CrawlCoverageDecision,
    CrawlCoverageItem,
    CrawlCoverageSummary
)
from services.scanner.main import app
from services.scanner.db import (
    init_db,
    create_scan_record,
    save_crawl_coverage_records,
    get_scan_coverage_summary
)


class TestCrawlCoverage(unittest.TestCase):
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

    def test_coverage_schema_validation(self) -> None:
        """Should correctly instantiate CrawlCoverageItem and CrawlCoverageSummary models."""
        item = CrawlCoverageItem(
            url="https://example.com/page1",
            discovery_source="https://example.com/",
            depth=1,
            decision=CrawlCoverageDecision.VISITED,
            status_code=200,
            content_type="text/html"
        )
        self.assertEqual(item.url, "https://example.com/page1")
        self.assertEqual(item.decision, CrawlCoverageDecision.VISITED)

        summary = CrawlCoverageSummary(
            scan_id="SCAN-TEST-01",
            total_discovered=1,
            visited_count=1,
            skipped_count=0,
            blocked_count=0,
            items=[item]
        )
        self.assertEqual(summary.scan_id, "SCAN-TEST-01")
        self.assertEqual(len(summary.items), 1)

    def test_db_save_and_get_coverage_summary(self) -> None:
        """Should save crawl coverage records in SQLite DB and fetch calculated summary."""
        create_scan_record(self.conn, "SCAN-COVERAGE-DB", ["example.com"], self.valid_policy)

        coverage_items = [
            {
                "url": "https://example.com/",
                "discovery_source": "seed",
                "depth": 0,
                "decision": CrawlCoverageDecision.VISITED,
                "status_code": 200,
                "content_type": "text/html"
            },
            {
                "url": "https://example.com/about",
                "discovery_source": "https://example.com/",
                "depth": 1,
                "decision": CrawlCoverageDecision.VISITED,
                "status_code": 200,
                "content_type": "text/html"
            },
            {
                "url": "https://external.com/link",
                "discovery_source": "https://example.com/",
                "depth": 1,
                "decision": CrawlCoverageDecision.BLOCKED,
                "rejection_reason": "Out of scope domain"
            },
            {
                "url": "https://example.com/doc.pdf",
                "discovery_source": "https://example.com/",
                "depth": 1,
                "decision": CrawlCoverageDecision.SKIPPED,
                "rejection_reason": "Unsupported MIME type"
            }
        ]

        save_crawl_coverage_records(self.conn, "SCAN-COVERAGE-DB", coverage_items)
        summary = get_scan_coverage_summary(self.conn, "SCAN-COVERAGE-DB")

        self.assertEqual(summary["scan_id"], "SCAN-COVERAGE-DB")
        self.assertEqual(summary["total_discovered"], 4)
        self.assertEqual(summary["visited_count"], 2)
        self.assertEqual(summary["blocked_count"], 1)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertEqual(len(summary["items"]), 4)

    def test_db_invalid_scan_id_raises_value_error(self) -> None:
        """Should raise ValueError when saving or getting coverage for unknown scan_id."""
        with self.assertRaises(ValueError):
            save_crawl_coverage_records(self.conn, "NONEXISTENT-SCAN", [])

        with self.assertRaises(ValueError):
            get_scan_coverage_summary(self.conn, "NONEXISTENT-SCAN")

    def test_api_coverage_endpoints(self) -> None:
        """Should test POST & GET /api/v1/scans/{scan_id}/coverage endpoints."""
        # 1. Create scan job via API
        create_req = {
            "scan_id": "SCAN-API-COVERAGE",
            "policy": self.valid_policy
        }
        res_create = self.client.post("/api/v1/scans", json=create_req)
        self.assertEqual(res_create.status_code, 201)

        # 2. Record coverage items via POST API
        coverage_payload = {
            "items": [
                {
                    "url": "https://example.com/",
                    "discovery_source": "seed",
                    "depth": 0,
                    "decision": "visited",
                    "status_code": 200,
                    "content_type": "text/html"
                },
                {
                    "url": "https://example.com/blocked-path",
                    "discovery_source": "https://example.com/",
                    "depth": 1,
                    "decision": "blocked",
                    "rejection_reason": "Disallowed path"
                }
            ]
        }
        res_post = self.client.post("/api/v1/scans/SCAN-API-COVERAGE/coverage", json=coverage_payload)
        self.assertEqual(res_post.status_code, 201)
        summary_post = res_post.json()
        self.assertEqual(summary_post["total_discovered"], 2)
        self.assertEqual(summary_post["visited_count"], 1)
        self.assertEqual(summary_post["blocked_count"], 1)

        # 3. Fetch coverage summary via GET API
        res_get = self.client.get("/api/v1/scans/SCAN-API-COVERAGE/coverage")
        self.assertEqual(res_get.status_code, 200)
        summary_get = res_get.json()
        self.assertEqual(summary_get["scan_id"], "SCAN-API-COVERAGE")
        self.assertEqual(summary_get["total_discovered"], 2)
        self.assertEqual(len(summary_get["items"]), 2)

    def test_api_coverage_nonexistent_scan_returns_404(self) -> None:
        """Should return 404 for unknown scan_id on POST and GET coverage endpoints."""
        res_get = self.client.get("/api/v1/scans/UNKNOWN-SCAN/coverage")
        self.assertEqual(res_get.status_code, 404)

        res_post = self.client.post("/api/v1/scans/UNKNOWN-SCAN/coverage", json={"items": []})
        self.assertEqual(res_post.status_code, 404)


if __name__ == "__main__":
    unittest.main()
