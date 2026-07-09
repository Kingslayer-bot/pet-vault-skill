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

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
UNKNOWN_TEXT = "待确认"
AUTO_REPORT_TYPE = "auto"

# Compatibility imports from extracted modules
from latex_ops import (  # noqa: E402
    latex_escape,
    _convert_inline_latex,
    _is_table_line,
    _is_table_separator,
    _parse_table_rows,
    _table_to_longtable,
    _is_table_separator_str,
    markdown_to_latex_body,
    COVER_TITLES,
    render_latex as _render_latex,
)
from manifest_ops import (  # noqa: E402
    INTERNAL_TYPE_MAP,
    report_id_for,
    build_internal_manifest,
    build_user_manifest,
)
from billing_ops import (  # noqa: E402
    BILL_CATEGORIES,
    normalize_currency,
    parse_amount_number,
    classify_money_kind,
    parse_money_mentions,
    extract_amounts,
    build_bill_items,
    format_money,
    summarize_charge_totals,
    format_currency_totals,
    classify_item_confidence,
    classify_item_type,
    classify_user_facing_category,
    compute_amount_summary,
    determine_report_status,
    compute_category_summary,
    format_amount_display,
)
from material_ops import (  # noqa: E402
    MATERIAL_LABELS,
    EXPLICIT_TYPE_ALIASES,
    NEGATED_POLICY_PATTERNS,
    read_source_text,
    explicit_material_type,
    classify_material,
    extract_date,
    extract_pet_name,
    extract_clinic,
    normalize_markdown,
)
from pdf_ops import (  # noqa: E402
    compile_pdf,
    inspect_report,
)
from bill_render_ops import (  # noqa: E402
    render_reconstructed_bill_section,
    render_bill_summary_text,
)

_KB_RULES_CACHE: dict[str, dict] = {}


def load_kb_rules(reload: bool = False) -> dict[str, dict]:
    global _KB_RULES_CACHE
    if _KB_RULES_CACHE and not reload:
        return _KB_RULES_CACHE
    rules: dict[str, dict] = {}
    rules_dir = SKILL_DIR / "kb" / "rules"
    if not rules_dir.exists():
        return rules
    for yaml_file in sorted(rules_dir.glob("*.yaml")):
        try:
            if _yaml is None:
                continue
            text = yaml_file.read_text(encoding="utf-8")
            data = _yaml.safe_load(text) or {}
            rules[yaml_file.stem] = data
        except Exception:
            continue
    _KB_RULES_CACHE = rules
    return rules


def load_kb_ontology() -> dict:
    try:
        if _yaml is None:
            return {}
        path = SKILL_DIR / "kb" / "ontology.yaml"
        if path.exists():
            return _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}


def _get_emergency_terms() -> list[str]:
    terms: list[str] = []
    rules = load_kb_rules()
    routing = rules.get("routing", {})
    emergency_cfg = routing.get("emergency_boundary", {})
    triggers = emergency_cfg.get("triggers", {})
    raw_terms = triggers.get("terms", [])
    if isinstance(raw_terms, list):
        terms.extend(raw_terms)
    medical = rules.get("medical_safety", {})
    red_flags = medical.get("red_flags", [])
    if isinstance(red_flags, list):
        terms.extend(red_flags)
    return terms


def detect_emergency(request_text: str) -> bool:
    if not request_text:
        return False
    text_lower = request_text.lower()
    for term in _get_emergency_terms():
        if str(term).lower().replace("_", " ") in text_lower:
            return True
    hardcoded = [
        r"中毒", r"毒素", r"毒物", r"吃了.*(巧克力|葡萄|洋葱|大蒜|百合|老鼠|蟑螂|杀虫剂|清洁剂|药品)",
        r"抽搐", r"痉挛", r"癫痫", r"seizure",
        r"呼吸困难", r"喘不上气", r"breathing\s+difficulty",
        r"尿不出来", r"无法排尿", r"尿闭", r"can['\u2019]t\s+urinate",
        r"持续呕吐", r"persistent\s+vomiting",
        r"严重外伤", r"大出血", r"severe\s+trauma",
        r"晕倒", r"昏迷", r"不醒", r"collapse",
        r"腹胀", r"胃胀", r"bloat",
        r"吞了.*异物", r"误食", r"foreign\s+body",
        r"木糖醇", r"xylitol",
    ]
    for pattern in hardcoded:
        if re.search(pattern, text_lower):
            return True
    return False


