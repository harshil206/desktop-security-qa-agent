import os
import sys
import shutil
import tempfile
import unittest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import ArtifactType, EvidenceRef
from services.scanner.storage.redactor import (
    redact_headers,
    redact_cookies,
    redact_url_query_params,
    redact_text_content,
    redact_evidence_metadata
)
from services.scanner.storage.artifact_store import ArtifactStore


class TestRedactionAndStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.store = ArtifactStore(base_output_dir=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_redact_headers(self) -> None:
        """Should redact sensitive header keys and mask cookie values."""
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.K5...",
            "Cookie": "session_id=secret123; theme=dark",
            "X-API-Key": "key-secret-999",
            "Content-Type": "application/json"
        }
        sanitized = redact_headers(headers)
        self.assertEqual(sanitized["Authorization"], "[REDACTED]")
        self.assertEqual(sanitized["Cookie"], "session_id=[REDACTED]; theme=[REDACTED]")
        self.assertEqual(sanitized["X-API-Key"], "[REDACTED]")
        self.assertEqual(sanitized["Content-Type"], "application/json")

    def test_redact_cookies(self) -> None:
        """Should mask cookie values while keeping cookie names intact."""
        cookie_str = "sess=12345; token=abcde; prefs=default"
        redacted = redact_cookies(cookie_str)
        self.assertEqual(redacted, "sess=[REDACTED]; token=[REDACTED]; prefs=[REDACTED]")

    def test_redact_url_query_params(self) -> None:
        """Should mask sensitive query parameter values in URLs."""
        url = "https://example.com/api/v1/user?id=123&token=supersecret&apikey=key99"
        redacted = redact_url_query_params(url)
        self.assertIn("id=123", redacted)
        self.assertIn("token=%5BREDACTED%5D", redacted)
        self.assertIn("apikey=%5BREDACTED%5D", redacted)

    def test_redact_text_content(self) -> None:
        """Should redact JWTs, Bearer tokens, Basic auth, and emails in text."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        raw_text = f"User logged in with token: {jwt}, Bearer secret-token-123, Basic dXNlcjpwYXNz, email: user@example.com"
        redacted = redact_text_content(raw_text)

        self.assertNotIn(jwt, redacted)
        self.assertNotIn("secret-token-123", redacted)
        self.assertNotIn("user@example.com", redacted)
        self.assertIn("Bearer [REDACTED]", redacted)
        self.assertIn("Basic [REDACTED]", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_redact_evidence_metadata(self) -> None:
        """Should recursively redact metadata dictionary contents."""
        metadata = {
            "status_code": 200,
            "headers": {
                "Authorization": "Bearer token123",
                "Content-Type": "text/html"
            },
            "location_url": "https://example.com/login?password=secretpass",
            "user_email": "admin@example.com"
        }
        clean = redact_evidence_metadata(metadata)
        self.assertEqual(clean["status_code"], 200)
        self.assertEqual(clean["headers"]["Authorization"], "[REDACTED]")
        self.assertEqual(clean["headers"]["Content-Type"], "text/html")
        self.assertIn("password=%5BREDACTED%5D", clean["location_url"])
        self.assertEqual(clean["user_email"], "[REDACTED]")

    def test_artifact_store_save_and_read(self) -> None:
        """Should save text and screenshot binary artifacts to disk and return redacted EvidenceRef."""
        scan_id = "SCAN-STORAGE-TEST"
        
        # 1. Save HTML DOM artifact
        dom_content = "<html><body><h1>Dashboard</h1><p>Token: eyJ1MjM... admin@example.com</p></body></html>"
        ref_dom = self.store.save_artifact(
            scan_id=scan_id,
            artifact_id="ART-DOM-100",
            artifact_type=ArtifactType.DOM_SNAPSHOT,
            content=dom_content,
            location_url="https://example.com/dashboard?token=secret123",
            metadata={"headers": {"Authorization": "Bearer secret"}}
        )

        self.assertIsInstance(ref_dom, EvidenceRef)
        self.assertEqual(ref_dom.artifact_id, "ART-DOM-100")
        self.assertEqual(ref_dom.artifact_type, ArtifactType.DOM_SNAPSHOT)
        self.assertNotIn("secret123", ref_dom.location_url)
        self.assertNotIn("admin@example.com", ref_dom.snippet_or_description)

        # Verify disk file creation
        filepath = self.store.get_artifact_filepath(scan_id, "ART-DOM-100")
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))

        # Read back saved text content
        read_text, mime_type = self.store.read_artifact(scan_id, "ART-DOM-100")
        self.assertEqual(read_text, dom_content)
        self.assertEqual(mime_type, "text/plain")

        # 2. Save PNG screenshot binary artifact
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
        ref_scr = self.store.save_artifact(
            scan_id=scan_id,
            artifact_id="ART-SCR-100",
            artifact_type=ArtifactType.SCREENSHOT,
            content=png_bytes,
            location_url="https://example.com/page",
            metadata={"format": "png"}
        )

        self.assertEqual(ref_scr.artifact_id, "ART-SCR-100")
        self.assertEqual(ref_scr.artifact_type, ArtifactType.SCREENSHOT)

        read_bin, mime_scr = self.store.read_artifact(scan_id, "ART-SCR-100")
        self.assertEqual(read_bin, png_bytes)
        self.assertEqual(mime_scr, "image/png")


if __name__ == "__main__":
    unittest.main()
