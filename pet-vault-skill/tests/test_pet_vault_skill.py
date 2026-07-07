import json
import shutil
import sqlite3
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parent
TMP_ROOT = ROOT / "work" / "tmp" / "package_tests"
sys.path.insert(0, str(SKILL / "scripts"))
import petvault_core

HARNESS = json.loads((SKILL / "config" / "pet_care_report_harness.yaml").read_text(encoding="utf-8-sig"))
MATERIAL_SCHEMA = json.loads((SKILL / "schemas" / "material_index.schema.json").read_text(encoding="utf-8-sig"))
MANIFEST_SCHEMA = json.loads((SKILL / "schemas" / "report_manifest.schema.json").read_text(encoding="utf-8-sig"))


class PetVaultSkillPackageTests(unittest.TestCase):
    def test_skill_metadata_and_readme(self):
        skill_md = SKILL / "SKILL.md"
        readme_en = SKILL / "README.md"
        readme_zh = SKILL / "README.zh-CN.md"
        root_readme_en = ROOT / "README.md"
        root_readme_zh = ROOT / "README.zh-CN.md"
        self.assertTrue(skill_md.exists())
        text = skill_md.read_text(encoding="utf-8")
        self.assertNotIn("TODO", text)
        self.assertIn("name: pet-vault-skill", text)
        self.assertIn("claim_check", text)

        skill_en_text = readme_en.read_text(encoding="utf-8")
        skill_zh_text = readme_zh.read_text(encoding="utf-8")
        self.assertIn("[中文说明](README.zh-CN.md)", skill_en_text)
        self.assertIn("[English](README.md)", skill_zh_text)
        self.assertIn("not fully implemented", skill_en_text)
        self.assertIn("未完整实现", skill_zh_text)

        root_en_text = root_readme_en.read_text(encoding="utf-8")
        root_zh_text = root_readme_zh.read_text(encoding="utf-8")
        self.assertIn("[中文说明](README.zh-CN.md)", root_en_text)
        self.assertIn("[English](README.md)", root_zh_text)
        self.assertIn("first open-source version", root_en_text)
        self.assertIn("第一版开源内容", root_zh_text)
        self.assertNotIn("C:/Users/20833/.codex", root_en_text)

    def test_required_resources_exist(self):
        required = [
            "agents/openai.yaml",
            "config/agents.yaml",
            "config/pet_care_report_harness.yaml",
            "config/latex_layout.yaml",
            "config/material_types.yaml",
            "config/safety_rules.yaml",
            "README.md",
            "README.zh-CN.md",
            "prompts/orchestrator_agent.md",
            "prompts/material_organizer_agent.md",
            "prompts/report_composer_agent.md",
            "prompts/quality_inspector_agent.md",
            "prompts/clinic_soap_draft_agent.md",
            "prompts/clinic_client_summary_agent.md",
            "schemas/material_index.schema.json",
            "schemas/report_manifest.schema.json",
            "schemas/qa_result.schema.json",
            "schemas/soap_note_draft.schema.json",
            "templates/report_general.tex.j2",
            "templates/report_medical_summary.tex.j2",
            "templates/report_bill_explain.tex.j2",
            "templates/report_claim_check.tex.j2",
            "templates/report_timeline.tex.j2",
            "templates/report_chronic_review.tex.j2",
            "templates/report_clinic_client_summary.tex.j2",
            "templates/styles.tex.j2",
            "templates/cover.tex.j2",
            "templates/tables.tex.j2",
            "scripts/run_pipeline.py",
            "scripts/init_vault.py",
            "scripts/ingest_materials.py",
            "scripts/classify_materials.py",
            "scripts/normalize_markdown.py",
            "scripts/extract_tables.py",
            "scripts/latex_escape.py",
            "scripts/markdown_to_latex.py",
            "scripts/build_report.py",
            "scripts/compile_pdf.py",
            "scripts/render_pdf_pages.py",
            "scripts/inspect_pdf_layout.py",
            "scripts/quick_validate.py",
            "scripts/query_knowledge_base.py",
            "scripts/update_local_db.py",
            "adapters/einvault_mapper.py",
            "adapters/einvault_exporter.py",
            "adapters/paperless_importer.py",
            "adapters/sqlite_store.py",
            "kb/articles/claim-packet-us.md",
            "kb/articles/billing-line-items.md",
            "kb/articles/nutrition-prescription-food.md",
            "kb/articles/toxin-emergency-boundary.md",
            "kb/sources.yaml",
            "references/local_knowledge_base.md",
            "references/petvault_ai_prd_v1_1.md",
        ]
        missing = [name for name in required if not (SKILL / name).exists()]
        self.assertEqual([], missing)
        self.assertTrue((ROOT / ".gitattributes").exists())
        self.assertTrue((ROOT / ".github" / "workflows" / "ci.yml").exists())
        self.assertTrue((ROOT / "README.zh-CN.md").exists())

    def test_latex_style_inherits_reference_constraints(self):
        styles = (SKILL / "templates" / "styles.tex.j2").read_text(encoding="utf-8")
        for expected in [
            r"\documentclass[UTF8,a4paper,11pt,fontset=windows]{ctexart}",
            r"left=2.35cm",
            r"right=2.35cm",
            r"top=2.15cm",
            r"bottom=2.20cm",
            r"\linespread{1.28}",
            r"\Large\bfseries",
            r"\large\bfseries",
            r"\normalsize\bfseries",
            "longtable",
        ]:
            self.assertIn(expected, styles)

    def test_pipeline_local_first_outputs_follow_harness(self):
        output_dir, vault_dir = self._run_pipeline_case("claim_check", include_pdf_placeholder=True)
        for path in HARNESS["required_files"]["report"]:
            self.assertTrue((output_dir / path).exists(), path)
        for path in HARNESS["required_files"]["vault"]:
            self.assertTrue((vault_dir / path).exists(), path)

        report_text = (output_dir / "report.md").read_text(encoding="utf-8")
        for forbidden in HARNESS["forbidden_user_terms"]:
            self.assertNotIn(forbidden, report_text)
        for required in HARNESS["required_report_sections"]:
            self.assertIn(required, report_text)
        self.assertIn("不承诺理赔结果", report_text)
        self.assertIn("费用明细", report_text)

        index_data = json.loads((vault_dir / "structured" / "materials_index.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(index_data, MATERIAL_SCHEMA)

        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        self._assert_schema_shape(manifest, MANIFEST_SCHEMA)

        qa_data = json.loads((output_dir / "qa_result.json").read_text(encoding="utf-8"))
        self.assertTrue(qa_data["passed"], qa_data)
        for dimension in [
            "source_integrity",
            "identity_consistency",
            "visit_completeness",
            "fee_explanation",
            "insurance_boundary",
            "timeline",
            "pdf_readability",
            "local_storage",
        ]:
            self.assertIn(dimension, qa_data["checks"])

        with sqlite3.connect(vault_dir / "pet_vault.sqlite3") as conn:
            self.assertEqual("ok", conn.execute("PRAGMA integrity_check").fetchone()[0])
            self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0], 3)
            self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0], 3)
            self.assertEqual(1, conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0])

    def test_report_type_smoke_cases(self):
        expectations = {
            "general": ["综合整理摘要", "待确认"],
            "medical_summary": ["一句话摘要", "建议向兽医确认的问题"],
            "bill_explain": ["费用分类", "高额项目"],
            "claim_check": ["已有材料", "不承诺理赔结果"],
            "timeline": ["就诊时间线", "转诊摘要"],
            "chronic_review": ["月度概览", "长期病情趋势"],
            "clinic_client_summary": ["客户版解释草稿", "发送前需由医生或前台审核"],
        }
        for report_type, required_terms in expectations.items():
            with self.subTest(report_type=report_type):
                output_dir, _vault_dir = self._run_pipeline_case(report_type)
                report_text = (output_dir / "report.md").read_text(encoding="utf-8")
                for term in required_terms:
                    self.assertIn(term, report_text)

    def test_mixed_pet_warning_and_no_invention(self):
        output_dir, _vault_dir = self._run_pipeline_case("timeline", mixed_pets=True)
        report_text = (output_dir / "report.md").read_text(encoding="utf-8")
        self.assertIn("发现多只宠物或不同名称混在同一批材料中", report_text)
        self.assertNotIn("擅自补充", report_text)

    def test_pdf_path_records_status_without_forcing_skip(self):
        output_dir, _vault_dir = self._run_pipeline_case("medical_summary", skip_pdf_compile=False)
        build_log = (output_dir / "build.log").read_text(encoding="utf-8")
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn(manifest["pdf_status"], {"compiled", "skipped", "failed"})
        self.assertTrue(build_log.strip())
        if shutil.which("xelatex") or shutil.which("latexmk"):
            self.assertIn(manifest["pdf_status"], {"compiled", "failed"})
        else:
            self.assertEqual("skipped", manifest["pdf_status"])
            self.assertIn("No xelatex or latexmk found", build_log)

    def test_usd_invoice_lines_are_extracted_and_not_classified_as_policy(self):
        text = "\n".join(
            [
                "Material type: invoice / bill",
                "Pet: Oreo",
                "Clinic: Chino Hills Animal Hospital",
                "Date: 2026-03-28",
                "Examination - Consult USD 80.00",
                "Feline Sedation $174.25",
                "X-Ray Orthopedic US$333.00",
                "CBC, Chem 17, Lytes, UA $347.39",
                "Payment: CareCredit USD -938.49",
                "Discount: ($10.55)",
                "Insurance policy terms are not visible on this invoice.",
            ]
        )
        material_type, _confidence = petvault_core.classify_material("2026-03-28_Oreo_invoice_transcription.md", text)
        self.assertIn(material_type, {"bill", "invoice"})
        self.assertNotEqual("insurance_policy", material_type)
        report_text, _warnings = petvault_core.build_report_markdown(
            "bill_explain",
            "Oreo",
            {
                "materials": [
                    {
                        "id": "mat_001",
                        "type": material_type,
                        "pet_name": "Oreo",
                        "clinic": "Chino Hills Animal Hospital",
                        "date": "2026-03-28",
                        "source_file": "2026-03-28_Oreo_invoice_transcription.md",
                        "raw_path": "raw/invoice/2026-03-28_Oreo_invoice_transcription.md",
                        "cleaned_markdown_path": "cleaned/markdown/mat_001.md",
                        "confidence": 0.95,
                        "status": "extracted",
                        "text": text,
                    }
                ],
                "created_at": "2026-07-07T00:00:00",
            },
        )
        self.assertIn("934.64 USD", report_text)
        self.assertIn("CareCredit", report_text)
        self.assertIn("80.00 USD", report_text)

    def test_auto_report_type_from_bill_request(self):
        output_dir, _vault_dir = self._run_pipeline_case(
            "auto",
            request_text="请帮我解释这张账单并生成报告。",
            skip_pdf_compile=True,
        )
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("bill_explain", manifest["report_type"])
        self.assertEqual("auto", manifest["routing"]["requested_report_type"])
        report_text = (output_dir / "report.md").read_text(encoding="utf-8")
        self.assertIn("费用分类", report_text)
        self.assertIn("高额项目", report_text)

    def test_pdf_required_fails_when_pdf_is_missing(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        output_dir = TMP_ROOT / f"missing_pdf_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True)
        (output_dir / "report.md").write_text(
            "# 宠物医疗账单解释报告\n\n## 使用材料\n- sample.txt\n\n## 事实\n- 仅基于材料。\n\n## 整理结果\n- 费用分类。\n\n## 待确认\n- 待确认。\n\n## 后续建议\n- 保存材料。\n",
            encoding="utf-8",
        )
        (output_dir / "report.tex").write_text("longtable", encoding="utf-8")
        (output_dir / "manifest.json").write_text("{}", encoding="utf-8")
        (output_dir / "build.log").write_text("compiled elsewhere", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "inspect_pdf_layout.py"),
                str(output_dir),
                "--pdf-required",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("report.pdf is missing", result.stdout)

    def test_quick_validate_and_knowledge_query_entrypoints(self):
        validate = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / "quick_validate.py"), str(SKILL)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(validate.returncode, 0, validate.stderr + validate.stdout)
        query = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "query_knowledge_base.py"),
                "理赔需要哪些材料",
                "--limit",
                "1",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(query.returncode, 0, query.stderr + query.stdout)
        payload = json.loads(query.stdout)
        self.assertGreaterEqual(len(payload["matches"]), 1)
        self.assertIn("article_id", payload["matches"][0])

    def _assert_schema_shape(self, payload, schema):
        for field in schema.get("required", []):
            self.assertIn(field, payload)
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in payload:
                continue
            if field_schema.get("type") == "array" and "items" in field_schema and payload[field]:
                sample = payload[field][0]
                for nested_field in field_schema["items"].get("required", []):
                    self.assertIn(nested_field, sample)
            elif field_schema.get("type") == "object" and "required" in field_schema:
                for nested_field in field_schema["required"]:
                    self.assertIn(nested_field, payload[field])

    def _run_pipeline_case(
        self,
        report_type,
        mixed_pets=False,
        skip_pdf_compile=True,
        include_pdf_placeholder=False,
        request_text=None,
    ):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmpdir = TMP_ROOT / f"{report_type}_{uuid.uuid4().hex[:8]}"
        input_dir = tmpdir / "materials"
        output_dir = tmpdir / "out"
        vault_dir = tmpdir / "vault"
        input_dir.mkdir(parents=True)
        (input_dir / "2026-07-05_mimi_bill.txt").write_text(
            "\n".join(
                [
                    "宠物：Mimi",
                    "日期：2026-07-05",
                    "医院：星河动物医院",
                    "项目：血常规 120 元；B超 350 元；处方药 86.5 元",
                    "诉求：帮我看看账单和理赔材料是否够用。",
                ]
            ),
            encoding="utf-8",
        )
        (input_dir / "mimi_policy.txt").write_text(
            "宠物保险保单：Mimi，等待期需核对，理赔通常需要发票、费用明细、处方、检查报告。",
            encoding="utf-8",
        )
        other_pet = "Luna" if mixed_pets else "Mimi"
        (input_dir / "mimi_lab.txt").write_text(
            "\n".join(
                [
                    f"宠物：{other_pet}",
                    "日期：2026-07-04",
                    "医院：星河动物医院",
                    "ALT 132 高",
                    "CREA 1.9 高",
                    "医生建议：一周后复查。",
                ]
            ),
            encoding="utf-8",
        )
        if include_pdf_placeholder:
            (input_dir / "scan_result.pdf").write_bytes(b"%PDF-1.4\nplaceholder\n")

        command = [
            sys.executable,
            str(SKILL / "scripts" / "run_pipeline.py"),
            "--input",
            str(input_dir),
            "--output",
            str(output_dir),
            "--vault",
            str(vault_dir),
            "--report-type",
            report_type,
            "--pet-name",
            "Mimi",
        ]
        if request_text:
            command.extend(["--request", request_text])
        if skip_pdf_compile:
            command.append("--skip-pdf-compile")
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return output_dir, vault_dir


if __name__ == "__main__":
    unittest.main()
