"""Tests for KB retrieval quality — verify queries return expected articles."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parent


class TestKBRetrievalQuality(unittest.TestCase):
    """Verify knowledge base queries return correct and relevant results."""

    def _query(self, query_text: str, limit: int = 3) -> dict:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "query_knowledge_base.py"),
             query_text, "--limit", str(limit)],
            cwd=ROOT, text=True, capture_output=True, timeout=30, encoding="utf-8",
        )
        self.assertEqual(0, result.returncode, (result.stderr or "") + (result.stdout or ""))
        return json.loads(result.stdout or "{}")

    def _assert_query_matches_domain(self, query: str, expected_domain: str):
        payload = self._query(query)
        matches = payload.get("matches", [])
        self.assertGreaterEqual(len(matches), 1, f"No matches for: {query}")
        domains = [m["domain"] for m in matches]
        self.assertIn(expected_domain, domains,
                      f"Query '{query}': expected domain '{expected_domain}', got {domains}")

    def _assert_query_matches_any_domain(self, query: str, expected_domains: list[str]):
        payload = self._query(query)
        matches = payload.get("matches", [])
        self.assertGreaterEqual(len(matches), 1, f"No matches for: {query}")
        domains = [m["domain"] for m in matches]
        self.assertTrue(
            any(d in expected_domains for d in domains),
            f"Query '{query}': expected one of {expected_domains}, got {domains}"
        )

    # Billing queries
    def test_exam_fee_query(self):
        self._assert_query_matches_domain("为什么账单里有 exam fee", "billing")

    def test_vaccine_billing_query(self):
        self._assert_query_matches_domain("疫苗费用为什么会出现在账单里", "billing")

    def test_lab_work_query(self):
        self._assert_query_matches_domain("宠物账单里的 lab work 是什么", "billing")

    # Insurance queries
    def test_insurance_guarantee_query(self):
        self._assert_query_matches_any_domain("保险是不是一定能理赔", ["insurance", "jurisdiction"])

    def test_claim_materials_query(self):
        self._assert_query_matches_domain("理赔需要哪些材料", "insurance")

    # Emergency queries
    def test_breathing_difficulty_query(self):
        self._assert_query_matches_domain("宠物呼吸困难怎么办", "safety")

    def test_chocolate_query(self):
        self._assert_query_matches_domain("狗吃了巧克力怎么办", "safety")

    # Medical queries
    def test_lab_report_query(self):
        self._assert_query_matches_any_domain("化验报告里的 ALT 是什么", ["medical"])

    # Travel queries
    def test_travel_flight_query(self):
        self._assert_query_matches_domain("带宠物坐飞机需要什么", "travel")

    def test_travel_health_certificate_query(self):
        self._assert_query_matches_domain("宠物健康证明怎么办", "travel")

    # Product/nutrition queries
    def test_senior_cat_diet_query(self):
        self._assert_query_matches_any_domain("老年猫饮食需要注意什么", ["nutrition", "medical"])

    def test_prescription_diet_query(self):
        self._assert_query_matches_any_domain("处方粮是什么意思", ["nutrition", "medical"])


if __name__ == "__main__":
    unittest.main()
