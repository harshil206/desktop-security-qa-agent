import re
from typing import Dict, Any, Union, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

SENSITIVE_HEADER_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "proxy-authorization",
    "x-auth-token",
    "x-csrf-token",
    "bearer",
    "session",
    "sec-websocket-key",
}

SENSITIVE_PARAM_KEYWORDS = {
    "token",
    "access_token",
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "auth",
    "session",
    "sessionid",
    "jwt",
    "key",
}

JWT_REGEX = re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*")
BEARER_REGEX = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/=]+")
BASIC_AUTH_REGEX = re.compile(r"(?i)(basic\s+)[A-Za-z0-9+/=]+")
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
REDACTED_SUBST = "[REDACTED]"


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Redact sensitive HTTP header values."""
    if not headers:
        return {}
    sanitized = {}
    for key, val in headers.items():
        k_lower = key.lower().strip()
        if k_lower in ("cookie", "set-cookie"):
            sanitized[key] = redact_cookies(str(val))
        elif k_lower in SENSITIVE_HEADER_KEYS:
            sanitized[key] = REDACTED_SUBST
        else:
            sanitized[key] = redact_text_content(str(val))
    return sanitized



def redact_cookies(cookie_str: str) -> str:
    """Mask cookie values while preserving cookie names."""
    if not cookie_str:
        return ""
    parts = cookie_str.split(";")
    sanitized_parts = []
    for part in parts:
        if "=" in part:
            name, _ = part.split("=", 1)
            sanitized_parts.append(f"{name.strip()}={REDACTED_SUBST}")
        else:
            sanitized_parts.append(part.strip())
    return "; ".join(sanitized_parts)


def redact_url_query_params(url: str) -> str:
    """Mask sensitive parameters in URL query strings."""
    if not url or "?" not in url:
        return url
    try:
        parsed = urlparse(url)
        query_dict = parse_qs(parsed.query, keep_blank_values=True)
        new_query = []
        for param, vals in query_dict.items():
            param_lower = param.lower().strip()
            is_sensitive = any(kw in param_lower for kw in SENSITIVE_PARAM_KEYWORDS)
            if is_sensitive:
                new_query.append((param, REDACTED_SUBST))
            else:
                for v in vals:
                    new_query.append((param, redact_text_content(v)))
        encoded_query = urlencode(new_query)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            encoded_query,
            parsed.fragment
        ))
    except Exception:
        return url


def redact_text_content(text: str) -> str:
    """Redact JWTs, Bearer tokens, Basic Auth credentials, and emails from text."""
    if not text:
        return text
    text = JWT_REGEX.sub(REDACTED_SUBST, text)
    text = BEARER_REGEX.sub(r"\1" + REDACTED_SUBST, text)
    text = BASIC_AUTH_REGEX.sub(r"\1" + REDACTED_SUBST, text)
    text = EMAIL_REGEX.sub(REDACTED_SUBST, text)
    return text


def redact_evidence_metadata(data: Union[Dict[str, Any], List[Any], str, Any]) -> Any:
    """Recursively redact sensitive data structure values and dictionary keys."""
    if isinstance(data, dict):
        sanitized_dict = {}
        for key, val in data.items():
            key_lower = str(key).lower().strip()
            if key_lower in SENSITIVE_HEADER_KEYS or any(kw in key_lower for kw in SENSITIVE_PARAM_KEYWORDS):
                if isinstance(val, dict) and key_lower in ("headers", "response_headers"):
                    sanitized_dict[key] = redact_headers(val)
                else:
                    sanitized_dict[key] = REDACTED_SUBST
            elif key_lower == "headers":
                sanitized_dict[key] = redact_headers(val) if isinstance(val, dict) else redact_evidence_metadata(val)
            elif key_lower == "url" or key_lower.endswith("_url"):
                sanitized_dict[key] = redact_url_query_params(str(val))
            else:
                sanitized_dict[key] = redact_evidence_metadata(val)
        return sanitized_dict
    elif isinstance(data, list):
        return [redact_evidence_metadata(item) for item in data]
    elif isinstance(data, str):
        return redact_text_content(redact_url_query_params(data))
    return data
