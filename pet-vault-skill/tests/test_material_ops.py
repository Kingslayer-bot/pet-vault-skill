"""Tests for material_ops module."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from material_ops import (
    classify_material,
    extract_date,
    extract_pet_name,
    extract_clinic,
    normalize_markdown,
    read_source_text,
)


class TestClassifyMaterial(unittest.TestCase):
    def test_invoice_text(self):
        """Invoice-like text should classify as invoice or bill."""
        text = "Invoice #12345\nBalance due: $500.00"
        type_, conf = classify_material("invoice.txt", text)
        self.assertIn(type_, {"invoice", "bill"})
        self.assertGreater(conf, 0.5)

    def test_insurance_text(self):
        """Insurance-like text should classify as insurance_policy."""
        text = "Policy number: ABC123\nCoverage: $10,000\nDeductible: $500"
        type_, conf = classify_material("policy.txt", text)
        self.assertEqual(type_, "insurance_policy")
        self.assertGreater(conf, 0.5)

    def test_lab_report_text(self):
        """Lab report text should classify as lab_report."""
        text = "血常规\nALT 132 高\nCREA 1.9 高"
        type_, conf = classify_material("lab_results.txt", text)
        self.assertEqual(type_, "lab_report")
        self.assertGreater(conf, 0.5)

    def test_explicit_type_hint(self):
        """Explicit type hint should override classification."""
        text = "Material type: invoice\nPet: Mimi"
        type_, conf = classify_material("unknown.txt", text)
        self.assertEqual(type_, "invoice")
        self.assertGreater(conf, 0.9)

    def test_negated_policy_not_classified_as_policy(self):
        """Text with 'policy not visible' should not classify as insurance_policy."""
        text = "Invoice\nInsurance policy terms are not visible on this invoice."
        type_, conf = classify_material("invoice.txt", text)
        self.assertNotEqual(type_, "insurance_policy")


class TestExtractDate(unittest.TestCase):
    def test_date_from_text(self):
        """Should extract date from text."""
        date = extract_date("Date: 2026-07-05\nPet: Mimi")
        self.assertEqual(date, "2026-07-05")

    def test_date_from_filename(self):
        """Should extract date from filename."""
        date = extract_date("", "2026-07-05_invoice.txt")
        self.assertEqual(date, "2026-07-05")

    def test_no_date_returns_none(self):
        """Should return None if no date found."""
        date = extract_date("No date here")
        self.assertIsNone(date)


class TestExtractPetName(unittest.TestCase):
    def test_pet_name_from_text(self):
        """Should extract pet name from text."""
        name = extract_pet_name("宠物：Mimi\n日期：2026-07-05")
        self.assertEqual(name, "Mimi")

    def test_pet_name_with_fallback(self):
        """Should use fallback if no pet name found."""
        name = extract_pet_name("没有宠物信息", fallback="Default")
        self.assertEqual(name, "Default")


class TestExtractClinic(unittest.TestCase):
    def test_clinic_from_text(self):
        """Should extract clinic name from text."""
        clinic = extract_clinic("医院：星河动物医院\n日期：2026-07-05")
        self.assertEqual(clinic, "星河动物医院")

    def test_no_clinic_returns_none(self):
        """Should return None if no clinic found."""
        clinic = extract_clinic("没有医院信息")
        self.assertIsNone(clinic)


class TestNormalizeMarkdown(unittest.TestCase):
    def test_normalizes_line_endings(self):
        """Should normalize line endings."""
        text = "line1\r\nline2\rline3\n"
        result = normalize_markdown(text, "test.txt")
        self.assertIn("line1", result)
        self.assertIn("line2", result)
        self.assertIn("line3", result)

    def test_includes_source_name(self):
        """Should include source filename."""
        result = normalize_markdown("content", "invoice.txt")
        self.assertIn("invoice.txt", result)


class TestNoInternalLabels(unittest.TestCase):
    def test_classify_does_not_return_internal_labels(self):
        """Classification should not return internal labels visible to users."""
        text = "Invoice #12345"
        type_, _ = classify_material("invoice.txt", text)
        # Should return raw type code, not translated label
        self.assertIn(type_, {"invoice", "bill", "unknown"})


if __name__ == "__main__":
    unittest.main()
