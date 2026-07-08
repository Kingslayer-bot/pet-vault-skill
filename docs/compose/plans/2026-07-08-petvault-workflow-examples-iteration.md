# PetVault Skill 工作流、Examples、材料理解与 Golden Eval 迭代 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使 PetVault 从"有工程化管线"变成"有用户任务流验证的 skill"，通过 examples、行为测试和材料理解提取。

**Architecture:** 创建 examples/ 展示用户流程，添加 skill_workflow_cases.yaml 接入测试，提取 material_ops.py 减轻 petvault_core.py 负担，同步 SKILL.md 反映当前 4-pipeline 架构。

**Tech Stack:** Python 3.11+, PyYAML (optional), unittest

---

## Task 1: 创建 examples/ 目录 — 覆盖 4 个主用户流程

**Covers:** examples/ 存在且覆盖主流程

**Files:**
- Create: `pet-vault-skill/examples/README.md`
- Create: `pet-vault-skill/examples/bill_explain/README.md`
- Create: `pet-vault-skill/examples/bill_explain/input/request.txt`
- Create: `pet-vault-skill/examples/bill_explain/input/sample_invoice_transcription.md`
- Create: `pet-vault-skill/examples/bill_explain/expected/report.md`
- Create: `pet-vault-skill/examples/knowledge_query/README.md`
- Create: `pet-vault-skill/examples/knowledge_query/input/request.txt`
- Create: `pet-vault-skill/examples/knowledge_query/expected/answer.md`
- Create: `pet-vault-skill/examples/emergency_guardrail/README.md`
- Create: `pet-vault-skill/examples/emergency_guardrail/input/request.txt`
- Create: `pet-vault-skill/examples/emergency_guardrail/expected/response.md`
- Create: `pet-vault-skill/examples/insurance_boundary/README.md`
- Create: `pet-vault-skill/examples/insurance_boundary/input/request.txt`
- Create: `pet-vault-skill/examples/insurance_boundary/expected/response.md`

- [ ] **Step 1: 创建 examples/README.md**

```markdown
# PetVault Skill Examples

This directory contains synthetic examples showing how the PetVault skill handles common user tasks.

## Running Examples

### Bill Explanation
```bash
python scripts/run_pipeline.py \
  --input examples/bill_explain/input \
  --output /tmp/petvault_bill_explain \
  --vault /tmp/petvault_vault \
  --request "帮我解释这张账单" \
  --pet-name Mimi \
  --skip-pdf-compile
```

### Knowledge Query
```bash
python scripts/query_knowledge_base.py "理赔需要哪些材料" --limit 3
```

### Emergency Detection
```bash
python scripts/petvault_dispatch.py --request "狗吃了巧克力怎么办"
```

## What's User-Visible vs Internal

| Artifact | User-Visible? | Description |
|----------|--------------|-------------|
| `report.md` | ✅ Yes | Main report content |
| `report.pdf` | ✅ Yes | PDF version of report |
| `user_manifest.json` | ✅ Yes | User-safe metadata |
| `manifest.json` | ❌ Internal | Contains routing reasons |
| `qa_result.json` | ❌ Internal | QA check details |
| `build.log` | ❌ Internal | PDF compilation log |
| `materials_index.json` | ❌ Internal | Material classification |

## Safety Boundaries

- No diagnosis replacement
- No legal judgment
- No insurance payout promise
- No hospital fraud accusation
- No internal terms in user output
```

- [ ] **Step 2: 创建 bill_explain 示例**

`examples/bill_explain/README.md`:
```markdown
# Bill Explanation Example

This example shows how PetVault explains a veterinary bill.

## Input
- `request.txt`: User request to explain a bill
- `sample_invoice_transcription.md`: Synthetic invoice transcription

## Expected Output
- `report.md`: Bill explanation report with cost categories, high-value items, and questions for the clinic

## Workflow
1. Dispatch detects bill-related request → routes to report pipeline
2. Material organizer classifies as invoice/bill
3. Bill analysis extracts line items and totals
4. Report composer creates structured explanation
5. Sanitizer removes any internal terms
6. Output: user-facing report.md
```

