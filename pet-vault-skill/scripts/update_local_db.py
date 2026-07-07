from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import update_local_db


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--materials-index", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report-type", default="general")
    parser.add_argument("--pet-name", default="待确认")
    parser.add_argument("--pdf-status", default="skipped", choices=["compiled", "skipped", "failed"])
    parser.add_argument("--qa-status", default="unchecked", choices=["passed", "failed", "unchecked"])
    args = parser.parse_args()
    data = json.loads(args.materials_index.read_text(encoding="utf-8"))
    report_id = update_local_db(
        args.vault,
        args.report_type,
        args.pet_name,
        args.output,
        data,
        args.pdf_status,
        qa_status=args.qa_status,
    )
    print(report_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
