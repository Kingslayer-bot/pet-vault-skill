"""Tests for product_fit / nutrition KB coverage."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parent
sys.path.insert(0, str(SKILL / "scripts"))

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

from query_knowledge_base import parse_frontmatter


class TestProductFitKB(unittest.TestCase):
    """Verify nutrition KB articles exist and are properly structured."""

    def test_nutrition_articles_exist(self):
        nutrition_dir = SKILL / "kb" / "articles" / "nutrition"
        self.assertTrue(nutrition_dir.exists(), "kb/articles/nutrition/ directory missing")
        articles = list(nutrition_dir.glob("*.md"))
        self.assertGreaterEqual(len(articles), 2, "Need at least 2 nutrition articles")

    def test_nutrition_articles_have_valid_frontmatter(self):
        sources_path = SKILL / "kb" / "sources.yaml"
        sources_text = sources_path.read_text(encoding="utf-8")
        source_ids = set()
        for line in sources_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- id:") or stripped.startswith("id:"):
                source_ids.add(stripped.split(":", 1)[1].strip())
        required = {
            "id", "title", "domain", "jurisdiction", "language", "species",
            "source_tier", "risk_level", "allowed_outputs", "forbidden_outputs",
            "sources", "last_reviewed", "expires_at",
        }
        nutrition_dir = SKILL / "kb" / "articles" / "nutrition"
        for path in sorted(nutrition_dir.glob("*.md")):
            metadata, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
            with self.subTest(article=path.name):
                self.assertIn("id", metadata, f"Missing id in {path}")
                self.assertFalse(required - set(metadata), f"Missing fields in {path}")
                self.assertTrue(metadata["forbidden_outputs"], f"Empty forbidden_outputs in {path}")
                self.assertEqual("nutrition", metadata["domain"], f"Wrong domain in {path}")
                for source_id in metadata["sources"]:
                    self.assertIn(source_id, source_ids, f"Invalid source '{source_id}' in {path}")

    def test_nutrition_articles_forbid_brand_recommendation(self):
        """Nutrition articles must explicitly forbid brand recommendations."""
        nutrition_dir = SKILL / "kb" / "articles" / "nutrition"
        for path in sorted(nutrition_dir.glob("*.md")):
            metadata, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
            with self.subTest(article=path.name):
                forbidden = metadata.get("forbidden_outputs", [])
                self.assertIn("recommend_brand", forbidden,
                              f"{path.name} should forbid brand recommendations")

    def test_nutrition_articles_have_no_dangerous_content(self):
        """Nutrition articles should not contain diagnosis or brand recommendations."""
        dangerous_terms = ["确诊", "诊断为", "推荐你买"]
        nutrition_dir = SKILL / "kb" / "articles" / "nutrition"
        for path in sorted(nutrition_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for term in dangerous_terms:
                with self.subTest(article=path.name, term=term):
                    self.assertNotIn(term, text, f"Dangerous term '{term}' in {path.name}")

    def test_nutrition_domain_in_ontology(self):
        ontology_path = SKILL / "kb" / "ontology.yaml"
        ontology_text = ontology_path.read_text(encoding="utf-8")
        self.assertIn("nutrition", ontology_text)


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestProductFitEval(unittest.TestCase):
    """Verify product_fit eval cases load and are valid."""

    def test_product_fit_eval_cases_exist(self):
        path = SKILL / ".agents" / "eval_cases" / "product_fit_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_product_fit_eval_cases_have_ids(self):
        path = SKILL / ".agents" / "eval_cases" / "product_fit_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreaterEqual(len(cases), 3, "Need at least 3 product_fit eval cases")
        for case in cases:
            self.assertIn("id", case, f"Missing id in case: {case}")
            self.assertIn("input", case, f"Missing input in case: {case.get('id')}")


class TestProductFitRetrieval(unittest.TestCase):
    """Verify product/nutrition queries can find nutrition articles."""

    def _query(self, query_text: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "query_knowledge_base.py"),
             query_text, "--limit", "3"],
            cwd=ROOT, text=True, capture_output=True, timeout=30, encoding="utf-8",
        )
        self.assertEqual(0, result.returncode, (result.stderr or "") + (result.stdout or ""))
        return json.loads(result.stdout or "{}")

    def test_senior_cat_nutrition_query(self):
        payload = self._query("老年猫饮食需要注意什么")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertTrue(
            "nutrition" in domains or "medical" in domains,
            f"Expected nutrition or medical domain, got: {domains}"
        )

    def test_prescription_diet_query(self):
        payload = self._query("处方粮是什么")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertTrue(
            "nutrition" in domains or "medical" in domains,
            f"Expected nutrition or medical domain, got: {domains}"
        )


if __name__ == "__main__":
    unittest.main()
