from typing import Tuple
from urllib.parse import urlparse
from packages.contracts.schemas import ScanPolicy, is_subdomain_or_equal
from services.scanner.crawler.url_utils import normalize_url

def is_url_in_scope(raw_url: str, policy: ScanPolicy, base_url: str = None) -> Tuple[bool, str]:
    """
    Evaluates whether a URL is in-scope according to the provided ScanPolicy.
    Returns (True, "in_scope") if permitted, or (False, reason_code) if rejected.
    """
    if not raw_url or not isinstance(raw_url, str):
        return False, "empty_url"

    # Reject non-http(s) schemes immediately
    cleaned_lower = raw_url.strip().lower()
    if cleaned_lower.startswith(("javascript:", "data:", "mailto:", "tel:", "about:")):
        return False, "invalid_scheme"

    try:
        norm_url = normalize_url(raw_url, base_url=base_url)
    except Exception:
        return False, "malformed_url"

    parsed = urlparse(norm_url)

    if parsed.scheme not in ("http", "https"):
        return False, "invalid_scheme"

    hostname = parsed.hostname
    if not hostname:
        return False, "missing_hostname"

    hostname = hostname.lower().strip()

    # 1. Verify hostname matches target_domains (or subdomain of target_domains)
    domain_matched = False
    for target_domain in policy.target_domains:
        target_host = target_domain.split(":")[0].lower().strip()
        if is_subdomain_or_equal(hostname, target_host):
            domain_matched = True
            break

    if not domain_matched:
        return False, "out_of_scope_domain"

    # 2. Verify URL matches at least one allowed_url_prefix
    prefix_matched = False
    for allowed_prefix in policy.allowed_url_prefixes:
        try:
            norm_prefix = normalize_url(allowed_prefix)
            if norm_url.startswith(norm_prefix):
                prefix_matched = True
                break
        except Exception:
            pass

    if not prefix_matched:
        return False, "out_of_scope_prefix"

    return True, "in_scope"