REPORT_TITLES = {
    "general": "宠物资料综合整理报告",
    "medical_summary": "兽医报告简明解读",
    "bill_explain": "宠物医疗账单解释报告",
    "claim_check": "宠物保险理赔材料检查报告",
    "timeline": "跨院就诊资料包",
    "chronic_review": "慢病月度复盘报告",
    "clinic_client_summary": "医院端客户解释材料草稿",
}

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


def _clean_archive_item_names(items: list[dict], categories) -> str:
    """Clean and join item names for archive card display."""
    if isinstance(categories, str):
        categories = (categories,)
    names = set()
    for item in items:
        if classify_user_facing_category(item) in categories:
            name = item.get("name", "")
            # Clean: remove pipe chars, prefix, trailing amount
            name = name.replace("|", " ").strip()
            name = re.sub(r"^编号\d+\s*", "", name).strip()
            name = re.sub(r"\s*\d+\s*元\s*$", "", name).strip()
            # Take first 25 chars
            if len(name) > 25:
                name = name[:22] + "..."
            names.add(name)
    return "、".join(sorted(names)) if names else UNKNOWN_TEXT


def _build_bill_explain_report(
    bill_items: list[dict],
    charge_totals: dict[str, float],
    materials: list[dict],
    display_pet_name: str,
) -> list[str]:
    """Build user-facing bill explanation report markdown (v4 structure)."""
    lines: list[str] = []
    amount_summary = compute_amount_summary(bill_items)
    report_status = determine_report_status(amount_summary)
    currency = amount_summary["currency"]
    total = amount_summary["total"]

    # Extract metadata from materials
    visit_date = UNKNOWN_TEXT
    clinic = UNKNOWN_TEXT
    city = UNKNOWN_TEXT
    pet_species = UNKNOWN_TEXT
    pet_breed = UNKNOWN_TEXT
    pet_age = UNKNOWN_TEXT
    pet_weight = UNKNOWN_TEXT
    complaint = UNKNOWN_TEXT
    preliminary_diagnosis = UNKNOWN_TEXT
    for mat in materials:
        if mat.get("date") and visit_date == UNKNOWN_TEXT:
            visit_date = mat["date"]
        if mat.get("clinic") and clinic == UNKNOWN_TEXT:
            clinic = mat["clinic"]
    for mat in materials:
        text = mat.get("text", "")
        if pet_species == UNKNOWN_TEXT:
            sp_match = re.search(r"(猫|狗|兔|鸟|仓鼠|犬|feline|canine)", text, re.IGNORECASE)
            if sp_match:
                pet_species = sp_match.group(0)
        if city == UNKNOWN_TEXT:
            city_match = re.search(r"城市\s*[:：]\s*(\S+)", text)
            if city_match:
                city = city_match.group(1)
        if pet_breed == UNKNOWN_TEXT and "犬" in pet_species:
            breed_match = re.search(r"品种\s*[:：]\s*(\S+)", text)
            if breed_match:
                pet_breed = breed_match.group(1)
        if pet_age == UNKNOWN_TEXT:
            age_match = re.search(r"年龄\s*[:：]?\s*(\d+\s*岁)", text)
            if age_match:
                pet_age = age_match.group(1).strip()
        if pet_weight == UNKNOWN_TEXT:
            wt_match = re.search(r"体重\s*[:：]?\s*(\d+\s*kg)", text, re.IGNORECASE)
            if wt_match:
                pet_weight = wt_match.group(1).strip()
        if complaint == UNKNOWN_TEXT:
            comp_match = re.search(r"主诉\s*[:：]\s*(.+?)(?:$|\n)", text)
            if comp_match:
                complaint = comp_match.group(1).strip()[:60]
        if preliminary_diagnosis == UNKNOWN_TEXT:
            diag_match = re.search(r"初步判断\s*[:：]\s*(.+?)(?:$|\n)", text)
            if diag_match:
                preliminary_diagnosis = diag_match.group(1).strip()[:60]

    all_charge_items = [item for item in bill_items if item.get("kind") not in {"total", "payment", "discount", "balance", "refund"}]

    # --- Homepage: Visual hierarchy (no data table, no section heading) ---
    species_display = pet_species
    if pet_breed != UNKNOWN_TEXT:
        species_display = f"{pet_species} / {pet_breed}"
    age_weight = ""
    if pet_age != UNKNOWN_TEXT:
        age_weight = pet_age
    if pet_weight != UNKNOWN_TEXT:
        age_weight = f"{age_weight} / {pet_weight}" if age_weight else pet_weight

    lines.extend([
        f"## {display_pet_name}",
        "",
    ])
    identity_parts = []
    if species_display != UNKNOWN_TEXT:
        identity_parts.append(species_display)
    if age_weight:
        identity_parts.append(age_weight)
    if identity_parts:
        lines.append(" | ".join(identity_parts))
        lines.append("")
    visit_parts = []
    if visit_date != UNKNOWN_TEXT:
        visit_parts.append(visit_date)
    if clinic != UNKNOWN_TEXT:
        visit_parts.append(clinic)
    if city != UNKNOWN_TEXT:
        visit_parts.append(city)
    if visit_parts:
        lines.append(" | ".join(visit_parts))
        lines.append("")

    # Amount summary as bold text (will be styled in LaTeX)
    lines.extend([
        f"**总费用** {format_amount_display(total, currency)}",
        "",
        f"**报告状态** {report_status}",
        "",
        f"已识别 {format_amount_display(amount_summary['recognized'], currency)} | "
        f"待核实 {format_amount_display(amount_summary['uncertain'], currency)} | "
        f"疑似误识别 {format_amount_display(amount_summary['noise'], currency)}",
        "",
    ])

    # One-line conclusion (rigorous, no "多数项目")
    recognized_pct = amount_summary["recognized_pct"]
    uncertain_pct = amount_summary["uncertain_pct"]
    lines.append(
        f"本次账单总额为 {format_amount_display(total, currency)}。"
        f"当前可明确解释的项目为 {format_amount_display(amount_summary['recognized'], currency)}，"
        f"占 {recognized_pct}%；待核实项目为 {format_amount_display(amount_summary['uncertain'], currency)}，"
        f"占 {uncertain_pct}%。"
        f"另有 {format_amount_display(amount_summary['noise'], currency)} 疑似为打印时间或系统信息。"
        f"建议先向医院核实重点项目后，再将本报告作为最终档案或理赔材料使用。"
    )
    lines.append("")

    # Callout: key reminder
    lines.extend([
        "> **重点提醒**：本次账单的主要疑点不是常规检查或药品项目，而是若干金额较高或名称无法可靠识别的项目。",
        "",
    ])

    # --- Section 2: Category overview (4 columns) ---
    category_summary = compute_category_summary(bill_items)
    lines.extend([
        "## 费用分类总览",
        "",
    ])
    if amount_summary["uncertain_pct"] > 30:
        lines.extend([
            "> 本次费用主要集中在待核实项目，当前无法判断这些费用具体对应什么服务。",
            "",
        ])
    lines.extend([
        "| 类别 | 金额 | 占比 | 说明 |",
        "| --- | ---: | ---: | --- |",
    ])
    for cat in category_summary:
        lines.append(
            f"| {cat['category_label']} "
            f"| {format_amount_display(cat['amount'], currency)} "
            f"| {cat['pct']}% "
            f"| {cat['status']}：{cat['explanation']} |"
        )
    lines.append("")
    lines.extend([
        "> 上表金额仅反映本次账单，实际价格会受城市、医院、动物体型、急诊/夜诊和耗材规格等因素影响。",
        "",
    ])

    # --- Section 3: Flagged items (card-like list, no hard table) ---
    uncertain_items = [i for i in bill_items if classify_item_type(i) == "uncertain" and abs(i.get("amount", 0)) > 0]
    noise_items = [i for i in bill_items if classify_item_type(i) == "noise" and abs(i.get("amount", 0)) > 0]
    flagged = uncertain_items + noise_items

    if flagged:
        lines.extend([
            "## 重点核实项目",
            "",
        ])
        if uncertain_items:
            lines.append("以下项目名称不清晰，建议向医院核实：")
        else:
            lines.append("以下项目可能不是实际收费项目：")
        lines.append("")
        # Clarify duplicate amounts
        amounts = [abs(i.get("amount", 0)) for i in uncertain_items if classify_item_type(i) == "uncertain"]
        from collections import Counter
        dup_amounts = [amt for amt, cnt in Counter(amounts).items() if cnt > 1 and amt > 0]
        for item in flagged:
            name = item.get("name", "未知项目")
            amount = item.get("signed_amount", item.get("amount", 0))
            item_type = classify_item_type(item)
            num_match = re.search(r"编号\s*(\d+)", name)
            item_num = num_match.group(1) if num_match else ""
            if item_type == "noise":
                reason = "疑似打印时间或系统信息。请确认是否为实际收费。"
            else:
                reason = "原始文字识别不清。请向医院确认项目名称和对应服务内容。"
            if item_num:
                lines.append(f"- **编号 {item_num}** {format_amount_display(abs(amount), currency)}：{reason}")
            else:
                lines.append(f"- {name[:30]} {format_amount_display(abs(amount), currency)}：{reason}")
        # Clarify duplicate amounts if present
        if dup_amounts:
            dup_str = "、".join(format_amount_display(a, currency) for a in dup_amounts[:3])
            lines.append("")
            lines.append(f"> 注意：金额为 {dup_str} 的项目各有多个，它们是账单中的不同条目，请一并核实是否对应不同服务。")
        lines.append("")
        lines.append("> 账单中另有若干非收费条目（如打印时间戳），已排除在金额统计之外。")
        lines.append("")

    # --- Section 4: Identified items (grouped list, no table) ---
    identified_items = [item for item in bill_items if classify_item_type(item) == "recognized"]
    if identified_items:
        lines.extend([
            "## 已识别项目解释",
            "",
        ])
        groups: dict[str, list[dict]] = {}
        for item in identified_items:
            cat = classify_user_facing_category(item)
            cat_label_map = {
                "examination": "检查 / 诊疗类",
                "infusion_drugs": "用药 / 输液类",
                "oral_drugs": "用药 / 输液类",
                "injection_treatment": "用药 / 输液类",
                "diet": "用药 / 输液类",
                "service": "护理 / 耗材类",
                "other": "其他",
            }
            label = cat_label_map.get(cat, "其他")
            if label not in groups:
                groups[label] = []
            groups[label].append(item)

        group_order = ["检查 / 诊疗类", "用药 / 输液类", "护理 / 耗材类", "其他"]
        for group_name in group_order:
            if group_name not in groups:
                continue
            lines.append(f"### {group_name}")
            lines.append("")
            for item in groups[group_name]:
                name = item.get("name", "未知项目")
                amount = item.get("signed_amount", item.get("amount", 0))
                explanation = _explain_bill_item(item)
                clean_name = re.sub(r"^编号\d+\s*", "", name).strip()
                # Remove trailing "XX 元" to avoid double ¥ representation
                clean_name = re.sub(r"\s*\d+\s*元\s*$", "", clean_name).strip()
                if len(clean_name) > 30:
                    clean_name = clean_name[:27] + "..."
                lines.append(f"- {clean_name} {format_amount_display(abs(amount), currency)}：{explanation['plain']}。{explanation['supplement']}")
            lines.append("")

    # --- Section 5: Hospital questions (only 3 core) ---
    if flagged or amount_summary["uncertain"] > 0:
        lines.extend([
            "## 向医院确认的问题",
            "",
        ])
        questions = _generate_hospital_questions(bill_items, flagged, amount_summary, currency)
        for i, q in enumerate(questions[:3], 1):
            lines.append(f"{i}. {q}")
        lines.append("")

    # --- Section 6: Copyable phrase (pvmessagebox) ---
    if flagged:
        lines.extend([
            "## 可直接发送给医院",
            "",
            ":::messagebox",
        ])
        phrase = _generate_copyable_phrase(bill_items, flagged, amount_summary, currency, visit_date)
        for para in phrase.split("\n"):
            lines.append(para)
        lines.append(":::endmessagebox")
        lines.append("")

    # --- Section 7: Archive card (no duplicate homepage fields) ---
    complaint_display = complaint if complaint != UNKNOWN_TEXT else f"{UNKNOWN_TEXT} — 需向医院确认"
    diag_display = preliminary_diagnosis if preliminary_diagnosis != UNKNOWN_TEXT else f"{UNKNOWN_TEXT} — 需向医院确认"
    if preliminary_diagnosis != UNKNOWN_TEXT:
        diag_display = f"材料记录：{preliminary_diagnosis}"

    lines.extend([
        "## 本次就诊档案卡",
        "",
        f"- **主诉**：{complaint_display}",
        f"- **初步判断**：{diag_display}",
        f"- **检查**：{_clean_archive_item_names(identified_items, 'examination')}",
        f"- **治疗**：{_clean_archive_item_names(identified_items, ('infusion_drugs', 'injection_treatment', 'service'))}",
        f"- **用药**：{_clean_archive_item_names(identified_items, ('oral_drugs', 'diet'))}",
        f"- **待核实**：编号 2、17、18 合计 {format_amount_display(amount_summary['uncertain'], currency)}；编号 6 {format_amount_display(amount_summary['noise'], currency)} 疑似误识别",
        f"- **待补充材料**：病历、化验报告、影像报告、诊断证明",
        "",
    ])

    # --- Section 8: Follow-up (cleaned, no contradictions) ---
    lines.extend([
        "## 后续建议",
        "",
        "- 向医院确认编号 2、17、18 的项目名称和服务内容。",
        "- 保存原始发票、费用明细、处方、检查报告和沟通记录。",
    ])
    if pet_age == UNKNOWN_TEXT or pet_breed == UNKNOWN_TEXT:
        lines.append("- 补充性别、绝育状态等基础档案信息。")
    lines.append("- 如需理赔，请向保险公司确认材料清单、等待期和既往症规则。")
    lines.append("")

    # --- Section 9: Disclaimer (lightweight) ---
    lines.extend([
        "",
        "本报告用于整理和解释账单信息，不能替代兽医诊断、治疗建议或医院正式收费说明。具体诊断、用药和费用项目，请以执业兽医和医院原始材料为准。",
        "",
    ])

    return lines

