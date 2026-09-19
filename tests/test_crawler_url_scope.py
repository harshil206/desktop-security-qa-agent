import os
import sys
from datetime import datetime, timedelta
import unittest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import AuthorizationRecord, ScanPolicy
from services.scanner.crawler.url_utils import normalize_url
from services.scanner.crawler.scope_gate import is_url_in_scope
from services.scanner.crawler.deduplicator import URLDeduplicator

class TestCrawlerURLScope(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime.now()
        future = now + timedelta(hours=2)

        self.auth = AuthorizationRecord(
            contact_email="security@example.com",
            authorized_by="Security Team",
            owner_confirmed=True,
            valid_from=now,
            valid_until=future,
            target_domains=["example.com", "api.example.com"]
        )

        self.policy = ScanPolicy(
            authorization=self.auth,
            target_domains=["example.com", "api.example.com"],
            allowed_url_prefixes=["https://example.com/", "https://api.example.com/v1/"],
            max_depth=3,
            requests_per_minute=60,
            total_request_budget=500,
            max_duration_seconds=1800,
            scan_mode="passive"
        )

    def test_normalize_url_basic_and_fragments(self) -> None:
        """Should lowercase scheme/host and strip fragments."""
        url = "HTTP://Example.COM:80/path/to/page.html#section-1"
        norm = normalize_url(url)
        self.assertEqual(norm, "http://example.com/path/to/page.html")

    def test_normalize_url_default_ports(self) -> None:
        """Should strip default ports 80 for HTTP and 443 for HTTPS."""
        self.assertEqual(normalize_url("http://example.com:80/"), "http://example.com/")
        self.assertEqual(normalize_url("https://example.com:443/"), "https://example.com/")
        # Preserve custom ports
        self.assertEqual(normalize_url("http://example.com:8080/"), "http://example.com:8080/")

    def test_normalize_url_query_canonicalization(self) -> None:
        """Should sort query parameters predictably."""
        url1 = "https://example.com/search?z=3&a=1&m=2"
        url2 = "https://example.com/search?a=1&m=2&z=3"
        self.assertEqual(normalize_url(url1), normalize_url(url2))
        self.assertEqual(normalize_url(url1), "https://example.com/search?a=1&m=2&z=3")

    def test_normalize_relative_urls(self) -> None:
        """Should resolve relative URLs against a base URL."""
        base = "https://example.com/docs/index.html"
        self.assertEqual(normalize_url("../page.html", base_url=base), "https://example.com/page.html")
        self.assertEqual(normalize_url("/api/v1/data", base_url=base), "https://example.com/api/v1/data")

    def test_scope_gate_in_scope_urls(self) -> None:
        """Should accept valid in-scope URLs matching policy targets and prefixes."""
        valid_urls = [
            "https://example.com/",
            "https://example.com/about/team.html",
            "https://api.example.com/v1/users",
            "HTTPS://EXAMPLE.COM/PATH?q=test#frag"
        ]
        for url in valid_urls:
            in_scope, reason = is_url_in_scope(url, self.policy)
            self.assertTrue(in_scope, f"Should be in-scope: {url} (Reason: {reason})")

    def test_scope_gate_lookalike_domain_rejection(self) -> None:
        """Should reject lookalike attacker domains and out-of-scope hostnames."""
        lookalikes = [
            "https://example.com.attacker.org/phish",
            "https://notexample.com/",
            "https://fake-example.com/",
            "https://example.org/"
        ]
        for url in lookalikes:
            in_scope, reason = is_url_in_scope(url, self.policy)
            self.assertFalse(in_scope, f"Should reject lookalike URL: {url}")
            self.assertEqual(reason, "out_of_scope_domain")

    def test_scope_gate_out_of_scope_prefix_rejection(self) -> None:
        """Should reject URLs matching target domain but not matching allowed URL prefixes."""
        # Policy requires prefixes: https://example.com/ and https://api.example.com/v1/
        # https://api.example.com/v2/ does not match https://api.example.com/v1/
        url = "https://api.example.com/v2/admin"
        in_scope, reason = is_url_in_scope(url, self.policy)
        self.assertFalse(in_scope)
        self.assertEqual(reason, "out_of_scope_prefix")

    def test_scope_gate_invalid_schemes(self) -> None:
        """Should reject non-HTTP(S) schemes (javascript, data, mailto, etc.)."""
        invalid_schemes = [
            "javascript:alert(1)",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
            "mailto:admin@example.com",
            "ftp://example.com/file.txt"
        ]
        for url in invalid_schemes:
            in_scope, reason = is_url_in_scope(url, self.policy)
            self.assertFalse(in_scope, f"Should reject non-HTTP scheme: {url}")

    def test_url_deduplicator(self) -> None:
        """Should track visited and queued URLs, deduplicating equivalent URLs."""
        dedup = URLDeduplicator()

        url_a1 = "https://example.com/page.html#section1"
        url_a2 = "HTTPS://EXAMPLE.COM/page.html#section2"

        self.assertTrue(dedup.mark_queued(url_a1))
        # Equivalent URL with different fragment or casing should be recognized as seen
        self.assertFalse(dedup.mark_queued(url_a2))
        self.assertTrue(dedup.is_seen(url_a2))

        # Transition queued to visited
        self.assertTrue(dedup.mark_visited(url_a1))
        self.assertFalse(dedup.mark_visited(url_a2))

        stats = dedup.get_stats()
        self.assertEqual(stats["visited_count"], 1)
        self.assertEqual(stats["queued_count"], 0)

if __name__ == "__main__":
    unittest.main()
