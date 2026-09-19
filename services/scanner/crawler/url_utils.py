import re
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode, unquote

UNRESERVED_CHARS_REGEX = re.compile(r"%([0-9a-fA-F]{2})")

def _unquote_unreserved(match: re.Match) -> str:
    hex_val = match.group(1)
    char_code = int(hex_val, 16)
    char = chr(char_code)
    # Unreserved RFC 3986 chars: A-Z, a-z, 0-9, "-", ".", "_", "~"
    if char.isalnum() or char in ("-", ".", "_", "~"):
        return char
    return f"%{hex_val.upper()}"

def normalize_url(raw_url: str, base_url: str = None) -> str:
    if not raw_url or not isinstance(raw_url, str):
        raise ValueError("URL must be a non-empty string.")

    cleaned = raw_url.strip()

    # Reject non-HTTP(S) pseudo-schemes directly
    if cleaned.lower().startswith(("javascript:", "data:", "mailto:", "tel:", "about:")):
        return cleaned.lower()

    # Resolve relative URL if base_url is provided
    if base_url:
        cleaned = urljoin(base_url, cleaned)

    parsed = urlparse(cleaned)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path

    # Extract hostname and port
    if ":" in netloc:
        host, port_str = netloc.split(":", 1)
        try:
            port = int(port_str)
            # Remove default ports
            if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
                netloc = host
        except ValueError:
            pass
    else:
        host = netloc

    # Unquote unreserved characters in path
    if path:
        path = UNRESERVED_CHARS_REGEX.sub(_unquote_unreserved, path)
        # Normalize duplicate slashes
        path = re.sub(r"/{2,}", "/", path)

    # Remove trailing slash for non-root paths
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    # Canonicalize query parameters (sorted by key, then value)
    query_str = ""
    if parsed.query:
        qsl = parse_qsl(parsed.query, keep_blank_values=True)
        qsl_sorted = sorted(qsl, key=lambda x: (x[0], x[1]))
        query_str = urlencode(qsl_sorted)

    # Strip fragment completely (fragments are client-side only)
    normalized = urlunparse((scheme, netloc, path or "/", "", query_str, ""))
    return normalized
