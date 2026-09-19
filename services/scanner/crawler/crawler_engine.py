import urllib.request
import urllib.error
from collections import deque
from typing import List, Dict, Any, Optional, Callable
from packages.contracts.schemas import ScanPolicy
from services.scanner.crawler.url_utils import normalize_url
from services.scanner.crawler.scope_gate import is_url_in_scope
from services.scanner.crawler.deduplicator import URLDeduplicator
from services.scanner.crawler.link_extractor import extract_html_links

class PassiveCrawlerEngine:
    def __init__(self, policy: ScanPolicy, seed_urls: List[str]):
        self.policy = policy
        self.seed_urls = seed_urls
        self.deduplicator = URLDeduplicator()
        
        self.visited_records: List[Dict[str, Any]] = []
        self.skipped_records: List[Dict[str, Any]] = []
        self.blocked_records: List[Dict[str, Any]] = []
        self.request_count: int = 0
        self.max_depth_seen: int = 0

    def _default_fetch(self, url: str) -> Dict[str, Any]:
        """
        Executes a safe GET request using standard urllib.
        """
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DesktopSecurityQAAgent/0.1.0 (Passive Scan Engine)"},
            method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                status_code = response.status
                content_type = response.headers.get("Content-Type", "")
                body_bytes = response.read(1024 * 512) # Read up to 512KB
                body_str = body_bytes.decode("utf-8", errors="ignore")
                return {
                    "status_code": status_code,
                    "content_type": content_type,
                    "body": body_str,
                    "final_url": response.url
                }
        except urllib.error.HTTPError as e:
            return {
                "status_code": e.code,
                "content_type": e.headers.get("Content-Type", "") if e.headers else "",
                "body": "",
                "final_url": url
            }
        except Exception as e:
            return {
                "status_code": 0,
                "content_type": "",
                "body": "",
                "error": str(e),
                "final_url": url
            }

    def crawl(self, fetch_fn: Optional[Callable[[str], Dict[str, Any]]] = None) -> Dict[str, Any]:
        fetch = fetch_fn or self._default_fetch
        queue: deque = deque()

        # Seed queue initialization
        for seed in self.seed_urls:
            try:
                norm_seed = normalize_url(seed)
                in_scope, reason = is_url_in_scope(norm_seed, self.policy)
                if in_scope:
                    if self.deduplicator.mark_queued(norm_seed):
                        queue.append((norm_seed, 0))
                else:
                    self.blocked_records.append({
                        "url": norm_seed,
                        "reason": reason,
                        "source": "seed"
                    })
            except Exception:
                pass

        while queue and self.request_count < self.policy.total_request_budget:
            current_url, depth = queue.popleft()

            # Verify depth limit
            if depth > self.policy.max_depth:
                self.skipped_records.append({
                    "url": current_url,
                    "reason": "max_depth_exceeded",
                    "depth": depth
                })
                continue

            # Verify scope gate
            in_scope, reason = is_url_in_scope(current_url, self.policy)
            if not in_scope:
                self.blocked_records.append({
                    "url": current_url,
                    "reason": reason,
                    "depth": depth
                })
                continue

            self.deduplicator.mark_visited(current_url)
            self.request_count += 1
            self.max_depth_seen = max(self.max_depth_seen, depth)

            # Fetch page content
            res = fetch(current_url)
            status_code = res.get("status_code", 0)
            content_type = res.get("content_type", "")
            body = res.get("body", "")

            self.visited_records.append({
                "url": current_url,
                "status_code": status_code,
                "content_type": content_type,
                "depth": depth
            })

            # If HTML, extract links for crawling next level
            if "html" in content_type.lower() and body and depth < self.policy.max_depth:
                extracted_links = extract_html_links(body, current_url)
                for link in extracted_links:
                    link_in_scope, link_reason = is_url_in_scope(link, self.policy)
                    if not link_in_scope:
                        if not any(r["url"] == link for r in self.blocked_records):
                            self.blocked_records.append({
                                "url": link,
                                "reason": link_reason,
                                "source": current_url
                            })
                        continue

                    if self.deduplicator.mark_queued(link):
                        queue.append((link, depth + 1))

        return {
            "summary": {
                "total_requests": self.request_count,
                "visited_count": len(self.visited_records),
                "skipped_count": len(self.skipped_records),
                "blocked_count": len(self.blocked_records),
                "max_depth_reached": self.max_depth_seen,
                "budget_reached": self.request_count >= self.policy.total_request_budget
            },
            "visited": self.visited_records,
            "skipped": self.skipped_records,
            "blocked": self.blocked_records
        }