`examples/bill_explain/input/request.txt`:
```text
帮我解释这张账单，我想知道每项费用是什么。
```

`examples/bill_explain/input/sample_invoice_transcription.md`:
```text
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

`examples/bill_explain/expected/report.md`:
```markdown
# 宠物医疗账单解释报告

宠物名称：Mimi

## 使用材料

- sample_invoice_transcription.md，日期 2026-07-05，医院 星河动物医院

## 事实

- 本次账单总收费为 586.50 元。
- 账单包含检查、药品和服务等项目。

## 费用分类

### 检查

- 血常规：120.00 CNY
- B超：350.00 CNY

### 药品

- 处方药：86.50 CNY

### 服务

- 挂号费：30.00 CNY

## 高额项目

- B超：350.00 CNY
- 血常规：120.00 CNY
- 处方药：86.50 CNY

## 待确认

- 宠物品种、性别、绝育状态：材料中未显示。
- 医院诊断和治疗计划：材料中未显示。

## 后续建议

- 保存原始发票和费用明细。
- 如需理赔，请向保险公司确认材料清单。
```

- [ ] **Step 3: 创建 knowledge_query 示例**

`examples/knowledge_query/README.md`:
```markdown
# Knowledge Query Example

This example shows how PetVault answers a knowledge-only question without generating a report.

## Input
- `request.txt`: User question about pet insurance

## Expected Output
- `answer.md`: Brief answer from local knowledge base

## Workflow
1. Dispatch detects knowledge-only question → routes to KB query
2. KB search finds relevant articles
3. Returns concise answer with article references
4. No report generated, no vault update
```

`examples/knowledge_query/input/request.txt`:
```text
理赔需要哪些材料？
```

`examples/knowledge_query/expected/answer.md`:
```markdown
## 本地知识库查询结果

### 1. 理赔材料清单
领域：insurance | 地区：US
常见理赔材料包括：保单、发票、费用明细、处方、检查报告、医生病历。

### 2. 理赔流程说明
领域：insurance | 地区：CN
理赔通常需要：填写理赔申请表、提供原始发票、费用清单、诊断证明、处方复印件。
```

- [ ] **Step 4: 创建 emergency_guardrail 示例**

`examples/emergency_guardrail/README.md`:
```markdown
# Emergency Guardrail Example

This example shows how PetVault detects emergency symptoms and returns urgent safety guidance.

## Input
- `request.txt`: User describing emergency symptoms

## Expected Output
- `response.md`: Urgent safety response with emergency contacts

## Workflow
1. Dispatch detects emergency keywords → routes to emergency response
2. Returns immediate safety guidance
3. Does NOT proceed to report or KB query
4. User must confirm emergency resolved before continuing
```

`examples/emergency_guardrail/input/request.txt`:
```text
狗吃了巧克力，现在在呕吐，怎么办？
```

`examples/emergency_guardrail/expected/response.md`:
```markdown
⚠️ 紧急提醒：你描述的情况可能属于需要立即处理的宠物急症。

请立即联系兽医或拨打宠物中毒热线：
- 美国 ASPCA Poison Control: (888) 426-4435
- 请尽快带宠物到最近的动物医院就诊。

不要等待观察，不要自行用药。记录摄入毒物的种类、数量、时间并带到医院。

---

⚠️ URGENT: The situation you described may be a pet emergency.

Contact your veterinarian immediately or call:
- ASPCA Poison Control (US): (888) 426-4435
- Take your pet to the nearest veterinary hospital now.

Do not wait to observe. Do not self-medicate. Record what was ingested, how much, and when, and bring this information to the hospital.
```

- [ ] **Step 5: 创建 insurance_boundary 示例**

`examples/insurance_boundary/README.md`:
```markdown
# Insurance Boundary Example

This example shows how PetVault handles requests that cross insurance/medical boundaries.

