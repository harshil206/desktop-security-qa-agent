import os
import sys
import json
import threading
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
import unittest

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
SITE_DIR = os.path.join(FIXTURES_DIR, "site")

class TestLocalFixturesServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Custom handler serving files from SITE_DIR
        class QuietFixtureHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=SITE_DIR, **kwargs)

            def log_message(self, format, *args):
                # Suppress log output during unit tests
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

    def test_serve_index_html(self) -> None:
        """Should serve index.html with 200 OK and expected links."""
        url = f"http://127.0.0.1:{self.port}/index.html"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            content = response.read().decode("utf-8")
            self.assertIn("Local Fixture Site", content)
            self.assertIn("href=\"page-two.html\"", content)
            self.assertIn("href=\"https://external.example.org/\"", content)

    def test_serve_qa_errors_html(self) -> None:
        """Should serve qa-errors.html containing controlled error triggers."""
        url = f"http://127.0.0.1:{self.port}/qa-errors.html"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            content = response.read().decode("utf-8")
            self.assertIn("Controlled local fixture console error", content)
            self.assertIn("assets/does-not-exist.png", content)

    def test_missing_asset_returns_404(self) -> None:
        """Should return HTTP 404 for missing static asset."""
        url = f"http://127.0.0.1:{self.port}/assets/does-not-exist.png"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url)
        self.assertEqual(ctx.exception.code, 404)

    def test_expected_findings_fixture_validity(self) -> None:
        """Should validate the expected_findings.json fixture format."""
        file_path = os.path.join(FIXTURES_DIR, "expected_findings.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("expected_coverage", data)
        self.assertIn("expected_qa_findings", data)
        self.assertGreater(len(data["expected_coverage"]["in_scope_urls"]), 0)

if __name__ == "__main__":
    unittest.main()
