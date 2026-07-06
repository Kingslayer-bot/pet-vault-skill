from pathlib import Path
import argparse
import csv
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract simple pipe-delimited table-like lines from text.")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8", errors="replace")
    writer = csv.writer(sys.stdout)
    for line in text.splitlines():
        if "|" in line:
            writer.writerow([part.strip() for part in line.split("|")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
