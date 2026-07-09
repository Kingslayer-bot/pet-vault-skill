"""latex_ops: LaTeX escaping, inline formatting, table conversion, and rendering."""
from __future__ import annotations

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

COVER_TITLES = {
    "general": "PetVault 综合整理报告",
    "medical_summary": "PetVault 兽医报告简明解读",
    "bill_explain": "宠物医疗账单解释报告",
    "claim_check": "PetVault 理赔材料检查报告",
    "timeline": "PetVault 跨院就诊资料包",
    "chronic_review": "PetVault 慢病月度复盘报告",
    "clinic_client_summary": "PetVault 医院端客户解释材料",
}


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _convert_inline_latex(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\\href{\2}{\1}', text)
    return text


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r'^\|[\s\-:|]+\|$', stripped))


def _parse_table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def _is_table_separator_str(cells: list[str]) -> bool:
    return all(re.match(r'^[\s\-:]+$', c) for c in cells if c.strip())


def _table_to_longtable(lines: list[str]) -> str:
    """Convert markdown table lines to structured LaTeX longtable with p{} cols."""
    rows = _parse_table_rows(lines)
    if len(rows) < 2:
        return ""
    header = rows[0]
    ncols = len(header)
    # Column specs by column count: 2, 3, 4, 5 columns
    # Widths reduced to account for >{\raggedright} prefix overhead
    _SPECS = {
        2: r"p{0.26\linewidth} p{0.62\linewidth}",
        3: r"p{0.30\linewidth} p{0.20\linewidth} p{0.36\linewidth}",
        4: r"p{0.30\linewidth} p{0.14\linewidth} p{0.16\linewidth} p{0.20\linewidth}",
        5: r"p{0.26\linewidth} p{0.11\linewidth} p{0.16\linewidth} p{0.16\linewidth} p{0.14\linewidth}",
    }
    col_spec = _SPECS.get(ncols, " ".join([f"p{{0.90/linewidth}}"] * ncols))
    # Add \\raggedright to each column to prevent single-char line breaks
    col_spec = " ".join(f">{{\\raggedright\\arraybackslash}}{c}" for c in col_spec.split())
    parts = [
        r"\begin{longtable}{" + col_spec + "}",
        r"\toprule",
    ]
    parts.append(" & ".join(latex_escape(h) for h in header) + r" \\")
    parts.append(r"\midrule")
    parts.append(r"\endhead")
    for row in rows[1:]:
        if _is_table_separator_str(row):
            continue
        while len(row) < ncols:
            row.append("")
        row = row[:ncols]
        parts.append(" & ".join(latex_escape(c) for c in row) + r" \\")
    parts.append(r"\bottomrule")
    parts.append(r"\end{longtable}")
    return "\n".join(parts)


def markdown_to_latex_body(markdown: str) -> str:
    body = []
    in_items = False
    in_enumerate = False
    in_table = False
    in_blockquote = False
    in_raw_latex = False
    table_lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        # Messagebox passthrough
        if line.startswith(":::messagebox"):
            in_raw_latex = True
            body.append(r"\begin{pvmessagebox}")
            continue
        if line.startswith(":::endmessagebox") and in_raw_latex:
            body.append(r"\end{pvmessagebox}")
            in_raw_latex = False
            continue
        # Raw LaTeX passthrough
        if line.startswith(":::raw"):
            in_raw_latex = True
            continue
        if line.startswith(":::end") and in_raw_latex:
            in_raw_latex = False
            continue
        if in_raw_latex:
            body.append(line)
            continue
        if not line:
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            if in_blockquote:
                body.append(r"\end{pvcallout}")
                in_blockquote = False
            if in_table:
                body.append(_table_to_longtable(table_lines))
                table_lines = []
                in_table = False
            body.append("")
            continue
        if _is_table_line(line):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            if in_blockquote:
                body.append(r"\end{pvcallout}")
                in_blockquote = False
            in_table = True
            table_lines.append(line)
            continue
        if in_table:
            body.append(_table_to_longtable(table_lines))
            table_lines = []
            in_table = False
        # Blockquote lines -> callout boxes
        if line.startswith("> "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            if not in_blockquote:
                body.append(r"\begin{pvcallout}")
                in_blockquote = True
            escaped = latex_escape(line[2:].strip())
            escaped = _convert_inline_latex(escaped)
            body.append(escaped)
            continue
        if in_blockquote:
            body.append(r"\end{pvcallout}")
            in_blockquote = False
        if line.startswith("# "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            body.append(r"\pvsection{" + latex_escape(line[2:].strip()) + "}")
        elif line.startswith("## "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            body.append(r"\pvsubsection{" + latex_escape(line[3:].strip()) + "}")
        elif line.startswith("### "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            body.append(r"\pvsubsubsection{" + latex_escape(line[4:].strip()) + "}")
        elif re.match(r"^\d+\.\s", line):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if not in_enumerate:
                body.append(r"\begin{enumerate}[leftmargin=2.5em,itemsep=2pt,topsep=4pt]")
                in_enumerate = True
            item_text = latex_escape(re.sub(r"^\d+\.\s", "", line).strip())
            item_text = _convert_inline_latex(item_text)
            body.append(r"  \item " + item_text)
        elif line.startswith("- "):
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            if not in_items:
                body.append(r"\begin{itemize}")
                in_items = True
            item_text = latex_escape(line[2:].strip())
            item_text = _convert_inline_latex(item_text)
            body.append(r"  \item " + item_text)
        else:
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            if in_enumerate:
                body.append(r"\end{enumerate}")
                in_enumerate = False
            escaped = latex_escape(line)
            escaped = _convert_inline_latex(escaped)
            body.append(escaped)
    if in_items:
        body.append(r"\end{itemize}")
    if in_enumerate:
        body.append(r"\end{enumerate}")
    if in_blockquote:
        body.append(r"\end{pvcallout}")
    if in_table:
        body.append(_table_to_longtable(table_lines))
    return "\n".join(body)


def render_latex(markdown: str, report_type: str, pet_name: str, unknown_text: str = "待确认") -> str:
    styles = (SKILL_DIR / "templates" / "styles.tex.j2").read_text(encoding="utf-8")
    template_name = {
        "medical_summary": "report_medical_summary.tex.j2",
        "bill_explain": "report_bill_explain.tex.j2",
        "claim_check": "report_claim_check.tex.j2",
        "timeline": "report_timeline.tex.j2",
        "chronic_review": "report_chronic_review.tex.j2",
        "clinic_client_summary": "report_clinic_client_summary.tex.j2",
    }.get(report_type, "report_general.tex.j2")
    template = (SKILL_DIR / "templates" / template_name).read_text(encoding="utf-8")
    cover_title = COVER_TITLES.get(report_type, COVER_TITLES["general"])
    return (
        template.replace("{{ styles }}", styles)
        .replace("{{ title }}", latex_escape(cover_title))
        .replace("{{ pet_name }}", latex_escape(pet_name or unknown_text))
        .replace("{{ body }}", markdown_to_latex_body(markdown))
    )