## Input
- `request.txt`: User asking for insurance guarantee

## Expected Output
- `response.md`: Safe completion explaining what PetVault can and cannot do

## Workflow
1. Dispatch detects forbidden request (insurance guarantee) → routes to forbidden response
2. Returns safe completion explaining boundaries
3. Does NOT proceed to report generation
4. Explains what PetVault can help with instead
```

`examples/insurance_boundary/input/request.txt`:
```text
这份材料能保证理赔成功吗？
```

`examples/insurance_boundary/expected/response.md`:
```markdown
抱歉，您的请求不在 PetVault 的服务范围内。

PetVault 可以帮您：
- 整理和解释宠物医疗账单
- 检查理赔材料是否齐全
- 整理长期就诊时间线

PetVault 无法帮您：
- 修改、隐藏或伪造医疗记录
- 提供法律判断或建议
- 推荐特定保险产品

如果您需要整理真实的医疗记录，请上传原始材料。
```

- [ ] **Step 6: 验证 examples 不包含内部词**

```python
# Add to tests/test_examples.py
class TestExamplesNoInternalTerms(unittest.TestCase):
    def test_expected_outputs_no_internal_terms(self):
        """All expected outputs must not contain internal terms."""
        from agent_registry_loader import load_forbidden_terms
        forbidden = load_forbidden_terms()
        examples_dir = SKILL / "examples"
        for expected_file in examples_dir.rglob("expected/*.md"):
            content = expected_file.read_text(encoding="utf-8")
            for term in forbidden:
                self.assertNotIn(term, content, f"{expected_file}: '{term}' found")
```

- [ ] **Step 7: Commit**

```bash
git add pet-vault-skill/examples/
git commit -m "feat: add examples/ with 4 user flow demonstrations"
```

---

## Task 2: 创建 skill_workflow_cases.yaml

**Covers:** skill_workflow_cases.yaml 存在且被测试读取

**Files:**
- Create: `pet-vault-skill/.agents/eval_cases/skill_workflow_cases.yaml`
- Create: `pet-vault-skill/tests/test_skill_workflow_cases.py`

- [ ] **Step 1: 创建 skill_workflow_cases.yaml**

```yaml
# Skill Workflow Eval Cases — Tests user task routing and output safety

cases:
  - id: bill_explain_routing
    name: "Bill explanation routes to report generation"
    input:
      request_text: "帮我解释这张账单"
      materials:
        - name: "bill.txt"
          content: "血常规 120 元；B超 350 元"
    expected:
      route: "report"
      user_visible_must_include:
        - "费用"
      user_visible_must_not_include:
        - "insurance_policy"
        - "routing"
        - "dispatch"

  - id: knowledge_query_routing
    name: "Knowledge question routes to KB query"
    input:
      request_text: "等待期是什么意思"
    expected:
      route: "knowledge_query"
      user_visible_must_include:
        - "等待期"
      user_visible_must_not_include:
        - "report.md"
        - "manifest"

  - id: emergency_routing
    name: "Emergency symptom routes to emergency response"
    input:
      request_text: "狗吃了巧克力怎么办"
    expected:
      route: "emergency"
      user_visible_must_include:
        - "紧急"
        - "兽医"
      user_visible_must_not_include:
        - "report"
        - "知识库"

  - id: forbidden_insurance_guarantee
    name: "Insurance guarantee request is blocked"
    input:
      request_text: "这份材料能保证理赔成功吗"
    expected:
      route: "forbidden"
      user_visible_must_include:
        - "不在"
        - "服务范围"
      user_visible_must_not_include:
        - "可以保证"
        - "一定能赔"

  - id: forbidden_legal_judgment
    name: "Legal judgment request is blocked"
    input:
      request_text: "医院这样收费违法吗"
    expected:
      route: "forbidden"
      user_visible_must_include:
        - "不在"
      user_visible_must_not_include:
        - "违法"
        - "合法"

  - id: mixed_materials_routing
    name: "Mixed bill + medical materials route to report"
    input:
      request_text: "帮我整理这些材料"
      materials:
        - name: "bill.txt"
          content: "血常规 120 元"
        - name: "lab.txt"
          content: "ALT 132 高"
    expected:
      route: "report"
      user_visible_must_include:
        - "材料"
      user_visible_must_not_include:
        - "insurance_policy"
        - "lab_report"

  - id: empty_input_fallback
    name: "Empty input defaults to knowledge query"
    input:
      request_text: ""
    expected:
      route: "knowledge_query"
      user_visible_must_not_include:
        - "routing"
        - "dispatch"

  - id: unknown_input_fallback
    name: "Unknown input defaults to knowledge query"
    input:
      request_text: "今天天气怎么样"
    expected:
      route: "knowledge_query"
      user_visible_must_not_include:
        - "routing"
