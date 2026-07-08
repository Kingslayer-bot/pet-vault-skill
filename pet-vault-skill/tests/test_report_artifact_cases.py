"""Tests for report_artifact_cases.yaml."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

EVAL_DIR = SKILL / ".agents" / "eval_cases"


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestReportArtifactCasesExist(unittest.TestCase):
    def test_file_exists(self):
        path = EVAL_DIR / "report_artifact_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_cases_have_required_fields(self):
        path = EVAL_DIR / "report_artifact_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreater(len(cases), 0)
        for case in cases:
            self.assertIn("id", case)
            self.assertIn("expected", case)


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestReportArtifactBehavior(unittest.TestCase):
    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "report_artifact_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_bill_report_has_reconstructed_section(self):
        """Bill report should have reconstructed section."""
        from petvault_core import build_report_markdown
        from report_sanitizer import sanitize_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_report_has_reconstructed_section")
        materials_index = {
            "materials": [{
                "id": "mat_001",
                "type": "bill",
                "pet_name": "Mimi",
                "source_file": "bill.txt",
                "text": case["input"]["materials"][0]["text"],
                "confidence": 0.9,
                "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        report = sanitize_report_markdown(report)
        for term in case["expected"]["must_contain"]:
            self.assertIn(term, report, f"Missing: {term}")

    def test_no_internal_leakage_in_report(self):
        """Report should not contain internal terms."""
        from petvault_core import build_report_markdown
        from report_sanitizer import sanitize_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "report_no_internal_leakage")
        materials_index = {
            "materials": [{
                "id": "mat_001",
                "type": "bill",
                "pet_name": "Mimi",
                "source_file": "bill.txt",
                "text": "血常规 120 元",
                "confidence": 0.9,
                "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        report = sanitize_report_markdown(report)
        for term in case["expected"]["must_not_contain"]:
            self.assertNotIn(term, report, f"Forbidden: {term}")


if __name__ == "__main__":
    unittest.main()
