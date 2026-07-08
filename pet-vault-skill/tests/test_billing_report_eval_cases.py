"""Behavior tests for billing_report_cases.yaml — verifies billing extraction and output safety."""
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
class TestBillingReportBehavior(unittest.TestCase):
    """Behavior tests for billing report cases."""

    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "billing_report_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_bill_explain_basic_has_required_sections(self):
        """Bill explanation report must contain required sections."""
        from petvault_core import build_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_basic")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        for term in case["must_contain"]:
            self.assertIn(term, report, f"Missing required section: {term}")

    def test_bill_explain_charges_are_counted(self):
        """Charge items must be counted in totals."""
        from billing_ops import build_bill_items, summarize_charge_totals
        materials = [{
            "text": "血常规 120 元；B超 350 元；处方药 86.5 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        self.assertGreater(totals.get("CNY", 0), 0, "Charges should be counted")

    def test_payments_not_counted_as_charges(self):
        """Payment items must not be counted as charges."""
        from billing_ops import build_bill_items, summarize_charge_totals
        materials = [{
            "text": "血常规 120 元；付款 -120 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        # Only the charge should be counted, not the payment
        self.assertEqual(totals.get("CNY", 0), 120.0)

    def test_empty_charges_return_pending(self):
        """Empty charge totals must return '待确认'."""
        from billing_ops import format_currency_totals
        result = format_currency_totals({})
        self.assertEqual(result, "待确认")

    def test_multi_currency_totals_are_deterministic(self):
        """Multi-currency totals must format deterministically."""
        from billing_ops import format_currency_totals
        result = format_currency_totals({"USD": 100.0, "CNY": 200.0})
        self.assertIn("100.00 USD", result)
        self.assertIn("200.00 CNY", result)

    def test_no_internal_leakage_in_report(self):
        """Generated report must not contain internal terms."""
        from petvault_core import build_report_markdown
        from report_sanitizer import sanitize_report_markdown
        from agent_registry_loader import load_forbidden_terms
        forbidden = load_forbidden_terms()
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "source_file": "bill.txt",
                    "text": "血常规 120 元",
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        report = sanitize_report_markdown(report)
        for term in forbidden:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in report")


if __name__ == "__main__":
    unittest.main()
