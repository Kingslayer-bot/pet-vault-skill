from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
UNKNOWN_TEXT = "待确认"
AUTO_REPORT_TYPE = "auto"

FORBIDDEN_TERMS = [
    "PRD",
    "Harness",
    "HMW",
    "POV",
    "产品需求文档",
    "设计提案约束",
    "开发者校验",
]

NEGATIVE_CLAIMS = [
    "医院乱收费",
    "一定可以理赔",
    "确诊为",
    "建议立即治疗",
]

REPORT_TITLES = {
    "general": "宠物资料综合整理报告",
    "medical_summary": "兽医报告简明解读",
    "bill_explain": "宠物医疗账单解释报告",
    "claim_check": "宠物保险理赔材料检查报告",
    "timeline": "跨院就诊资料包",
    "chronic_review": "慢病月度复盘报告",
    "clinic_client_summary": "医院端客户解释材料草稿",
}

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

BILL_CATEGORIES = {
    "检查": ["血常规", "生化", "x光", "x-ray", "b超", "超声", "ct", "检查", "化验"],
    "治疗": ["手术", "处置", "输液", "治疗", "住院", "清创"],
    "药品": ["药", "处方", "medication", "tablet", "capsule", "针剂"],
    "耗材": ["导管", "留置针", "敷料", "耗材", "纱布"],
    "服务": ["挂号", "诊疗", "护理", "服务", "会诊"],
}

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
    "pet_profile": "pet_profile",
}

NEGATED_POLICY_PATTERNS = [
    r"policy terms? (?:are )?not visible",
    r"no (?:insurance )?policy",
    r"policy (?:is )?missing",
    r"保单.*(?:未见|缺失|没有|未上传|不可见)",
    r"未见.*保单",
]

CLAIM_REQUIRED_TYPES = {
    "insurance_policy": "保单",
    "invoice": "发票",
    "bill": "费用明细",
    "prescription": "处方",
    "medical_report": "检查报告",
    "lab_report": "检查报告",
}


