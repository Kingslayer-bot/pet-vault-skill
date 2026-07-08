"""Tests that material_ops types align with routing and pdf_policy rules."""
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

from material_ops import MATERIAL_LABELS


# Canonical material type names from material_ops.py
CANONICAL_TYPES = {name for name, _labels in MATERIAL_LABELS}


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestMaterialRoutingAlignment(unittest.TestCase):
    """Verify routing.yaml and pdf_policy.yaml use canonical material type names."""

    def _load_routing(self) -> dict:
        path = SKILL / "kb" / "rules" / "routing.yaml"
        return _yaml.safe_load(path.read_text(encoding="utf-8"))

    def _load_pdf_policy(self) -> dict:
        path = SKILL / "kb" / "rules" / "pdf_policy.yaml"
        return _yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_routing_material_types_are_canonical(self):
        """Every material_type in routing.yaml must be a canonical type from material_ops."""
        routing = self._load_routing()
        for route_name, route_def in routing.items():
            triggers = route_def.get("triggers", {})
            for mt in triggers.get("material_types", []):
                self.assertIn(
                    mt, CANONICAL_TYPES,
                    f"routing.{route_name}.material_types contains '{mt}' "
                    f"which is not a canonical material_ops type. "
                    f"Canonical types: {sorted(CANONICAL_TYPES)}"
                )

    def test_pdf_policy_material_types_are_canonical(self):
        """Every material type in pdf_policy.yaml must be a canonical type from material_ops."""
        policy = self._load_pdf_policy()
        for mt in policy.get("default_pdf_required_for", []):
            self.assertIn(
                mt, CANONICAL_TYPES,
                f"pdf_policy.default_pdf_required_for contains '{mt}' "
                f"which is not a canonical material_ops type."
            )

    def test_bill_triggers_bill_report(self):
        """A classified 'bill' material should be able to trigger bill_report."""
        routing = self._load_routing()
        bill_types = routing["bill_report"]["triggers"]["material_types"]
        self.assertIn("bill", bill_types)
        self.assertIn("invoice", bill_types)

    def test_claim_document_triggers_insurance_precheck(self):
        """A classified 'claim_document' should trigger insurance_precheck."""
        routing = self._load_routing()
        insurance_types = routing["insurance_precheck"]["triggers"]["material_types"]
        self.assertIn("claim_document", insurance_types)

    def test_medical_report_triggers_timeline_update(self):
        """A classified 'medical_report' should trigger timeline_update."""
        routing = self._load_routing()
        timeline_types = routing["timeline_update"]["triggers"]["material_types"]
        self.assertIn("medical_report", timeline_types)

    def test_clinic_communication_triggers_timeline_update(self):
        """A classified 'clinic_communication' should trigger timeline_update."""
        routing = self._load_routing()
        timeline_types = routing["timeline_update"]["triggers"]["material_types"]
        self.assertIn("clinic_communication", timeline_types)

    def test_all_canonical_types_have_user_visible_label(self):
        """Every canonical material type should have a user-visible translation."""
        boundaries_path = SKILL / ".agents" / "prompt_boundaries.yaml"
        if not boundaries_path.exists():
            self.skipTest("prompt_boundaries.yaml not found")
        boundaries = _yaml.safe_load(boundaries_path.read_text(encoding="utf-8"))
        translations = boundaries.get("type_code_translations", {})
        for mt in CANONICAL_TYPES:
            self.assertIn(
                mt, translations,
                f"Canonical type '{mt}' has no user-visible label in prompt_boundaries.yaml"
            )

    def test_no_old_mismatched_names_in_routing(self):
        """Old mismatched names should NOT appear in routing material_types."""
        routing = self._load_routing()
        old_names = {"claim_form", "medical_record", "chat_record", "payment_record",
                     "rejection_letter", "imaging_report"}
        for route_name, route_def in routing.items():
            triggers = route_def.get("triggers", {})
            for mt in triggers.get("material_types", []):
                self.assertNotIn(
                    mt, old_names,
                    f"routing.{route_name} still uses old name '{mt}' — should use canonical name"
                )


if __name__ == "__main__":
    unittest.main()
