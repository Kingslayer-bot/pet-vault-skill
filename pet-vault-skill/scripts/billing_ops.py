"""billing_ops: Pure billing functions for amount parsing, item extraction, totals, and classification."""
from __future__ import annotations

import re

BILL_CATEGORIES = {
    "检查": ["血常规", "生化", "x光", "x-ray", "b超", "超声", "ct", "检查", "化验"],
    "治疗": ["手术", "处置", "输液", "治疗", "住院", "清创"],
    "药品": ["药", "处方", "medication", "tablet", "capsule", "针剂"],
    "耗材": ["导管", "留置针", "敷料", "耗材", "纱布"],
    "服务": ["挂号", "诊疗", "护理", "服务", "会诊"],
}

# User-facing category labels for bill_explain report
USER_FACING_CATEGORIES = {
    "examination": "检查类",
    "infusion_drugs": "输液/注射药品类",
    "oral_drugs": "口服药品类",
    "injection_treatment": "注射治疗类",
    "diet": "处方粮/食品类",
    "service": "服务类",
    "other": "其他",
}

# Noise patterns — text that is not a real bill item
_NOISE_PATTERNS = [
    re.compile(r"\d{2}[-/]\d{2}\s+\d{1,2}:\d{2}"),  # timestamps like "01-16 18:06" or "01/16 18:06"
    re.compile(r"printed?\s+at", re.IGNORECASE),
    re.compile(r"page\s+\d+", re.IGNORECASE),
    re.compile(r"invoice\s*#?\s*\d+", re.IGNORECASE),
    re.compile(r"^date\s*:", re.IGNORECASE),
    re.compile(r"^pet\s*:", re.IGNORECASE),
    re.compile(r"^clinic\s*:", re.IGNORECASE),
    re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}"),  # full datetime
]

# Clearly identifiable medical item patterns
_CLEAR_MEDICAL_PATTERNS = [
    re.compile(r"examination|consult|consultation", re.IGNORECASE),
    re.compile(r"x-ray|xray|x ray|radiograph|orthopedic", re.IGNORECASE),
    re.compile(r"cbc|chem|lytes|ua|blood|urine|lab|ultrasound|idexx|heska", re.IGNORECASE),
    re.compile(r"sedation|sedative|anesthesia", re.IGNORECASE),
    re.compile(r"inj|inject|injection|shot", re.IGNORECASE),
    re.compile(r"oral|solution|tablet|capsule|mg/ml|mg\.?/ml", re.IGNORECASE),
    re.compile(r"biohazard|service fee", re.IGNORECASE),
    re.compile(r"solensia|gabapentin|ketamine|butorphanol|dexmeded|revertidine", re.IGNORECASE),
    re.compile(r"purina|royal canin|prescription diet|ha feline", re.IGNORECASE),
    re.compile(r"血常规|生化|b超|超声|x光|ct检查|化验", re.IGNORECASE),
    re.compile(r"处方药|口服药|注射液|针剂", re.IGNORECASE),
    re.compile(r"declined|拒绝", re.IGNORECASE),
]

