"""Tests for travel_care KB coverage."""
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


class TestTravelCareKB(unittest.TestCase):
    """Verify travel_care KB articles exist and are properly structured."""

    def test_travel_articles_exist(self):
        travel_dir = SKILL / "kb" / "articles" / "travel"
        self.assertTrue(travel_dir.exists(), "kb/articles/travel/ directory missing")
        articles = list(travel_dir.glob("*.md"))
        self.assertGreaterEqual(len(articles), 3, "Need at least 3 travel articles")

    def test_travel_articles_have_valid_frontmatter(self):
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
        travel_dir = SKILL / "kb" / "articles" / "travel"
        for path in sorted(travel_dir.glob("*.md")):
            metadata, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
            with self.subTest(article=path.name):
                self.assertIn("id", metadata, f"Missing id in {path}")
                self.assertFalse(required - set(metadata), f"Missing fields in {path}")
                self.assertTrue(metadata["forbidden_outputs"], f"Empty forbidden_outputs in {path}")
                self.assertEqual("travel", metadata["domain"], f"Wrong domain in {path}")
                for source_id in metadata["sources"]:
                    self.assertIn(source_id, source_ids, f"Invalid source '{source_id}' in {path}")

    def test_travel_articles_have_no_dangerous_content(self):
        dangerous_terms = ["保证", "一定能", "肯定可以", "确诊", "诊断为"]
        travel_dir = SKILL / "kb" / "articles" / "travel"
        for path in sorted(travel_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for term in dangerous_terms:
                with self.subTest(article=path.name, term=term):
                    self.assertNotIn(term, text, f"Dangerous term '{term}' in {path.name}")

    def test_travel_sources_exist(self):
        sources_path = SKILL / "kb" / "sources.yaml"
        sources_text = sources_path.read_text(encoding="utf-8")
        self.assertIn("usda-aphis-pet-travel", sources_text)
        self.assertIn("cn-customs-pet-travel", sources_text)

    def test_travel_domain_in_ontology(self):
        ontology_path = SKILL / "kb" / "ontology.yaml"
        ontology_text = ontology_path.read_text(encoding="utf-8")
        self.assertIn("travel", ontology_text)


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestTravelCareEval(unittest.TestCase):
    """Verify travel_care eval cases load and are valid."""

    def test_travel_eval_cases_exist(self):
        path = SKILL / ".agents" / "eval_cases" / "travel_care_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_travel_eval_cases_have_ids(self):
        path = SKILL / ".agents" / "eval_cases" / "travel_care_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreaterEqual(len(cases), 3, "Need at least 3 travel eval cases")
        for case in cases:
            self.assertIn("id", case, f"Missing id in case: {case}")
            self.assertIn("input", case, f"Missing input in case: {case.get('id')}")


class TestTravelCareRetrieval(unittest.TestCase):
    """Verify travel queries can find travel articles."""

    def _query(self, query_text: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "query_knowledge_base.py"),
             query_text, "--limit", "3"],
            cwd=ROOT, text=True, capture_output=True, timeout=30, encoding="utf-8",
        )
        self.assertEqual(0, result.returncode, (result.stderr or "") + (result.stdout or ""))
        return json.loads(result.stdout or "{}")

    def test_travel_query_returns_travel_article(self):
        payload = self._query("带宠物坐飞机需要准备什么")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertIn("travel", domains, f"Expected travel domain, got: {domains}")

    def test_travel_health_certificate_query(self):
        payload = self._query("宠物健康证明怎么办")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertIn("travel", domains, f"Expected travel domain, got: {domains}")

    def test_travel_carrier_query(self):
        payload = self._query("航空箱有什么要求")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertIn("travel", domains, f"Expected travel domain, got: {domains}")


if __name__ == "__main__":
    unittest.main()
