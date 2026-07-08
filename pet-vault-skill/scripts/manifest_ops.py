"""manifest_ops: Internal and user-facing manifest construction."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


INTERNAL_TYPE_MAP = {
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


def _translate_type_label(raw_type: str) -> str:
    return INTERNAL_TYPE_MAP.get(raw_type, raw_type)


def report_id_for(report_type: str, pet_name: str, output_dir: Path) -> str:
    return hashlib.sha1(f"{report_type}|{pet_name}|{output_dir}".encode("utf-8")).hexdigest()[:12]


def build_internal_manifest(
    report_id: str,
    pet_name: str,
    report_type: str,
    pdf_status: str,
    pdf_policy: str,
    routing: dict,
    materials_index: dict,
    output_dir: Path,
    warnings: list[str],
) -> dict:
    return {
        "id": report_id,
        "pet_name": pet_name,
        "report_type": report_type,
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


def build_user_manifest(internal_manifest: dict) -> dict:
    """Create user-safe manifest without internal routing/QA details."""
    return {
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
