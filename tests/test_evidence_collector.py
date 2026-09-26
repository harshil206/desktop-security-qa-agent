import os
import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import unittest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import ArtifactType
from services.scanner.browser.context_manager import BrowserContextManager
from services.scanner.browser.evidence_collector import collect_page_evidence, CapturedPageResult

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
SITE_DIR = os.path.join(FIXTURES_DIR, "site")


class TestEvidenceCollector(unittest.TestCase):
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

    def test_collect_page_evidence_normal_page(self) -> None:
        """Should capture title, screenshot, DOM snapshot, response headers, and EvidenceRefs."""
        target_url = f"http://127.0.0.1:{self.port}/index.html"
        mgr = BrowserContextManager()

        with mgr as (browser, context):
            page = context.new_page()
            result = collect_page_evidence(page, target_url)

            self.assertIsInstance(result, CapturedPageResult)
            self.assertEqual(result.url, target_url)
            self.assertEqual(result.status_code, 200)
            self.assertTrue(len(result.title) > 0)

            # Screenshot binary check (PNG header b'\x89PNG')
            self.assertIsNotNone(result.screenshot_bytes)
            self.assertTrue(result.screenshot_bytes.startswith(b"\x89PNG"))

            # DOM snapshot check
            self.assertIsNotNone(result.dom_snapshot)
            self.assertIn("<html", result.dom_snapshot.lower())

            # Response headers check
            self.assertTrue(len(result.response_headers) > 0)

            # EvidenceRef checks
            artifact_types = [ref.artifact_type for ref in result.evidence_refs]
            self.assertIn(ArtifactType.SCREENSHOT, artifact_types)
            self.assertIn(ArtifactType.DOM_SNAPSHOT, artifact_types)
            self.assertIn(ArtifactType.RESPONSE_HEADER, artifact_types)

            # Verify every EvidenceRef passes schema validation
            for ref in result.evidence_refs:
                self.assertTrue(ref.artifact_id.startswith("ART-"))
                self.assertEqual(ref.location_url, result.final_url)

    def test_collect_page_evidence_errors_page(self) -> None:
        """Should capture console log and page error artifacts from pages with JS errors."""
        target_url = f"http://127.0.0.1:{self.port}/qa-errors.html"
        mgr = BrowserContextManager()

        with mgr as (browser, context):
            page = context.new_page()
            result = collect_page_evidence(page, target_url)

            self.assertEqual(result.status_code, 200)
            self.assertTrue(len(result.console_logs) > 0 or len(result.page_errors) > 0)

            artifact_types = [ref.artifact_type for ref in result.evidence_refs]
            self.assertTrue(
                ArtifactType.CONSOLE_LOG in artifact_types or ArtifactType.PAGE_ERROR in artifact_types
            )


if __name__ == "__main__":
    unittest.main()