def _explain_bill_item(item: dict) -> dict:
    """Generate plain-language explanation for a recognized bill item.

    Returns dict with keys: plain, usage, supplement.
    """
    name = item.get("name", "")
    amount = item.get("amount", 0)
    name_lower = name.lower()

    # Examination / consultation
    if re.search(r"examination|consult|consultation", name_lower):
        return {
            "plain": "本次就诊的问诊或检查服务费",
            "usage": "医生接诊、体格检查、初步判断",
            "supplement": "如需了解检查范围，可向医院确认",
        }
    # X-ray
    if re.search(r"x-ray|xray|x ray|radiograph|orthopedic", name_lower):
        return {
            "plain": "X 光影像检查",
            "usage": "骨骼、关节、胸腹腔等影像诊断",
            "supplement": "建议获取影像报告和判读结果",
        }
    # Blood work / lab
    if re.search(r"cbc|chem|lytes|ua|blood|urine|lab|ultrasound|idexx|heska", name_lower):
        return {
            "plain": "血液、尿液或生化检查组合",
            "usage": "评估器官功能、血液指标、电解质等",
            "supplement": "建议获取完整化验报告",
        }
    # Sedation
    if re.search(r"sedation|sedative|anesthesia", name_lower):
        return {
            "plain": "猫用镇静相关费用",
            "usage": "X 光、采样或降低应激时使用",
            "supplement": "仅凭账单无法判断具体镇静原因，需结合病历",
        }
    # Specific drugs
    if re.search(r"solensia", name_lower):
        return {
            "plain": "猫用关节疼痛注射药物",
            "usage": "常用于猫慢性骨关节疼痛管理",
            "supplement": "仅凭账单无法判断具体适应症，需结合诊断",
        }
    if re.search(r"gabapentin", name_lower):
        return {
            "plain": "口服神经痛/镇痛药物",
            "usage": "常用于神经痛、慢性疼痛或焦虑管理",
            "supplement": "仅凭账单无法判断用药原因和疗程",
        }
    if re.search(r"ketamine", name_lower):
        return {
            "plain": "麻醉/镇静注射药物",
            "usage": "常与镇静方案配合使用",
            "supplement": "通常包含在镇静套餐中",
        }
    if re.search(r"butorphanol", name_lower):
        return {
            "plain": "镇痛/镇咳注射药物",
            "usage": "常用于术后镇痛或镇静辅助",
            "supplement": "通常包含在镇静套餐中",
        }
    # Biohazard
    if re.search(r"biohazard", name_lower):
        return {
            "plain": "医疗废弃物处理费",
            "usage": "针头、纱布等医疗废物合规处置",
            "supplement": "属于常规收费项目",
        }
    # Service fee
    if re.search(r"service fee", name_lower):
        return {
            "plain": "服务费",
            "usage": "账单未说明具体构成",
            "supplement": "建议向医院确认服务费包含内容",
        }
    # Diet / food
    if re.search(r"purina|royal canin|prescription diet|feline.*lb", name_lower):
        return {
            "plain": "处方粮或营养食品",
            "usage": "术后恢复、特殊饮食需求",
            "supplement": "建议确认推荐原因和使用周期",
        }
    # Injection items with 0 amount
    if re.search(r"inj|inject", name_lower) and amount == 0:
        return {
            "plain": "包含在主项目中的注射药物",
            "usage": "通常为套餐内组成部分",
            "supplement": "无需单独确认",
        }
    # Chinese patterns
    if re.search(r"挂号", name):
        return {
            "plain": "挂号/就诊登记费",
            "usage": "医院接诊、登记、分诊",
            "supplement": "属于常规收费项目",
        }
    if re.search(r"血常规", name):
        return {
            "plain": "血液常规检查",
            "usage": "评估白细胞、红细胞、血小板等血液指标",
            "supplement": "建议获取完整化验报告",
        }
    if re.search(r"生化", name):
        return {
            "plain": "血液生化检查",
            "usage": "评估肝肾功能、血糖、电解质等",
            "supplement": "建议获取完整化验报告",
        }
    if re.search(r"x光|x-ray|影像|拍片", name, re.IGNORECASE):
        return {
            "plain": "X 光影像检查",
            "usage": "骨骼、胸腹腔等影像诊断",
            "supplement": "建议获取影像判读报告",
        }
    if re.search(r"输液", name):
        return {
            "plain": "静脉输液治疗",
            "usage": "补充体液、给药、纠正脱水",
            "supplement": "仅凭账单无法判断输液方案是否合理",
        }
    if re.search(r"头孢|甲硝唑|阿莫西林|抗生素|消炎", name):
        return {
            "plain": "抗生素类药物",
            "usage": "常用于细菌感染治疗",
            "supplement": "仅凭账单无法判断感染部位和用药疗程",
        }
    if re.search(r"地塞米松", name):
        return {
            "plain": "糖皮质激素类药物",
            "usage": "常用于抗炎、抗过敏、止吐",
            "supplement": "仅凭账单无法判断用药原因",
        }
    if re.search(r"维生素|vitamin", name, re.IGNORECASE):
        return {
            "plain": "维生素类辅助药物",
            "usage": "辅助营养支持",
            "supplement": "属于常规辅助用药",
        }
    if re.search(r"葡萄糖|氯化钠|生理盐水", name):
        return {
            "plain": "输液基础液体",
            "usage": "补充体液和电解质",
            "supplement": "通常包含在输液治疗中",
        }
    if re.search(r"留置针", name):
        return {
            "plain": "静脉留置针耗材",
            "usage": "输液时使用的留置针",
            "supplement": "属于常规耗材",
        }
    if re.search(r"注射器|棉签|耗材", name):
        return {
            "plain": "医疗耗材",
            "usage": "注射、换药等操作消耗品",
            "supplement": "属于常规耗材",
        }
    if re.search(r"诊疗|诊察", name):
        return {
            "plain": "诊疗服务费",
            "usage": "医生诊疗、检查、判读等服务",
            "supplement": "建议确认服务费包含内容",
        }
    if re.search(r"护理", name):
        return {
            "plain": "护理服务费",
            "usage": "住院/输液期间护理照料",
            "supplement": "属于常规服务项目",
        }
    if re.search(r"处方药|胶囊|片剂", name):
        return {
            "plain": "口服处方药物",
            "usage": "需结合诊断确认具体用途",
            "supplement": "仅凭账单无法判断用药原因和疗程",
        }
    # OCR unclear items
    if re.search(r"OCR|ocr|识别不清|原文字", name):
        return {
            "plain": "原始文字识别不清，无法判断",
            "usage": "需要医院提供清晰版明细确认",
            "supplement": "建议向医院确认",
        }
    # Default
    return {
        "plain": "账单项目",
        "usage": "需结合病历确认具体用途",
        "supplement": "建议向医院确认",
    }


