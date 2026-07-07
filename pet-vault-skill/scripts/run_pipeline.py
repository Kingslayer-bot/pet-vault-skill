from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import (
    AUTO_REPORT_TYPE,
    REPORT_TITLES,
    UNKNOWN_TEXT,
    run_pipeline,
)
from petvault_dispatch import (
    detect_emergency,
    dispatch,
    get_emergency_response,
    knowledge_only_answer,
)


def _resolve_input_dir(args) -> Path | None:
    if args.input is not None:
        return args.input
    default = Path("input")
    if default.exists() and default.is_dir():
        return default
    return None


def _resolve_output_dir(args) -> Path | None:
    if args.output is not None:
        return args.output
    default = Path("output")
    return default


def _resolve_vault_dir(args) -> Path | None:
    if args.vault is not None:
        return args.vault
    default = Path("vault")
    return default


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the PetVault Phase 1 pipeline with dispatch support."
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "report", "knowledge", "emergency"],
        default="auto",
        help="Dispatch mode: auto (detect), report (force pipeline), "
             "knowledge (force KB query), emergency (force emergency check).",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="User query text for knowledge-only or emergency mode. "
             "Alternative to --request.",
    )
    parser.add_argument("--input", type=Path, default=None, help="Input directory with materials.")
    parser.add_argument("--output", type=Path, default=None, help="Output directory for reports.")
    parser.add_argument("--vault", type=Path, default=None, help="Vault directory for storage.")
    parser.add_argument(
        "--report-type",
        default=AUTO_REPORT_TYPE,
        choices=sorted([AUTO_REPORT_TYPE, *REPORT_TITLES]),
    )
    parser.add_argument("--request", default="", help="Original user request text for auto routing.")
    parser.add_argument("--pet-name", default=UNKNOWN_TEXT)
    parser.add_argument("--skip-pdf-compile", action="store_true")
    parser.add_argument(
        "--pdf-policy",
        default="attempt",
        choices=["attempt", "required", "skip"],
    )

    args = parser.parse_args()

    mode = args.mode
    request_text = args.request or args.query or ""

    if mode == "auto":
        input_dir = _resolve_input_dir(args)
        has_materials = (
            input_dir is not None
            and input_dir.exists()
            and input_dir.is_dir()
        )
        result = dispatch(request_text, input_dir, has_materials)

        if result == "emergency":
            print(get_emergency_response())
            return 0

        if result == "knowledge_query":
            answer = knowledge_only_answer(request_text or args.query or "")
            print(answer)
            return 0

        mode = "report"

    if mode == "knowledge":
        if not request_text:
            raise SystemExit("--query or --request is required for knowledge mode.")
        answer = knowledge_only_answer(args.query or args.request or "")
        print(answer)
        return 0

    if mode == "emergency":
        if not request_text:
            raise SystemExit("--query or --request is required for emergency mode.")
        if detect_emergency(request_text):
            print(get_emergency_response())
        else:
            print(
                "未检测到宠物急症关键词。请仍根据实际情况联系兽医。\n"
                "No pet emergency keywords detected. "
                "Please still consult a veterinarian based on actual conditions."
            )
        return 0

    input_dir = _resolve_input_dir(args)
    if input_dir is None:
        raise SystemExit(
            "Input directory not found. Use --input to specify a directory, "
            "or use --mode knowledge/emergency for non-report workflows."
        )
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    output_dir = _resolve_output_dir(args)
    vault_dir = _resolve_vault_dir(args)

    run_pipeline(
        input_dir=input_dir,
        output_dir=output_dir,
        vault_dir=vault_dir,
        report_type=args.report_type,
        pet_name=args.pet_name,
        skip_pdf_compile=args.skip_pdf_compile,
        request_text=args.request,
        pdf_policy=args.pdf_policy,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