# Uncertain name patterns — items where the name itself is unclear
_UNCERTAIN_NAME_PATTERNS = [
    re.compile(r"不明|未知|不清|不清楚|不确定|unknown|unclear|other", re.IGNORECASE),
]


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
    """Build bill items from materials with amount, category, and source.

    Also includes non-monetary segments that match noise patterns as zero-amount
    items so they can be flagged in the report.
    """
    items = []
    seen_segments: set[str] = set()

    # Patterns for summary/totals lines that should not be individual items
    _summary_patterns = [
        re.compile(r"^-?\s*(old\s+balance|new\s+balance|charges|payments|discount|total|subtotal)\s*:", re.IGNORECASE),
        re.compile(r"^-?\s*payment\s+method\s+shown", re.IGNORECASE),
        re.compile(r"^(合计|已支付|已付|余额|旧余额|新余额|折扣|减免)\s*[:：]?\s*[\d.,元]+\s*(元|$)", re.IGNORECASE),
        re.compile(r"^-?\s*(Total\s+charges|Paid|Balance|Discount)\s*[:：]?\s*[¥$￥]?\s*[\d.,]+", re.IGNORECASE),
    ]

    for material in materials:
        text = material.get("text", "")
        for raw_line in text.splitlines():
            for segment in re.split(r"[;；]", raw_line):
                segment = segment.strip()
                if not segment:
                    continue
                # Skip summary/totals lines
                if any(p.search(segment) for p in _summary_patterns):
                    continue
                # Clean Markdown table formatting but preserve amount text
                cleaned = re.sub(r"^\|+\s*", "", segment)
                cleaned = re.sub(r"\s*\|+$", "", cleaned)
                # For table rows like "03-28-26 | Examination - Consult | USD 80.00"
                # Parse money from the full text first to preserve amounts
                mentions = parse_money_mentions(cleaned)
                if mentions:
                    # Extract description name from table row if applicable
                    item_name = cleaned
                    if "|" in cleaned:
                        cells = [c.strip() for c in cleaned.split("|")]
                        desc_parts = []
                        for cell in cells:
                            if re.match(r"^\d{2}[-/]\d{2}[-/]\d{2}$", cell):
                                continue
                            if re.match(r"^(USD|CNY|RMB|\$|¥)\s*$", cell, re.IGNORECASE):
                                continue
                            if re.match(r"^[\d.,]+$", cell):
                                continue
                            if cell:
                                desc_parts.append(cell)
                        if desc_parts:
                            item_name = " - ".join(desc_parts)
                        # Strip trailing price from item name
                        item_name = re.sub(r"\s*-\s*(?:USD|CNY|RMB|\$|¥)\s*[\d.,]+\s*$", "", item_name)
                        item_name = re.sub(r"\s*-\s*USD\s*[\d.,]+\s*$", "", item_name, flags=re.IGNORECASE)
                        item_name = item_name.strip(" -")
                    for mention in mentions:
                        category = "其他"
                        lower_line = cleaned.lower()
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
                            "name": item_name,
                            "amount": abs(mention["amount"]),
                            "signed_amount": mention["amount"],
                            "currency": mention["currency"],
                            "kind": mention["kind"],
                            "category": category,
                            "source_file": material["source_file"],
                        })
                    seen_segments.add(cleaned)
                else:
                    # Non-monetary segment — check if it's noise (timestamp, etc.)
                    for pattern in _NOISE_PATTERNS:
                        if pattern.search(cleaned) and cleaned not in seen_segments:
                            items.append({
                                "name": cleaned,
                                "amount": 0,
                                "signed_amount": 0,
                                "currency": material.get("currency", "CNY"),
                                "kind": "charge",
                                "category": "其他",
                                "source_file": material["source_file"],
                            })
                            seen_segments.add(cleaned)
                            break
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


# ---------------------------------------------------------------------------
# Confidence scoring and item classification for user-facing reports
# ---------------------------------------------------------------------------

def classify_item_confidence(item: dict) -> str:
    """Classify a bill item's confidence level.

    Returns: 'high', 'medium', 'low', or 'noise'.
    """
    name = item.get("name", "").strip()
    amount = item.get("amount", 0)
    kind = item.get("kind", "charge")

    # Noise: timestamps, page numbers, print info
    if kind in {"total", "payment", "discount", "balance", "refund"}:
        return "medium"
    for pattern in _NOISE_PATTERNS:
        if pattern.search(name):
            return "noise"

    # High: clearly identifiable medical items
    for pattern in _CLEAR_MEDICAL_PATTERNS:
        if pattern.search(name):
            return "high"

    # Low: uncertain name patterns
    for pattern in _UNCERTAIN_NAME_PATTERNS:
        if pattern.search(name):
            return "low"

    # Medium: recognized name but unclear exact purpose
    if len(name) > 5 and any(c.isalpha() for c in name):
        return "medium"

    # Low: very short or garbled names
    return "low"


def classify_item_type(item: dict) -> str:
    """Classify a bill item as 'recognized', 'uncertain', or 'noise'."""
    confidence = classify_item_confidence(item)
    if confidence == "noise":
        return "noise"
    if confidence in ("high", "medium"):
        return "recognized"
    return "uncertain"


def classify_user_facing_category(item: dict) -> str:
    """Classify a bill item into a user-facing category string."""
    name = item.get("name", "").lower()
    kind = item.get("kind", "charge")
    if kind in {"payment", "discount", "refund", "balance"}:
        return "other"
    # Examination / consultation
    if re.search(r"examination|consult|consultation|问诊|挂号|诊", name):
        return "examination"
    # Imaging / lab tests
    if re.search(r"x-ray|xray|x ray|radiograph|orthopedic|cbc|chem|lytes|ua|blood|urine|lab|ultrasound|idexx|heska|血常规|生化|b超|超声|ct|x光|检查|化验|影像", name):
        return "examination"
    # Sedation / anesthesia (treat as examination-related)
    if re.search(r"sedation|sedative|anesthesia|镇静|麻醉", name):
        return "examination"
    # Injection drugs
    if re.search(r"inj|inject|injection|shot|针剂|注射", name):
        if re.search(r"solensia|gabapentin|ketamine|butorphanol|dexmeded|revertidine", name):
            return "injection_treatment"
        return "infusion_drugs"
    # Oral drugs (check before injection to avoid "or" in "oral" matching "inj")
    if re.search(r"oral\s|oral$|oral solution|solution|tablet|capsule|mg/ml|口服|片剂|胶囊", name):
        return "oral_drugs"
    # Diet / food
    if re.search(r"purina|royal canin|prescription diet|处方粮|food|feline.*\d+\s*lb", name):
        return "diet"
    # Service fee
    if re.search(r"service fee|biohazard|服务费|挂号费|处置费", name):
        return "service"
    return "other"


