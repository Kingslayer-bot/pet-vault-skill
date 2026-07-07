from __future__ import annotations

from pathlib import Path
import argparse
import re
import sys


PATTERNS = [
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"), "[REDACTED_PHONE]"),
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[REDACTED_PHONE]"),
    (re.compile(r"\b(?:policy|保单号?)\s*[:#：]?\s*[A-Z0-9-]{6,}\b", re.I), "[REDACTED_POLICY_NUMBER]"),
    (re.compile(r"\b(?:claim|理赔号?)\s*[:#：]?\s*[A-Z0-9-]{6,}\b", re.I), "[REDACTED_CLAIM_NUMBER]"),
    (re.compile(r"\b(?:\d[ -]?){12,19}\b"), "[REDACTED_PAYMENT_CARD]"),
    (re.compile(r"[\w\s#.-]{2,80}(?:Street|St\.|Road|Rd\.|Avenue|Ave\.|地址|小区|路|街|号)[\w\s#.-]{0,80}", re.I), "[REDACTED_ADDRESS]"),
]


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact basic personal information from text.")
    parser.add_argument("input", type=Path, nargs="?")
    args = parser.parse_args()
    if args.input:
        text = args.input.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    print(redact(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
