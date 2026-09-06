import os
import sys
import unittest

DESKTOP_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "desktop", "src"))

class TestDesktopScanSetup(unittest.TestCase):
    def test_scan_setup_form_component_exists(self) -> None:
        """Should verify ScanSetupForm.tsx exists and contains required controls."""
        form_path = os.path.join(DESKTOP_SRC_DIR, "ScanSetupForm.tsx")
        self.assertTrue(os.path.exists(form_path), f"File not found: {form_path}")

        with open(form_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ScanSetupForm", content)
        self.assertIn("ownerConfirmed", content)
        self.assertIn("targetDomains", content)
        self.assertIn("allowedUrlPrefixes", content)
        self.assertIn("maxDepth", content)
        self.assertIn("requestsPerMinute", content)
        self.assertIn("PASSIVE (Read-Only)", content)

    def test_preload_api_includes_validate_policy(self) -> None:
        """Should verify preload-api.ts includes validatePolicy signature."""
        api_path = os.path.join(DESKTOP_SRC_DIR, "preload-api.ts")
        self.assertTrue(os.path.exists(api_path), f"File not found: {api_path}")

        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("validatePolicy", content)
        self.assertIn("PolicyValidationResult", content)

if __name__ == "__main__":
    unittest.main()
