import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from packages.contracts.schemas import EvidenceRef, ArtifactType

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any  # type: ignore


@dataclass
class CapturedPageResult:
    url: str
    final_url: str
    status_code: int
    title: str
    screenshot_bytes: Optional[bytes] = None
    dom_snapshot: Optional[str] = None
    console_logs: List[Dict[str, Any]] = field(default_factory=list)
    page_errors: List[Dict[str, Any]] = field(default_factory=list)
    response_headers: Dict[str, str] = field(default_factory=dict)
    evidence_refs: List[EvidenceRef] = field(default_factory=list)


def collect_page_evidence(page: Page, url: str) -> CapturedPageResult:
    """
    Passively navigate to target URL using Playwright page, collecting:
    - Final URL after redirects & page title
    - Full page screenshot PNG bytes
    - DOM HTML snapshot
    - Console logs and uncaught JS page errors
    - Response headers and HTTP status
    - Linked EvidenceRef contract instances
    """
    console_logs: List[Dict[str, Any]] = []
    page_errors: List[Dict[str, Any]] = []
    response_headers: Dict[str, str] = {}
    main_status: int = 200

    def handle_console(msg: Any) -> None:
        loc = ""
        if hasattr(msg, "location") and msg.location:
            url_val = msg.location.get("url", "")
            line_val = msg.location.get("lineNumber", 0)
            loc = f"{url_val}:{line_val}"
        console_logs.append({
            "level": getattr(msg, "type", "log"),
            "text": getattr(msg, "text", str(msg)),
            "location": loc
        })

    def handle_pageerror(err: Any) -> None:
        page_errors.append({
            "message": str(err),
            "stack": getattr(err, "stack", str(err))
        })

    def handle_response(res: Any) -> None:
        nonlocal main_status, response_headers
        if res.url == url or res.url == page.url or not response_headers:
            main_status = getattr(res, "status", 200)
            try:
                response_headers = dict(res.headers)
            except Exception:
                pass

    page.on("console", handle_console)
    page.on("pageerror", handle_pageerror)
    page.on("response", handle_response)

    response = page.goto(url, wait_until="domcontentloaded")
    if response:
        main_status = response.status
        try:
            response_headers = dict(response.headers)
        except Exception:
            pass

    final_url = page.url
    title = page.title()
    now = datetime.now()

    # Capture DOM HTML snapshot
    dom_snapshot = page.content()

    # Capture full page screenshot PNG
    try:
        screenshot_bytes = page.screenshot(type="png", full_page=True)
    except Exception:
        screenshot_bytes = page.screenshot(type="png", full_page=False)

    evidence_refs: List[EvidenceRef] = []

    # 1. Screenshot EvidenceRef
    scr_id = f"ART-SCR-{uuid.uuid4().hex[:12]}"
    evidence_refs.append(EvidenceRef(
        artifact_id=scr_id,
        artifact_type=ArtifactType.SCREENSHOT,
        location_url=final_url,
        timestamp=now,
        snippet_or_description=f"Full page PNG screenshot of {final_url} ({len(screenshot_bytes)} bytes)",
        metadata={"size_bytes": len(screenshot_bytes), "format": "png"}
    ))

    # 2. DOM Snapshot EvidenceRef
    dom_id = f"ART-DOM-{uuid.uuid4().hex[:12]}"
    snippet_text = dom_snapshot[:200].strip().replace("\n", " ") + "..." if len(dom_snapshot) > 200 else dom_snapshot
    evidence_refs.append(EvidenceRef(
        artifact_id=dom_id,
        artifact_type=ArtifactType.DOM_SNAPSHOT,
        location_url=final_url,
        timestamp=now,
        snippet_or_description=f"DOM snapshot snippet: {snippet_text}",
        metadata={"length_chars": len(dom_snapshot)}
    ))

    # 3. Console Logs EvidenceRef (if logs captured)
    if console_logs:
        con_id = f"ART-CON-{uuid.uuid4().hex[:12]}"
        evidence_refs.append(EvidenceRef(
            artifact_id=con_id,
            artifact_type=ArtifactType.CONSOLE_LOG,
            location_url=final_url,
            timestamp=now,
            snippet_or_description=f"Captured {len(console_logs)} browser console log messages",
            metadata={"log_count": len(console_logs), "logs": console_logs[:10]}
        ))

    # 4. Page Errors EvidenceRef (if page errors captured)
    if page_errors:
        err_id = f"ART-ERR-{uuid.uuid4().hex[:12]}"
        evidence_refs.append(EvidenceRef(
            artifact_id=err_id,
            artifact_type=ArtifactType.PAGE_ERROR,
            location_url=final_url,
            timestamp=now,
            snippet_or_description=f"Captured {len(page_errors)} uncaught JavaScript page errors",
            metadata={"error_count": len(page_errors), "errors": page_errors[:10]}
        ))

    # 5. Response Headers EvidenceRef
    hdr_id = f"ART-HDR-{uuid.uuid4().hex[:12]}"
    evidence_refs.append(EvidenceRef(
        artifact_id=hdr_id,
        artifact_type=ArtifactType.RESPONSE_HEADER,
        location_url=final_url,
        timestamp=now,
        snippet_or_description=f"HTTP response headers for {final_url} (Status: {main_status})",
        metadata={"status_code": main_status, "header_count": len(response_headers), "headers": response_headers}
    ))

    return CapturedPageResult(
        url=url,
        final_url=final_url,
        status_code=main_status,
        title=title,
        screenshot_bytes=screenshot_bytes,
        dom_snapshot=dom_snapshot,
        console_logs=console_logs,
        page_errors=page_errors,
        response_headers=response_headers,
        evidence_refs=evidence_refs
    )
