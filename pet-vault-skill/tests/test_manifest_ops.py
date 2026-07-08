"""Tests for manifest_ops module."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from manifest_ops import (
    INTERNAL_TYPE_MAP,
    report_id_for,
    build_internal_manifest,
    build_user_manifest,
    _translate_type_label,
)


class TestTranslateTypeLabel(unittest.TestCase):
    def test_known_types(self):
        self.assertEqual(_translate_type_label("invoice"), "发票/收据")
        self.assertEqual(_translate_type_label("bill"), "账单/费用明细")
        self.assertEqual(_translate_type_label("insurance_policy"), "保险保单")
        self.assertEqual(_translate_type_label("lab_report"), "化验报告")

    def test_unknown_type_passthrough(self):
        self.assertEqual(_translate_type_label("something_new"), "something_new")


class TestReportIdFor(unittest.TestCase):
    def test_deterministic(self):
        p = Path("/tmp/out")
        id1 = report_id_for("bill_explain", "Mimi", p)
        id2 = report_id_for("bill_explain", "Mimi", p)
        self.assertEqual(id1, id2)

    def test_different_for_different_inputs(self):
        p = Path("/tmp/out")
        id1 = report_id_for("bill_explain", "Mimi", p)
        id2 = report_id_for("claim_check", "Mimi", p)
        self.assertNotEqual(id1, id2)


class TestBuildUserManifest(unittest.TestCase):
    def test_no_routing_field(self):
        internal = {
            "id": "test123",
            "pet_name": "Mimi",
            "report_type": "bill_explain",
            "created_at": "2026-07-08",
            "pdf_status": "compiled",
            "pdf_policy": "attempt",
            "routing": {"reason": "request_mentions_billing"},
            "materials": [{"source_file": "bill.txt", "type": "bill", "date": "2026-01-01"}],
            "outputs": {},
            "warnings": [],
        }
        user = build_user_manifest(internal)
        self.assertNotIn("routing", user)
        self.assertNotIn("pdf_policy", user)

    def test_materials_have_translated_labels(self):
        internal = {
            "id": "test",
            "pet_name": "Mimi",
            "report_type": "bill_explain",
            "created_at": "2026-07-08",
            "pdf_status": "compiled",
            "pdf_policy": "attempt",
            "routing": {},
            "materials": [
                {"source_file": "bill.txt", "type": "insurance_policy", "date": "2026-01-01"},
                {"source_file": "lab.txt", "type": "lab_report"},
            ],
            "outputs": {},
            "warnings": [],
        }
        user = build_user_manifest(internal)
        labels = [m["type_label"] for m in user["materials"]]
        self.assertIn("保险保单", labels)
        self.assertIn("化验报告", labels)
        self.assertNotIn("insurance_policy", str(user))
        self.assertNotIn("lab_report", str(user))

    def test_preserves_required_fields(self):
        internal = {
            "id": "abc",
            "pet_name": "Oreo",
            "report_type": "claim_check",
            "created_at": "2026-07-08",
            "pdf_status": "compiled",
            "materials": [],
            "outputs": {"report_md": "/path"},
            "warnings": ["test warning"],
        }
        user = build_user_manifest(internal)
        for field in ["id", "pet_name", "report_type", "created_at", "pdf_status", "materials", "outputs", "warnings"]:
            self.assertIn(field, user)


if __name__ == "__main__":
    unittest.main()
