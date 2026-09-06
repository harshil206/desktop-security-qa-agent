import os
import sys
import unittest

DESKTOP_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "desktop", "src"))
DOCS_ARCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "architecture"))

class TestProcessOwnershipSpecification(unittest.TestCase):
    def test_process_ownership_doc_exists(self) -> None:
        """Should verify process_ownership.md exists and contains state definitions."""
        doc_path = os.path.join(DOCS_ARCH_DIR, "process_ownership.md")
        self.assertTrue(os.path.exists(doc_path), f"File not found: {doc_path}")

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Parent Process:", content)
        self.assertIn("Child Process:", content)
        self.assertIn("127.0.0.1:8000", content)
        self.assertIn("HANDSHAKE", content)
        self.assertIn("SIGTERM", content)

    def test_scanner_process_manager_implementation(self) -> None:
        """Should verify scanner-process.ts implements process lifecycle states."""
        ts_path = os.path.join(DESKTOP_SRC_DIR, "scanner-process.ts")
        self.assertTrue(os.path.exists(ts_path), f"File not found: {ts_path}")

        with open(ts_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ScannerProcessManager", content)
        self.assertIn("performHandshake", content)
        self.assertIn("handleProcessExit", content)
        self.assertIn("Security Violation", content)

if __name__ == "__main__":
    unittest.main()
