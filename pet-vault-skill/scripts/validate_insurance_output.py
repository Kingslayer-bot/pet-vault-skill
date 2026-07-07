from __future__ import annotations

from pathlib import Path
import argparse
import sys


FORBIDDEN = [
    "一定能赔", "一定可以理赔", "一定不能赔", "保险公司违法",
    "推荐你买", "建议购买", "帮你修改病历", "改一下病历",
    "规避既往症", "隐瞒既往症", "把时间写到等待期之后",
]

ALLOWED_EXAMPLES = [
    "需要检查条款后才能判断。",
    "基于上传保单估算，不代表最终审核。",
]


def check_text(text: str) -> list[str]:
    return [f"Forbidden insurance output: {phrase}" for phrase in FORBIDDEN if phrase in text]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate insurance output guardrails.")
    parser.add_argument("path", type=Path, nargs="?")
    parser.add_argument("--text")
    args = parser.parse_args()
    texts = list(ALLOWED_EXAMPLES)
    if args.text:
        texts.append(args.text)
    elif args.path and args.path.is_file():
        texts.append(args.path.read_text(encoding="utf-8"))
    errors = []
    for text in texts:
        errors.extend(check_text(text))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PetVault insurance output validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
