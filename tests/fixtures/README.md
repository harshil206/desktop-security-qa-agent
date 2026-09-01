# Local Test Fixtures

The files in `site/` are deliberately harmless local pages for early crawler, browser-evidence, and deterministic-rule tests.

## Expected Behavior & Assertions

- `/index.html`: Links to in-scope pages (`page-two.html`, `qa-errors.html`, `redirect.html`), fragment link (`page-two.html#section1`), and an external out-of-scope link (`https://external.example.org/`).
- `/page-two.html`: Provides a valid linked page returning to home.
- `/qa-errors.html`: Emits a controlled browser console error and references a missing static asset (`assets/does-not-exist.png`).
- `/redirect.html`: Uses an HTML meta refresh to `/page-two.html`.
- `expected_findings.json`: Defines machine-readable expected assertions for automated crawler and rule engine verification.

## Serving Local Fixtures

Serve only through `127.0.0.1` using the following command:

```powershell
python -m http.server 8080 --directory tests/fixtures/site
```

Do not add real credentials, external targets, exploit payloads, or sensitive data to fixtures.
