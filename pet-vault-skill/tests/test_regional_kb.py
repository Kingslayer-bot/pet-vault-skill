"""Tests for HK/SG/JP regional KB coverage."""
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


class TestRegionalArticlesExist(unittest.TestCase):
    """Verify regional articles exist for HK, SG, JP."""

    def test_hk_articles_exist(self):
        self.assertTrue((SKILL / "kb" / "articles" / "jurisdiction" / "hk-vet-records.md").exists())
        self.assertTrue((SKILL / "kb" / "articles" / "billing" / "billing-line-items-hk.md").exists())
        self.assertTrue((SKILL / "kb" / "articles" / "insurance" / "insurance-terms-hk.md").exists())

    def test_sg_articles_exist(self):
        self.assertTrue((SKILL / "kb" / "articles" / "jurisdiction" / "sg-vet-records.md").exists())
        self.assertTrue((SKILL / "kb" / "articles" / "billing" / "billing-line-items-sg.md").exists())
        self.assertTrue((SKILL / "kb" / "articles" / "insurance" / "insurance-terms-sg.md").exists())

    def test_jp_articles_exist(self):
        self.assertTrue((SKILL / "kb" / "articles" / "jurisdiction" / "jp-vet-records.md").exists())
        self.assertTrue((SKILL / "kb" / "articles" / "billing" / "billing-line-items-jp.md").exists())
        self.assertTrue((SKILL / "kb" / "articles" / "insurance" / "insurance-terms-jp.md").exists())


class TestRegionalArticleStructure(unittest.TestCase):
    """Verify regional articles have valid frontmatter."""

    def _check_article(self, path: Path):
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
        metadata, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        self.assertIn("id", metadata, f"Missing id in {path}")
        self.assertFalse(required - set(metadata), f"Missing fields in {path}")
        self.assertTrue(metadata["forbidden_outputs"], f"Empty forbidden_outputs in {path}")
        for source_id in metadata["sources"]:
            self.assertIn(source_id, source_ids, f"Invalid source '{source_id}' in {path}")

    def test_hk_jurisdiction_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "jurisdiction" / "hk-vet-records.md")

    def test_sg_jurisdiction_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "jurisdiction" / "sg-vet-records.md")

    def test_jp_jurisdiction_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "jurisdiction" / "jp-vet-records.md")

    def test_hk_billing_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "billing" / "billing-line-items-hk.md")

    def test_sg_billing_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "billing" / "billing-line-items-sg.md")

    def test_jp_billing_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "billing" / "billing-line-items-jp.md")

    def test_hk_insurance_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "insurance" / "insurance-terms-hk.md")

    def test_sg_insurance_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "insurance" / "insurance-terms-sg.md")

    def test_jp_insurance_structure(self):
        self._check_article(SKILL / "kb" / "articles" / "insurance" / "insurance-terms-jp.md")


class TestRegionalRetrieval(unittest.TestCase):
    """Verify regional queries can find regional articles."""

    def _query(self, query_text: str, limit: int = 3) -> dict:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "query_knowledge_base.py"),
             query_text, "--limit", str(limit)],
            cwd=ROOT, text=True, capture_output=True, timeout=30, encoding="utf-8",
        )
        self.assertEqual(0, result.returncode, (result.stderr or "") + (result.stdout or ""))
        return json.loads(result.stdout or "{}")

    def test_hk_billing_query(self):
        payload = self._query("香港兽医 consultation 是什么")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertTrue(any(d in ("billing", "jurisdiction") for d in domains))

    def test_sg_insurance_query(self):
        payload = self._query("新加坡保险条款等待期")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertTrue(any(d in ("insurance", "jurisdiction") for d in domains))

    def test_jp_billing_query(self):
        payload = self._query("日本领收书费用")
        domains = [m["domain"] for m in payload.get("matches", [])]
        self.assertTrue(any(d in ("billing", "jurisdiction") for d in domains))


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestRegionalEvalCases(unittest.TestCase):
    """Verify regional eval cases exist and are valid."""

    def test_regional_cases_exist(self):
        path = SKILL / ".agents" / "eval_cases" / "regional_cases.yaml"
        self.assertTrue(path.exists())

    def test_regional_cases_have_ids(self):
        path = SKILL / ".agents" / "eval_cases" / "regional_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreaterEqual(len(cases), 3)
        for case in cases:
            self.assertIn("id", case)


if __name__ == "__main__":
    unittest.main()
