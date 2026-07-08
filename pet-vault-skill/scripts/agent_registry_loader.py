"""agent_registry_loader: Single source of truth for forbidden terms and registry data.

Loads from .agents/forbidden_terms_registry.yaml with graceful fallback.
"""
from __future__ import annotations

from pathlib import Path

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

SKILL_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = SKILL_DIR / ".agents" / "forbidden_terms_registry.yaml"

_FALLBACK_FORBIDDEN_TERMS = [
    "insurance_policy", "claim_document", "lab_report", "medical_report",
    "prescription", "appointment", "clinic_communication", "pet_profile",
    "extracted", "indexed_only", "encoding_repaired",
    "置信度", "confidence",
    "routing", "dispatch", "harness",
    "classification", "intent", "debug", "trace", "internal",
    "PRD", "Harness", "HMW", "POV",
    "产品需求文档", "设计提案约束", "开发者校验",
    "request_mentions_", "materials_include_", "fallback_",
    "[FORBIDDEN]", "[INTERNAL]", "[DEBUG]",
]

_FALLBACK_TYPE_MAP = {
    "invoice": "发票/收据",
    "bill": "账单/费用明细",
    "insurance_policy": "保险保单",
    "claim_document": "理赔材料",
    "lab_report": "化验报告",
    "medical_report": "检查报告",
    "prescription": "处方",
    "appointment": "预约记录",
    "clinic_communication": "医院沟通记录",
    "pet_profile": "宠物资料",
    "unknown": "待分类材料",
}

_FALLBACK_STATUS_MAP = {
    "extracted": "已提取",
    "indexed_only": "已索引（未解析正文）",
    "encoding_repaired": "已修复编码",
    "indexed_with_manual_transcription": "已索引（含人工核对）",
}

_registry_cache: dict | None = None


def get_registry_path() -> Path:
    """Return the path to the forbidden terms registry YAML."""
    return REGISTRY_PATH


def _load_registry() -> dict:
    """Load registry YAML with fallback."""
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache
    if not REGISTRY_PATH.exists():
        _registry_cache = {}
        return _registry_cache
    if _yaml is None:
        _registry_cache = {}
        return _registry_cache
    try:
        _registry_cache = _yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        _registry_cache = {}
    return _registry_cache


def load_forbidden_terms() -> list[str]:
    """Load forbidden terms from registry, with fallback."""
    registry = _load_registry()
    terms = []
    for key in ["internal_type_codes", "internal_status_codes", "internal_metadata_keywords",
                 "developer_terms", "forbidden_tags", "routing_reason_prefixes"]:
        items = registry.get(key, [])
        if isinstance(items, list):
            terms.extend(items)
    return terms if terms else list(_FALLBACK_FORBIDDEN_TERMS)


def load_internal_type_map() -> dict[str, str]:
    """Load internal type code to user-visible label mapping."""
    registry = _load_registry()
    translations = registry.get("type_code_translations", {})
    return translations if translations else dict(_FALLBACK_TYPE_MAP)


def load_internal_status_map() -> dict[str, str]:
    """Load internal status code to user-visible label mapping."""
    registry = _load_registry()
    translations = registry.get("status_code_translations", {})
    return translations if translations else dict(_FALLBACK_STATUS_MAP)


def registry_exists() -> bool:
    """Check if the registry file exists."""
    return REGISTRY_PATH.exists()
