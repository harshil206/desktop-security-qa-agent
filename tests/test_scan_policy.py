import os
import sys
from datetime import datetime, timedelta
import unittest
from pydantic import ValidationError

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import AuthorizationRecord, ScanPolicy

class TestScanPolicyValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime.now()
        self.future = self.now + timedelta(hours=2)
        
        # Valid Authorization Data
        self.valid_auth_data = {
            "contact_email": "security@example.com",
            "authorized_by": "John Doe",
            "owner_confirmed": True,
            "valid_from": self.now,
            "valid_until": self.future,
            "target_domains": ["example.com", "myproject.org"]
        }
        
        # Valid Policy Data (using target domain subset & valid prefixes)
        self.valid_policy_data = {
            "target_domains": ["example.com"],
            "allowed_url_prefixes": ["https://example.com/api", "http://example.com/blog"],
            "max_depth": 3,
            "requests_per_minute": 60,
            "total_request_budget": 500,
            "max_duration_seconds": 1800,
            "scan_mode": "passive",
            "allowed_http_methods": ["GET", "HEAD"]
        }

    def test_valid_authorization_and_policy(self) -> None:
        """Should validate successfully with clean valid input."""
        auth = AuthorizationRecord(**self.valid_auth_data)
        self.assertEqual(auth.contact_email, "security@example.com")
        self.assertTrue(auth.owner_confirmed)
        
        policy = ScanPolicy(authorization=auth, **self.valid_policy_data)
        self.assertEqual(policy.scan_mode, "passive")
        self.assertEqual(policy.allowed_http_methods, ["GET", "HEAD"])

    def test_missing_or_unconfirmed_authorization(self) -> None:
        """Should reject when authorization is not owner_confirmed or missing."""
        # Unconfirmed authorization
        bad_auth = dict(self.valid_auth_data)
        bad_auth["owner_confirmed"] = False
        with self.assertRaises(ValidationError):
            AuthorizationRecord(**bad_auth)

        # Missing authorization object in policy instantiation
        with self.assertRaises(ValidationError):
            ScanPolicy(
                target_domains=self.valid_policy_data["target_domains"],
                allowed_url_prefixes=self.valid_policy_data["allowed_url_prefixes"]
            )

    def test_invalid_email_format(self) -> None:
        """Should reject invalid contact email formats."""
        bad_emails = ["not-an-email", "user@", "@domain.com", "user@domain", "user@.com"]
        for email in bad_emails:
            data = dict(self.valid_auth_data)
            data["contact_email"] = email
            with self.assertRaises(ValidationError, msg=f"Should have rejected email: {email}"):
                AuthorizationRecord(**data)

    def test_empty_or_whitespace_authorized_by(self) -> None:
        """Should reject empty names for authorized_by."""
        for name in ["", "   "]:
            data = dict(self.valid_auth_data)
            data["authorized_by"] = name
            with self.assertRaises(ValidationError):
                AuthorizationRecord(**data)

    def test_invalid_time_window(self) -> None:
        """Should reject when valid_until is before or equal to valid_from."""
        data = dict(self.valid_auth_data)
        data["valid_until"] = self.now - timedelta(minutes=1)
        with self.assertRaises(ValidationError):
            AuthorizationRecord(**data)

        data["valid_until"] = self.now
        with self.assertRaises(ValidationError):
            AuthorizationRecord(**data)

    def test_empty_scope_domains_or_prefixes(self) -> None:
        """Should reject empty list of target domains or allowed prefixes."""
        # Empty target domains in authorization
        auth_data = dict(self.valid_auth_data)
        auth_data["target_domains"] = []
        with self.assertRaises(ValidationError):
            AuthorizationRecord(**auth_data)

        # Empty target domains in policy
        auth = AuthorizationRecord(**self.valid_auth_data)
        policy_data = dict(self.valid_policy_data)
        policy_data["target_domains"] = []
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **policy_data)

        # Empty allowed URL prefixes in policy
        policy_data = dict(self.valid_policy_data)
        policy_data["allowed_url_prefixes"] = []
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **policy_data)

    def test_invalid_domain_format(self) -> None:
        """Should reject target domains containing protocols, paths, query params, etc."""
        bad_domains = [
            "http://example.com",
            "https://example.com/",
            "example.com/path",
            "example.com?query=1",
            "example.com#fragment",
            "example.com/",
            "invalid_domain_with_spaces.com ",
            "http://sub.example.com/page.html"
        ]
        for domain in bad_domains:
            data = dict(self.valid_auth_data)
            data["target_domains"] = [domain]
            with self.assertRaises(ValidationError, msg=f"Should have rejected domain: {domain}"):
                AuthorizationRecord(**data)

            # Test in ScanPolicy as well
            auth = AuthorizationRecord(**self.valid_auth_data)
            p_data = dict(self.valid_policy_data)
            p_data["target_domains"] = [domain]
            with self.assertRaises(ValidationError, msg=f"Should have rejected domain in policy: {domain}"):
                ScanPolicy(authorization=auth, **p_data)

    def test_scoping_policy_subset_of_authorization(self) -> None:
        """Should enforce target domains are a subset/subdomain of authorized domains."""
        auth = AuthorizationRecord(**self.valid_auth_data) # authorized: example.com, myproject.org
        
        # Exact match (authorized)
        p_data = dict(self.valid_policy_data)
        p_data["target_domains"] = ["example.com"]
        ScanPolicy(authorization=auth, **p_data)

        # Subdomain match (authorized)
        p_data = dict(self.valid_policy_data)
        p_data["target_domains"] = ["api.example.com"]
        p_data["allowed_url_prefixes"] = ["https://api.example.com/v1"]
        ScanPolicy(authorization=auth, **p_data)

        # Unrelated domain (not authorized)
        p_data = dict(self.valid_policy_data)
        p_data["target_domains"] = ["google.com"]
        p_data["allowed_url_prefixes"] = ["https://google.com/"]
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

    def test_allowed_url_prefixes_belong_to_target_domains(self) -> None:
        """Should reject URL prefixes that do not match policy target domains."""
        auth = AuthorizationRecord(**self.valid_auth_data)
        p_data = dict(self.valid_policy_data)
        p_data["target_domains"] = ["example.com"]
        
        # Valid subdomain prefix of target domain
        p_data["allowed_url_prefixes"] = ["https://sub.example.com/path"]
        ScanPolicy(authorization=auth, **p_data)
        
        # Invalid prefix belonging to another authorized but non-targeted domain
        p_data["allowed_url_prefixes"] = ["https://myproject.org/prefix"]
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

        # Invalid prefix belonging to a completely unauthorized domain
        p_data["allowed_url_prefixes"] = ["https://unauthorized.com/path"]
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

        # Invalid prefix scheme (ftp)
        p_data["allowed_url_prefixes"] = ["ftp://example.com/path"]
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

    def test_unsafe_budgets(self) -> None:
        """Should reject when crawl depth, rate limit, request budget, or duration limits are unsafe."""
        auth = AuthorizationRecord(**self.valid_auth_data)

        # Unsafe crawl depth (max 5)
        p_data = dict(self.valid_policy_data)
        p_data["max_depth"] = 6
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)
            
        p_data["max_depth"] = 0
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

        # Unsafe requests per minute (max 120)
        p_data = dict(self.valid_policy_data)
        p_data["requests_per_minute"] = 121
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)
            
        p_data["requests_per_minute"] = 0
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

        # Unsafe total request budget (max 1000)
        p_data = dict(self.valid_policy_data)
        p_data["total_request_budget"] = 1001
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)
            
        p_data["total_request_budget"] = 0
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

        # Unsafe scan duration (max 3600 seconds)
        p_data = dict(self.valid_policy_data)
        p_data["max_duration_seconds"] = 3601
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)
            
        p_data["max_duration_seconds"] = 0
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

    def test_unsafe_scan_modes(self) -> None:
        """Should reject any scan mode that is not 'passive'."""
        auth = AuthorizationRecord(**self.valid_auth_data)
        
        p_data = dict(self.valid_policy_data)
        p_data["scan_mode"] = "active"
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

        p_data["scan_mode"] = "semi-passive"
        with self.assertRaises(ValidationError):
            ScanPolicy(authorization=auth, **p_data)

    def test_unsafe_http_methods(self) -> None:
        """Should reject state-changing HTTP methods (POST, PUT, DELETE) in passive mode."""
        auth = AuthorizationRecord(**self.valid_auth_data)

        unsafe_methods_lists = [
            ["GET", "POST"],
            ["PUT"],
            ["DELETE"],
            ["GET", "HEAD", "PATCH"]
        ]
        
        for methods in unsafe_methods_lists:
            p_data = dict(self.valid_policy_data)
            p_data["allowed_http_methods"] = methods
            with self.assertRaises(ValidationError, msg=f"Should have rejected unsafe methods list: {methods}"):
                ScanPolicy(authorization=auth, **p_data)

if __name__ == "__main__":
    unittest.main()
