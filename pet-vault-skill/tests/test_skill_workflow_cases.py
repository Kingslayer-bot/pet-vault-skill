"""Tests that read and validate skill_workflow_cases.yaml."""
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
class TestSkillWorkflowCasesExist(unittest.TestCase):
    def test_file_exists(self):
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_cases_have_required_fields(self):
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreater(len(cases), 0)
        for case in cases:
            self.assertIn("id", case)
            self.assertIn("input", case)
            self.assertIn("expected", case)
            self.assertIn("route", case["expected"])


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestSkillWorkflowRouteBehavior(unittest.TestCase):
    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_emergency_cases_route_to_emergency(self):
        from petvault_dispatch import dispatch
        cases = self._load_cases()
        for case in cases:
            if case["expected"]["route"] == "emergency":
                with self.subTest(case_id=case["id"]):
                    result = dispatch(case["input"]["request_text"])
                    self.assertEqual(result, "emergency")

    def test_forbidden_cases_route_to_forbidden(self):
        from petvault_dispatch import dispatch
        cases = self._load_cases()
        for case in cases:
            if case["expected"]["route"] == "forbidden":
                with self.subTest(case_id=case["id"]):
                    result = dispatch(case["input"]["request_text"])
                    self.assertEqual(result, "forbidden")

    def test_knowledge_cases_route_to_knowledge(self):
        from petvault_dispatch import dispatch
        cases = self._load_cases()
        for case in cases:
            if case["expected"]["route"] == "knowledge_query":
                with self.subTest(case_id=case["id"]):
                    result = dispatch(case["input"]["request_text"])
                    self.assertEqual(result, "knowledge_query")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestSkillWorkflowOutputSafety(unittest.TestCase):
    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_must_not_include_terms_are_not_empty(self):
        """Each case should have at least one must_not_include term."""
        cases = self._load_cases()
        for case in cases:
            with self.subTest(case_id=case["id"]):
                must_not = case["expected"].get("user_visible_must_not_include", [])
                self.assertGreater(len(must_not), 0, f"Case '{case['id']}' should have must_not_include terms")


if __name__ == "__main__":
    unittest.main()
