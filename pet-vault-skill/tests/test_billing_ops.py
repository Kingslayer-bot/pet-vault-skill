"""Tests for billing_ops module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from billing_ops import (
    parse_money_mentions,
    build_bill_items,
    summarize_charge_totals,
    format_currency_totals,
    format_money,
    normalize_currency,
    classify_money_kind,
)


class TestNormalizeCurrency(unittest.TestCase):
    def test_usd_variants(self):
        self.assertEqual(normalize_currency("$"), "USD")
        self.assertEqual(normalize_currency("US$"), "USD")
        self.assertEqual(normalize_currency("USD"), "USD")

    def test_cny_variants(self):
        self.assertEqual(normalize_currency("元"), "CNY")
        self.assertEqual(normalize_currency("RMB"), "CNY")
        self.assertEqual(normalize_currency("CNY"), "CNY")
        self.assertEqual(normalize_currency("¥"), "CNY")


class TestClassifyMoneyKind(unittest.TestCase):
    def test_charge(self):
        self.assertEqual(classify_money_kind("Exam $80.00", 80.0), "charge")

    def test_payment(self):
        self.assertEqual(classify_money_kind("Payment -$80.00", -80.0), "payment")
        self.assertEqual(classify_money_kind("CareCredit $80.00", 80.0), "payment")

    def test_discount(self):
        self.assertEqual(classify_money_kind("Discount ($100.00)", -100.0), "discount")

    def test_total(self):
        self.assertEqual(classify_money_kind("Total $500.00", 500.0), "total")


class TestParseMoneyMentions(unittest.TestCase):
    def test_basic_amount(self):
        mentions = parse_money_mentions("Exam $80.00")
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0]["amount"], 80.0)
        self.assertEqual(mentions[0]["currency"], "USD")

    def test_cny_amount(self):
        mentions = parse_money_mentions("血常规 120 元")
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0]["amount"], 120.0)
        self.assertEqual(mentions[0]["currency"], "CNY")

    def test_multiple_amounts(self):
        mentions = parse_money_mentions("Exam $80.00; X-Ray $333.00")
        self.assertEqual(len(mentions), 2)


class TestBuildBillItems(unittest.TestCase):
    def test_basic_items(self):
        materials = [{
            "text": "血常规 120 元；B超 350 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["category"], "检查")
        self.assertEqual(items[1]["category"], "检查")


class TestSummarizeChargeTotals(unittest.TestCase):
    def test_empty_items(self):
        totals = summarize_charge_totals([])
        self.assertEqual(totals, {})

    def test_charge_items(self):
        items = [
            {"kind": "charge", "amount": 100.0, "currency": "USD"},
            {"kind": "charge", "amount": 200.0, "currency": "USD"},
        ]
        totals = summarize_charge_totals(items)
        self.assertEqual(totals["USD"], 300.0)

    def test_payment_not_counted(self):
        items = [
            {"kind": "payment", "amount": 100.0, "currency": "USD"},
        ]
        totals = summarize_charge_totals(items)
        self.assertEqual(totals, {})


class TestFormatCurrencyTotals(unittest.TestCase):
    def test_empty_totals(self):
        self.assertEqual(format_currency_totals({}), "待确认")

    def test_zero_totals(self):
        self.assertEqual(format_currency_totals({"USD": 0.0}), "待确认")

    def test_normal_totals(self):
        result = format_currency_totals({"USD": 500.0})
        self.assertIn("500.00", result)
        self.assertIn("USD", result)


class TestNoInternalLabels(unittest.TestCase):
    def test_no_internal_labels_in_output(self):
        materials = [{
            "text": "Exam $80.00",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        for item in items:
            self.assertNotIn("insurance_policy", str(item))
            self.assertNotIn("lab_report", str(item))
            self.assertNotIn("dispatch", str(item))


if __name__ == "__main__":
    unittest.main()
