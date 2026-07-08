"""Tests for agent_registry_loader module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from agent_registry_loader import (
    get_registry_path,
    load_forbidden_terms,
    load_internal_type_map,
    load_internal_status_map,
    registry_exists,
    _FALLBACK_FORBIDDEN_TERMS,
)


class TestRegistryExists(unittest.TestCase):
    def test_registry_file_exists(self):
        self.assertTrue(registry_exists())

    def test_registry_path_points_to_yaml(self):
        path = get_registry_path()
        self.assertTrue(path.name.endswith(".yaml"))
        self.assertTrue(path.exists())


class TestLoadForbiddenTerms(unittest.TestCase):
    def test_returns_non_empty_list(self):
        terms = load_forbidden_terms()
        self.assertGreater(len(terms), 0)

    def test_contains_representative_entries(self):
        terms = load_forbidden_terms()
        self.assertIn("insurance_policy", terms)
        self.assertIn("routing", terms)
        self.assertIn("dispatch", terms)
        self.assertIn("置信度", terms)
        self.assertIn("[FORBIDDEN]", terms)
        self.assertIn("PRD", terms)
        self.assertIn("Harness", terms)

    def test_contains_all_fallback_terms_if_registry_missing(self):
        terms = load_forbidden_terms()
        for term in _FALLBACK_FORBIDDEN_TERMS:
            self.assertIn(term, terms, f"Missing term: {term}")


class TestLoadTypeMap(unittest.TestCase):
    def test_returns_non_empty_dict(self):
        type_map = load_internal_type_map()
        self.assertGreater(len(type_map), 0)

    def test_maps_known_types(self):
        type_map = load_internal_type_map()
        self.assertEqual(type_map["invoice"], "发票/收据")
        self.assertEqual(type_map["insurance_policy"], "保险保单")
        self.assertEqual(type_map["lab_report"], "化验报告")


class TestLoadStatusMap(unittest.TestCase):
    def test_returns_non_empty_dict(self):
        status_map = load_internal_status_map()
        self.assertGreater(len(status_map), 0)

    def test_maps_known_statuses(self):
        status_map = load_internal_status_map()
        self.assertEqual(status_map["extracted"], "已提取")
        self.assertEqual(status_map["indexed_only"], "已索引（未解析正文）")


if __name__ == "__main__":
    unittest.main()
