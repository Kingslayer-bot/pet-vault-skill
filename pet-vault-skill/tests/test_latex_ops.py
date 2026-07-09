"""Tests for latex_ops module."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from latex_ops import (
    latex_escape,
    _convert_inline_latex,
    _is_table_line,
    _is_table_separator,
    _parse_table_rows,
    _table_to_longtable,
    markdown_to_latex_body,
    render_latex,
    COVER_TITLES,
)


class TestLatexEscape(unittest.TestCase):
    def test_escapes_special_chars(self):
        self.assertEqual(latex_escape("a&b"), r"a\&b")
        self.assertEqual(latex_escape("a%b"), r"a\%b")
        self.assertEqual(latex_escape("a$b"), r"a\$b")
        self.assertEqual(latex_escape("a#b"), r"a\#b")
        self.assertEqual(latex_escape("a_b"), r"a\_b")
        self.assertEqual(latex_escape("a{b"), r"a\{b")
        self.assertEqual(latex_escape("a}b"), r"a\}b")
        self.assertEqual(latex_escape("a~b"), r"a\textasciitilde{}b")
        self.assertEqual(latex_escape("a^b"), r"a\textasciicircum{}b")

    def test_preserves_normal_text(self):
        self.assertEqual(latex_escape("hello world"), "hello world")

    def test_escapes_backslash(self):
        self.assertEqual(latex_escape("a\\b"), r"a\textbackslash{}b")


class TestConvertInlineLatex(unittest.TestCase):
    def test_bold(self):
        self.assertIn("\\textbf{bold}", _convert_inline_latex("**bold**"))

    def test_italic(self):
        self.assertIn("\\textit{italic}", _convert_inline_latex("*italic*"))

    def test_link(self):
        result = _convert_inline_latex("[text](http://example.com)")
        self.assertIn("\\href{http://example.com}{text}", result)


class TestTableDetection(unittest.TestCase):
    def test_table_line(self):
        self.assertTrue(_is_table_line("| a | b |"))
        self.assertTrue(_is_table_line("|---|---|"))

    def test_not_table_line(self):
        self.assertFalse(_is_table_line("normal text"))
        self.assertFalse(_is_table_line("- list item"))

    def test_table_separator(self):
        self.assertTrue(_is_table_separator("|---|---|"))
        self.assertTrue(_is_table_separator("| :--- | :---: |"))

    def test_parse_table_rows(self):
        lines = ["| A | B |", "| 1 | 2 |"]
        rows = _parse_table_rows(lines)
        self.assertEqual(rows, [["A", "B"], ["1", "2"]])


class TestTableToLongtable(unittest.TestCase):
    def test_basic_table(self):
        lines = ["| Item | Amount |", "|------|--------|", "| Exam | $80.00 |"]
        result = _table_to_longtable(lines)
        self.assertIn("\\begin{longtable}", result)
        self.assertIn("\\end{longtable}", result)
        self.assertIn("\\toprule", result)
        self.assertIn("\\bottomrule", result)
        self.assertIn("Exam", result)
        self.assertIn("$80.00", result)

    def test_empty_table_returns_empty(self):
        self.assertEqual(_table_to_longtable(["| A |"]), "")


class TestMarkdownToLatexBody(unittest.TestCase):
    def test_headings(self):
        md = "# Title\n## Sub\n### SubSub"
        result = markdown_to_latex_body(md)
        self.assertIn("\\pvsection{Title}", result)
        self.assertIn("\\pvsubsection{Sub}", result)
        self.assertIn("\\pvsubsubsection{SubSub}", result)

    def test_list(self):
        md = "- item1\n- item2"
        result = markdown_to_latex_body(md)
        self.assertIn("\\begin{itemize}", result)
        self.assertIn("\\item item1", result)
        self.assertIn("\\item item2", result)
        self.assertIn("\\end{itemize}", result)

    def test_table_in_markdown(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = markdown_to_latex_body(md)
        self.assertIn("\\begin{longtable}", result)
        self.assertIn("A", result)
        self.assertIn("1", result)


class TestCoverTitles(unittest.TestCase):
    def test_all_report_types_have_titles(self):
        for rt in ["general", "medical_summary", "bill_explain", "claim_check",
                    "timeline", "chronic_review", "clinic_client_summary"]:
            self.assertIn(rt, COVER_TITLES)


if __name__ == "__main__":
    unittest.main()
