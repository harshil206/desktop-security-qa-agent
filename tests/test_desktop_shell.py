import os
import sys
import unittest

DESKTOP_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "desktop", "src"))

class TestDesktopShellSecurity(unittest.TestCase):
    def test_window_config_security_flags(self) -> None:
        """Should verify window-config.ts contains mandatory Electron security settings."""
        config_path = os.path.join(DESKTOP_SRC_DIR, "window-config.ts")
        self.assertTrue(os.path.exists(config_path), f"File not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("nodeIntegration: false", content)
        self.assertIn("contextIsolation: true", content)
        self.assertIn("sandbox: true", content)
        self.assertIn("webSecurity: true", content)

    def test_preload_api_definitions(self) -> None:
        """Should verify typed preload API interface file exists."""
        api_path = os.path.join(DESKTOP_SRC_DIR, "preload-api.ts")
        self.assertTrue(os.path.exists(api_path), f"File not found: {api_path}")

        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("export interface DesktopPreloadAPI", content)
        self.assertIn("getAppMetadata", content)
        self.assertIn("getHealth", content)

    def test_preload_script(self) -> None:
        """Should verify preload script exposes allowlisted capabilities."""
        preload_path = os.path.join(DESKTOP_SRC_DIR, "preload.ts")
        self.assertTrue(os.path.exists(preload_path), f"File not found: {preload_path}")

        with open(preload_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("exposeInMainWorld", content)

    def test_renderer_csp(self) -> None:
        """Should verify index.html contains Content-Security-Policy meta tag."""
        html_path = os.path.join(DESKTOP_SRC_DIR, "index.html")
        self.assertTrue(os.path.exists(html_path), f"File not found: {html_path}")

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Content-Security-Policy", content)

if __name__ == "__main__":
    unittest.main()
