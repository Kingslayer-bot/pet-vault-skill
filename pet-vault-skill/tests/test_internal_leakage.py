"""Tests for internal term leakage prevention.
Verifies that report.md, manifest, and dispatch responses never contain
internal classification codes, status codes, or developer-facing terms.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
import tempfile
import os
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parent
sys.path.insert(0, str(SKILL / "scripts"))

import petvault_core
from report_sanitizer import sanitize_report_markdown, build_user_manifest
from agent_registry_loader import load_forbidden_terms, load_internal_type_map, load_internal_status_map

TMP_ROOT = Path(os.environ.get("PETVAULT_TEST_TMP", Path(tempfile.gettempdir()) / "pet_vault_leakage_tests"))

# Load from registry (single source of truth)
FORBIDDEN_IN_REPORT = load_forbidden_terms()
INTERNAL_TYPE_MAP = load_internal_type_map()
INTERNAL_STATUS_MAP = load_internal_status_map()

FORBIDDEN_IN_MANIFEST = [
    "routing",
    "pdf_policy",
]


class TestSanitizeReportMarkdown(unittest.TestCase):
    """sanitize_report_markdown must remove all internal terms."""

    def test_translates_type_codes(self):
        raw = "- file.md：类型=insurance_policy；日期=2026-01-01"
        result = sanitize_report_markdown(raw)
        self.assertIn("类型=保险保单", result)
        self.assertNotIn("insurance_policy", result)

    def test_translates_all_type_codes(self):
        for code, label in INTERNAL_TYPE_MAP.items():
            raw = f"类型={code}"
            result = sanitize_report_markdown(raw)
            self.assertNotIn(code, result, f"Type code '{code}' should be translated")
            self.assertIn(label, result, f"Label '{label}' should appear for '{code}'")

    def test_removes_confidence_scores(self):
        raw = "- file.md：类型=bill；置信度=0.9；状态=extracted"
        result = sanitize_report_markdown(raw)
        self.assertNotIn("置信度", result)
        self.assertNotIn("0.9", result)

    def test_translates_status_codes(self):
        for code, label in INTERNAL_STATUS_MAP.items():
            raw = f"状态={code}"
            result = sanitize_report_markdown(raw)
            self.assertNotIn(code, result, f"Status code '{code}' should be translated")
            self.assertIn(label, result, f"Label '{label}' should appear for '{code}'")

    def test_removes_forbidden_tags(self):
        raw = "This is [FORBIDDEN] and [INTERNAL] and [DEBUG] content."
        result = sanitize_report_markdown(raw)
        self.assertNotIn("[FORBIDDEN]", result)
        self.assertNotIn("[INTERNAL]", result)
        self.assertNotIn("[DEBUG]", result)

    def test_removes_developer_terms(self):
        raw = "This PRD uses Harness with HMW and POV analysis."
        result = sanitize_report_markdown(raw)
        self.assertNotIn("PRD", result)
        self.assertNotIn("Harness", result)
        self.assertNotIn("HMW", result)
        self.assertNotIn("POV", result)

    def test_removes_routing_metadata(self):
        raw = "Route: request_mentions_billing, dispatch routing"
        result = sanitize_report_markdown(raw)
        self.assertNotIn("request_mentions_", result)
        self.assertNotIn("dispatch", result)
        self.assertNotIn("routing", result)


class TestBuildReportNoInternalTerms(unittest.TestCase):
    """Full pipeline report.md must not contain any internal terms."""

    def _run_pipeline_and_get_report(self, report_type: str = "bill_explain") -> str:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmpdir = TMP_ROOT / f"leakage_{uuid.uuid4().hex[:8]}"
        input_dir = tmpdir / "materials"
        output_dir = tmpdir / "out"
        vault_dir = tmpdir / "vault"
        input_dir.mkdir(parents=True)
        (input_dir / "bill.txt").write_text(
            "宠物：Mimi\n日期：2026-07-05\n医院：星河动物医院\n项目：血常规 120 元；B超 350 元",
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(SKILL / "scripts" / "run_pipeline.py"),
            "--input", str(input_dir),
            "--output", str(output_dir),
            "--vault", str(vault_dir),
            "--report-type", report_type,
            "--pet-name", "Mimi",
            "--skip-pdf-compile",
        ]
        result = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return (output_dir / "report.md").read_text(encoding="utf-8")

    def test_bill_explain_no_internal_terms(self):
        report = self._run_pipeline_and_get_report("bill_explain")
        for term in FORBIDDEN_IN_REPORT:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in bill_explain report")

    def test_claim_check_no_internal_terms(self):
        report = self._run_pipeline_and_get_report("claim_check")
        for term in FORBIDDEN_IN_REPORT:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in claim_check report")

    def test_timeline_no_internal_terms(self):
        report = self._run_pipeline_and_get_report("timeline")
        for term in FORBIDDEN_IN_REPORT:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in timeline report")

    def test_general_no_internal_terms(self):
        report = self._run_pipeline_and_get_report("general")
        for term in FORBIDDEN_IN_REPORT:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in general report")


class TestUserManifestNoInternalTerms(unittest.TestCase):
    """user_manifest.json must not contain routing.reason or internal fields."""

    def _run_pipeline_and_get_user_manifest(self) -> dict:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmpdir = TMP_ROOT / f"manifest_{uuid.uuid4().hex[:8]}"
        input_dir = tmpdir / "materials"
        output_dir = tmpdir / "out"
        vault_dir = tmpdir / "vault"
        input_dir.mkdir(parents=True)
        (input_dir / "bill.txt").write_text(
            "宠物：Mimi\n日期：2026-07-05\n医院：星河动物医院\n项目：血常规 120 元",
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(SKILL / "scripts" / "run_pipeline.py"),
            "--input", str(input_dir),
            "--output", str(output_dir),
            "--vault", str(vault_dir),
            "--report-type", "bill_explain",
            "--pet-name", "Mimi",
            "--skip-pdf-compile",
        ]
        result = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads((output_dir / "user_manifest.json").read_text(encoding="utf-8"))

    def test_user_manifest_no_routing(self):
        manifest = self._run_pipeline_and_get_user_manifest()
        self.assertNotIn("routing", manifest)
        self.assertNotIn("pdf_policy", manifest)

    def test_user_manifest_has_required_fields(self):
        manifest = self._run_pipeline_and_get_user_manifest()
        for field in ["id", "pet_name", "report_type", "created_at", "pdf_status", "materials", "outputs"]:
            self.assertIn(field, manifest)

    def test_user_manifest_materials_use_translated_labels(self):
        manifest = self._run_pipeline_and_get_user_manifest()
        for material in manifest.get("materials", []):
            self.assertNotIn("insurance_policy", str(material))
            self.assertNotIn("lab_report", str(material))
            if "type_label" in material:
                self.assertNotIn("_", material["type_label"])


class TestDispatchNoForbiddenTag(unittest.TestCase):
    """Dispatch forbidden response must not contain [FORBIDDEN] tag."""

    def test_forbidden_response_no_tag(self):
        from petvault_dispatch import get_forbidden_response
        response = get_forbidden_response()
        self.assertNotIn("[FORBIDDEN]", response)
        self.assertIn("PetVault", response)

    def test_dispatch_returns_clean_response(self):
        from petvault_dispatch import dispatch
        result = dispatch("帮我改病历")
        self.assertEqual(result, "forbidden")


class TestMarkdownTableToLatex(unittest.TestCase):
    """Markdown table must convert to LaTeX longtable."""

    def test_table_conversion(self):
        md = "# Report\n\n| Item | Amount |\n|------|--------|\n| Exam | $80.00 |\n| X-Ray | $333.00 |\n"
        latex = petvault_core.markdown_to_latex_body(md)
        self.assertIn("\\begin{longtable}", latex)
        self.assertIn("\\end{longtable}", latex)
        self.assertIn("\\toprule", latex)
        self.assertIn("\\bottomrule", latex)
        self.assertIn("Exam", latex)
        self.assertIn("X-Ray", latex)

    def test_bold_conversion(self):
        md = "# Report\n\nThis is **important** text.\n"
        latex = petvault_core.markdown_to_latex_body(md)
        self.assertIn("\\textbf{important}", latex)

    def test_italic_conversion(self):
        md = "# Report\n\nThis is *emphasized* text.\n"
        latex = petvault_core.markdown_to_latex_body(md)
        self.assertIn("\\textit{emphasized}", latex)


class TestCoverageOfAllReportTypes(unittest.TestCase):
    """All report types must pass leakage check."""

    def test_all_report_types(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        for report_type in ["general", "bill_explain", "claim_check", "timeline",
                            "medical_summary", "chronic_review", "clinic_client_summary"]:
            with self.subTest(report_type=report_type):
                tmpdir = TMP_ROOT / f"all_{report_type}_{uuid.uuid4().hex[:8]}"
                input_dir = tmpdir / "materials"
                output_dir = tmpdir / "out"
                vault_dir = tmpdir / "vault"
                input_dir.mkdir(parents=True)
                (input_dir / "bill.txt").write_text(
                    "宠物：Mimi\n日期：2026-07-05\n医院：星河动物医院\n项目：血常规 120 元",
                    encoding="utf-8",
                )
                command = [
                    sys.executable,
                    str(SKILL / "scripts" / "run_pipeline.py"),
                    "--input", str(input_dir),
                    "--output", str(output_dir),
                    "--vault", str(vault_dir),
                    "--report-type", report_type,
                    "--pet-name", "Mimi",
                    "--skip-pdf-compile",
                ]
                result = subprocess.run(
                    command, cwd=ROOT, text=True, capture_output=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, f"{report_type}: {result.stderr}")
                report = (output_dir / "report.md").read_text(encoding="utf-8")
                for term in FORBIDDEN_IN_REPORT:
                    self.assertNotIn(term, report, f"{report_type}: forbidden term '{term}'")


if __name__ == "__main__":
    unittest.main()
