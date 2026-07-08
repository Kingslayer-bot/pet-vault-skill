# PetVault Skill 工作流与脚本工程迭代 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一禁止词注册表、提取 billing_ops.py、连接 eval_cases、建立 fixtures，提升 PetVault 工程质量。

**Architecture:** 创建 `agent_registry_loader.py` 作为单一真相源，从 `.agents/forbidden_terms_registry.yaml` 加载禁止词。提取 `billing_ops.py` 包含纯账单函数。创建 `test_eval_cases.py` 连接 YAML 测试用例。

**Tech Stack:** Python 3.11+, PyYAML (optional), unittest

---

## Task 1: 创建 agent_registry_loader.py — 统一禁止词注册表

**Covers:** 禁止词统一注册表真正接入代码

**Files:**
- Create: `pet-vault-skill/scripts/agent_registry_loader.py`
- Test: `pet-vault-skill/tests/test_agent_registry_loader.py`

- [ ] **Step 1: 创建 agent_registry_loader.py**

```python
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
```

- [ ] **Step 2: 创建 test_agent_registry_loader.py**

```python
"""Tests for agent_registry_loader module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from agent_registry_loader import (
    get_registry_path,
    load_forbidden_terms,
    load_internal_type_map,
    load_internal_status_map,
    registry_exists,
    _FALLBACK_FORBIDDEN_TERMS,
)


class TestRegistryExists(unittest.TestCase):
    def test_registry_file_exists(self):
        self.assertTrue(registry_exists())

    def test_registry_path_points_to_yaml(self):
        path = get_registry_path()
        self.assertTrue(path.name.endswith(".yaml"))
        self.assertTrue(path.exists())


class TestLoadForbiddenTerms(unittest.TestCase):
    def test_returns_non_empty_list(self):
        terms = load_forbidden_terms()
        self.assertGreater(len(terms), 0)

    def test_contains_representative_entries(self):
        terms = load_forbidden_terms()
        self.assertIn("insurance_policy", terms)
        self.assertIn("routing", terms)
        self.assertIn("dispatch", terms)
        self.assertIn("置信度", terms)
        self.assertIn("[FORBIDDEN]", terms)
        self.assertIn("PRD", terms)
        self.assertIn("Harness", terms)

    def test_contains_all_fallback_terms_if_registry_missing(self):
        terms = load_forbidden_terms()
        for term in _FALLBACK_FORBIDDEN_TERMS:
            self.assertIn(term, terms, f"Missing term: {term}")


class TestLoadTypeMap(unittest.TestCase):
    def test_returns_non_empty_dict(self):
        type_map = load_internal_type_map()
        self.assertGreater(len(type_map), 0)

    def test_maps_known_types(self):
        type_map = load_internal_type_map()
        self.assertEqual(type_map["invoice"], "发票/收据")
        self.assertEqual(type_map["insurance_policy"], "保险保单")
        self.assertEqual(type_map["lab_report"], "化验报告")


class TestLoadStatusMap(unittest.TestCase):
    def test_returns_non_empty_dict(self):
        status_map = load_internal_status_map()
        self.assertGreater(len(status_map), 0)

    def test_maps_known_statuses(self):
        status_map = load_internal_status_map()
        self.assertEqual(status_map["extracted"], "已提取")
        self.assertEqual(status_map["indexed_only"], "已索引（未解析正文）")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试验证加载器**

Run: `python -m unittest pet-vault-skill.tests.test_agent_registry_loader -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add pet-vault-skill/scripts/agent_registry_loader.py pet-vault-skill/tests/test_agent_registry_loader.py
git commit -m "feat: add agent_registry_loader for unified forbidden terms loading"
```

---

## Task 2: 修改 report_sanitizer.py 使用统一加载器

**Covers:** 禁止词统一注册表真正接入代码

**Files:**
- Modify: `pet-vault-skill/scripts/report_sanitizer.py`

- [ ] **Step 1: 修改 report_sanitizer.py 导入**

将 `report_sanitizer.py` 修改为从 `agent_registry_loader` 加载：

```python
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
```

- [ ] **Step 2: 运行 sanitizer 测试验证**

Run: `python -m unittest pet-vault-skill.tests.test_internal_leakage -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add pet-vault-skill/scripts/report_sanitizer.py
git commit -m "refactor: report_sanitizer loads terms from agent_registry_loader"
```

---

## Task 3: 修改 test_internal_leakage.py 使用统一加载器

**Covers:** 禁止词统一注册表真正接入代码

**Files:**
- Modify: `pet-vault-skill/tests/test_internal_leakage.py`

- [ ] **Step 1: 修改 test_internal_leakage.py 导入**

将 `test_internal_leakage.py` 修改为从 `agent_registry_loader` 加载：

```python
"""Tests for internal term leakage prevention."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
import uuid
import tempfile
import os
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parent
sys.path.insert(0, str(SKILL / "scripts"))

import petvault_core
from report_sanitizer import sanitize_report_markdown, build_user_manifest
from agent_registry_loader import load_forbidden_terms, load_internal_type_map, load_internal_status_map

TMP_ROOT = Path(os.environ.get("PETVAULT_TEST_TMP", Path(tempfile.gettempdir()) / "pet_vault_leakage_tests"))

# Load from registry (single source of truth)
FORBIDDEN_IN_REPORT = load_forbidden_terms()
INTERNAL_TYPE_MAP = load_internal_type_map()
INTERNAL_STATUS_MAP = load_internal_status_map()

FORBIDDEN_IN_MANIFEST = [
    "routing",
    "pdf_policy",
]
```

- [ ] **Step 2: 运行全部泄漏测试**

Run: `python -m unittest pet-vault-skill.tests.test_internal_leakage -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add pet-vault-skill/tests/test_internal_leakage.py
git commit -m "refactor: test_internal_leakage loads terms from agent_registry_loader"
```

---

## Task 4: 提取 billing_ops.py

**Covers:** 提取 billing_ops.py

**Files:**
- Create: `pet-vault-skill/scripts/billing_ops.py`
- Modify: `pet-vault-skill/scripts/petvault_core.py` (add compatibility imports)
- Test: `pet-vault-skill/tests/test_billing_ops.py`

- [ ] **Step 1: 创建 billing_ops.py**

从 `petvault_core.py` 提取以下函数和常量：

```python
"""billing_ops: Pure billing functions for amount parsing, item extraction, and totals."""
from __future__ import annotations

import re

BILL_CATEGORIES = {
    "检查": ["血常规", "生化", "x光", "x-ray", "b超", "超声", "ct", "检查", "化验"],
    "治疗": ["手术", "处置", "输液", "治疗", "住院", "清创"],
    "药品": ["药", "处方", "medication", "tablet", "capsule", "针剂"],
    "耗材": ["导管", "留置针", "敷料", "耗材", "纱布"],
    "服务": ["挂号", "诊疗", "护理", "服务", "会诊"],
}


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
    """Build bill items from materials with amount, category, and source."""
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
                        "name": segment,
                        "amount": abs(mention["amount"]),
                        "signed_amount": mention["amount"],
                        "currency": mention["currency"],
                        "kind": mention["kind"],
                        "category": category,
                        "source_file": material["source_file"],
                    })
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
```

- [ ] **Step 2: 更新 petvault_core.py 添加兼容性导入**

在 `petvault_core.py` 中添加：

```python
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
)
```

移除 `petvault_core.py` 中已提取的函数定义。

- [ ] **Step 3: 创建 test_billing_ops.py**

```python
"""Tests for billing_ops module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from billing_ops import (
    parse_money_mentions,
    build_bill_items,
    summarize_charge_totals,
    format_currency_totals,
    format_money,
    normalize_currency,
    classify_money_kind,
)


