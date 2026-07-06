from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import UNKNOWN_TEXT, build_report_markdown


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("materials_index", type=Path)
    parser.add_argument("--report-type", default="general")
    parser.add_argument("--pet-name", default=UNKNOWN_TEXT)
    args = parser.parse_args()
    data = json.loads(args.materials_index.read_text(encoding="utf-8"))
    report, _warnings = build_report_markdown(args.report_type, args.pet_name, data)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