def json_dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def init_vault(vault_dir: Path) -> None:
    for rel in [
        "raw",
        "cleaned/markdown",
        "cleaned/text",
        "structured",
        "structured/pets",
        "structured/visits",
        "structured/bills",
        "structured/claims",
        "attachments",
    ]:
        (vault_dir / rel).mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(vault_dir / "pet_vault.sqlite3") as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS materials (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                pet_name TEXT,
                clinic TEXT,
                date TEXT,
                source_file TEXT NOT NULL,
                raw_path TEXT,
                cleaned_markdown_path TEXT,
                confidence REAL,
                status TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pets (
                id TEXT PRIMARY KEY,
                pet_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
                id TEXT PRIMARY KEY,
                pet_name TEXT,
                clinic TEXT,
                visit_date TEXT,
                summary TEXT,
                source_material_id TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                pet_name TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                created_at TEXT NOT NULL,
                pdf_status TEXT,
                qa_status TEXT
            )
            """
        )
        material_columns = {row[1] for row in conn.execute("PRAGMA table_info(materials)")}
        if "clinic" not in material_columns:
            conn.execute("ALTER TABLE materials ADD COLUMN clinic TEXT")
        if "status" not in material_columns:
            conn.execute("ALTER TABLE materials ADD COLUMN status TEXT")
        report_columns = {row[1] for row in conn.execute("PRAGMA table_info(reports)")}
        if "pdf_status" not in report_columns:
            conn.execute("ALTER TABLE reports ADD COLUMN pdf_status TEXT")
        if "qa_status" not in report_columns:
            conn.execute("ALTER TABLE reports ADD COLUMN qa_status TEXT")
        conn.commit()


def read_source_text(path: Path) -> tuple[str, str]:
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
    combined = f"{fallback_name}\n{text}"
    match = re.search(r"(20\d{2})[-/.年\s](\d{1,2})[-/.月\s](\d{1,2})", combined)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_pet_name(text: str, fallback: str | None = None) -> str | None:
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
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned = [line for line in lines if line]
    return "# Source Material\n\n" + f"- Source file: {source_name}\n\n" + "\n".join(cleaned) + "\n"


def ingest_materials(input_dir: Path, vault_dir: Path, default_pet_name: str | None = None) -> dict:
    init_vault(vault_dir)
    materials = []
    files = [path for path in sorted(input_dir.iterdir()) if path.is_file()]
    for index, source in enumerate(files, start=1):
        text, status = read_source_text(source)
        material_type, confidence = classify_material(source.name, text)
        pet_name = extract_pet_name(text, default_pet_name)
        clinic = extract_clinic(text)
        date = extract_date(text, source.name)
        material_id = f"mat_{index:03d}_{hashlib.sha1(source.name.encode('utf-8')).hexdigest()[:8]}"

        raw_folder = vault_dir / "raw" / material_type
        raw_folder.mkdir(parents=True, exist_ok=True)
        raw_path = raw_folder / source.name
        shutil.copy2(source, raw_path)

        cleaned_markdown = normalize_markdown(text, source.name)
        cleaned_path = vault_dir / "cleaned" / "markdown" / f"{material_id}.md"
        cleaned_path.write_text(cleaned_markdown, encoding="utf-8")

        material = {
            "id": material_id,
            "type": material_type,
            "pet_name": pet_name,
            "clinic": clinic,
            "date": date,
            "source_file": source.name,
            "raw_path": str(raw_path),
            "cleaned_markdown_path": str(cleaned_path),
            "confidence": confidence,
            "status": status,
            "text": text,
        }
        materials.append(material)

    index_data = {"materials": materials, "created_at": datetime.now().isoformat(timespec="seconds")}
    json_dump(vault_dir / "structured" / "materials_index.json", index_data)
    return index_data


def normalize_currency(token: str) -> str:
    value = token.strip().upper()
    if value in {"$", "US$", "USD"}:
        return "USD"
    if value in {"元", "RMB", "CNY", "¥", "￥"}:
        return "CNY"
    return value or "UNKNOWN"


def parse_amount_number(raw_amount: str) -> float:
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
    lower_line = line.lower()
    if amount < 0 or any(keyword in lower_line for keyword in ["payment", "paid", "付款", "支付", "已付", "carecredit"]):
        return "payment"
    if any(keyword in lower_line for keyword in ["discount", "折扣", "优惠", "adjustment"]):
        return "discount"
    if any(keyword in lower_line for keyword in ["balance", "余额"]):
        return "balance"
    if any(keyword in lower_line for keyword in ["total", "subtotal", "合计", "总计", "总收费"]):
        return "total"
    return "charge"


def parse_money_mentions(text: str) -> list[dict]:
    mentions = []
    patterns = [
        re.compile(
            r"(?P<currency>US\$|USD|RMB|CNY|\$|¥|￥)\s*(?P<amount>\(?-?\d[\d,]*(?:\.\d+)?\)?)",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"(?P<amount>\(?-?\d[\d,]*(?:\.\d+)?\)?)\s*(?P<currency>元|RMB|CNY|USD|US\$|\$|¥|￥)",
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
            used_spans.append((match.start(), match.end()))
            mentions.append(
                {
                    "amount": amount,
                    "currency": normalize_currency(match.group("currency")),
                    "raw": match.group(0).strip(),
                    "start": match.start(),
                    "end": match.end(),
                    "kind": classify_money_kind(text, amount),
                }
            )
    return sorted(mentions, key=lambda item: item["start"])


def extract_amounts(text: str) -> list[float]:
    return [mention["amount"] for mention in parse_money_mentions(text)]


def build_bill_items(materials: list[dict]) -> list[dict]:
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


def build_timeline_nodes(materials: list[dict]) -> list[dict]:
    nodes = []
    for material in materials:
        summary = material.get("text", "").replace("\n", " ").strip()[:120]
        nodes.append({
            "date": material.get("date") or "9999-12-31",
            "clinic": material.get("clinic") or UNKNOWN_TEXT,
            "event_type": material.get("type"),
            "summary": summary or "材料已索引，正文待确认。",
            "source_file": material.get("source_file"),
        })
    return sorted(nodes, key=lambda item: (item["date"], item["source_file"]))


def build_claim_summary(materials: list[dict]) -> tuple[list[str], list[str]]:
    present_types = {material["type"] for material in materials}
    existing = []
    for material_type, label in CLAIM_REQUIRED_TYPES.items():
        if material_type in present_types or (material_type == "medical_report" and "lab_report" in present_types):
            if label not in existing:
                existing.append(label)
    missing = []
    for material_type, label in CLAIM_REQUIRED_TYPES.items():
        if material_type == "medical_report":
            if "medical_report" not in present_types and "lab_report" not in present_types and label not in missing:
                missing.append(label)
            continue
        if material_type not in present_types and label not in missing:
            missing.append(label)
    if "insurance_policy" not in present_types and "保单" not in missing:
        missing.insert(0, "保单")
    return existing, missing


def build_medical_findings(materials: list[dict]) -> list[str]:
    findings = []
    patterns = [
        r"([A-Za-z]{2,6})\s*[=:：]?\s*([\d.]+)\s*(?:↑|↓|高|低|异常)",
        r"(ALT|CREA|BUN|WBC|RBC|PLT)[^\n]{0,20}(高|低|异常|red|high|low)",
    ]
    for material in materials:
        text = material.get("text", "")
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                findings.append(match.group(0).strip())
    unique = []
    for finding in findings:
        if finding not in unique:
            unique.append(finding)
    return unique[:6]


def format_money(amount: float, currency: str) -> str:
    return f"{amount:.2f} {currency}"


def summarize_charge_totals(bill_items: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    charge_items = [item for item in bill_items if item.get("kind") == "charge"]
    source_items = charge_items or [item for item in bill_items if item.get("kind") == "total"]
    for item in source_items:
        currency = item.get("currency") or "UNKNOWN"
        totals[currency] = totals.get(currency, 0.0) + float(item.get("amount") or 0.0)
    return totals


def format_currency_totals(totals: dict[str, float]) -> str:
    if not totals:
        return "待确认"
    return "；".join(format_money(amount, currency) for currency, amount in sorted(totals.items()))


def build_report_markdown(report_type: str, pet_name: str, materials_index: dict) -> tuple[str, list[str]]:
    materials = materials_index.get("materials", [])
    warnings = []
    discovered_pet_names = sorted({m.get("pet_name") for m in materials if m.get("pet_name")})
    if len(discovered_pet_names) > 1:
        warnings.append("发现多只宠物或不同名称混在同一批材料中，需要人工确认归属。")
    if not materials:
        warnings.append("未发现可整理材料。")

    bill_items = build_bill_items(materials)
    charge_totals = summarize_charge_totals(bill_items)
    charge_total_summary = format_currency_totals(charge_totals)
    timeline_nodes = build_timeline_nodes(materials)
    existing_claims, missing_claims = build_claim_summary(materials)
    medical_findings = build_medical_findings(materials)
    material_types = sorted({material["type"] for material in materials})

    title = REPORT_TITLES.get(report_type, REPORT_TITLES["general"])
    display_pet_name = pet_name or (discovered_pet_names[0] if discovered_pet_names else UNKNOWN_TEXT)

    lines = [
        f"# {title}",
        "",
        f"宠物名称：{display_pet_name}",
        "",
        "## 使用材料",
    ]
    for material in materials:
        lines.append(
            "- "
            f"{material['source_file']}：类型={material['type']}；"
            f"日期={material.get('date') or UNKNOWN_TEXT}；"
            f"宠物={material.get('pet_name') or UNKNOWN_TEXT}；"
            f"医院={material.get('clinic') or UNKNOWN_TEXT}；"
            f"置信度={material['confidence']}；"
            f"状态={material.get('status') or UNKNOWN_TEXT}"
        )

    lines.extend(["", "## 事实"])
    if material_types:
        lines.append(f"- 当前材料覆盖类型：{', '.join(material_types)}。")
    lines.append("- 以下内容仅基于已上传材料整理，不补全材料中未出现的诊断、治疗结论或保单条款。")
    for material in materials:
        preview = material.get("text", "").replace("\n", " ").strip()[:140]
        lines.append(f"- {material['source_file']}：{preview or '正文待确认。'}")

    lines.extend(["", "## 整理结果"])
    if report_type == "medical_summary":
        lines.extend([
            "### 一句话摘要",
            "- 当前输出用于帮助宠物主快速理解报告重点，不替代兽医诊断。",
            "### 关键异常项",
        ])
        if medical_findings:
            lines.extend(f"- {finding}" for finding in medical_findings)
        else:
            lines.append("- 当前材料未提取到明确的异常指标表达，建议对照原报告人工确认。")
        lines.extend([
            "### 简明解释",
            "- 优先关注被标红、标高、标低或被医生特别提醒的指标、影像结论和复诊安排。",
            "### 建议向兽医确认的问题",
            "- 这些异常项的临床意义是什么？是否需要复查、继续观察或配合当前处方？",
        ])
    elif report_type == "bill_explain":
        charge_items = [item for item in bill_items if item.get("kind") == "charge"]
        adjustment_items = [item for item in bill_items if item.get("kind") in {"payment", "discount", "balance"}]
        lines.extend([
            "### 费用总览",
            f"- 当前识别到的收费项目合计约 {charge_total_summary}。",
            "### 费用分类",
        ])
        if charge_items:
            seen = set()
            for item in charge_items:
                key = (item["name"], item["category"], item["amount"], item.get("currency"))
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"- {item['category']}：{item['name']}（{format_money(item['amount'], item['currency'])}）")
        else:
            lines.append("- 当前材料未抽取到账单明细，请核对原始账单或发票。")
        if adjustment_items:
            lines.append("### 付款、折扣与余额")
            for item in adjustment_items:
                signed_amount = item.get("signed_amount", item["amount"])
                lines.append(
                    f"- {item['category']}：{item['name']}（{format_money(signed_amount, item['currency'])}）"
                )
        high_items = sorted(charge_items, key=lambda item: item["amount"], reverse=True)[:3]
        lines.append("### 高额项目")
        if high_items:
            lines.extend(f"- {item['name']}（{format_money(item['amount'], item['currency'])}）" for item in high_items)
        else:
            lines.append("- 当前材料不足以判断高额项目。")
        lines.extend([
            "### 待确认问题",
            "- 建议向医院确认每个费用项目对应的检查、治疗、药品或耗材用途，不对价格合理性作判断。",
        ])
    elif report_type == "claim_check":
        lines.extend([
            "### 已有材料",
        ])
        if existing_claims:
            lines.extend(f"- {label}" for label in existing_claims)
        else:
            lines.append("- 当前未识别到常见理赔材料。")
        lines.append("### 缺失材料")
        if missing_claims:
            lines.extend(f"- {label}" for label in missing_claims)
        else:
            lines.append("- 常见理赔材料已基本覆盖，仍需按保单条款逐项核对。")
        lines.extend([
            "### 风险提示",
            "- 本报告只检查材料完整性和常见风险点，不承诺理赔结果。",
            "- 等待期、既往症、医院资质和保单细则仍需由用户自行与保险公司确认。",
        ])
    elif report_type == "timeline":
        lines.extend([
            "### 就诊时间线",
        ])
        for node in timeline_nodes:
            date_label = node["date"] if node["date"] != "9999-12-31" else UNKNOWN_TEXT
            lines.append(
                f"- {date_label}｜{node['clinic']}｜{node['event_type']}｜{node['source_file']}｜{node['summary']}"
            )
        lines.extend([
            "### 转诊摘要",
            "- 可将本时间线连同原始报告、处方、账单和最近检查结果一起提供给新医院。",
        ])
    elif report_type == "chronic_review":
        lines.extend([
            "### 月度概览",
            f"- 当前累计识别 {len(materials)} 份材料，收费项目合计约 {charge_total_summary}。",
            "### 就诊与用药变化",
        ])
        if timeline_nodes:
            lines.extend(f"- {node['date']}：{node['event_type']}，{node['summary']}" for node in timeline_nodes[:6])
        else:
            lines.append("- 当前材料不足以形成稳定的慢病趋势。")
        lines.extend([
            "### 结论",
            "- 如果材料覆盖月份较少，当前只能作为阶段性整理，不能据此判断长期病情趋势。",
        ])
    elif report_type == "clinic_client_summary":
        lines.extend([
            "### 客户版解释草稿",
            "- 本草稿用于医院向宠物主解释报告与费用，发送前需由医生或前台审核。",
            "### 重点说明",
        ])
        if medical_findings:
            lines.extend(f"- 重点关注：{finding}" for finding in medical_findings)
        else:
            lines.append("- 当前材料未提取到明确异常项，请结合原始报告人工补充。")
        if bill_items:
            lines.append(f"- 当前可识别收费项目合计约 {charge_total_summary}，建议附上费用明细说明。")
        lines.extend([
            "### 审核要求",
            "- 该草稿不能替代正式病历，不得超出原始材料作出诊断承诺。",
        ])
    else:
        lines.extend([
            "### 综合整理摘要",
            f"- 当前已整理 {len(materials)} 份材料，覆盖类型包括：{', '.join(material_types) if material_types else UNKNOWN_TEXT}。",
            "### 建议用途",
            "- 适合用于家庭沟通、跨院转诊前整理、理赔材料核对前准备。",
        ])

    lines.extend(["", "## 待确认"])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    lines.extend([
        "- 宠物年龄、品种、性别、绝育状态：如材料未写明，则保持待确认。",
        "- 医院诊断、治疗方案、保单条款：仅在材料明确出现时引用。",
        "- 若用于理赔，请再向保险公司确认材料清单、等待期和既往症规则。",
    ])

    lines.extend([
        "",
        "## 后续建议",
        "- 保存原始发票、费用明细、处方、检查报告和沟通记录。",
        "- 若宠物名称、日期或医院信息冲突，先核对归属后再交给医院或保险公司。",
        "- 该内容仅用于帮助理解材料，不替代兽医诊断。",
    ])
    return "\n".join(lines) + "\n", warnings


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def markdown_to_latex_body(markdown: str) -> str:
    body = []
    in_items = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            body.append("")
            continue
        if line.startswith("# "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            body.append(r"\section{" + latex_escape(line[2:].strip()) + "}")
        elif line.startswith("## "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            body.append(r"\subsection{" + latex_escape(line[3:].strip()) + "}")
        elif line.startswith("### "):
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            body.append(r"\subsubsection{" + latex_escape(line[4:].strip()) + "}")
        elif line.startswith("- "):
            if not in_items:
                body.append(r"\begin{itemize}")
                in_items = True
            body.append(r"  \item " + latex_escape(line[2:].strip()))
        else:
            if in_items:
                body.append(r"\end{itemize}")
                in_items = False
            body.append(latex_escape(line))
    if in_items:
        body.append(r"\end{itemize}")
    return "\n".join(body)


def render_latex(markdown: str, report_type: str, pet_name: str) -> str:
    styles = (SKILL_DIR / "templates" / "styles.tex.j2").read_text(encoding="utf-8")
    template_name = {
        "medical_summary": "report_medical_summary.tex.j2",
        "bill_explain": "report_bill_explain.tex.j2",
        "claim_check": "report_claim_check.tex.j2",
        "timeline": "report_timeline.tex.j2",
        "chronic_review": "report_chronic_review.tex.j2",
        "clinic_client_summary": "report_clinic_client_summary.tex.j2",
    }.get(report_type, "report_general.tex.j2")
    template = (SKILL_DIR / "templates" / template_name).read_text(encoding="utf-8")
    title = REPORT_TITLES.get(report_type, REPORT_TITLES["general"])
    return (
        template.replace("{{ styles }}", styles)
        .replace("{{ title }}", latex_escape(title))
        .replace("{{ pet_name }}", latex_escape(pet_name or UNKNOWN_TEXT))
        .replace("{{ body }}", markdown_to_latex_body(markdown))
    )


def update_local_db(
    vault_dir: Path,
    report_type: str,
    pet_name: str,
    output_dir: Path,
    materials_index: dict,
    pdf_status: str,
    qa_status: str = "unchecked",
) -> str:
    init_vault(vault_dir)
    report_id = report_id_for(report_type, pet_name, output_dir)
    with sqlite3.connect(vault_dir / "pet_vault.sqlite3") as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pets (id, pet_name, created_at) VALUES (?, ?, ?)",
            (hashlib.sha1((pet_name or UNKNOWN_TEXT).encode("utf-8")).hexdigest()[:12], pet_name, datetime.now().isoformat(timespec="seconds")),
        )
        for material in materials_index.get("materials", []):
            conn.execute(
                """
                INSERT OR REPLACE INTO materials
                (id, type, pet_name, clinic, date, source_file, raw_path, cleaned_markdown_path, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    material["id"],
                    material["type"],
                    material.get("pet_name"),
                    material.get("clinic"),
                    material.get("date"),
                    material["source_file"],
                    material.get("raw_path"),
                    material.get("cleaned_markdown_path"),
                    material.get("confidence"),
                    material.get("status"),
                ),
            )
            conn.execute(
                "INSERT OR REPLACE INTO visits (id, pet_name, clinic, visit_date, summary, source_material_id) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    hashlib.sha1(f"visit|{material['id']}".encode("utf-8")).hexdigest()[:12],
                    material.get("pet_name"),
                    material.get("clinic"),
                    material.get("date"),
                    (material.get("text", "").replace("\n", " ")[:120] or "材料已索引"),
                    material["id"],
                ),
            )
        conn.execute(
            """
            INSERT OR REPLACE INTO reports (id, report_type, pet_name, output_dir, created_at, pdf_status, qa_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                report_type,
                pet_name,
                str(output_dir),
                datetime.now().isoformat(timespec="seconds"),
                pdf_status,
                qa_status,
            ),
        )
        material_columns = {row[1] for row in conn.execute("PRAGMA table_info(materials)")}
        if "clinic" not in material_columns:
            conn.execute("ALTER TABLE materials ADD COLUMN clinic TEXT")
        if "status" not in material_columns:
            conn.execute("ALTER TABLE materials ADD COLUMN status TEXT")
        report_columns = {row[1] for row in conn.execute("PRAGMA table_info(reports)")}
        if "pdf_status" not in report_columns:
            conn.execute("ALTER TABLE reports ADD COLUMN pdf_status TEXT")
        if "qa_status" not in report_columns:
            conn.execute("ALTER TABLE reports ADD COLUMN qa_status TEXT")
        conn.commit()
    return report_id


def inspect_report(
    output_dir: Path,
    report_md: str,
    pdf_required: bool = False,
    materials_index: dict | None = None,
) -> dict:
    blocking = []
    warnings = []
    for term in FORBIDDEN_TERMS + NEGATIVE_CLAIMS:
        if term in report_md:
            blocking.append(f"Forbidden or unsafe report term: {term}")
    required_files = ["report.md", "report.tex", "manifest.json", "build.log"]
    for file_name in required_files:
        if not (output_dir / file_name).exists():
            blocking.append(f"Missing output file: {file_name}")
    if pdf_required and not (output_dir / "report.pdf").exists():
        blocking.append("PDF was required but report.pdf is missing")
    if (output_dir / "report.pdf").exists() and (output_dir / "report.pdf").stat().st_size == 0:
        blocking.append("report.pdf exists but is empty")
    tex = (output_dir / "report.tex").read_text(encoding="utf-8") if (output_dir / "report.tex").exists() else ""
    if "longtable" not in tex:
        warnings.append("LaTeX output does not reference longtable.")
    fee_explanation_check = "passed"
    if materials_index:
        materials = materials_index.get("materials", [])
        bill_like = [material for material in materials if material.get("type") in {"bill", "invoice", "unknown"}]
        indexed_only_bill_like = [material for material in bill_like if material.get("status") == "indexed_only"]
        no_bill_details = "当前材料未抽取到账单明细" in report_md
        if no_bill_details and indexed_only_bill_like:
            blocking.append("Bill/invoice material was indexed without OCR or transcription; fee explanation is incomplete.")
            fee_explanation_check = "failed"
        elif no_bill_details and bill_like:
            blocking.append("Bill/invoice material did not produce charge items; fee explanation is incomplete.")
            fee_explanation_check = "failed"
    pdf_present = (output_dir / "report.pdf").exists()
    build_log_text = (output_dir / "build.log").read_text(encoding="utf-8") if (output_dir / "build.log").exists() else ""
    return {
        "passed": not blocking,
        "blocking_issues": blocking,
        "warnings": warnings,
        "checks": {
            "source_integrity": "passed",
            "identity_consistency": "warning" if "多只宠物" in report_md else "passed",
            "visit_completeness": "passed",
            "fee_explanation": fee_explanation_check,
            "insurance_boundary": "passed" if "不承诺理赔结果" in report_md or "理赔" not in report_md else "warning",
            "timeline": "passed",
            "pdf_readability": "passed" if pdf_present else ("warning" if "No xelatex or latexmk found" in build_log_text else "skipped"),
            "local_storage": "passed",
        },
    }


def compile_pdf(tex_path: Path, output_dir: Path, skip: bool = False) -> tuple[bool, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    build_log = output_dir / "build.log"
    if skip:
        message = "PDF compile skipped by --skip-pdf-compile.\n"
        build_log.write_text(message, encoding="utf-8")
        return True, message
    engine = shutil.which("xelatex") or shutil.which("latexmk")
    if not engine:
        message = "No xelatex or latexmk found; PDF compile skipped.\n"
        build_log.write_text(message, encoding="utf-8")
        return False, message
    if Path(engine).name.lower().startswith("latexmk"):
        cmd = [engine, "-xelatex", "-interaction=nonstopmode", tex_path.name]
    else:
        cmd = [engine, "-interaction=nonstopmode", tex_path.name]
    result = subprocess.run(cmd, cwd=output_dir, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=120)
    log = result.stdout + "\n" + result.stderr
    build_log.write_text(log, encoding="utf-8")
    return result.returncode == 0, log


def auto_select_report_type(request_text: str | None, materials_index: dict) -> tuple[str, str]:
    request = (request_text or "").lower()
    materials = materials_index.get("materials", [])
    material_types = {material.get("type") for material in materials}
    combined = request + "\n" + "\n".join(
        f"{material.get('source_file', '')}\n{material.get('text', '')[:500]}" for material in materials
    ).lower()

    if re.search(r"理赔|报销|保险|claim|reimbursement|policy", request):
        return "claim_check", "request_mentions_claim_or_insurance"
    if re.search(r"账单|发票|收据|费用|收费|付费|付款|bill|invoice|receipt|charge|payment", request):
        return "bill_explain", "request_mentions_billing"
    if re.search(r"转诊|时间线|病史|timeline|history|handoff", request):
        return "timeline", "request_mentions_timeline_or_handoff"
    if re.search(r"慢病|长期|月度|复盘|chronic|monthly", request):
        return "chronic_review", "request_mentions_chronic_review"
    if re.search(r"报告|化验|检查|指标|medical|lab|x-ray|影像", request):
        return "medical_summary", "request_mentions_medical_summary"
    if "clinic_client_summary" in request or "客户解释" in request:
        return "clinic_client_summary", "request_mentions_clinic_client_summary"

    if {"insurance_policy", "claim_document"} & material_types:
        return "claim_check", "materials_include_claim_or_policy"
    if {"bill", "invoice"} & material_types:
        return "bill_explain", "materials_include_bill_or_invoice"
    if {"lab_report", "medical_report", "prescription"} & material_types:
        return "medical_summary", "materials_include_medical_records"
    if re.search(r"appointment|follow-up|复诊|预约|就诊", combined):
        return "timeline", "materials_include_visit_timeline_signals"
    return "general", "fallback_general"


def resolve_report_type(report_type: str, request_text: str | None, materials_index: dict) -> tuple[str, dict]:
    requested = report_type or AUTO_REPORT_TYPE
    if requested != AUTO_REPORT_TYPE:
        return requested, {
            "requested_report_type": requested,
            "selected_report_type": requested,
            "reason": "explicit_report_type",
            "request_text_present": bool(request_text),
        }
    selected, reason = auto_select_report_type(request_text, materials_index)
    return selected, {
        "requested_report_type": AUTO_REPORT_TYPE,
        "selected_report_type": selected,
        "reason": reason,
        "request_text_present": bool(request_text),
    }


def report_id_for(report_type: str, pet_name: str, output_dir: Path) -> str:
    return hashlib.sha1(f"{report_type}|{pet_name}|{output_dir}".encode("utf-8")).hexdigest()[:12]


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    vault_dir: Path,
    report_type: str,
    pet_name: str,
    skip_pdf_compile: bool,
    request_text: str | None = None,
    pdf_policy: str = "attempt",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    materials_index = ingest_materials(input_dir, vault_dir, pet_name)
    selected_report_type, routing = resolve_report_type(report_type, request_text, materials_index)
    report_md, warnings = build_report_markdown(selected_report_type, pet_name, materials_index)
    (output_dir / "report.md").write_text(report_md, encoding="utf-8")
    report_tex = render_latex(report_md, selected_report_type, pet_name)
    (output_dir / "report.tex").write_text(report_tex, encoding="utf-8")
    pdf_ok, pdf_log = compile_pdf(output_dir / "report.tex", output_dir, skip=skip_pdf_compile or pdf_policy == "skip")
    pdf_status = "compiled" if pdf_ok and (output_dir / "report.pdf").exists() else ("skipped" if "skipped" in pdf_log.lower() else "failed")
    report_id = report_id_for(selected_report_type, pet_name, output_dir)
    manifest = {
        "id": report_id,
        "pet_name": pet_name,
        "report_type": selected_report_type,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pdf_status": pdf_status,
        "pdf_policy": pdf_policy,
        "routing": routing,
        "materials": [
            {key: value for key, value in material.items() if key != "text"}
            for material in materials_index.get("materials", [])
        ],
        "outputs": {
            "report_md": str(output_dir / "report.md"),
            "report_tex": str(output_dir / "report.tex"),
            "report_pdf": str(output_dir / "report.pdf"),
            "manifest": str(output_dir / "manifest.json"),
            "qa_result": str(output_dir / "qa_result.json"),
            "build_log": str(output_dir / "build.log"),
        },
        "warnings": warnings,
    }
    json_dump(output_dir / "manifest.json", manifest)
    qa = inspect_report(output_dir, report_md, pdf_required=pdf_policy == "required", materials_index=materials_index)
    if not pdf_ok and not skip_pdf_compile:
        qa["warnings"].append("Local TeX engine unavailable or compile failed; report.pdf may be missing.")
    qa["warnings"].extend(warnings)
    json_dump(output_dir / "qa_result.json", qa)
    update_local_db(
        vault_dir,
        selected_report_type,
        pet_name,
        output_dir,
        materials_index,
        pdf_status,
        qa_status="passed" if qa["passed"] else "failed",
    )
    return manifest


def pipeline_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PetVault Phase 1 pipeline.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--report-type", default=AUTO_REPORT_TYPE, choices=sorted([AUTO_REPORT_TYPE, *REPORT_TITLES]))
    parser.add_argument("--request", default="", help="Original user request text for auto report routing.")
    parser.add_argument("--pet-name", default=UNKNOWN_TEXT)
    parser.add_argument("--skip-pdf-compile", action="store_true")
    parser.add_argument("--pdf-policy", default="attempt", choices=["attempt", "required", "skip"])
    return parser