class TestNormalizeCurrency(unittest.TestCase):
    def test_usd_variants(self):
        self.assertEqual(normalize_currency("$"), "USD")
        self.assertEqual(normalize_currency("US$"), "USD")
        self.assertEqual(normalize_currency("USD"), "USD")

    def test_cny_variants(self):
        self.assertEqual(normalize_currency("元"), "CNY")
        self.assertEqual(normalize_currency("RMB"), "CNY")
        self.assertEqual(normalize_currency("CNY"), "CNY")
        self.assertEqual(normalize_currency("¥"), "CNY")


class TestClassifyMoneyKind(unittest.TestCase):
    def test_charge(self):
        self.assertEqual(classify_money_kind("Exam $80.00", 80.0), "charge")

    def test_payment(self):
        self.assertEqual(classify_money_kind("Payment -$80.00", -80.0), "payment")
        self.assertEqual(classify_money_kind("CareCredit $80.00", 80.0), "payment")

    def test_discount(self):
        self.assertEqual(classify_money_kind("Discount ($100.00)", -100.0), "discount")

    def test_total(self):
        self.assertEqual(classify_money_kind("Total $500.00", 500.0), "total")


class TestParseMoneyMentions(unittest.TestCase):
    def test_basic_amount(self):
        mentions = parse_money_mentions("Exam $80.00")
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0]["amount"], 80.0)
        self.assertEqual(mentions[0]["currency"], "USD")

    def test_cny_amount(self):
        mentions = parse_money_mentions("血常规 120 元")
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0]["amount"], 120.0)
        self.assertEqual(mentions[0]["currency"], "CNY")

    def test_multiple_amounts(self):
        mentions = parse_money_mentions("Exam $80.00; X-Ray $333.00")
        self.assertEqual(len(mentions), 2)


