import os
import sys
import json
from datetime import datetime
import unittest
from pydantic import ValidationError

# Ensure the project root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.contracts.schemas import (
    ScanStatus,
    Severity,
    Confidence,
    ArtifactType,
    EvidenceRef,
    Finding,
    Report
)

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "contracts", "fixtures"))

class TestContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_evidence_data = {
            "artifact_id": "ART-001",
            "artifact_type": ArtifactType.SCREENSHOT,
            "location_url": "https://example.com/login",
            "timestamp": datetime.now(),
            "snippet_or_description": "Screenshot of login page",
            "metadata": {"viewport": "1920x1080"}
        }

        self.valid_finding_data = {
            "finding_id": "FIND-001",
            "title": "Broken Asset Observed",
            "description": "Failed to load script asset",
            "category": "qa_broken_asset",
            "affected_asset": "https://example.com/js/app.js",
            "severity": Severity.LOW,
            "confidence": Confidence.CONFIRMED,
            "rule_id": "QA-ASSET-01",
            "rule_version": "1.0.0",
            "remediation": "Restore missing JS file",
            "evidence": [EvidenceRef(**self.valid_evidence_data)]
        }

    def test_fixture_json_loading(self) -> None:
        """Should successfully parse and validate JSON fixtures."""
        finding_file = os.path.join(FIXTURES_DIR, "finding_fixture.json")
        with open(finding_file, "r", encoding="utf-8") as f:
            finding_json = json.load(f)
        
        finding = Finding(**finding_json)
        self.assertEqual(finding.finding_id, "FIND-2026-001")
        self.assertEqual(len(finding.evidence), 1)
        self.assertEqual(finding.evidence[0].artifact_type, ArtifactType.RESPONSE_HEADER)

        report_file = os.path.join(FIXTURES_DIR, "report_fixture.json")
        with open(report_file, "r", encoding="utf-8") as f:
            report_json = json.load(f)

        report = Report(**report_json)
        self.assertEqual(report.report_id, "REP-2026-001")
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings_count_by_severity["medium"], 1)

    def test_finding_requires_at_least_one_evidence(self) -> None:
        """A finding without evidence MUST be strictly rejected by validation."""
        # Empty evidence list
        bad_finding = dict(self.valid_finding_data)
        bad_finding["evidence"] = []
        with self.assertRaises(ValidationError) as ctx:
            Finding(**bad_finding)
        self.assertIn("A finding cannot exist without at least one evidence reference", str(ctx.exception))

        # Missing evidence field
        bad_finding_no_field = dict(self.valid_finding_data)
        del bad_finding_no_field["evidence"]
        with self.assertRaises(ValidationError):
            Finding(**bad_finding_no_field)

    def test_evidence_ref_validation(self) -> None:
        """Should validate EvidenceRef fields and reject empty string fields."""
        ev = EvidenceRef(**self.valid_evidence_data)
        self.assertEqual(ev.artifact_id, "ART-001")
        self.assertEqual(ev.artifact_type, ArtifactType.SCREENSHOT)

        # Empty string artifact_id
        bad_ev = dict(self.valid_evidence_data)
        bad_ev["artifact_id"] = "   "
        with self.assertRaises(ValidationError):
            EvidenceRef(**bad_ev)

    def test_report_severity_count_auto_calculation(self) -> None:
        """Should automatically compute severity counts when creating a Report."""
        finding1 = Finding(**self.valid_finding_data)
        
        finding_high = dict(self.valid_finding_data)
        finding_high["finding_id"] = "FIND-002"
        finding_high["severity"] = Severity.HIGH
        finding2 = Finding(**finding_high)

        report = Report(
            report_id="REP-002",
            scan_id="SCAN-002",
            created_at=datetime.now(),
            policy_summary={"target": "example.com"},
            coverage_summary={"visited": 10},
            findings=[finding1, finding2]
        )
        self.assertEqual(report.findings_count_by_severity["low"], 1)
        self.assertEqual(report.findings_count_by_severity["high"], 1)
        self.assertEqual(report.findings_count_by_severity["critical"], 0)

    def test_enums_values(self) -> None:
        """Verify enum string representations match contract specifications."""
        self.assertEqual(ScanStatus.RUNNING.value, "running")
        self.assertEqual(Severity.CRITICAL.value, "critical")
        self.assertEqual(Confidence.CONFIRMED.value, "confirmed")
        self.assertEqual(ArtifactType.SCREENSHOT.value, "screenshot")

if __name__ == "__main__":
    unittest.main()
