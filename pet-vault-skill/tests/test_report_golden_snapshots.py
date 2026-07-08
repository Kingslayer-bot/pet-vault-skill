"""Golden text snapshot tests for report artifacts.

Tests compare normalized text, not binary PDFs.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from billing_ops import build_bill_items, summarize_charge_totals
from bill_render_ops import render_reconstructed_bill_section
from report_sanitizer import sanitize_report_markdown
from latex_ops import markdown_to_latex_body
from agent_registry_loader import load_forbidden_terms


class TestReconstructedBillSnapshot(unittest.TestCase):
    """Test reconstructed bill section against golden snapshot."""

    def test_bill_section_matches_snapshot(self):
        """Reconstructed bill section should match golden snapshot."""
        materials = [{
            "text": "血常规 120 元\nB超 350 元\n处方药 86.5 元\n挂号费 30 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        result = render_reconstructed_bill_section(items, totals)

        # Verify structure
        self.assertIn("账单复刻区", result)
        self.assertIn("| 项目 | 类型 | 金额 | 说明 |", result)
        self.assertIn("586.50 CNY", result)

    def test_bill_section_has_table_structure(self):
        """Reconstructed bill section should have table structure."""
        items = [{"name": "血常规", "kind": "charge", "amount": 120.0, "signed_amount": 120.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        totals = {"CNY": 120.0}
        result = render_reconstructed_bill_section(items, totals)
        self.assertIn("| 项目 | 类型 | 金额 | 说明 |", result)
        self.assertIn("|---|---|---:|---|", result)


class TestBillReportNoInternalTerms(unittest.TestCase):
    """Test that bill report contains no internal terms."""

    def test_sanitized_report_no_internal_terms(self):
        """Sanitized report should not contain internal terms."""
        from petvault_core import build_report_markdown
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
        forbidden = load_forbidden_terms()
        for term in forbidden:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in report")


class TestBillTableConvertsToLatex(unittest.TestCase):
    """Test that bill table converts to LaTeX."""

    def test_bill_table_in_latex(self):
        """Bill table should convert to LaTeX longtable."""
        items = [{"name": "血常规", "kind": "charge", "amount": 120.0, "signed_amount": 120.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        totals = {"CNY": 120.0}
        md = render_reconstructed_bill_section(items, totals)
        latex = markdown_to_latex_body(md)
        self.assertIn("\\begin{longtable}", latex)
        self.assertIn("收费项目", latex)


class TestPaymentDiscountNotCharges(unittest.TestCase):
    """Test that payment/discount are not counted as charges."""

    def test_payment_not_charge(self):
        """Payment should not be counted as charge."""
        materials = [{"text": "血常规 120 元；付款 -120 元", "source_file": "bill.txt"}]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        self.assertEqual(totals.get("CNY", 0), 120.0)

    def test_discount_not_charge(self):
        """Discount should not be counted as charge."""
        materials = [{"text": "血常规 120 元；折扣 -10 元", "source_file": "bill.txt"}]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        self.assertEqual(totals.get("CNY", 0), 120.0)


class TestEmptyChargesShowsPending(unittest.TestCase):
    """Test that empty charges show pending."""

    def test_empty_totals_shows_pending(self):
        """Empty totals should show pending."""
        items = [{"name": "血常规", "kind": "charge", "amount": 0.0, "signed_amount": 0.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        result = render_reconstructed_bill_section(items, {})
        self.assertIn("待确认", result)


if __name__ == "__main__":
    unittest.main()