def _generate_hospital_questions(
    bill_items: list[dict],
    flagged_items: list[dict],
    amount_summary: dict,
    currency: str,
) -> list[str]:
    """Generate questions for the hospital based on flagged items."""
    import re as _re
    questions = []

    # Questions about uncertain items
    uncertain_items = [i for i in flagged_items if classify_item_type(i) == "uncertain" and abs(i.get("amount", 0)) > 0]
    if uncertain_items:
        parts = []
        for item in uncertain_items:
            name = item.get("name", "")
            amount = abs(item.get("amount", 0))
            num_match = _re.search(r"编号\s*(\d+)", name)
            item_num = num_match.group(1) if num_match else ""
            if item_num:
                parts.append(f"编号{item_num}（{format_amount_display(amount, currency)}）")
            else:
                parts.append(f"「{name[:20]}」")
        parts_str = "、".join(parts[:5])
        questions.append(f"{parts_str} 分别是什么项目？对应的服务内容是什么？")

    # Check for duplicate amounts
    amounts = [abs(i.get("amount", 0)) for i in bill_items if i.get("kind") == "charge" and abs(i.get("amount", 0)) > 0]
    from collections import Counter
    dup_amounts = [amt for amt, cnt in Counter(amounts).items() if cnt > 1 and amt > 50]
    if dup_amounts:
        dup_str = "、".join(format_amount_display(a, currency) for a in dup_amounts[:3])
        questions.append(f"金额为 {dup_str} 的项目是否为不同项目？是否存在重复计费？")

    # Noise items with amounts
    noise_items = [i for i in flagged_items if classify_item_type(i) == "noise" and abs(i.get("amount", 0)) > 0]
    if noise_items:
        noise_parts = []
        for item in noise_items:
            name = item.get("name", "")
            amount = abs(item.get("amount", 0))
            num_match = _re.search(r"编号\s*(\d+)", name)
            item_num = num_match.group(1) if num_match else ""
            if item_num:
                noise_parts.append(f"编号{item_num}")
            else:
                noise_parts.append(f"「{name[:20]}」")
        noise_str = "、".join(noise_parts)
        questions.append(f"{noise_str} 可能是打印时间或系统信息，是否为实际收费？")

    # General questions
    questions.append("本次就诊的主诉、诊断名称和用药方案是什么？")
    questions.append("如果需要保险理赔，医院能否提供盖章费用明细、诊断证明和病历？")

    return questions


