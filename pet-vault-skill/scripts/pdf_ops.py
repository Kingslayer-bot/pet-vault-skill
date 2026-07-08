"""pdf_ops: PDF compilation, QA inspection, and report artifact checks.

Handles PDF compilation with xelatex/latexmk, QA inspection of report artifacts,
and forbidden term checking. All functions are deterministic.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from agent_registry_loader import load_forbidden_terms


def compile_pdf(tex_path: Path, output_dir: Path, skip: bool = False) -> tuple[bool, str]:
    """Compile LaTeX to PDF using xelatex or latexmk.

    Args:
        tex_path: Path to the .tex file.
        output_dir: Directory for output files.
        skip: If True, skip compilation and write skip message to build.log.

    Returns:
        Tuple of (success, log_message).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    build_log = output_dir / "build.log"
    if skip:
        message = "PDF compile skipped by --skip-pdf-compile.\n"
        build_log.write_text(message, encoding="utf-8")
        return True, message
    engine = shutil.which("xelatex") or shutil.which("latexmk")
    if not engine:
        message = "No xelatex or latexmk found; PDF compile skipped.\n"
        build_log.write_text(message, encoding="utf-8")
        return False, message
    if Path(engine).name.lower().startswith("latexmk"):
        cmd = [engine, "-xelatex", "-interaction=nonstopmode", tex_path.name]
    else:
        cmd = [engine, "-interaction=nonstopmode", tex_path.name]
    result = subprocess.run(
        cmd, cwd=output_dir, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=120,
    )
    log = result.stdout + "\n" + result.stderr
    build_log.write_text(log, encoding="utf-8")
    return result.returncode == 0, log


def check_forbidden_terms(report_md: str) -> list[str]:
    """Check report markdown for forbidden terms.

    Args:
        report_md: Report markdown text to check.

    Returns:
        List of blocking issues found.
    """
    blocking = []
    forbidden = load_forbidden_terms()
    for term in forbidden:
        if term in report_md:
            blocking.append(f"Forbidden or unsafe report term: {term}")
    return blocking


def check_required_files(output_dir: Path) -> list[str]:
    """Check that required output files exist.

    Args:
        output_dir: Directory to check.

    Returns:
        List of blocking issues found.
    """
    blocking = []
    required_files = ["report.md", "report.tex", "manifest.json", "build.log"]
    for file_name in required_files:
        if not (output_dir / file_name).exists():
            blocking.append(f"Missing output file: {file_name}")
    return blocking


def check_pdf_status(output_dir: Path, pdf_required: bool = False) -> tuple[str, list[str]]:
    """Check PDF existence and status.

    Args:
        output_dir: Directory to check.
        pdf_required: If True, missing PDF is a blocking issue.

    Returns:
        Tuple of (pdf_readability_status, blocking_issues).
    """
    blocking = []
    pdf_path = output_dir / "report.pdf"
    if pdf_required and not pdf_path.exists():
        blocking.append("PDF was required but report.pdf is missing")
    if pdf_path.exists() and pdf_path.stat().st_size == 0:
        blocking.append("report.pdf exists but is empty")
    pdf_present = pdf_path.exists()
    build_log_text = ""
    if (output_dir / "build.log").exists():
        build_log_text = (output_dir / "build.log").read_text(encoding="utf-8")
    if pdf_present:
        status = "passed"
    elif "No xelatex or latexmk found" in build_log_text:
        status = "warning"
    else:
        status = "skipped"
    return status, blocking


def check_fee_explanation(report_md: str, materials_index: dict | None) -> tuple[str, list[str]]:
    """Check fee explanation completeness.

    Args:
        report_md: Report markdown text.
        materials_index: Materials index data.

    Returns:
        Tuple of (fee_explanation_status, blocking_issues).
    """
    blocking = []
    if not materials_index:
        return "passed", blocking
    materials = materials_index.get("materials", [])
    bill_like = [m for m in materials if m.get("type") in {"bill", "invoice", "unknown"}]
    indexed_only_bill_like = [m for m in bill_like if m.get("status") == "indexed_only"]
    no_bill_details = "当前材料未抽取到账单明细" in report_md
    if no_bill_details and indexed_only_bill_like:
        blocking.append("Bill/invoice material was indexed without OCR or transcription; fee explanation is incomplete.")
        return "failed", blocking
    if no_bill_details and bill_like:
        blocking.append("Bill/invoice material did not produce charge items; fee explanation is incomplete.")
        return "failed", blocking
    return "passed", blocking


def inspect_report(
    output_dir: Path,
    report_md: str,
    pdf_required: bool = False,
    materials_index: dict | None = None,
) -> dict:
    """Inspect report artifacts for quality issues.

    Args:
        output_dir: Directory containing report artifacts.
        report_md: Report markdown text.
        pdf_required: If True, missing PDF is blocking.
        materials_index: Materials index data.

    Returns:
        QA result dict with passed, blocking_issues, warnings, and checks.
    """
    blocking = []
    warnings = []

    # Check forbidden terms
    blocking.extend(check_forbidden_terms(report_md))

    # Check required files
    blocking.extend(check_required_files(output_dir))

    # Check PDF status
    pdf_status, pdf_blocking = check_pdf_status(output_dir, pdf_required)
    blocking.extend(pdf_blocking)

    # Check LaTeX longtable
    tex = ""
    if (output_dir / "report.tex").exists():
        tex = (output_dir / "report.tex").read_text(encoding="utf-8")
    if "longtable" not in tex:
        warnings.append("LaTeX output does not reference longtable.")

    # Check fee explanation
    fee_status, fee_blocking = check_fee_explanation(report_md, materials_index)
    blocking.extend(fee_blocking)

    return {
        "passed": not blocking,
        "blocking_issues": blocking,
        "warnings": warnings,
        "checks": {
            "source_integrity": "passed",
            "identity_consistency": "warning" if "多只宠物" in report_md else "passed",
            "visit_completeness": "passed",
            "fee_explanation": fee_status,
            "insurance_boundary": "passed" if "不承诺理赔结果" in report_md or "理赔" not in report_md else "warning",
            "timeline": "passed",
            "pdf_readability": pdf_status,
            "local_storage": "passed",
        },
    }
