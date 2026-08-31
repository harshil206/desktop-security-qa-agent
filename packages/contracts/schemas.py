import re
from datetime import datetime
from typing import List, Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator

# Regular expression for basic email validation without external dependencies
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Regular expression for hostname/domain validation:
# - Must not contain schemes (http://)
# - Must not contain paths (/)
# - Must not contain query parameters (?) or fragments (#)
# - Valid hostname characters: alphanumeric, dots, and hyphens (optionally ports like hostname:port)
DOMAIN_REGEX = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-.]*[a-zA-Z0-9])?(:[0-9]+)?$")

def is_valid_domain(domain: str) -> bool:
    if not domain or "/" in domain or "://" in domain:
        return False
    return bool(DOMAIN_REGEX.match(domain))

def is_subdomain_or_equal(sub: str, parent: str) -> bool:
    sub = sub.lower().strip()
    parent = parent.lower().strip()
    if sub == parent:
        return True
    return sub.endswith("." + parent)

class AuthorizationRecord(BaseModel):
    contact_email: str = Field(..., description="Email address of the authorizing contact.")
    authorized_by: str = Field(..., description="Name of the person/entity providing authorization.")
    owner_confirmed: Literal[True] = Field(..., description="Confirmation of target ownership or explicit scanning rights.")
    valid_from: datetime = Field(..., description="Start of authorization window.")
    valid_until: datetime = Field(..., description="End of authorization window.")
    target_domains: List[str] = Field(..., description="List of authorized hostnames/domains.")

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator("authorized_by")
    @classmethod
    def validate_authorized_by(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Authorized by contact name cannot be empty.")
        return v

    @field_validator("target_domains")
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Target domains list cannot be empty.")
        cleaned_domains = []
        for domain in v:
            domain = domain.strip().lower()
            if not is_valid_domain(domain):
                raise ValueError(f"Invalid domain format: '{domain}'. Must be a pure hostname/domain (e.g. 'example.com').")
            cleaned_domains.append(domain)
        return cleaned_domains

    @model_validator(mode="after")
    def validate_time_window(self) -> "AuthorizationRecord":
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be strictly after valid_from")
        return self


class ScanPolicy(BaseModel):
    authorization: AuthorizationRecord = Field(..., description="The referenced authorization record.")
    target_domains: List[str] = Field(..., description="Hostnames to scan.")
    allowed_url_prefixes: List[str] = Field(..., description="Absolute URL prefixes permitted for scanning.")
    max_depth: int = Field(default=3, ge=1, le=5, description="Max recursion depth of the web crawler.")
    requests_per_minute: int = Field(default=60, ge=1, le=120, description="Rate limiting budget.")
    total_request_budget: int = Field(default=500, ge=1, le=1000, description="Maximum total requests allowed.")
    max_duration_seconds: int = Field(default=1800, ge=1, le=3600, description="Maximum duration of the scan job.")
    scan_mode: Literal["passive"] = Field(default="passive", description="Scan execution mode (must be passive).")
    allowed_http_methods: List[str] = Field(default_factory=lambda: ["GET", "HEAD"], description="HTTP methods allowed.")

    @field_validator("target_domains")
    @classmethod
    def validate_target_domains(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Target domains list cannot be empty.")
        cleaned = []
        for domain in v:
            domain = domain.strip().lower()
            if not is_valid_domain(domain):
                raise ValueError(f"Invalid target domain format: '{domain}'. Must be a pure hostname/domain.")
            cleaned.append(domain)
        return cleaned

    @field_validator("allowed_url_prefixes")
    @classmethod
    def validate_prefixes(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Allowed URL prefixes list cannot be empty.")
        cleaned = []
        for prefix in v:
            prefix = prefix.strip()
            parsed = urlparse(prefix)
            if not parsed.scheme or parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid prefix scheme in '{prefix}': must be http or https.")
            if not parsed.netloc:
                raise ValueError(f"Invalid prefix in '{prefix}': missing domain/hostname.")
            cleaned.append(prefix)
        return cleaned

    @field_validator("allowed_http_methods")
    @classmethod
    def validate_http_methods(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Allowed HTTP methods list cannot be empty.")
        allowed_set = {"GET", "HEAD"}
        for method in v:
            method_upper = method.upper().strip()
            if method_upper not in allowed_set:
                raise ValueError(f"HTTP method '{method}' is not allowed in passive mode. Only GET and HEAD are permitted.")
        return [m.upper().strip() for m in v]

    @model_validator(mode="after")
    def validate_policy_against_authorization(self) -> "ScanPolicy":
        auth = self.authorization
        
        # 1. Enforce that policy target_domains are a subset of authorization target_domains
        for target_domain in self.target_domains:
            # check if target_domain is a subdomain or equal to any authorized domain
            authorized = False
            for auth_domain in auth.target_domains:
                if is_subdomain_or_equal(target_domain, auth_domain):
                    authorized = True
                    break
            if not authorized:
                raise ValueError(f"Target domain '{target_domain}' is not authorized by the provided AuthorizationRecord.")

        # 2. Enforce that allowed_url_prefixes belong to one of the target_domains
        for prefix in self.allowed_url_prefixes:
            parsed = urlparse(prefix)
            # parsed.netloc can contain a port (e.g. hostname:port), extract hostname
            prefix_host = parsed.hostname
            if not prefix_host:
                raise ValueError(f"Unable to extract hostname from prefix '{prefix}'")
            prefix_host = prefix_host.lower().strip()

            scoped = False
            for target_domain in self.target_domains:
                # Strip port from target_domain if present for matching (target_domain can be host:port)
                target_host = target_domain
                if ":" in target_domain:
                    target_host = target_domain.split(":")[0]
                
                if is_subdomain_or_equal(prefix_host, target_host):
                    scoped = True
                    break
            if not scoped:
                raise ValueError(f"URL prefix '{prefix}' does not match any of the policy target_domains: {self.target_domains}")

        return self