class TestBuildBillItems(unittest.TestCase):
    def test_basic_items(self):
        materials = [{
            "text": "血常规 120 元；B超 350 元",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["category"], "检查")
        self.assertEqual(items[1]["category"], "检查")


class TestSummarizeChargeTotals(unittest.TestCase):
    def test_empty_items(self):
        totals = summarize_charge_totals([])
        self.assertEqual(totals, {})

    def test_charge_items(self):
        items = [
            {"kind": "charge", "amount": 100.0, "currency": "USD"},
            {"kind": "charge", "amount": 200.0, "currency": "USD"},
        ]
        totals = summarize_charge_totals(items)
        self.assertEqual(totals["USD"], 300.0)

    def test_payment_not_counted(self):
        items = [
            {"kind": "payment", "amount": 100.0, "currency": "USD"},
        ]
        totals = summarize_charge_totals(items)
        self.assertEqual(totals, {})


class TestFormatCurrencyTotals(unittest.TestCase):
    def test_empty_totals(self):
        self.assertEqual(format_currency_totals({}), "待确认")

    def test_zero_totals(self):
        self.assertEqual(format_currency_totals({"USD": 0.0}), "待确认")

    def test_normal_totals(self):
        result = format_currency_totals({"USD": 500.0})
        self.assertIn("500.00", result)
        self.assertIn("USD", result)


class TestNoInternalLabels(unittest.TestCase):
    def test_no_internal_labels_in_output(self):
        materials = [{
            "text": "Exam $80.00",
            "source_file": "bill.txt",
        }]
        items = build_bill_items(materials)
        for item in items:
            self.assertNotIn("insurance_policy", str(item))
            self.assertNotIn("lab_report", str(item))
            self.assertNotIn("dispatch", str(item))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: 运行全部测试**

Run: `python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v`
Expected: PASS (>= 88 tests)

- [ ] **Step 5: Commit**

```bash
git add pet-vault-skill/scripts/billing_ops.py pet-vault-skill/tests/test_billing_ops.py pet-vault-skill/scripts/petvault_core.py
git commit -m "feat: extract billing_ops.py with pure billing functions"
```

---

## Task 5: 连接 eval_cases 到测试

**Covers:** .agents/eval_cases 被测试读取

**Files:**
- Create: `pet-vault-skill/tests/test_eval_cases.py`

- [ ] **Step 1: 创建 test_eval_cases.py**

```python
"""Tests that read and validate .agents/eval_cases/*.yaml golden fixtures."""
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
class TestEvalCaseFilesExist(unittest.TestCase):
    """Verify eval case files exist and are valid YAML."""

    def test_internal_leakage_cases_exist(self):
        path = EVAL_DIR / "internal_leakage_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_pdf_render_cases_exist(self):
        path = EVAL_DIR / "pdf_render_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_billing_report_cases_exist(self):
        path = EVAL_DIR / "billing_report_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_emergency_routing_cases_exist(self):
        path = EVAL_DIR / "emergency_routing_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestEvalCaseSchema(unittest.TestCase):
    """Verify eval cases have required fields."""

    def _load_cases(self, filename: str) -> list[dict]:
        path = EVAL_DIR / filename
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_internal_leakage_cases_have_ids(self):
        cases = self._load_cases("internal_leakage_cases.yaml")
        for case in cases:
            self.assertIn("id", case, f"Missing id in case: {case}")
            self.assertIn("must_not_contain", case, f"Missing must_not_contain in case: {case.get('id')}")

    def test_pdf_render_cases_have_ids(self):
        cases = self._load_cases("pdf_render_cases.yaml")
        for case in cases:
            self.assertIn("id", case)
            self.assertIn("must_contain_latex", case)

    def test_billing_report_cases_have_ids(self):
        cases = self._load_cases("billing_report_cases.yaml")
        for case in cases:
            self.assertIn("id", case)


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestInternalLeakageEvalCases(unittest.TestCase):
    """Run internal leakage eval cases against sanitizer."""

    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "internal_leakage_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_all_cases_pass_sanitizer(self):
        from report_sanitizer import sanitize_report_markdown
        cases = self._load_cases()
        for case in cases:
            with self.subTest(case_id=case.get("id")):
                input_md = case.get("input", "")
                result = sanitize_report_markdown(input_md)
                for term in case.get("must_not_contain", []):
                    self.assertNotIn(term, result, f"Case '{case.get('id')}': '{term}' found in sanitized output")
                for term in case.get("must_contain", []):
                    self.assertIn(term, result, f"Case '{case.get('id')}': '{term}' not found in sanitized output")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestPdfRenderEvalCases(unittest.TestCase):
    """Run PDF render eval cases against latex_ops."""

    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "pdf_render_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_all_cases_pass_latex(self):
        from latex_ops import markdown_to_latex_body
        cases = self._load_cases()
        for case in cases:
            with self.subTest(case_id=case.get("id")):
                input_md = case.get("input", "")
                result = markdown_to_latex_body(input_md)
                for term in case.get("must_contain_latex", []):
                    self.assertIn(term, result, f"Case '{case.get('id')}': '{term}' not found in LaTeX output")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行 eval_cases 测试**

Run: `python -m unittest pet-vault-skill.tests.test_eval_cases -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add pet-vault-skill/tests/test_eval_cases.py
git commit -m "feat: connect .agents/eval_cases to automated tests"
```

---

## Task 6: 创建测试 fixtures

**Covers:** 建立 tests/fixtures 与 tests/golden

**Files:**
- Create: `pet-vault-skill/tests/fixtures/sample_invoice_transcription.md`
- Create: `pet-vault-skill/tests/fixtures/sample_report_with_table.md`
- Create: `pet-vault-skill/tests/fixtures/sample_internal_leakage_report.md`

- [ ] **Step 1: 创建 sample_invoice_transcription.md**

```markdown
Material type: invoice / bill
Pet: Mimi
Clinic: 星河动物医院
Date: 2026-07-05

血常规 120 元
B超 350 元
处方药 86.5 元
挂号费 30 元
总计 586.5 元
```

- [ ] **Step 2: 创建 sample_report_with_table.md**

```markdown
# 宠物医疗账单解释报告

宠物名称：Mimi

## 费用分类

| 项目 | 金额 | 类别 |
|------|------|------|
| 血常规 | 120.00 CNY | 检查 |
| B超 | 350.00 CNY | 检查 |
| 处方药 | 86.50 CNY | 药品 |

## 待确认

- 宠物品种：未确认
```

- [ ] **Step 3: 创建 sample_internal_leakage_report.md**

```markdown
# 宠物医疗账单解释报告

## 使用材料
- bill.txt：类型=insurance_policy；日期=2026-01-01；置信度=0.9；状态=extracted

## 事实
- routing: request_mentions_billing
- classification: dispatch
```

- [ ] **Step 4: Commit**

```bash
git add pet-vault-skill/tests/fixtures/
git commit -m "feat: add test fixtures for billing, latex, and leakage tests"
```

---

## Task 7: 更新 AGENTS.md 添加代码质量指南

**Covers:** Code quality review

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 在 AGENTS.md 中添加代码质量部分**

在 `## Safe Refactor Rules` 之后添加：

```markdown
## Code Quality Standards

### Google-style Consistency
- Module docstrings required for all scripts
- Function docstrings for public helpers
- Type annotations on function signatures
- Clear, descriptive variable names
- No unused imports
- No broad `except` unless justified
- Stable import order: stdlib → third-party → local

### Karpathy-style Simplicity
- Plain, readable functions
- Minimal abstraction — prefer direct code over clever patterns
- No unnecessary classes — use functions when possible
- No dependency bloat — check existing deps before adding new ones
- Simple data flow — explicit over implicit
- Easy to debug — function length should be reasonable
- Module responsibilities should be clear from the filename

### Deterministic vs Agent Logic
- **Deterministic Python**: All data processing, classification, rendering, sanitization, QA
- **Agent/LLM**: Only for natural-language interpretation at the boundary (e.g., understanding user intent)
- Never mix deterministic logic with LLM calls in the same function
- Keep LLM calls isolated and testable

### Commands to Run Tests
```bash
# All tests
python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v

# Specific module tests
python -m unittest pet-vault-skill.tests.test_agent_registry_loader -v
python -m unittest pet-vault-skill.tests.test_billing_ops -v
python -m unittest pet-vault-skill.tests.test_eval_cases -v
python -m unittest pet-vault-skill.tests.test_internal_leakage -v
```
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add Google-style and Karpathy-style code quality guidelines to AGENTS.md"
```

---

## Task 8: 最终验证

- [ ] **Step 1: 运行全部测试**

Run: `python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v`
Expected: PASS (>= 88 tests, likely 100+)

- [ ] **Step 2: 验证禁止词统一**

检查 `report_sanitizer.py` 和 `test_internal_leakage.py` 都从 `agent_registry_loader` 加载，不再有独立的完整禁止词列表。

- [ ] **Step 3: 验证 billing_ops.py**

检查 `billing_ops.py` 包含纯账单函数，`petvault_core.py` 通过兼容性导入使用。

- [ ] **Step 4: 验证 eval_cases 连接**

检查 `test_eval_cases.py` 读取并验证 `.agents/eval_cases/*.yaml`。

- [ ] **Step 5: 验证 git 状态**

Run: `git status`
Expected: 干净的工作树或只有预期的更改。
