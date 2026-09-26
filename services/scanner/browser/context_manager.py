from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import logging

try:
    from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Playwright = Any  # type: ignore
    Browser = Any  # type: ignore
    BrowserContext = Any  # type: ignore
    Page = Any  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "DesktopSecurityQAAgent/1.0 (Passive Scan; Ephemeral Evidence Worker)"
DEFAULT_NAVIGATION_TIMEOUT_MS = 15000
DEFAULT_VIEWPORT = {"width": 1280, "height": 800}


@dataclass
class BrowserContextOptions:
    navigation_timeout_ms: int = DEFAULT_NAVIGATION_TIMEOUT_MS
    accept_downloads: bool = False
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800
    user_agent: str = DEFAULT_USER_AGENT
    ignore_https_errors: bool = True
    extra_http_headers: Dict[str, str] = field(default_factory=dict)

    def to_context_args(self) -> Dict[str, Any]:
        return {
            "accept_downloads": self.accept_downloads,
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "user_agent": self.user_agent,
            "ignore_https_errors": self.ignore_https_errors,
            "extra_http_headers": self.extra_http_headers,
        }


class BrowserContextManager:
    """
    Manages isolated, ephemeral Playwright browser contexts for passive scan evidence gathering.

    Security & Hardening Controls:
    1. Ephemeral context: Creates a fresh browser context per invocation (no persistent profile reuse).
    2. Download restrictions: Disables download acceptance and cancels any triggered download events.
    3. Navigation timeouts: Configures strict page and navigation timeouts.
    4. Guaranteed cleanup: Ensures context and browser instances are closed even on failure.
    """

    def __init__(self, options: Optional[BrowserContextOptions] = None):
        self.options = options or BrowserContextOptions()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    @property
    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE

    def __enter__(self) -> Tuple[Browser, BrowserContext]:
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright package is not available in the current environment.")

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.options.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                ]
            )
            
            context_args = self.options.to_context_args()
            self._context = self._browser.new_context(**context_args)
            self._context.set_default_navigation_timeout(self.options.navigation_timeout_ms)
            self._context.set_default_timeout(self.options.navigation_timeout_ms)

            if not self.options.accept_downloads:
                def handle_download(download: Any) -> None:
                    try:
                        download.cancel()
                        logger.warning("Canceled unexpected file download attempt during passive scan.")
                    except Exception as err:
                        logger.error(f"Error canceling download: {err}")

                self._context.on("download", handle_download)

            return self._browser, self._context

        except Exception as e:
            self.close()
            raise e

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Safely close context, browser, and playwright engine."""
        if self._context:
            try:
                self._context.close()
            except Exception as e:
                logger.error(f"Error closing browser context: {e}")
            finally:
                self._context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception as e:
                logger.error(f"Error closing browser process: {e}")
            finally:
                self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.error(f"Error stopping playwright engine: {e}")
            finally:
                self._playwright = None
