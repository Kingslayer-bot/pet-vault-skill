from pathlib import Path
import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Placeholder renderer for Phase 1 PDF page checks.")
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    if not args.pdf.exists():
        print(f"missing: {args.pdf}")
        return 1
    print(f"indexed: {args.pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
