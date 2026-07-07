from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import petvault_core


SAMPLES = [
    ("Exam $80.00", "USD", "charge"),
    ("CareCredit Payment -$80.00", "USD", "payment"),
    ("Subtotal $1,150.35", "USD", "total"),
    ("Discount ($100.00)", "USD", "discount"),
    ("Paid $1,050.35", "USD", "payment"),
    ("检查费 ¥300.00", "CNY", "charge"),
    ("付款 -¥300.00", "CNY", "payment"),
    ("RMB 1200", "CNY", "charge"),
    ("CNY 1200", "CNY", "charge"),
    ("HKD 300", "HKD", "charge"),
    ("SGD 200", "SGD", "charge"),
    ("JPY 12000", "JPY", "charge"),
]


def validate() -> list[str]:
    errors: list[str] = []
    for sample, expected_currency, expected_kind in SAMPLES:
        mentions = petvault_core.parse_money_mentions(sample)
        if not mentions:
            errors.append(f"No amount parsed from {sample!r}")
            continue
        mention = mentions[0]
        if mention["currency"] != expected_currency:
            errors.append(f"{sample!r}: expected currency {expected_currency}, got {mention['currency']}")
        if mention["kind"] != expected_kind:
            errors.append(f"{sample!r}: expected kind {expected_kind}, got {mention['kind']}")
    materials = [{"source_file": "sample.txt", "text": "\n".join(sample for sample, _currency, _kind in SAMPLES)}]
    items = petvault_core.build_bill_items(materials)
    charge_total = sum(item["amount"] for item in items if item["kind"] == "charge" and item["currency"] == "USD")
    discount_total = sum(item["signed_amount"] for item in items if item["kind"] == "discount" and item["currency"] == "USD")
    if abs(charge_total - 80.0) > 0.001:
        errors.append(f"USD payment/discount leaked into charges: {charge_total}")
    if discount_total >= 0:
        errors.append(f"USD discounts should stay signed and separate: {discount_total}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PetVault billing amount classification.")
    parser.add_argument("skill_dir", type=Path, nargs="?")
    parser.parse_args()
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PetVault billing validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
