"""Tests for pdf_ops module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from pdf_ops import (
    compile_pdf,
    check_forbidden_terms,
    check_required_files,
    check_pdf_status,
    check_fee_explanation,
    inspect_report,
)


class TestCompilePdf(unittest.TestCase):
    def test_skip_returns_true(self):
        """Skipping compilation should return True with skip message."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = Path(tmpdir) / "test.tex"
            tex_path.write_text("test", encoding="utf-8")
            output_dir = Path(tmpdir) / "out"
            ok, log = compile_pdf(tex_path, output_dir, skip=True)
            self.assertTrue(ok)
            self.assertIn("skipped", log.lower())

    def test_missing_compiler_returns_false(self):
        """Missing LaTeX compiler should return False or compilation fails."""
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = Path(tmpdir) / "test.tex"
            tex_path.write_text("\\documentclass{article}\\begin{document}test\\end{document}", encoding="utf-8")
            output_dir = Path(tmpdir) / "out"
            # This will fail if no xelatex/latexmk is available
            ok, log = compile_pdf(tex_path, output_dir, skip=False)
            # Should either succeed (if compiler found and tex is valid) or return False
            # If compiler is found but tex has issues, ok may be False
            if not ok:
                # Either no compiler or compilation failed
                self.assertTrue(
                    "No xelatex or latexmk found" in log or "Emergency stop" in log or "error" in log.lower(),
                    f"Unexpected log: {log[:200]}"
                )


class TestCheckForbiddenTerms(unittest.TestCase):
    def test_clean_text_no_issues(self):
        """Clean text should have no blocking issues."""
        issues = check_forbidden_terms("这是一份正常的账单报告。")
        self.assertEqual(issues, [])

    def test_forbidden_term_detected(self):
        """Forbidden terms should be detected."""
        issues = check_forbidden_terms("这份报告使用了 PRD 文档。")
        self.assertGreater(len(issues), 0)
        self.assertIn("PRD", issues[0])


class TestCheckRequiredFiles(unittest.TestCase):
    def test_missing_files_detected(self):
        """Missing required files should be detected."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = check_required_files(Path(tmpdir))
            self.assertGreater(len(issues), 0)


class TestCheckPdfStatus(unittest.TestCase):
    def test_no_pdf_not_required(self):
        """Missing PDF when not required should not block."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            status, blocking = check_pdf_status(Path(tmpdir), pdf_required=False)
            self.assertEqual(status, "skipped")
            self.assertEqual(blocking, [])

    def test_pdf_required_but_missing(self):
        """Missing PDF when required should block."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            status, blocking = check_pdf_status(Path(tmpdir), pdf_required=True)
            self.assertGreater(len(blocking), 0)


class TestCheckFeeExplanation(unittest.TestCase):
    def test_no_materials_passes(self):
        """No materials should pass."""
        status, blocking = check_fee_explanation("report", None)
        self.assertEqual(status, "passed")
        self.assertEqual(blocking, [])


class TestInspectReport(unittest.TestCase):
    def test_clean_report_passes(self):
        """Clean report should pass inspection."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "report.md").write_text("报告内容", encoding="utf-8")
            (output_dir / "report.tex").write_text("longtable", encoding="utf-8")
            (output_dir / "manifest.json").write_text("{}", encoding="utf-8")
            (output_dir / "build.log").write_text("ok", encoding="utf-8")
            result = inspect_report(output_dir, "报告内容", pdf_required=False)
            self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
