from pathlib import Path
import argparse
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import render_latex


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--report-type", default="general")
    parser.add_argument("--pet-name", default="待确认")
    args = parser.parse_args()
    print(render_latex(args.markdown.read_text(encoding="utf-8"), args.report_type, args.pet_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