def compute_amount_summary(bill_items: list[dict]) -> dict:
    """Compute amount summary for recognized, uncertain, and noise items.

    Returns dict with keys: total, recognized, uncertain, noise, currency, recognized_pct.
    """
    currency = "USD"
    total = 0.0
    recognized = 0.0
    uncertain = 0.0
    noise = 0.0

    for item in bill_items:
        kind = item.get("kind", "charge")
        if kind in {"total", "payment", "discount", "balance", "refund"}:
            continue
        amount = abs(item.get("amount", 0))
        item_currency = item.get("currency", "USD")
        if item_currency != currency:
            currency = item_currency
        total += amount
        item_type = classify_item_type(item)
        if item_type == "recognized":
            recognized += amount
        elif item_type == "uncertain":
            uncertain += amount
        else:
            noise += amount

    recognized_pct = (recognized / total * 100) if total > 0 else 0.0
    uncertain_pct = (uncertain / total * 100) if total > 0 else 0.0
    noise_pct = (noise / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "recognized": recognized,
        "uncertain": uncertain,
        "noise": noise,
        "currency": currency,
        "recognized_pct": round(recognized_pct, 1),
        "uncertain_pct": round(uncertain_pct, 1),
        "noise_pct": round(noise_pct, 1),
    }


def determine_report_status(amount_summary: dict) -> str:
    """Determine the report status label based on amount summary."""
    uncertain_pct = amount_summary.get("uncertain_pct", 0)
    noise_pct = amount_summary.get("noise_pct", 0)
    combined = uncertain_pct + noise_pct
    if combined > 50:
        return "不建议作为最终解释"
    if combined > 20:
        return "关键项目待核实"
    if combined > 0:
        return "部分待确认"
    return "可归档"


def compute_category_summary(bill_items: list[dict]) -> list[dict]:
    """Compute per-category amount summary for user-facing display.

    Categories are mutually exclusive: each item contributes to exactly one category.
    Uncertain and noise items get their own categories, NOT mixed into "其他".
    """
    amount_summary = compute_amount_summary(bill_items)
    total = amount_summary["total"]
    currency = amount_summary["currency"]

    cat_amounts: dict[str, float] = {}
    cat_items: dict[str, int] = {}
    for item in bill_items:
        kind = item.get("kind", "charge")
        if kind in {"total", "payment", "discount", "balance", "refund"}:
            continue
        item_type = classify_item_type(item)
        amount = abs(item.get("amount", 0))
        if item_type == "noise":
            cat_amounts["noise"] = cat_amounts.get("noise", 0) + amount
            cat_items["noise"] = cat_items.get("noise", 0) + 1
        elif item_type == "uncertain":
            cat_amounts["uncertain"] = cat_amounts.get("uncertain", 0) + amount
            cat_items["uncertain"] = cat_items.get("uncertain", 0) + 1
        else:
            cat = classify_user_facing_category(item)
            cat_amounts[cat] = cat_amounts.get(cat, 0) + amount
            cat_items[cat] = cat_items.get(cat, 0) + 1

    categories = []
    label_map = {
        "examination": "检查类",
        "infusion_drugs": "输液/注射药品类",
        "oral_drugs": "口服药品类",
        "injection_treatment": "注射治疗类",
        "diet": "处方粮/食品类",
        "service": "服务类",
        "other": "其他",
        "noise": "疑似误识别项目",
        "uncertain": "待核实项目",
    }
    explanation_map = {
        "examination": "检查、化验、影像相关费用",
        "infusion_drugs": "注射类药品相关费用",
        "oral_drugs": "口服药品相关费用",
        "injection_treatment": "注射治疗类费用",
        "diet": "处方粮、营养食品相关费用",
        "service": "挂号、诊疗、服务费等",
        "other": "其他费用",
        "noise": "可能不是实际收费项目",
        "uncertain": "OCR 不清或项目含义不明",
    }

    for cat_key in ["examination", "infusion_drugs", "oral_drugs", "injection_treatment",
                     "diet", "service", "other", "uncertain", "noise"]:
        amount = cat_amounts.get(cat_key, 0)
        if amount <= 0:
            continue
        pct = round(amount / total * 100, 1) if total > 0 else 0
        label = label_map.get(cat_key, cat_key)
        status = "已识别"
        if cat_key == "noise":
            status = "疑似误识别"
        elif cat_key == "uncertain":
            status = "待核实"
        categories.append({
            "category_label": label,
            "amount": amount,
            "pct": pct,
            "status": status,
            "explanation": explanation_map.get(cat_key, ""),
            "item_count": cat_items.get(cat_key, 0),
        })

    return categories


def format_amount_display(amount: float, currency: str) -> str:
    """Format amount with ¥ or $ prefix for display."""
    if currency in ("CNY", "RMB"):
        return f"¥{amount:,.2f}"
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"
