from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import pipeline_arg_parser, run_pipeline


def main() -> int:
    args = pipeline_arg_parser().parse_args()
    if not args.input.exists() or not args.input.is_dir():
        raise SystemExit(f"Input directory not found: {args.input}")
    run_pipeline(
        input_dir=args.input,
        output_dir=args.output,
        vault_dir=args.vault,
        report_type=args.report_type,
        pet_name=args.pet_name,
        skip_pdf_compile=args.skip_pdf_compile,
        request_text=args.request,
        pdf_policy=args.pdf_policy,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
