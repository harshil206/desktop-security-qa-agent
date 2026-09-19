import os
import sys
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
import unittest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import AuthorizationRecord, ScanPolicy
from services.scanner.crawler.crawler_engine import PassiveCrawlerEngine

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
SITE_DIR = os.path.join(FIXTURES_DIR, "site")

class TestPassiveCrawlerEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        class QuietFixtureHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=SITE_DIR, **kwargs)

            def log_message(self, format, *args):
                pass

        cls.server = HTTPServer(("127.0.0.1", 0), QuietFixtureHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        now = datetime.now()
        future = now + timedelta(hours=2)

        self.target_host = f"127.0.0.1:{self.port}"
        self.base_url = f"http://{self.target_host}/"

        self.auth = AuthorizationRecord(
            contact_email="security@example.com",
            authorized_by="Security Team",
            owner_confirmed=True,
            valid_from=now,
            valid_until=future,
            target_domains=[self.target_host]
        )

        self.policy = ScanPolicy(
            authorization=self.auth,
            target_domains=[self.target_host],
            allowed_url_prefixes=[self.base_url],
            max_depth=3,
            requests_per_minute=60,
            total_request_budget=500,
            max_duration_seconds=1800,
            scan_mode="passive"
        )

    def test_crawl_local_fixture_site(self) -> None:
        """Should crawl in-scope fixture pages and record external links as blocked."""
        seed_url = f"{self.base_url}index.html"
        engine = PassiveCrawlerEngine(self.policy, [seed_url])
        result = engine.crawl()

        summary = result["summary"]
        visited = result["visited"]
        blocked = result["blocked"]

        visited_urls = [r["url"] for r in visited]
        self.assertIn(f"{self.base_url}index.html", visited_urls)
        self.assertIn(f"{self.base_url}page-two.html", visited_urls)
        self.assertIn(f"{self.base_url}qa-errors.html", visited_urls)

        # External link should be recorded as blocked/out of scope
        blocked_urls = [b["url"] for b in blocked]
        self.assertIn("https://external.example.org/", blocked_urls)
        self.assertGreater(summary["visited_count"], 0)
        self.assertGreater(summary["blocked_count"], 0)

    def test_crawl_request_budget_enforcement(self) -> None:
        """Should stop crawling immediately when request budget is reached."""
        budget_policy = ScanPolicy(
            authorization=self.auth,
            target_domains=[self.target_host],
            allowed_url_prefixes=[self.base_url],
            max_depth=3,
            requests_per_minute=60,
            total_request_budget=2,  # Strict limit of 2 requests
            max_duration_seconds=1800,
            scan_mode="passive"
        )

        seed_url = f"{self.base_url}index.html"
        engine = PassiveCrawlerEngine(budget_policy, [seed_url])
        result = engine.crawl()

        summary = result["summary"]
        self.assertEqual(summary["total_requests"], 2)
        self.assertTrue(summary["budget_reached"])

    def test_crawl_depth_limit_enforcement(self) -> None:
        """Should not traverse beyond max_depth limit."""
        depth_policy = ScanPolicy(
            authorization=self.auth,
            target_domains=[self.target_host],
            allowed_url_prefixes=[self.base_url],
            max_depth=1,  # Only fetch seed URL & immediate level-1 links
            requests_per_minute=60,
            total_request_budget=10,
            max_duration_seconds=1800,
            scan_mode="passive"
        )

        seed_url = f"{self.base_url}index.html"
        engine = PassiveCrawlerEngine(depth_policy, [seed_url])
        result = engine.crawl()

        summary = result["summary"]
        self.assertLessEqual(summary["max_depth_reached"], 1)

if __name__ == "__main__":
    unittest.main()
