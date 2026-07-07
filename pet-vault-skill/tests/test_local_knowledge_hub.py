import json
import subprocess
import sys
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parent
sys.path.insert(0, str(SKILL / "scripts"))
import petvault_core
from query_knowledge_base import parse_frontmatter


class PetVaultLocalKnowledgeHubTests(unittest.TestCase):
    def test_kb_structure_rules_and_schemas_exist(self):
        required = [
            "kb/sources.yaml",
            "kb/ontology.yaml",
            "kb/articles/billing/billing-line-items-us.md",
            "kb/articles/billing/billing-line-items-cn.md",
            "kb/articles/billing/payment-discount-refund.md",
            "kb/articles/insurance/insurance-terms-us.md",
            "kb/articles/insurance/insurance-terms-cn.md",
            "kb/articles/insurance/claim-packet-us.md",
            "kb/articles/insurance/claim-packet-cn.md",
            "kb/articles/medical/lab-report-basics.md",
            "kb/articles/safety/emergency-boundary.md",
            "kb/articles/jurisdiction/us-vet-records.md",
            "kb/articles/jurisdiction/cn-vet-records.md",
            "kb/rules/routing.yaml",
            "kb/rules/pdf_policy.yaml",
            "kb/rules/billing_validation.yaml",
            "kb/rules/insurance_guardrails.yaml",
            "kb/rules/medical_safety.yaml",
            "kb/rules/privacy.yaml",
            "schemas/kb_card.schema.json",
            "schemas/policy_harness.schema.json",
            "schemas/claim_case.schema.json",
            "schemas/medical_timeline.schema.json",
            "schemas/evidence.schema.json",
        ]
        missing = [rel for rel in required if not (SKILL / rel).exists()]
        self.assertEqual([], missing)

    def test_kb_cards_have_required_frontmatter_and_sources(self):
        sources_text = (SKILL / "kb" / "sources.yaml").read_text(encoding="utf-8")
        source_ids = set()
        for line in sources_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- id:") or stripped.startswith("id:"):
                source_ids.add(stripped.split(":", 1)[1].strip())
        required = {
            "id", "title", "domain", "jurisdiction", "language", "species",
            "source_tier", "risk_level", "allowed_outputs", "forbidden_outputs",
            "sources", "last_reviewed", "expires_at",
        }
        for path in sorted((SKILL / "kb" / "articles").rglob("*.md")):
            metadata, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
            if "id" not in metadata:
                continue
            self.assertFalse(required - set(metadata), path)
            self.assertTrue(metadata["forbidden_outputs"], path)
            if metadata["risk_level"] == "high":
                self.assertTrue(metadata["forbidden_outputs"], path)
            for source_id in metadata["sources"]:
                self.assertIn(source_id, source_ids, path)
            text = path.read_text(encoding="utf-8")
            if metadata["domain"] == "safety":
                self.assertNotIn("观察一下", text)
                self.assertNotIn("问题不大", text)

    def test_route_and_pdf_cases_are_encoded(self):
        routing = (SKILL / "kb" / "rules" / "routing.yaml").read_text(encoding="utf-8")
        pdf_policy = (SKILL / "kb" / "rules" / "pdf_policy.yaml").read_text(encoding="utf-8")
        self.assertIn("bill_report", routing)
        self.assertIn("insurance_precheck", routing)
        self.assertIn("knowledge_query", routing)
        self.assertIn("emergency_boundary", routing)
        self.assertIn("timeline_update", routing)
        self.assertIn("invoice", pdf_policy)
        self.assertIn("pure_term_explanation", pdf_policy)
        self.assertIn("not_required", pdf_policy)

    def test_amount_currency_and_separation_cases(self):
        cases = [
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
        for text, currency, kind in cases:
            with self.subTest(text=text):
                mention = petvault_core.parse_money_mentions(text)[0]
                self.assertEqual(currency, mention["currency"])
                self.assertEqual(kind, mention["kind"])

    def test_insurance_guardrail_script(self):
        allowed = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "validate_insurance_output.py"),
                "--text",
                "需要检查条款；基于上传保单估算，不代表最终审核。",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(0, allowed.returncode, allowed.stderr + allowed.stdout)
        forbidden = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "validate_insurance_output.py"),
                "--text",
                "这一定能赔。",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertNotEqual(0, forbidden.returncode)

    def test_kb_query_filters(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "query_knowledge_base.py"),
                "等待期是什么意思",
                "--domain",
                "insurance",
                "--jurisdiction",
                "US",
                "--language",
                "zh",
                "--limit",
                "3",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(len(payload["matches"]), 1)
        self.assertEqual("insurance", payload["matches"][0]["domain"])


if __name__ == "__main__":
    unittest.main()
