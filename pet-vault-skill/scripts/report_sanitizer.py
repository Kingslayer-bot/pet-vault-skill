"""report_sanitizer: clean internal terms from user-facing report markdown."""
from __future__ import annotations

import re
from agent_registry_loader import load_forbidden_terms, load_internal_type_map, load_internal_status_map

# Load from registry (single source of truth)
INTERNAL_TYPE_MAP = load_internal_type_map()
INTERNAL_STATUS_MAP = load_internal_status_map()
FORBIDDEN_IN_USER_REPORT = load_forbidden_terms()


def _translate_type_label(raw_type: str) -> str:
    return INTERNAL_TYPE_MAP.get(raw_type, raw_type)


def _translate_status_label(raw_status: str) -> str:
    return INTERNAL_STATUS_MAP.get(raw_status, raw_status)


def sanitize_report_markdown(report_md: str) -> str:
    """Remove internal terms from user-facing report markdown."""
    lines = report_md.split("\n")
    cleaned = []
    for line in lines:
        for code, label in INTERNAL_TYPE_MAP.items():
            line = line.replace(f"类型={code}", f"类型={label}")
            line = line.replace(f"覆盖类型：{code}", f"覆盖类型：{label}")
        for code, label in INTERNAL_STATUS_MAP.items():
            line = line.replace(f"状态={code}", f"状态={label}")
        line = re.sub(r"；置信度=[\d.]+", "", line)
        line = re.sub(r"；置信度=[\d.]+；", "；", line)
        for term in FORBIDDEN_IN_USER_REPORT:
            if term in line:
                line = line.replace(term, "")
        line = re.sub(r"  +", " ", line)
        line = re.sub(r"：\s*；", "：", line)
        line = re.sub(r"；\s*$", "", line)
        cleaned.append(line)
    return "\n".join(cleaned)


def build_user_manifest(internal_manifest: dict) -> dict:
    """Create user-safe manifest without internal routing/QA details."""
    user = {
        "id": internal_manifest.get("id"),
        "pet_name": internal_manifest.get("pet_name"),
        "report_type": internal_manifest.get("report_type"),
        "created_at": internal_manifest.get("created_at"),
        "pdf_status": internal_manifest.get("pdf_status"),
        "materials": [
            {
                "source_file": m.get("source_file"),
                "type_label": _translate_type_label(m.get("type", "")),
                "date": m.get("date"),
                "pet_name": m.get("pet_name"),
                "clinic": m.get("clinic"),
            }
            for m in internal_manifest.get("materials", [])
        ],
        "outputs": internal_manifest.get("outputs", {}),
        "warnings": internal_manifest.get("warnings", []),
    }
    return user
