from pathlib import Path
import argparse
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from petvault_core import classify_material


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8", errors="replace")
    material_type, confidence = classify_material(args.file.name, text)
    print(f"{material_type}\t{confidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