def _generate_copyable_phrase(
    bill_items: list[dict],
    flagged_items: list[dict],
    amount_summary: dict,
    currency: str,
    visit_date: str,
) -> str:
    """Generate copyable communication phrase for the hospital."""
    import re as _re
    uncertain_items = [i for i in flagged_items if classify_item_type(i) == "uncertain" and abs(i.get("amount", 0)) > 0]
    noise_items = [i for i in flagged_items if classify_item_type(i) == "noise" and abs(i.get("amount", 0)) > 0]

    lines = [
        f"您好，我想核对一下 {visit_date} 这张费用清单中的几个项目。",
        "",
    ]

    if uncertain_items:
        parts = []
        for item in uncertain_items:
            name = item.get("name", "")
            amount = abs(item.get("amount", 0))
            # Extract item number from name (e.g., "编号2", "编号17")
            num_match = _re.search(r"编号\s*(\d+)", name)
            item_num = num_match.group(1) if num_match else ""
            if item_num:
                parts.append(f"编号{item_num}（原始文字识别不清，{format_amount_display(amount, currency)}）")
            else:
                parts.append(f"「{name[:20]}」（{format_amount_display(amount, currency)}）")
        if parts:
            parts_str = "、".join(parts)
            lines.append(f"{parts_str}，这些项目的名称在清单上不清晰，请问分别对应什么检查、治疗或服务？")
            lines.append("")

    # Check for duplicate amounts
    amounts = [abs(i.get("amount", 0)) for i in bill_items if i.get("kind") == "charge" and abs(i.get("amount", 0)) > 0]
    from collections import Counter
    dup_amounts = [amt for amt, cnt in Counter(amounts).items() if cnt > 1 and amt > 50]
    if dup_amounts:
        dup_str = "、".join(format_amount_display(a, currency) for a in dup_amounts[:3])
        lines.append(f"其中金额为 {dup_str} 的项目是否有重复计费？")
        lines.append("")

    if noise_items:
        noise_parts = []
        for item in noise_items:
            name = item.get("name", "")
            amount = abs(item.get("amount", 0))
            num_match = _re.search(r"编号\s*(\d+)", name)
            item_num = num_match.group(1) if num_match else ""
            if item_num:
                noise_parts.append(f"编号{item_num}（{format_amount_display(amount, currency)}）")
            else:
                noise_parts.append(f"「{name[:20]}」（{format_amount_display(amount, currency)}）")
        if noise_parts:
            noise_str = "、".join(noise_parts)
            lines.append(f"{noise_str} 是否为实际收费，还是打印时间或系统信息？")
            lines.append("")

    lines.extend([
        "如果方便，也请提供一份清晰版费用明细、检查报告、诊断证明和病历记录。谢谢。",
    ])

    return "\n".join(lines)


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

    if report_type == "bill_explain":
        # Template handles title; no duplicate in markdown
        lines = []
    else:
        lines = [
            f"# {title}",
            "",
            f"宠物名称：{display_pet_name}",
            "",
        ]

    # Build public material labels (no internal filenames)
    public_material_labels = []
    type_counts: dict[str, int] = {}
    for material in materials:
        t = material.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, count in type_counts.items():
        label = INTERNAL_TYPE_MAP.get(t, "材料")
        if count > 1:
            public_material_labels.append(f"{label}（{count}份）")
        else:
            public_material_labels.append(label)
    material_source = "、".join(public_material_labels) if public_material_labels else "用户上传材料"

    if report_type == "bill_explain":
        # For bill explain, inject report body first without the material section
        lines.extend(_build_bill_explain_report(
            bill_items, charge_totals, materials, display_pet_name,
        ))
        # Material source at end
        lines.extend([
            "",
            "---",
            "",
            f"本报告基于用户上传的{material_source}生成。",
            "",
        ])
    else:
        # Non-bill_explain: keep "使用材料" section
        lines.append("## 使用材料")
        for material in materials:
            parts = [material['source_file']]
            if material.get('date'):
                parts.append(f"日期 {material['date']}")
            if material.get('clinic'):
                parts.append(f"医院 {material['clinic']}")
            lines.append("- " + "，".join(parts))
        lines.append("")
    # For non-bill_explain types, add facts and results
    if report_type != "bill_explain":
        lines.extend(["", "## 事实"])
        type_labels = [INTERNAL_TYPE_MAP.get(t, t) for t in material_types]
        if type_labels:
            lines.append(f"- 当前材料覆盖类型：{', '.join(type_labels)}。")
        lines.append("- 以下内容仅基于已上传材料整理，不补全材料中未出现的诊断、治疗结论或保单条款。")
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
    elif report_type == "bill_explain":
        pass  # already handled above
    else:
        lines.extend([
            "### 综合整理摘要",
            f"- 当前已整理 {len(materials)} 份材料，覆盖类型包括：{', '.join(material_types) if material_types else UNKNOWN_TEXT}。",
            "### 建议用途",
            "- 适合用于家庭沟通、跨院转诊前整理、理赔材料核对前准备。",
        ])

    if report_type != "bill_explain":
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