```

- [ ] **Step 2: 创建 test_skill_workflow_cases.py**

```python
"""Tests that read and validate skill_workflow_cases.yaml."""
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
class TestSkillWorkflowCasesExist(unittest.TestCase):
    def test_file_exists(self):
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        self.assertTrue(path.exists(), f"Missing: {path}")

    def test_cases_have_required_fields(self):
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreater(len(cases), 0)
        for case in cases:
            self.assertIn("id", case)
            self.assertIn("input", case)
            self.assertIn("expected", case)
            self.assertIn("route", case["expected"])


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestSkillWorkflowRouteBehavior(unittest.TestCase):
    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_emergency_cases_route_to_emergency(self):
        from petvault_dispatch import dispatch
        cases = self._load_cases()
        for case in cases:
            if case["expected"]["route"] == "emergency":
                with self.subTest(case_id=case["id"]):
                    result = dispatch(case["input"]["request_text"])
                    self.assertEqual(result, "emergency")

    def test_forbidden_cases_route_to_forbidden(self):
        from petvault_dispatch import dispatch
        cases = self._load_cases()
        for case in cases:
            if case["expected"]["route"] == "forbidden":
                with self.subTest(case_id=case["id"]):
                    result = dispatch(case["input"]["request_text"])
                    self.assertEqual(result, "forbidden")

    def test_knowledge_cases_route_to_knowledge(self):
        from petvault_dispatch import dispatch
        cases = self._load_cases()
        for case in cases:
            if case["expected"]["route"] == "knowledge_query":
                with self.subTest(case_id=case["id"]):
                    result = dispatch(case["input"]["request_text"])
                    self.assertEqual(result, "knowledge_query")


@unittest.skipIf(_yaml is None, "PyYAML not installed")
class TestSkillWorkflowOutputSafety(unittest.TestCase):
    def _load_cases(self) -> list[dict]:
        path = EVAL_DIR / "skill_workflow_cases.yaml"
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("cases", [])

    def test_no_internal_terms_in_expected_outputs(self):
        from agent_registry_loader import load_forbidden_terms
        forbidden = load_forbidden_terms()
        cases = self._load_cases()
        for case in cases:
            with self.subTest(case_id=case["id"]):
                for term in case["expected"].get("user_visible_must_not_include", []):
                    self.assertIn(term, forbidden, f"Case '{case['id']}': '{term}' should be in forbidden registry")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试**

Run: `python -m unittest pet-vault-skill.tests.test_skill_workflow_cases -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add pet-vault-skill/.agents/eval_cases/skill_workflow_cases.yaml pet-vault-skill/tests/test_skill_workflow_cases.py
git commit -m "feat: add skill_workflow_cases.yaml with routing and safety tests"
```

---

## Task 3: 加强 billing_report_cases 行为测试

**Covers:** billing_report_cases.yaml 从结构测试变成行为测试

**Files:**
- Create: `pet-vault-skill/tests/test_billing_report_eval_cases.py`

- [ ] **Step 1: 创建 test_billing_report_eval_cases.py**

