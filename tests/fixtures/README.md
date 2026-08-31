# Local Test Fixtures

The files in `site/` are deliberately harmless local pages for early crawler, browser-evidence, and deterministic-rule tests.

Expected behavior:

- `/` links to two in-scope pages.
- `/page-two.html` provides a valid linked page.
- `/qa-errors.html` creates a controlled browser console error and references a missing static asset.
- `/redirect.html` uses a local-only HTML meta refresh to `/page-two.html`; it is not an HTTP redirect test.

Serve only through `127.0.0.1` using the documented README command. Do not add real credentials, targets, exploit payloads, or sensitive data to fixtures.
