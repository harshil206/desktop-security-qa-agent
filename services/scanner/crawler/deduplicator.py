from typing import Set, Dict
from services.scanner.crawler.url_utils import normalize_url

class URLDeduplicator:
    def __init__(self):
        self._visited: Set[str] = set()
        self._queued: Set[str] = set()

    def is_seen(self, raw_url: str, base_url: str = None) -> bool:
        try:
            norm = normalize_url(raw_url, base_url=base_url)
            return (norm in self._visited) or (norm in self._queued)
        except Exception:
            return True

    def mark_queued(self, raw_url: str, base_url: str = None) -> bool:
        """
        Marks URL as queued if not already seen.
        Returns True if newly queued, False if already seen.
        """
        try:
            norm = normalize_url(raw_url, base_url=base_url)
            if norm in self._visited or norm in self._queued:
                return False
            self._queued.add(norm)
            return True
        except Exception:
            return False

    def mark_visited(self, raw_url: str, base_url: str = None) -> bool:
        """
        Marks URL as visited.
        Returns True if newly visited, False if already visited.
        """
        try:
            norm = normalize_url(raw_url, base_url=base_url)
            self._queued.discard(norm)
            if norm in self._visited:
                return False
            self._visited.add(norm)
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, int]:
        return {
            "visited_count": len(self._visited),
            "queued_count": len(self._queued),
            "total_seen": len(self._visited) + len(self._queued)
        }
