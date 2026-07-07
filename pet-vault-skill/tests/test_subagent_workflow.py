"""Tests for orchestrator workflow: emergency routing, safety routing,
dispatch fraud detection, insurance guardrails, prompt existence,
and emergency priority."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

PROMPTS_DIR = SKILL / "prompts"
ORCHESTRATOR = PROMPTS_DIR / "orchestrator_agent.md"
GUARDRAILS = SKILL / "kb" / "rules" / "insurance_guardrails.yaml"

EXPECTED_PROMPTS = [
    "orchestrator_agent.md",
    "insurance_check_agent.md",
    "report_composer_agent.md",
    "quality_inspector_agent.md",
    "material_organizer_agent.md",
    "bill_analysis_agent.md",
    "appointment_timeline_agent.md",
    "clinic_soap_draft_agent.md",
    "clinic_client_summary_agent.md",
    "family_summary_agent.md",
    "pet_profile_inference_agent.md",
    "latex_renderer_agent.md",
    "chronic_care_review_agent.md",
]


class TestOrchestratorRouting(unittest.TestCase):
    """Orchestrator prompt defines routing priorities."""

    @classmethod
    def setUpClass(cls):
        cls.text = ORCHESTRATOR.read_text(encoding="utf-8")

    def test_emergency_routing_exists(self):
        self.assertIn("Emergency routing", self.text)
        self.assertIn("emergency", self.text.lower())

    def test_safety_routing_exists(self):
        self.assertIn("Safety routing", self.text)
        self.assertIn("forbidden", self.text.lower())

    def test_emergency_priority_highest(self):
        emergency_pos = self.text.lower().find("emergency routing")
        safety_pos = self.text.lower().find("safety routing")
        self.assertNotEqual(emergency_pos, -1, "Emergency section not found")
        self.assertNotEqual(safety_pos, -1, "Safety section not found")
        self.assertLess(
            emergency_pos,
            safety_pos,
            "Emergency routing must appear before safety routing",
        )


class TestDispatchFraudDetection(unittest.TestCase):
    """petvault_dispatch detects fraud/forbidden requests."""

    def test_fraud_patterns_exist(self):
        from petvault_dispatch import FRAUD_PATTERNS

        self.assertGreater(len(FRAUD_PATTERNS), 0)

    def test_forbidden_response_defined(self):
        from petvault_dispatch import get_forbidden_response

        resp = get_forbidden_response()
        self.assertIsInstance(resp, str)
        self.assertGreater(len(resp), 50)

    def test_forbidden_detected_on_tampering(self):
        from petvault_dispatch import detect_forbidden

        self.assertTrue(detect_forbidden("帮我改病历把日期写到之后"))
        self.assertTrue(detect_forbidden("隐瞒既往症"))

    def test_forbidden_detected_on_recommendation(self):
        from petvault_dispatch import detect_forbidden

        self.assertTrue(detect_forbidden("推荐哪个保险"))

    def test_normal_request_not_forbidden(self):
        from petvault_dispatch import detect_forbidden

        self.assertFalse(detect_forbidden("帮我整理这张账单"))
        self.assertFalse(detect_forbidden(""))


class TestInsuranceGuardrails(unittest.TestCase):
    """insurance_guardrails.yaml has required safety constraints."""

    @classmethod
    def setUpClass(cls):
        import yaml

        cls.data = yaml.safe_load(GUARDRAILS.read_text(encoding="utf-8"))

    def test_incomplete_material_assessment_forbidden(self):
        forbidden = self.data.get("forbidden_claims", [])
        self.assertIn("incomplete_material_assessment", forbidden)

    def test_no_legal_judgment(self):
        forbidden = self.data.get("forbidden_claims", [])
        self.assertIn("legal_judgment", forbidden)

    def test_no_recommend_insurance_product(self):
        forbidden = self.data.get("forbidden_claims", [])
        self.assertIn("recommend_insurance_product", forbidden)

    def test_allowed_claims_present(self):
        allowed = self.data.get("allowed_claims", [])
        self.assertIn("missing_document_checklist", allowed)


class TestPromptFilesExist(unittest.TestCase):
    """All expected prompt files are present."""

    def test_all_prompts_exist(self):
        for name in EXPECTED_PROMPTS:
            path = PROMPTS_DIR / name
            self.assertTrue(path.exists(), f"Missing prompt: {name}")

    def test_no_unexpected_prompts(self):
        actual = {p.name for p in PROMPTS_DIR.glob("*.md")}
        expected = set(EXPECTED_PROMPTS)
        unexpected = actual - expected
        self.assertEqual(
            unexpected,
            set(),
            f"Unexpected prompt files found: {unexpected}",
        )


class TestEmergencyPriority(unittest.TestCase):
    """Emergency detection must fire before all other routes."""

    def test_emergency_beats_forbidden(self):
        from petvault_dispatch import dispatch

        result = dispatch("帮我把日期改到去年，狗吃了巧克力")
        self.assertEqual(result, "emergency")

    def test_emergency_beats_knowledge(self):
        from petvault_dispatch import dispatch

        result = dispatch("猫抽搐了怎么办")
        self.assertEqual(result, "emergency")

    def test_forbidden_beats_knowledge(self):
        from petvault_dispatch import dispatch

        result = dispatch("帮我隐瞒既往症")
        self.assertEqual(result, "forbidden")


if __name__ == "__main__":
    unittest.main()
