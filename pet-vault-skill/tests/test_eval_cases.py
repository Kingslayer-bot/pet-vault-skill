"""Tests that read and validate .agents/eval_cases/*.yaml golden fixtures."""
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
class TestEvalCaseFilesExist(unittest.TestCase):
    """Verify eval case files exist and are valid YAML."""

    def test_internal_leakage_cases_exist(self):
        path = EVAL_DIR / "internal_leakage_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_pdf_render_cases_exist(self):
        path = EVAL_DIR / "pdf_render_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_billing_report_cases_exist(self):
        path = EVAL_DIR / "billing_report_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_emergency_routing_cases_exist(self):
        path = EVAL_DIR / "emergency_routing_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestEvalCaseSchema(unittest.TestCase):
    """Verify eval cases have required fields."""

    def _load_cases(self, filename: str) -> list[dict]:
        path = EVAL_DIR / filename
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_internal_leakage_cases_have_ids(self):
        cases = self._load_cases("internal_leakage_cases.yaml")
        for case in cases:
            self.assertIn("id", case, f"Missing id in case: {case}")
            self.assertIn("must_not_contain", case, f"Missing must_not_contain in case: {case.get('id')}")

    def test_pdf_render_cases_have_ids(self):
        cases = self._load_cases("pdf_render_cases.yaml")
        for case in cases:
            self.assertIn("id", case)
            self.assertIn("must_contain_latex", case)

    def test_billing_report_cases_have_ids(self):
        cases = self._load_cases("billing_report_cases.yaml")
        for case in cases:
            self.assertIn("id", case)


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestInternalLeakageEvalCases(unittest.TestCase):
    """Run internal leakage eval cases against sanitizer."""

    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "internal_leakage_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_all_cases_pass_sanitizer(self):
        from report_sanitizer import sanitize_report_markdown
        cases = self._load_cases()
        for case in cases:
            with self.subTest(case_id=case.get("id")):
                input_md = case.get("input", "")
                result = sanitize_report_markdown(input_md)
                for term in case.get("must_not_contain", []):
                    self.assertNotIn(term, result, f"Case '{case.get('id')}': '{term}' found in sanitized output")
                for term in case.get("must_contain", []):
                    self.assertIn(term, result, f"Case '{case.get('id')}': '{term}' not found in sanitized output")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestTravelCareEvalCasesExist(unittest.TestCase):
    """Verify travel_care eval cases exist."""

    def test_travel_care_cases_exist(self):
        path = EVAL_DIR / "travel_care_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_travel_care_cases_have_ids(self):
        path = EVAL_DIR / "travel_care_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        for case in cases:
            self.assertIn("id", case, f"Missing id in case: {case}")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestProductFitEvalCasesExist(unittest.TestCase):
    """Verify product_fit eval cases exist."""

    def test_product_fit_cases_exist(self):
        path = EVAL_DIR / "product_fit_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_product_fit_cases_have_ids(self):
        path = EVAL_DIR / "product_fit_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        for case in cases:
            self.assertIn("id", case, f"Missing id in case: {case}")


class TestPdfRenderEvalCases(unittest.TestCase):
    """Run PDF render eval cases against latex_ops."""

    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "pdf_render_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_all_cases_pass_latex(self):
        from latex_ops import markdown_to_latex_body
        cases = self._load_cases()
        for case in cases:
            with self.subTest(case_id=case.get("id")):
                input_md = case.get("input", "")
                result = markdown_to_latex_body(input_md)
                for term in case.get("must_contain_latex", []):
                    self.assertIn(term, result, f"Case '{case.get('id')}': '{term}' not found in LaTeX output")


if __name__ == "__main__":
    unittest.main()
