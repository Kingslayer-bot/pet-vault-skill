from pathlib import Path
import argparse
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import compile_pdf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tex", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--skip", action="store_true")
    args = parser.parse_args()
    ok, _log = compile_pdf(args.tex, args.output_dir or args.tex.parent, skip=args.skip)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