```python
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
        """Bill explanation report must contain required sections."""
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
        # Only the charge should be counted, not the payment
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试**

Run: `python -m unittest pet-vault-skill.tests.test_billing_report_eval_cases -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add pet-vault-skill/tests/test_billing_report_eval_cases.py
git commit -m "feat: add behavior tests for billing_report_cases.yaml"
```

---

## Task 4: 提取 material_ops.py

**Covers:** material_ops.py 存在且包含低风险材料理解函数

**Files:**
- Create: `pet-vault-skill/scripts/material_ops.py`
- Modify: `pet-vault-skill/scripts/petvault_core.py` (add compatibility imports)
- Create: `pet-vault-skill/tests/test_material_ops.py`

- [ ] **Step 1: 创建 material_ops.py**

```python
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
```

- [ ] **Step 2: 更新 petvault_core.py 添加兼容性导入**

在 `petvault_core.py` 中添加：

```python
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
```

移除 `petvault_core.py` 中已提取的函数和常量定义。

- [ ] **Step 3: 创建 test_material_ops.py**

```python
"""Tests for material_ops module."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from material_ops import (
    classify_material,
    extract_date,
    extract_pet_name,
    extract_clinic,
    normalize_markdown,
    read_source_text,
)


class TestClassifyMaterial(unittest.TestCase):
    def test_invoice_text(self):
        """Invoice-like text should classify as invoice or bill."""
        text = "Invoice #12345\nBalance due: $500.00"
        type_, conf = classify_material("invoice.txt", text)
        self.assertIn(type_, {"invoice", "bill"})
        self.assertGreater(conf, 0.5)

    def test_insurance_text(self):
        """Insurance-like text should classify as insurance_policy."""
        text = "Policy number: ABC123\nCoverage: $10,000\nDeductible: $500"
        type_, conf = classify_material("policy.txt", text)
        self.assertEqual(type_, "insurance_policy")
        self.assertGreater(conf, 0.5)

    def test_lab_report_text(self):
        """Lab report text should classify as lab_report."""
        text = "血常规\nALT 132 高\nCREA 1.9 高"
        type_, conf = classify_material("lab_results.txt", text)
        self.assertEqual(type_, "lab_report")
        self.assertGreater(conf, 0.5)

    def test_explicit_type_hint(self):
        """Explicit type hint should override classification."""
        text = "Material type: invoice\nPet: Mimi"
        type_, conf = classify_material("unknown.txt", text)
        self.assertEqual(type_, "invoice")
        self.assertGreater(conf, 0.9)

    def test_negated_policy_not_classified_as_policy(self):
        """Text with 'policy not visible' should not classify as insurance_policy."""
        text = "Invoice\nInsurance policy terms are not visible on this invoice."
        type_, conf = classify_material("invoice.txt", text)
        self.assertNotEqual(type_, "insurance_policy")


class TestExtractDate(unittest.TestCase):
    def test_date_from_text(self):
        """Should extract date from text."""
        date = extract_date("Date: 2026-07-05\nPet: Mimi")
        self.assertEqual(date, "2026-07-05")

    def test_date_from_filename(self):
        """Should extract date from filename."""
        date = extract_date("", "2026-07-05_invoice.txt")
        self.assertEqual(date, "2026-07-05")

    def test_no_date_returns_none(self):
        """Should return None if no date found."""
        date = extract_date("No date here")
        self.assertIsNone(date)


class TestExtractPetName(unittest.TestCase):
    def test_pet_name_from_text(self):
        """Should extract pet name from text."""
        name = extract_pet_name("宠物：Mimi\n日期：2026-07-05")
        self.assertEqual(name, "Mimi")

    def test_pet_name_with_fallback(self):
        """Should use fallback if no pet name found."""
        name = extract_pet_name("No pet name", fallback="Default")
        self.assertEqual(name, "Default")


class TestExtractClinic(unittest.TestCase):
    def test_clinic_from_text(self):
        """Should extract clinic name from text."""
        clinic = extract_clinic("医院：星河动物医院\n日期：2026-07-05")
        self.assertEqual(clinic, "星河动物医院")

    def test_no_clinic_returns_none(self):
        """Should return None if no clinic found."""
        clinic = extract_clinic("No clinic here")
        self.assertIsNone(clinic)


class TestNormalizeMarkdown(unittest.TestCase):
    def test_normalizes_line_endings(self):
        """Should normalize line endings."""
        text = "line1\r\nline2\rline3\n"
        result = normalize_markdown(text, "test.txt")
        self.assertIn("line1", result)
        self.assertIn("line2", result)
        self.assertIn("line3", result)

    def test_includes_source_name(self):
        """Should include source filename."""
        result = normalize_markdown("content", "invoice.txt")
        self.assertIn("invoice.txt", result)


class TestNoInternalLabels(unittest.TestCase):
    def test_classify_does_not_return_internal_labels(self):
        """Classification should not return internal labels visible to users."""
        text = "Invoice #12345"
        type_, _ = classify_material("invoice.txt", text)
        # Should return raw type code, not translated label
        self.assertIn(type_, {"invoice", "bill", "unknown"})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: 运行全部测试**

Run: `python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v`
Expected: PASS (>= 123 tests)

- [ ] **Step 5: Commit**

```bash
git add pet-vault-skill/scripts/material_ops.py pet-vault-skill/tests/test_material_ops.py pet-vault-skill/scripts/petvault_core.py
git commit -m "feat: extract material_ops.py with low-risk material understanding helpers"
```

---

## Task 5: 更新 SKILL.md 反映当前架构

**Covers:** SKILL.md 反映 4-pipeline 工作流

**Files:**
- Modify: `pet-vault-skill/SKILL.md`

- [ ] **Step 1: 在 SKILL.md 中添加 4-pipeline 工作流部分**

在 `## Workflow` 部分之前添加：

```markdown
## 4-Pipeline Architecture

PetVault uses 4 logical pipelines for processing:

1. **Safety & Routing Pipeline** (`petvault_dispatch.py`)
   - Emergency detection → immediate safety response
   - Forbidden request detection → safe completion
   - Knowledge vs report routing

2. **Intake / Material Understanding Pipeline** (`material_ops.py`)
   - Material classification (invoice, bill, insurance, lab, etc.)
   - Date, pet name, clinic extraction
   - Text normalization

3. **Domain Analysis Pipeline** (`billing_ops.py`, `petvault_core.py`)
   - Bill item extraction and categorization
   - Timeline construction
   - Insurance material completeness check
   - Medical findings extraction

4. **Report & Rendering Pipeline** (`report_sanitizer.py`, `latex_ops.py`, `manifest_ops.py`)
   - Report composition
   - Internal term sanitization
   - LaTeX rendering
   - PDF compilation
   - QA inspection
   - User manifest generation

## Examples

See `examples/` for synthetic demonstrations of common user flows:
- `bill_explain/` — Bill explanation with uploaded invoice
- `knowledge_query/` — Knowledge-only pet care question
- `emergency_guardrail/` — Emergency symptom detection
- `insurance_boundary/` — Insurance/medical boundary handling

## Eval Cases

See `.agents/eval_cases/` for golden test cases:
- `internal_leakage_cases.yaml` — Tests sanitizer behavior
- `pdf_render_cases.yaml` — Tests LaTeX conversion
- `billing_report_cases.yaml` — Tests billing extraction behavior
- `skill_workflow_cases.yaml` — Tests user task routing
- `emergency_routing_cases.yaml` — Tests emergency detection
```

- [ ] **Step 2: 在 SKILL.md 中添加安全边界部分**

在 `## Quality Gate` 部分之前添加：

```markdown
## Safety Boundaries

**Must NOT do:**
- Replace veterinary diagnosis or treatment decisions
- Provide legal judgment or advice
- Promise insurance claim outcomes
- Accuse hospitals of fraud or overcharging
- Expose internal terms in user-facing output

**Must DO:**
- Mark uncertain information with explicit labels
- Base claims only on uploaded materials
- Route emergency symptoms to immediate safety guidance
- Block requests to falsify records
- Sanitize all user-facing output
```

- [ ] **Step 3: 更新 Bundled Resources 列表**

更新 `## Bundled Resources` 部分，添加新模块：

```markdown
## Bundled Resources

- `scripts/run_pipeline.py`: end-to-end Phase 1 pipeline.
- `scripts/petvault_dispatch.py`: unified request dispatcher (emergency/knowledge/report routing).
- `scripts/material_ops.py`: material classification, extraction, and normalization.
- `scripts/billing_ops.py`: amount parsing, bill item extraction, charge totals.
- `scripts/report_sanitizer.py`: internal term removal from user-facing output.
- `scripts/latex_ops.py`: Markdown to LaTeX conversion with table support.
- `scripts/manifest_ops.py`: internal and user-facing manifest construction.
- `scripts/agent_registry_loader.py`: loads forbidden terms from `.agents/forbidden_terms_registry.yaml`.
- `scripts/query_knowledge_base.py`: search curated local KB articles.
- `scripts/compile_pdf.py`: compile with XeLaTeX or latexmk when available.
- `scripts/inspect_pdf_layout.py`: check generated report artifacts.
- `scripts/quick_validate.py`: validate the skill package.
- `config/*.yaml`: agent roles, material types, safety rules, report checks.
- `schemas/*.json`: JSON schemas for generated indexes and QA data.
- `templates/*.tex.j2`: LaTeX report templates.
- `kb/articles/*.md` and `kb/sources.yaml`: curated local knowledge base.
- `examples/`: synthetic user flow demonstrations.
- `.agents/eval_cases/*.yaml`: golden test cases for leakage, routing, rendering.
```

- [ ] **Step 4: Commit**

```bash
git add pet-vault-skill/SKILL.md
git commit -m "docs: update SKILL.md to reflect 4-pipeline architecture and examples"
```

---

## Task 6: 创建 golden fixtures

**Covers:** tests/golden/ 存在且包含期望输出

**Files:**
- Create: `pet-vault-skill/tests/golden/expected_workflow_routes.yaml`

- [ ] **Step 1: 创建 expected_workflow_routes.yaml**

```yaml
# Expected workflow routes for common user inputs

routes:
  - input: "帮我解释这张账单"
    expected_route: "report"

  - input: "理赔需要哪些材料"
    expected_route: "knowledge_query"

  - input: "等待期是什么意思"
    expected_route: "knowledge_query"

  - input: "狗吃了巧克力怎么办"
    expected_route: "emergency"

  - input: "猫抽搐了"
    expected_route: "emergency"

  - input: "帮我改病历"
    expected_route: "forbidden"

  - input: "推荐哪个保险"
    expected_route: "forbidden"

  - input: "这份材料能保证理赔成功吗"
    expected_route: "forbidden"
```

- [ ] **Step 2: Commit**

```bash
git add pet-vault-skill/tests/golden/
git commit -m "feat: add golden fixtures for workflow route expectations"
```

---

## Task 7: 最终验证

- [ ] **Step 1: 运行全部测试**

Run: `python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v`
Expected: PASS (>= 135 tests)

- [ ] **Step 2: 检查 petvault_core.py 行数**

Run: `$lines = (Get-Content "pet-vault-skill/scripts/petvault_core.py").Count; Write-Output "petvault_core.py lines: $lines"`
Expected: <= 850 lines (if safely achievable)

- [ ] **Step 3: 验证 examples 不包含内部词**

```python
# In test_examples.py
def test_expected_outputs_no_internal_terms():
    from agent_registry_loader import load_forbidden_terms
    forbidden = load_forbidden_terms()
    examples_dir = SKILL / "examples"
    for expected_file in examples_dir.rglob("expected/*.md"):
        content = expected_file.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in content, f"{expected_file}: '{term}' found"
```

- [ ] **Step 4: 验证 git 状态**

Run: `git status`
Expected: 干净的工作树或只有预期的更改。
