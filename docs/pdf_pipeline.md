# PDF Rendering Pipeline

## Overview

PetVault generates PDF reports from Markdown source through a multi-stage pipeline:

```
report.md (sanitized)
    │
    ▼
markdown_to_latex_body()    # Markdown → LaTeX body
    │
    ▼
render_latex()              # Template substitution + cover title
    │
    ▼
report.tex                  # Complete LaTeX document
    │
    ▼
compile_pdf()               # xelatex/latexmk → PDF
    │
    ▼
report.pdf                  # Final output
```

## Stage 1: Markdown Generation

`build_report_markdown()` in `petvault_core.py` generates the raw report based on:
- Report type (bill_explain, claim_check, timeline, etc.)
- Materials index
- Analysis results (bill items, timeline nodes, claim summary, medical findings)

## Stage 2: Sanitization

`sanitize_report_markdown()` in `report_sanitizer.py`:
- Translates internal type codes → Chinese labels (e.g., `insurance_policy` → `保险保单`)
- Translates internal status codes → Chinese labels
- Removes confidence scores
- Removes forbidden terms (routing, dispatch, PRD, etc.)
- Removes forbidden tags ([FORBIDDEN], [INTERNAL], [DEBUG])

## Stage 3: Markdown → LaTeX Conversion

`markdown_to_latex_body()` in `petvault_core.py` handles:

### Supported Constructs

| Markdown | LaTeX Output |
|----------|-------------|
| `# Title` | `\section{Title}` |
| `## Subtitle` | `\subsection{Subtitle}` |
| `### Sub` | `\subsubsection{Sub}` |
| `- item` | `\begin{itemize} \item item \end{itemize}` |
| `**bold**` | `\textbf{bold}` |
| `*italic*` | `\textit{italic}` |
| `[text](url)` | `\href{url}{text}` |
| `\| col1 \| col2 \|` | `\begin{longtable}...\end{longtable}` |

### Table Conversion

Tables are converted to LaTeX `longtable` with:
- `\toprule` / `\midrule` / `\bottomrule` (booktabs style)
- `Y` column type (raggedright, flexible width)
- Automatic column count detection
- Separator row filtering

### Not Yet Supported

- Nested lists (flattened to single level)
- Code blocks (rendered as plain text)
- Images (`![alt](path)` — not converted to `\includegraphics`)
- Horizontal rules (`---`)
- Block quotes

## Stage 4: Template Application

`render_latex()` applies the LaTeX template:
- Loads `templates/styles.tex.j2` (shared style definitions)
- Loads report-type-specific template (e.g., `report_bill_explain.tex.j2`)
- Substitutes `{{ styles }}`, `{{ title }}`, `{{ pet_name }}`, `{{ body }}`

### Cover Title Selection

`COVER_TITLES` dict maps report types to Chinese cover titles:
- `general` → "PetVault 综合整理报告"
- `bill_explain` → "PetVault 账单解释报告"
- `claim_check` → "PetVault 理赔材料检查报告"
- etc.

## Stage 5: PDF Compilation

`compile_pdf()` attempts:
1. `xelatex -interaction=nonstopmode report.tex`
2. Falls back to `latexmk -xelatex -interaction=nonstopmode report.tex`
3. If no TeX engine found, writes "skipped" to build.log

### Layout Constraints

Defined in `templates/styles.tex.j2`:
- Document class: `ctexart` (Chinese LaTeX)
- Paper: A4, 11pt
- Font: `fontset=windows`
- Margins: left=2.35cm, right=2.35cm, top=2.15cm, bottom=2.20cm
- Line spread: 1.28

## Stage 6: QA Inspection

`inspect_report()` checks:
- Forbidden terms in report.md
- Required output files exist
- PDF exists (if policy=required)
- PDF is not empty
- longtable reference in .tex
- Fee explanation completeness

## Adding New Report Types

1. Add title to `REPORT_TITLES` in `petvault_core.py`
2. Add cover title to `COVER_TITLES` in `petvault_core.py`
3. Create template `templates/report_<type>.tex.j2`
4. Add report type logic to `build_report_markdown()`
5. Add routing logic to `auto_select_report_type()`
6. Add test cases to `tests/test_pet_vault_skill.py`
7. Add leakage test cases to `tests/test_internal_leakage.py`
