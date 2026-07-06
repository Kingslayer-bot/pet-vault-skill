from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import inspect_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--pdf-required", action="store_true")
    args = parser.parse_args()
    report = (args.output_dir / "report.md").read_text(encoding="utf-8", errors="replace")
    result = inspect_report(args.output_dir, report, pdf_required=args.pdf_required)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
