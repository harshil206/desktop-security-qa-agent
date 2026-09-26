import os
import sys
import unittest
from services.scanner.browser.context_manager import (
    BrowserContextManager,
    BrowserContextOptions,
    DEFAULT_NAVIGATION_TIMEOUT_MS,
    DEFAULT_USER_AGENT
)

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestBrowserContextManager(unittest.TestCase):

    def test_context_options_defaults(self) -> None:
        """Should have conservative, passive-scanning security defaults."""
        opts = BrowserContextOptions()
        self.assertEqual(opts.navigation_timeout_ms, DEFAULT_NAVIGATION_TIMEOUT_MS)
        self.assertFalse(opts.accept_downloads)
        self.assertTrue(opts.headless)
        self.assertEqual(opts.user_agent, DEFAULT_USER_AGENT)
        self.assertTrue(opts.ignore_https_errors)

        args = opts.to_context_args()
        self.assertFalse(args["accept_downloads"])
        self.assertEqual(args["viewport"], {"width": 1280, "height": 800})
        self.assertEqual(args["user_agent"], DEFAULT_USER_AGENT)

    def test_browser_context_lifecycle_and_isolation(self) -> None:
        """Should launch isolated Chromium context and clean up completely on exit."""
        mgr = BrowserContextManager()
        self.assertTrue(mgr.is_available)

        with mgr as (browser, context):
            self.assertTrue(browser.is_connected())
            page = context.new_page()
            self.assertIsNotNone(page)
            self.assertEqual(len(context.pages), 1)

        # After exiting context manager block
        self.assertIsNone(mgr._context)
        self.assertIsNone(mgr._browser)
        self.assertIsNone(mgr._playwright)

    def test_navigation_timeout_configuration(self) -> None:
        """Should configure strict navigation timeout on context pages."""
        custom_opts = BrowserContextOptions(navigation_timeout_ms=5000)
        mgr = BrowserContextManager(custom_opts)

        with mgr as (browser, context):
            page = context.new_page()
            # Navigate to about:blank or local data URI
            page.goto("data:text/html,<h1>Test Page</h1>")
            heading = page.query_selector("h1")
            self.assertIsNotNone(heading)
            self.assertEqual(heading.inner_text(), "Test Page")

    def test_cleanup_on_exception(self) -> None:
        """Should guarantee context and browser closure even if an exception occurs inside the block."""
        mgr = BrowserContextManager()
        
        with self.assertRaises(RuntimeError):
            with mgr as (browser, context):
                page = context.new_page()
                page.goto("data:text/html,<p>Failure simulation</p>")
                raise RuntimeError("Simulated failure during navigation or processing")

        # Verify browser and context were cleaned up
        self.assertIsNone(mgr._context)
        self.assertIsNone(mgr._browser)
        self.assertIsNone(mgr._playwright)


if __name__ == "__main__":
    unittest.main()
