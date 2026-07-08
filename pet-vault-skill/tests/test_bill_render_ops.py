"""Tests for bill_render_ops module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from bill_render_ops import (
    render_reconstructed_bill_section,
    render_bill_summary_text,
    KIND_LABELS,
)
from billing_ops import build_bill_items, summarize_charge_totals


class TestRenderReconstructedBillSection(unittest.TestCase):
    def test_contains_markdown_table(self):
        """Output should contain a Markdown table."""
        items = [{"name": "血常规", "kind": "charge", "amount": 120.0, "signed_amount": 120.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        totals = {"CNY": 120.0}
        result = render_reconstructed_bill_section(items, totals)
        self.assertIn("| 项目 | 类型 | 金额 | 说明 |", result)
        self.assertIn("|---|---|---:|---|", result)

    def test_charge_label_is_chinese(self):
        """Charge items should have Chinese labels."""
        items = [{"name": "血常规", "kind": "charge", "amount": 120.0, "signed_amount": 120.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        totals = {"CNY": 120.0}
        result = render_reconstructed_bill_section(items, totals)
        self.assertIn("收费项目", result)

    def test_payment_label_is_chinese(self):
        """Payment items should have Chinese labels."""
        items = [{"name": "付款", "kind": "payment", "amount": 120.0, "signed_amount": -120.0, "currency": "CNY", "category": "付款", "source_file": "bill.txt"}]
        totals = {}
        result = render_reconstructed_bill_section(items, totals)
        self.assertIn("已支付", result)

    def test_discount_label_is_chinese(self):
        """Discount items should have Chinese labels."""
        items = [{"name": "折扣", "kind": "discount", "amount": 10.0, "signed_amount": -10.0, "currency": "CNY", "category": "折扣", "source_file": "bill.txt"}]
        totals = {}
        result = render_reconstructed_bill_section(items, totals)
        self.assertIn("折扣/减免", result)

    def test_payment_not_counted_as_charge(self):
        """Payment should not be counted as charge in totals."""
        materials = [{"text": "血常规 120 元；付款 -120 元", "source_file": "bill.txt"}]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        self.assertEqual(totals.get("CNY", 0), 120.0)

    def test_empty_items_shows_pending(self):
        """Empty items should show pending message."""
        result = render_reconstructed_bill_section([], {})
        self.assertIn("未提取到账单明细", result)

    def test_empty_totals_shows_pending(self):
        """Empty totals should show pending message."""
        items = [{"name": "血常规", "kind": "charge", "amount": 0.0, "signed_amount": 0.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        result = render_reconstructed_bill_section(items, {})
        self.assertIn("待确认", result)

    def test_no_internal_terms_in_output(self):
        """Output should not contain internal terms."""
        from agent_registry_loader import load_forbidden_terms
        forbidden = load_forbidden_terms()
        items = [{"name": "血常规", "kind": "charge", "amount": 120.0, "signed_amount": 120.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        totals = {"CNY": 120.0}
        result = render_reconstructed_bill_section(items, totals)
        for term in forbidden:
            self.assertNotIn(term, result, f"Forbidden term '{term}' found in output")

    def test_table_converts_to_latex(self):
        """Markdown table should convert to LaTeX."""
        from latex_ops import markdown_to_latex_body
        items = [{"name": "血常规", "kind": "charge", "amount": 120.0, "signed_amount": 120.0, "currency": "CNY", "category": "检查", "source_file": "bill.txt"}]
        totals = {"CNY": 120.0}
        md = render_reconstructed_bill_section(items, totals)
        latex = markdown_to_latex_body(md)
        self.assertIn("\\begin{longtable}", latex)


class TestRenderBillSummaryText(unittest.TestCase):
    def test_empty_items(self):
        """Empty items should return pending message."""
        result = render_bill_summary_text([], {})
        self.assertIn("未提取到", result)

    def test_normal_items(self):
        """Normal items should return summary."""
        items = [
            {"kind": "charge", "amount": 120.0, "currency": "CNY"},
            {"kind": "charge", "amount": 350.0, "currency": "CNY"},
        ]
        totals = {"CNY": 470.0}
        result = render_bill_summary_text(items, totals)
        self.assertIn("2 个收费项目", result)
        self.assertIn("470.00 CNY", result)


if __name__ == "__main__":
    unittest.main()
