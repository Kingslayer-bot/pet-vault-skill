"""Tests for knowledge base structure: sources, ontology, article
subdirectories, rules, forbidden_outputs, and flat-article guard."""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[1]
KB = SKILL / "kb"
SOURCES = KB / "sources.yaml"
ONTOLOGY = KB / "ontology.yaml"
ARTICLES_DIR = KB / "articles"
RULES_DIR = KB / "rules"

EXPECTED_SUBDIRS = ["billing", "insurance", "jurisdiction", "medical", "safety"]

EXPECTED_RULES = [
    "billing_validation.yaml",
    "insurance_guardrails.yaml",
    "medical_safety.yaml",
    "pdf_policy.yaml",
    "privacy.yaml",
    "routing.yaml",
]


class TestCoreKbFiles(unittest.TestCase):
    """sources.yaml and ontology.yaml exist and are valid YAML."""

    def test_sources_yaml_exists(self):
        self.assertTrue(SOURCES.exists(), "kb/sources.yaml missing")

    def test_sources_yaml_valid(self):
        data = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
        self.assertIn("sources", data)
        self.assertGreater(len(data["sources"]), 0)

    def test_sources_have_required_fields(self):
        data = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
        required = {"id", "name", "url", "domains", "forbidden_use"}
        for src in data["sources"]:
            missing = required - set(src.keys())
            self.assertEqual(
                missing,
                set(),
                f"Source '{src.get('id', '?')}' missing fields: {missing}",
            )

    def test_ontology_yaml_exists(self):
        self.assertTrue(ONTOLOGY.exists(), "kb/ontology.yaml missing")

    def test_ontology_has_domains(self):
        data = yaml.safe_load(ONTOLOGY.read_text(encoding="utf-8"))
        self.assertIn("domains", data)
        self.assertGreater(len(data["domains"]), 0)


class TestArticleSubdirectories(unittest.TestCase):
    """Each expected article subdirectory exists and contains at least one article."""

    def test_five_subdirectories_exist(self):
        actual = [d.name for d in ARTICLES_DIR.iterdir() if d.is_dir()]
        for name in EXPECTED_SUBDIRS:
            self.assertIn(name, actual, f"Missing subdirectory: kb/articles/{name}")

    def test_each_subdirectory_has_articles(self):
        for name in EXPECTED_SUBDIRS:
            subdir = ARTICLES_DIR / name
            md_files = list(subdir.glob("*.md"))
            self.assertGreater(
                len(md_files),
                0,
                f"kb/articles/{name}/ has no .md articles",
            )


class TestRulesFiles(unittest.TestCase):
    """All 6 expected rules files exist."""

    def test_six_rules_files_exist(self):
        for name in EXPECTED_RULES:
            path = RULES_DIR / name
            self.assertTrue(path.exists(), f"Missing rules file: {name}")

    def test_no_unexpected_rules(self):
        actual = {f.name for f in RULES_DIR.glob("*.yaml")}
        expected = set(EXPECTED_RULES)
        unexpected = actual - expected
        self.assertEqual(
            unexpected,
            set(),
            f"Unexpected rules files found: {unexpected}",
        )


class TestHighRiskCardsForbiddenOutputs(unittest.TestCase):
    """Every article with a risk_level has a non-empty forbidden_outputs list."""

    def _load_articles_with_frontmatter(self):
        results = []
        for subdir in EXPECTED_SUBDIRS:
            for md_file in (ARTICLES_DIR / subdir).glob("*.md"):
                text = md_file.read_text(encoding="utf-8")
                if not text.startswith("---"):
                    continue
                end = text.find("---", 3)
                if end == -1:
                    continue
                frontmatter = yaml.safe_load(text[3:end])
                if frontmatter:
                    results.append((md_file, frontmatter))
        return results

    def test_high_risk_cards_have_forbidden_outputs(self):
        articles = self._load_articles_with_frontmatter()
        for md_file, meta in articles:
            risk = meta.get("risk_level", "")
            if risk in ("high", "critical"):
                forbidden = meta.get("forbidden_outputs", [])
                self.assertIsInstance(
                    forbidden,
                    list,
                    f"{md_file.name}: forbidden_outputs must be a list",
                )
                self.assertGreater(
                    len(forbidden),
                    0,
                    f"{md_file.name}: high-risk card missing forbidden_outputs",
                )


class TestNoFlatArticles(unittest.TestCase):
    """No article .md files should exist directly in kb/articles/ root."""

    def test_no_flat_articles(self):
        flat = list(ARTICLES_DIR.glob("*.md"))
        self.assertEqual(
            len(flat),
            0,
            f"Flat articles found in kb/articles/: {[f.name for f in flat]}",
        )


if __name__ == "__main__":
    unittest.main()