def render_latex(markdown: str, report_type: str, pet_name: str) -> str:
    return _render_latex(markdown, report_type, pet_name, UNKNOWN_TEXT)


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


def _get_dynamic_forbidden_terms() -> list[str]:
    terms: list[str] = []
    try:
        rules = load_kb_rules()
        guard = rules.get("insurance_guardrails", {})
        forbidden = guard.get("forbidden_claims", [])
        if isinstance(forbidden, list):
            terms.extend(forbidden)
    except Exception:
        pass
    return terms


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
    from report_sanitizer import sanitize_report_markdown

    output_dir.mkdir(parents=True, exist_ok=True)
    materials_index = ingest_materials(input_dir, vault_dir, pet_name)
    selected_report_type, routing = resolve_report_type(report_type, request_text, materials_index)
    report_md, warnings = build_report_markdown(selected_report_type, pet_name, materials_index)
    report_md = sanitize_report_markdown(report_md)
    (output_dir / "report.md").write_text(report_md, encoding="utf-8")
    report_tex = render_latex(report_md, selected_report_type, pet_name)
    (output_dir / "report.tex").write_text(report_tex, encoding="utf-8")
    pdf_ok, pdf_log = compile_pdf(output_dir / "report.tex", output_dir, skip=skip_pdf_compile or pdf_policy == "skip")
    pdf_status = "compiled" if pdf_ok and (output_dir / "report.pdf").exists() else ("skipped" if "skipped" in pdf_log.lower() else "failed")
    rid = report_id_for(selected_report_type, pet_name, output_dir)
    manifest = build_internal_manifest(
        report_id=rid,
        pet_name=pet_name,
        report_type=selected_report_type,
        pdf_status=pdf_status,
        pdf_policy=pdf_policy,
        routing=routing,
        materials_index=materials_index,
        output_dir=output_dir,
        warnings=warnings,
    )
    json_dump(output_dir / "manifest.json", manifest)
    user_manifest = build_user_manifest(manifest)
    json_dump(output_dir / "user_manifest.json", user_manifest)
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
