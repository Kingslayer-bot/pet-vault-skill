"""material_ops: Low-risk material understanding helpers.

Contains classification, extraction, and normalization functions for pet medical materials.
All functions are pure or have simple file I/O only.
"""
from __future__ import annotations

import re
from pathlib import Path

MATERIAL_LABELS = [
    ("invoice", ["发票", "收据", "invoice", "receipt"]),
    ("bill", ["账单", "费用", "收费", "bill", "expense", "charge", "payment"]),
    ("insurance_policy", ["保单", "保险", "policy"]),
    ("claim_document", ["理赔", "报销", "claim"]),
    ("lab_report", ["化验", "血常规", "生化", "尿检", "lab", "alt", "crea", "bun"]),
    ("medical_report", ["检查报告", "影像", "x光", "x-ray", "超声", "b超", "report", "imaging"]),
    ("prescription", ["处方", "用药", "药品", "prescription", "medication"]),
    ("appointment", ["预约", "复诊", "就诊", "appointment", "follow-up"]),
    ("clinic_communication", ["沟通", "医生说", "微信", "communication"]),
    ("pet_profile", ["宠物", "品种", "年龄", "绝育", "profile"]),
]

EXPLICIT_TYPE_ALIASES = {
    "invoice": "invoice",
    "receipt": "invoice",
    "发票": "invoice",
    "收据": "invoice",
    "bill": "bill",
    "expense": "bill",
    "账单": "bill",
    "费用": "bill",
    "insurance_policy": "insurance_policy",
    "policy": "insurance_policy",
    "保单": "insurance_policy",
    "claim_document": "claim_document",
    "claim": "claim_document",
    "理赔": "claim_document",
    "lab_report": "lab_report",
    "lab": "lab_report",
    "medical_report": "medical_report",
    "prescription": "prescription",
    "appointment": "appointment",
    "clinic_communication": "clinic_communication",
    "communication": "clinic_communication",
    "沟通": "clinic_communication",
    "pet_profile": "pet_profile",
}

NEGATED_POLICY_PATTERNS = [
    r"policy terms? (?:are )?not visible",
    r"no (?:insurance )?policy",
    r"policy (?:is )?missing",
    r"保单.*(?:未见|缺失|没有|未上传|不可见)",
    r"未见.*保单",
]


def read_source_text(path: Path) -> tuple[str, str]:
    """Read source text from file, detecting encoding."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json", ".tex"}:
        raw = path.read_bytes()
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
            try:
                return raw.decode(encoding), "extracted"
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace"), "encoding_repaired"
    return f"[待确认] Phase 1 已索引文件，但未解析该格式正文：{path.name}", "indexed_only"


def explicit_material_type(text: str) -> str | None:
    """Check for explicit material type hints in text."""
    for line in text.splitlines()[:12]:
        normalized = line.strip().lower()
        if not normalized:
            continue
        if "material type" not in normalized and "材料类型" not in normalized:
            continue
        for alias, material_type in EXPLICIT_TYPE_ALIASES.items():
            if alias.lower() in normalized:
                return material_type
    return None


def classify_material(name: str, text: str) -> tuple[str, float]:
    """Classify material type from filename and text content."""
    explicit_type = explicit_material_type(text)
    if explicit_type:
        return explicit_type, 0.98

    haystack = f"{name}\n{text}".lower()
    file_name = name.lower()
    scores = {material_type: 0.0 for material_type, _labels in MATERIAL_LABELS}
    best_type = "unknown"
    for material_type, labels in MATERIAL_LABELS:
        for label in labels:
            label_lower = label.lower()
            if label_lower in haystack:
                scores[material_type] += 1.0
            if label_lower in file_name:
                scores[material_type] += 2.0

    if re.search(r"\b(invoice|receipt)\b|发票号|invoice no|balance due|amount due", haystack):
        scores["invoice"] += 3.0
    if re.search(r"账单|费用明细|\bbill\b|\bcharge\b|收费|付款|payment", haystack):
        scores["bill"] += 2.5
    if re.search(r"policy number|coverage|deductible|premium|waiting period|保单号|免赔额|等待期|承保", haystack):
        scores["insurance_policy"] += 3.0
    if re.search(r"claim form|claim packet|reimbursement|理赔申请|报销材料", haystack):
        scores["claim_document"] += 2.5
    if any(re.search(pattern, haystack) for pattern in NEGATED_POLICY_PATTERNS):
        scores["insurance_policy"] = max(0.0, scores["insurance_policy"] - 4.0)

    best_type, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0:
        return "unknown", 0.35
    confidence = min(0.45 + best_score * 0.12, 0.95)
    return best_type, round(confidence, 2)


def extract_date(text: str, fallback_name: str = "") -> str | None:
    """Extract date from text or filename."""
    combined = f"{fallback_name}\n{text}"
    match = re.search(r"(20\d{2})[-/.年\s](\d{1,2})[-/.月\s](\d{1,2})", combined)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_pet_name(text: str, fallback: str | None = None) -> str | None:
    """Extract pet name from text."""
    patterns = [
        r"宠物[：: ]+([A-Za-z0-9_\-\u4e00-\u9fff]+)",
        r"宠物名称[：: ]+([A-Za-z0-9_\-\u4e00-\u9fff]+)",
        r"pet[：: ]+([A-Za-z0-9_\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return fallback


def extract_clinic(text: str) -> str | None:
    """Extract clinic name from text."""
    patterns = [
        r"医院[：: ]+([^\n，,;；]+)",
        r"诊所[：: ]+([^\n，,;；]+)",
        r"clinic[：: ]+([^\n,;]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def normalize_markdown(text: str, source_name: str) -> str:
    """Normalize raw text into stable Markdown."""
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned = [line for line in lines if line]
    return "# Source Material\n\n" + f"- Source file: {source_name}\n\n" + "\n".join(cleaned) + "\n"
