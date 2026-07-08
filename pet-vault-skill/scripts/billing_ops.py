"""billing_ops: Pure billing functions for amount parsing, item extraction, and totals."""
from __future__ import annotations

import re

BILL_CATEGORIES = {
    "检查": ["血常规", "生化", "x光", "x-ray", "b超", "超声", "ct", "检查", "化验"],
    "治疗": ["手术", "处置", "输液", "治疗", "住院", "清创"],
    "药品": ["药", "处方", "medication", "tablet", "capsule", "针剂"],
    "耗材": ["导管", "留置针", "敷料", "耗材", "纱布"],
    "服务": ["挂号", "诊疗", "护理", "服务", "会诊"],
}


def normalize_currency(token: str) -> str:
    """Normalize currency token to standard code."""
    value = token.strip().upper()
    if value in {"$", "US$", "USD"}:
        return "USD"
    if value in {"元", "RMB", "CNY", "¥", "￥"}:
        return "CNY"
    if value in {"HKD", "SGD", "JPY"}:
        return value
    return value or "UNKNOWN"


def parse_amount_number(raw_amount: str) -> float:
    """Parse amount string to float, handling negatives and commas."""
    value = raw_amount.strip()
    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1]
    value = value.replace(",", "")
    if value.startswith("-"):
        negative = True
        value = value[1:]
    amount = float(value)
    return -amount if negative else amount


def classify_money_kind(line: str, amount: float) -> str:
    """Classify money mention as charge/payment/discount/refund/balance/total."""
    lower_line = line.lower()
    if any(keyword in lower_line for keyword in ["discount", "折扣", "优惠", "adjustment"]):
        return "discount"
    if any(keyword in lower_line for keyword in ["refund", "退款", "退费"]):
        return "refund"
    if amount < 0 or any(keyword in lower_line for keyword in ["payment", "paid", "付款", "支付", "已付", "carecredit"]):
        return "payment"
    if any(keyword in lower_line for keyword in ["balance", "余额"]):
        return "balance"
    if any(keyword in lower_line for keyword in ["total", "subtotal", "合计", "总计", "总收费"]):
        return "total"
    return "charge"


def parse_money_mentions(text: str) -> list[dict]:
    """Extract all money mentions from text with currency, amount, and kind."""
    mentions = []
    patterns = [
        re.compile(
            r"(?P<currency>US\$|USD|RMB|CNY|HKD|SGD|JPY|\$|¥|￥)\s*(?P<amount>\(?-?\d[\d,]*(?:\.\d+)?\)?)",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"(?P<amount>\(?-?\d[\d,]*(?:\.\d+)?\)?)\s*(?P<currency>元|RMB|CNY|HKD|SGD|JPY|USD|US\$|\$|¥|￥)",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"\((?P<currency>US\$|USD|RMB|CNY|HKD|SGD|JPY|\$|¥|￥)\s*(?P<amount>-?\d[\d,]*(?:\.\d+)?)\)",
            flags=re.IGNORECASE,
        ),
    ]
    used_spans = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            if any(max(start, match.start()) < min(end, match.end()) for start, end in used_spans):
                continue
            try:
                amount = parse_amount_number(match.group("amount"))
            except ValueError:
                continue
            raw_match = match.group(0).strip()
            if raw_match.startswith("(") and raw_match.endswith(")") and amount > 0:
                amount = -amount
            used_spans.append((match.start(), match.end()))
            mentions.append(
                {
                    "amount": amount,
                    "currency": normalize_currency(match.group("currency")),
                    "raw": raw_match,
                    "start": match.start(),
                    "end": match.end(),
                    "kind": classify_money_kind(text, amount),
                }
            )
    return sorted(mentions, key=lambda item: item["start"])


def extract_amounts(text: str) -> list[float]:
    """Extract all amounts from text."""
    return [mention["amount"] for mention in parse_money_mentions(text)]


def build_bill_items(materials: list[dict]) -> list[dict]:
    """Build bill items from materials with amount, category, and source."""
    items = []
    for material in materials:
        text = material.get("text", "")
        for raw_line in text.splitlines():
            for segment in re.split(r"[;；]", raw_line):
                segment = segment.strip()
                if not segment:
                    continue
                for mention in parse_money_mentions(segment):
                    category = "其他"
                    lower_line = segment.lower()
                    if mention["kind"] == "payment":
                        category = "付款"
                    elif mention["kind"] == "discount":
                        category = "折扣"
                    elif mention["kind"] == "refund":
                        category = "退款"
                    elif mention["kind"] == "balance":
                        category = "余额"
                    elif mention["kind"] == "total":
                        category = "合计"
                    else:
                        for name, keywords in BILL_CATEGORIES.items():
                            if any(keyword.lower() in lower_line for keyword in keywords):
                                category = name
                                break
                    items.append({
                        "name": segment,
                        "amount": abs(mention["amount"]),
                        "signed_amount": mention["amount"],
                        "currency": mention["currency"],
                        "kind": mention["kind"],
                        "category": category,
                        "source_file": material["source_file"],
                    })
    return items


def format_money(amount: float, currency: str) -> str:
    """Format amount and currency into display string."""
    return f"{amount:.2f} {currency}"


def summarize_charge_totals(bill_items: list[dict]) -> dict[str, float]:
    """Summarize charge totals by currency from bill items."""
    totals: dict[str, float] = {}
    charge_items = [item for item in bill_items if item.get("kind") == "charge"]
    source_items = charge_items or [item for item in bill_items if item.get("kind") == "total"]
    for item in source_items:
        currency = item.get("currency") or "UNKNOWN"
        totals[currency] = totals.get(currency, 0.0) + float(item.get("amount") or 0.0)
    return totals


def format_currency_totals(totals: dict[str, float]) -> str:
    """Format currency totals into display string, returning '待确认' if empty."""
    if not totals:
        return "待确认"
    filtered = {c: a for c, a in totals.items() if abs(a) > 0.001}
    if not filtered:
        return "待确认"
    return "；".join(format_money(amount, currency) for currency, amount in sorted(filtered.items()))
