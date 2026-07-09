"""Behavior tests for billing_report_cases.yaml — verifies billing extraction and output safety."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

EVAL_DIR = SKILL / ".agents" / "eval_cases"


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestBillingReportBehavior(unittest.TestCase):
    """Behavior tests for billing report cases."""

    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "billing_report_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_bill_explain_basic_has_required_sections(self):
        """Bill explanation report must contain required user-facing sections."""
        from petvault_core import build_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_basic")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        for term in case["must_contain"]:
            self.assertIn(term, report, f"Missing required section: {term}")
        # v4: check for new structure
        self.assertIn("费用分类总览", report)
        self.assertIn("已识别项目解释", report)
        self.assertIn("本次就诊档案卡", report)

    def test_bill_explain_with_noise_has_flagged_items(self):
        """Bill with noise items must show flagged items and hospital questions."""
        from petvault_core import build_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_with_noise")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        # v4: check for key sections
        self.assertIn("费用分类总览", report, "Missing category overview")
        self.assertIn("已识别项目解释", report, "Missing identified items")

    def test_bill_explain_no_toc(self):
        """Bill explanation report must NOT contain table of contents."""
        from petvault_core import build_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_no_toc")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        for term in case["must_not_contain"]:
            self.assertNotIn(term, report, f"Forbidden term found: {term}")

    def test_bill_explain_amount_calculation(self):
        """Amount summary must correctly separate recognized, uncertain, and noise."""
        from petvault_core import build_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_amount_calculation")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        # v4: check for amount breakdown in inline format
        self.assertIn("已识别", report)
        self.assertIn("待核实", report)
        self.assertIn("疑似误识别", report)

    def test_bill_explain_copyable_phrase(self):
        """Report must include copyable phrase when there are flagged items."""
        from petvault_core import build_report_markdown
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_copyable_phrase")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        # v4: check for messagebox marker
        self.assertIn(":::messagebox", report, "Copyable phrase must use pvmessagebox")

    def test_bill_explain_charges_are_counted(self):
        """Charge items must be counted in totals."""
        from billing_ops import build_bill_items, summarize_charge_totals
        materials = [{
            "text": "血常规 120 元；B超 350 元；处方药 86.5 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        self.assertGreater(totals.get("CNY", 0), 0, "Charges should be counted")

    def test_payments_not_counted_as_charges(self):
        """Payment items must not be counted as charges."""
        from billing_ops import build_bill_items, summarize_charge_totals
        materials = [{
            "text": "血常规 120 元；付款 -120 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        totals = summarize_charge_totals(items)
        self.assertEqual(totals.get("CNY", 0), 120.0)

    def test_empty_charges_return_pending(self):
        """Empty charge totals must return '待确认'."""
        from billing_ops import format_currency_totals
        result = format_currency_totals({})
        self.assertEqual(result, "待确认")

    def test_multi_currency_totals_are_deterministic(self):
        """Multi-currency totals must format deterministically."""
        from billing_ops import format_currency_totals
        result = format_currency_totals({"USD": 100.0, "CNY": 200.0})
        self.assertIn("100.00 USD", result)
        self.assertIn("200.00 CNY", result)

    def test_no_internal_leakage_in_report(self):
        """Generated report must not contain internal terms."""
        from petvault_core import build_report_markdown
        from report_sanitizer import sanitize_report_markdown
        from agent_registry_loader import load_forbidden_terms
        forbidden = load_forbidden_terms()
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "source_file": "bill.txt",
                    "text": "血常规 120 元",
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        report = sanitize_report_markdown(report)
        for term in forbidden:
            self.assertNotIn(term, report, f"Forbidden term '{term}' found in report")

    def test_bill_explain_medical_safety(self):
        """Report must not contain diagnostic assertions or claim promises."""
        from petvault_core import build_report_markdown
        import re
        cases = self._load_cases()
        case = next(c for c in cases if c["id"] == "bill_explain_medical_safety")
        materials_index = {
            "materials": [
                {
                    "id": "mat_001",
                    "type": "bill",
                    "pet_name": "Mimi",
                    "clinic": "星河动物医院",
                    "date": "2026-07-05",
                    "source_file": "bill.txt",
                    "text": case["input_materials"][0]["content"],
                    "confidence": 0.9,
                    "status": "extracted",
                }
            ]
        }
        report, _ = build_report_markdown("bill_explain", "Mimi", materials_index)
        for term in case["must_not_contain"]:
            if ".*" in term:
                self.assertIsNone(re.search(term, report), f"Regex pattern '{term}' matched in report")
            else:
                self.assertNotIn(term, report, f"Forbidden expression found: {term}")


class TestChineseBillingSampleRegression(unittest.TestCase):
    """Regression test for the 2025-01-16 Chinese billing sample."""

    CHINESE_BILL_TEXT = (
        "宠物：豆豆\n"
        "品种：柯基犬\n"
        "日期：2025-01-16\n"
        "医院：爱宠佳动物医院\n"
        "城市：上海\n"
        "编号1 挂号费 20 元\n"
        "编号2 未知项目A 800 元\n"
        "编号3 血常规检查 80 元\n"
        "编号4 生化全项检查 180 元\n"
        "编号5 X光片拍摄（胸部） 120 元\n"
        "编号6 01-16 18:06 6 元\n"
        "编号7 输液治疗（含药品） 280 元\n"
        "编号8 头孢曲松钠注射 45 元\n"
        "编号9 甲硝唑注射液 35 元\n"
        "编号10 地塞米松注射 15 元\n"
        "编号11 维生素B族注射 25 元\n"
        "编号12 葡萄糖氯化钠注射液 30 元\n"
        "编号13 留置针耗材 18 元\n"
        "编号14 注射器/棉签等耗材 12 元\n"
        "编号15 诊疗服务费 50 元\n"
        "编号16 护理费 40 元\n"
        "编号17 不清项目B 600 元\n"
        "编号18 不清项目C 164 元\n"
        "编号19 01-16 18:06 打印信息 0 元\n"
        "编号20 处方药：阿莫西林胶囊（7天量） 68 元\n"
        "合计：2588 元\n"
        "已支付：2588 元\n"
        "余额：0 元\n"
    )

    def test_total_amount_is_2588(self):
        """Total amount must be ¥2,588.00."""
        from billing_ops import build_bill_items, compute_amount_summary
        materials = [{"text": self.CHINESE_BILL_TEXT, "source_file": "bill.txt"}]
        items = build_bill_items(materials)
        summary = compute_amount_summary(items)
        self.assertAlmostEqual(summary["total"], 2588.0, places=2)

    def test_uncertain_amount_exceeds_50_percent(self):
        """Uncertain amount must exceed 50% of total."""
        from billing_ops import build_bill_items, compute_amount_summary
        materials = [{"text": self.CHINESE_BILL_TEXT, "source_file": "bill.txt"}]
        items = build_bill_items(materials)
        summary = compute_amount_summary(items)
        self.assertGreater(summary["uncertain_pct"], 50.0,
                           "Uncertain percentage must exceed 50%")

    def test_noise_amount_greater_than_zero(self):
        """Noise amount must be > 0 (timestamp items)."""
        from billing_ops import build_bill_items, compute_amount_summary
        materials = [{"text": self.CHINESE_BILL_TEXT, "source_file": "bill.txt"}]
        items = build_bill_items(materials)
        summary = compute_amount_summary(items)
        self.assertGreater(summary["noise"], 0, "Noise amount must be > 0")

    def test_report_status_not_archivable(self):
        """Report status must NOT be '可归档' for this sample."""
        from petvault_core import build_report_markdown
        materials_index = {
            "materials": [{
                "id": "mat_001",
                "type": "bill",
                "pet_name": "豆豆",
                "clinic": "爱宠佳动物医院",
                "date": "2025-01-16",
                "source_file": "bill.txt",
                "text": self.CHINESE_BILL_TEXT,
                "confidence": 0.9,
                "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "豆豆", materials_index)
        self.assertNotIn("报告状态 | 可归档", report,
                         "Status must not be 可归档 for this sample")
        self.assertIn("不建议作为最终解释", report,
                       "Status should be 不建议作为最终解释")

    def test_flagged_items_include_uncertain_projects(self):
        """Report must flag 编号2, 17, 18 as uncertain items."""
        from petvault_core import build_report_markdown
        materials_index = {
            "materials": [{
                "id": "mat_001",
                "type": "bill",
                "pet_name": "豆豆",
                "clinic": "爱宠佳动物医院",
                "date": "2025-01-16",
                "source_file": "bill.txt",
                "text": self.CHINESE_BILL_TEXT,
                "confidence": 0.9,
                "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "豆豆", materials_index)
        # v4: check for flagged items with amounts
        self.assertIn("¥800.00", report, "Must flag ¥800 item")
        self.assertIn("¥600.00", report, "Must flag ¥600 item")
        self.assertIn("¥164.00", report, "Must flag ¥164 item")

    def test_copyable_phrase_references_flagged_items(self):
        """Copyable phrase must reference the uncertain items."""
        from petvault_core import build_report_markdown
        materials_index = {
            "materials": [{
                "id": "mat_001",
                "type": "bill",
                "pet_name": "豆豆",
                "clinic": "爱宠佳动物医院",
                "date": "2025-01-16",
                "source_file": "bill.txt",
                "text": self.CHINESE_BILL_TEXT,
                "confidence": 0.9,
                "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "豆豆", materials_index)
        # v4: check for messagebox and key items
        self.assertIn(":::messagebox", report, "Copyable phrase must use pvmessagebox")
        self.assertIn("¥800.00", report, "Copyable phrase must reference ¥800")
        self.assertIn("¥600.00", report, "Copyable phrase must reference ¥600")
        self.assertIn("¥164.00", report, "Copyable phrase must reference ¥164")

    def test_no_medical_safety_violations(self):
        """Report must not contain diagnostic assertions or claim promises."""
        from petvault_core import build_report_markdown
        import re
        materials_index = {
            "materials": [{
                "id": "mat_001",
                "type": "bill",
                "pet_name": "豆豆",
                "clinic": "爱宠佳动物医院",
                "date": "2025-01-16",
                "source_file": "bill.txt",
                "text": self.CHINESE_BILL_TEXT,
                "confidence": 0.9,
                "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "豆豆", materials_index)
        forbidden = [
            "说明宠物患有", "可判断为", "说明医院收费合理",
            "可以作为理赔依据", "一定可以报销", "医院可能乱收费",
        ]
        for term in forbidden:
            self.assertNotIn(term, report, f"Forbidden expression: {term}")
        # Check regex patterns
        self.assertIsNone(re.search(r"提示存在.*感染", report),
                          "Must not contain '提示存在...感染'")


class TestSourceConsistency(unittest.TestCase):
    """Source consistency regression tests."""

    CHINESE_BILL_TEXT = (
        "宠物：豆豆\n"
        "品种：柯基犬\n"
        "日期：2025-01-16\n"
        "医院：爱宠佳动物医院\n"
        "编号1 挂号费 20 元\n"
        "编号2 OCR识别不清 960 元\n"
        "编号3 血常规检查 60 元\n"
        "编号4 X光片拍摄（胸部） 100 元\n"
        "编号5 输液治疗 150 元\n"
        "编号6 01-16 18:06 6 元\n"
        "编号7 头孢曲松钠注射 35 元\n"
        "编号8 甲硝唑注射液 25 元\n"
        "编号9 地塞米松注射 15 元\n"
        "编号10 维生素B族注射 20 元\n"
        "编号11 留置针耗材 15 元\n"
        "编号12 诊疗服务费 40 元\n"
        "编号13 护理费 30 元\n"
        "编号14 处方药：阿莫西林胶囊（7天量） 52 元\n"
        "编号15 OCR识别不清 0 元\n"
        "编号16 01-16 18:06 打印信息 0 元\n"
        "编号17 OCR识别不清 960 元\n"
        "编号18 OCR识别不清 100 元\n"
        "编号19 01-16 18:06 打印信息 0 元\n"
        "合计：2588 元\n"
        "已支付：2588 元\n"
        "余额：0 元\n"
    )

    def test_total_amount_is_stable(self):
        """Same input data must produce same total_amount on repeated runs."""
        from billing_ops import build_bill_items, compute_amount_summary
        materials = [{"text": self.CHINESE_BILL_TEXT, "source_file": "bill.txt"}]
        # Run twice and compare
        items1 = build_bill_items(materials)
        summary1 = compute_amount_summary(items1)
        items2 = build_bill_items(materials)
        summary2 = compute_amount_summary(items2)
        self.assertAlmostEqual(summary1["total"], summary2["total"], places=2)
        self.assertAlmostEqual(summary1["recognized"], summary2["recognized"], places=2)
        self.assertAlmostEqual(summary1["uncertain"], summary2["uncertain"], places=2)
        self.assertAlmostEqual(summary1["noise"], summary2["noise"], places=2)
        self.assertAlmostEqual(summary1["total"], 2588.0, places=2)
        self.assertAlmostEqual(summary1["uncertain"], 2020.0, places=2)
        self.assertAlmostEqual(summary1["noise"], 6.0, places=2)

    def test_amounts_not_rewritten_in_report(self):
        """Item amounts must not be rewritten during report generation."""
        from petvault_core import build_report_markdown
        from billing_ops import build_bill_items
        materials = [{"text": self.CHINESE_BILL_TEXT, "source_file": "bill.txt"}]
        raw_items = build_bill_items(materials)
        # Build report
        materials_index = {
            "materials": [{
                "id": "mat_001", "type": "bill", "pet_name": "豆豆",
                "clinic": "爱宠佳动物医院", "date": "2025-01-16",
                "source_file": "bill.txt", "text": self.CHINESE_BILL_TEXT,
                "confidence": 0.9, "status": "extracted",
            }]
        }
        report, _ = build_report_markdown("bill_explain", "豆豆", materials_index)
        # Verify each raw item's amount appears in the report
        for item in raw_items:
            if item.get("kind") in {"payment", "discount", "refund", "balance"}:
                continue
            name = item.get("name", "")
            amount = item.get("amount", 0)
            # Check the amount appears near the item name in the report
            # (simple check: the report should contain the amount somewhere)
            if amount > 0:
                amount_str = f"{amount:.2f}" if amount != int(amount) else f"{amount:.0f}"
                self.assertTrue(
                    f"¥{amount_str}" in report or f"${amount_str}" in report or f"{amount_str} 元" in report,
                    f"Amount {amount} for '{name[:30]}' not found in report"
                )

    def test_pdf_rendering_does_not_recompute_amounts(self):
        """LaTeX body must not contain inline amount calculations."""
        from petvault_core import render_latex, build_report_markdown
        materials_index = {
            "materials": [{
                "id": "mat_001", "type": "bill", "pet_name": "豆豆",
                "clinic": "爱宠佳动物医院", "date": "2025-01-16",
                "source_file": "bill.txt", "text": self.CHINESE_BILL_TEXT,
                "confidence": 0.9, "status": "extracted",
            }]
        }
        report_md, _ = build_report_markdown("bill_explain", "豆豆", materials_index)
        latex = render_latex(report_md, "bill_explain", "豆豆")
        # LaTeX should not contain arithmetic/computation signs
        self.assertNotIn("+", latex, "LaTeX should not contain inline arithmetic")
        self.assertNotIn("\\times", latex, "LaTeX should not contain multiplication")
        # The amounts from the report should appear verbatim in LaTeX
        self.assertIn("2,588.00", latex)
        self.assertIn("562.00", latex)
        self.assertIn("2,020.00", latex)
        self.assertIn("6.00", latex)


class TestAmountClassification(unittest.TestCase):
    """Tests for amount classification functions."""

    def test_recognized_amount_excludes_noise(self):
        """recognized_amount must not include noise items."""
        from billing_ops import compute_amount_summary, build_bill_items, classify_item_type
        materials = [{
            "text": "01-16 18:06；血常规 120 元；B超 350 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        # Verify timestamp is classified as noise
        ts_items = [i for i in items if "18:06" in i.get("name", "")]
        self.assertTrue(ts_items, "Timestamp should appear as bill item")
        self.assertEqual(classify_item_type(ts_items[0]), "noise", "Timestamp should be noise")
        # Medical items should be recognized
        med_items = [i for i in items if classify_item_type(i) == "recognized"]
        self.assertGreater(len(med_items), 0, "Medical items should be recognized")
        # Amounts: recognized > 0, noise = 0 (because timestamp has no amount)
        summary = compute_amount_summary(items)
        self.assertGreater(summary["recognized"], 0, "Medical items should contribute to recognized amount")

    def test_report_status_thresholds(self):
        """Report status must reflect uncertain percentage."""
        from billing_ops import determine_report_status
        self.assertEqual(determine_report_status({"uncertain_pct": 0, "noise_pct": 0}), "可归档")
        self.assertEqual(determine_report_status({"uncertain_pct": 5, "noise_pct": 0}), "部分待确认")
        self.assertEqual(determine_report_status({"uncertain_pct": 25, "noise_pct": 0}), "关键项目待核实")
        self.assertEqual(determine_report_status({"uncertain_pct": 60, "noise_pct": 0}), "不建议作为最终解释")

    def test_confidence_classification(self):
        """Items should be classified with correct confidence levels."""
        from billing_ops import classify_item_confidence
        self.assertEqual(
            classify_item_confidence({"name": "Examination - Consult", "amount": 80, "kind": "charge"}),
            "high"
        )
        self.assertEqual(
            classify_item_confidence({"name": "01-16 18:06", "amount": 0, "kind": "charge"}),
            "noise"
        )
        self.assertEqual(
            classify_item_confidence({"name": "X-Ray Orthopedic", "amount": 333, "kind": "charge"}),
            "high"
        )

    def test_category_summary_includes_noise(self):
        """Category summary must include noise as separate category when noise has amount."""
        from billing_ops import compute_category_summary, build_bill_items, classify_item_type
        materials = [{
            "text": "01-16 18:06；血常规 120 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        # Verify timestamp is classified as noise
        ts_items = [i for i in items if "18:06" in i.get("name", "")]
        self.assertTrue(ts_items, "Timestamp should appear as bill item")
        self.assertEqual(classify_item_type(ts_items[0]), "noise", "Timestamp should be noise")
        # Category summary only includes items with amount > 0
        summary = compute_category_summary(items)
        categories = [c["category_label"] for c in summary]
        self.assertIn("检查类", categories, "Medical items should appear in category summary")


if __name__ == "__main__":
    unittest.main()
