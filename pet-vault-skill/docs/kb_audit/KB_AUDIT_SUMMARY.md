# PetVault 知识库只读审计 — 汇总报告

**审计日期**: 2026-07-08
**审计模式**: 只读，未修改任何文件
**项目根目录**: `remote_repo/pet-vault-skill`

---

## A. KB Map Summary

| 维度 | 数量 |
|------|------|
| KB 文章 | 17 篇 (5 个子目录: billing×3, insurance×6, jurisdiction×2, medical×4, safety×2) |
| 规则文件 | 6 个 (routing, insurance_guardrails, medical_safety, billing_validation, pdf_policy, privacy) |
| 评估用例 | kb/eval/ 5 文件 (~14 cases，**全部未被代码加载**) / .agents/eval_cases/ 6 文件 (~39 cases，活跃) |
| 来源 | 12 个 (US×6, CN×3, global×2, internal×1) |
| 索引 | kb.sqlite 61KB，2026-07-07 构建，与文章同步 |
| 示例流程 | 6 个 (bill_explain, knowledge_query, emergency_guardrail, insurance_boundary, travel_care, product_fit) |

**关键发现**: `kb/eval/` 整个目录是死代码——5 个 YAML 文件从未被任何脚本或测试加载。活跃的 eval 系统在 `.agents/eval_cases/`。

---

## B. User Flow Coverage

| Flow | 状态 | 说明 |
|------|------|------|
| **bill_explain** | **Strong** | 3 篇文章 + 1 规则 + 4 eval cases + 1 示例，全覆盖 |
| **knowledge_query** | **Strong** | 17 篇文章均可通过 FTS5 检索，有测试 |
| **emergency_guardrail** | **Strong** | 2 篇文章 + 1 规则 + 12 eval cases + 1 示例 |
| **insurance_boundary** | **Strong** | 6 篇文章 + 1 规则 + eval cases + 1 示例 |
| **travel_care** | **Missing** | 示例存在但：无 ontology domain、无文章、无路由规则、无来源、无 eval、无测试 |
| **product_fit** | **Weak** | 最接近的文章 (prescription-diet.md) 明确禁止推荐品牌，但示例期望品牌推荐 |

---

## C. Source Quality

**好的方面**:
- 12 个来源全部被至少 1 篇文章引用（无孤儿来源）
- 所有文章引用的 source_id 都存在于 sources.yaml 中（无断链）
- US 和 CN 来源覆盖充分，可信度高

**问题**:
- `nfra-pet-insurance-risk-cn` URL 指向首页而非具体文件
- `pingan-pet-insurance-terms-cn` URL 指向首页而非具体产品页
- HK/SG/JP 零来源
- 所有 `last_reviewed` 都是 2026-07-07（批量设置，未逐个验证）

---

## D. Ontology & Material Alignment

### CRITICAL: 材料类型命名不一致

| material_ops.py | routing.yaml | 问题 |
|----------------|-------------|------|
| `claim_document` | `claim_form` | **不匹配** — 分类结果无法触发路由 |
| `medical_report` | `medical_record` | **不匹配** — 同上 |
| `clinic_communication` | `chat_record` | **不匹配** — 同上 |
| `bill` | (缺失) | **缺失** — 账单材料无法触发 bill_report |
| — | `payment_record` | routing 期望但 classifier 无法产生 |
| — | `rejection_letter` | routing 期望但 classifier 无法产生 |
| — | `imaging_report` | routing 期望但 classifier 无法产生 |

**影响**: 这些不匹配会导致运行时路由失败——classified material 无法匹配 routing triggers。

### Ontology 域覆盖

| 域 | ontology | material_ops | rules | articles | eval | examples |
|----|----------|-------------|-------|----------|------|----------|
| billing | YES | YES | YES | YES | YES | YES |
| insurance | YES | YES | YES | YES | YES | YES |
| medical | YES | YES | YES | YES | YES | NO |
| nutrition | YES | **NO** | **NO** | YES(1) | **NO** | YES |
| safety | YES | NO | YES | YES | YES | YES |
| jurisdiction | YES | NO | NO | YES(2) | **NO** | NO |
| travel | **NO** | NO | NO | **NO** | **NO** | YES(孤儿) |

---

## E. Retrieval Behavior

| 查询 | 预期命中 | 实际命中 | 评估 |
|------|---------|---------|------|
| 为什么账单里有 exam fee？ | billing-line-items-cn | billing-line-items-cn | OK |
| 疫苗费用为什么会出现在账单里？ | billing-line-items-cn | 可能弱命中（"疫苗"不在 KNOWN_TERMS） | Partial |
| 保险是不是一定能理赔？ | insurance articles | insurance-terms-cn/claim-packet-cn | OK |
| 猫出差期间饮水怎么安排？ | travel_care | **无匹配** | FAIL |
| 自动喂食机适合胆小猫吗？ | product_fit | prescription-diet.md (弱匹配) | Weak |
| 宠物呼吸困难怎么办？ | emergency-boundary | emergency-boundary.md | OK |
| 宠物账单里的 lab work 是什么？ | lab-report-basics | lab-report-basics.md | OK |

**KNOWN_TERMS 缺失**: 疫苗、手术、麻醉、住院、影像、免赔额、赔付比例等重要查询词未收录。

---

## F. Safety Audit

### 整体评级: **STRONG**

- 零危险表述（确诊、保证、欺诈承诺等）出现在文章正文中
- 所有 17 篇文章都正确声明了 `forbidden_outputs`
- 保险护栏规则全面（10 条禁止声明 + 5 条允许声明）
- 内部术语与用户可见内容正确分离

### 3 个 P1 问题

| 问题 | 文件 | 修复建议 |
|------|------|---------|
| `置信度` 与 forbidden_terms_registry 冲突 | billing-line-items-us.md:49, policy-limits-and-deductibles.md:49 | 改为"识别准确度" |
| `diagnosis_or_assessment` 内部编码风格 | claim-packet-us.md:26 | 改为"诊断或评估" |
| forbidden_terms_registry 缺少 4 个术语 | .agents/forbidden_terms_registry.yaml | 添加 indexed_with_manual_transcription, pipeline, agent_registry, qa_result |

---

## G. Test Coverage

| 维度 | 覆盖状态 |
|------|---------|
| 文章结构/schema | **Strong** (test_kb_structure, test_local_knowledge_hub) |
| 内部术语泄漏防护 | **Strong** (test_internal_leakage, 265 行) |
| 账单解释全链路 | **Strong** (5 个测试文件) |
| 急症路由 | **Strong** (12 eval cases) |
| 保险护栏 | **Strong** |
| **travel_care** | **Missing** — 零 eval cases，零测试 |
| **product_fit** | **Missing** — 零 eval cases，零测试 |
| 检索质量 | **Weak** — 仅 1 条查询测试 |
| privacy.yaml | **Missing** — 零测试 |
| KB 索引一致性 | **Missing** — 无测试 |
| 文章过期检查 | **Missing** — 无测试 |
| P1 地区 (HK/SG/JP) | **Missing** — 无测试 |

---

## H. P0/P1/P2 Issues

### P0 — 必须修（危险输出或路由失败风险）

| # | 问题 | 影响 |
|---|------|------|
| 1 | material_ops ↔ routing 类型名不匹配 (3 处) | 路由失败 |
| 2 | `bill` 缺失于 routing | 账单材料可能无法触发报告 |
| 3 | routing 期望 3 个 material_ops 无法产生的类型 | 永远无法匹配 |
| 4 | `置信度` 出现在用户可见文章中 | sanitizer 可能破坏文本 |
| 5 | `diagnosis_or_assessment` 内部编码出现在文章中 | 内部术语泄漏 |

### P1 — 当前用户流程明显缺知识支撑

| # | 问题 | 影响 |
|---|------|------|
| 6 | travel_care 零 KB 支撑 | 示例完全孤儿 |
| 7 | product_fit 示例与 KB 安全边界矛盾 | 示例不可执行 |
| 8 | 急症联系方式仅美国 (ASPCA) | CN/HK/SG/JP 用户无本地信息 |
| 9 | 无检索质量测试 | 无法验证 KB 实际服务能力 |
| 10 | kb/eval/ 5 文件是死代码 | 维护混乱 |

### P2 — 结构优化、来源补充

| # | 问题 |
|---|------|
| 11 | nfra/pingan 来源 URL 指向首页 |
| 12 | HK/SG/JP 零来源 |
| 13 | clinic_communication 缺失于 EXPLICIT_TYPE_ALIASES |
| 14 | CNY/RMB 在 ontology 中重复 |
| 15 | medical_safety.yaml 缺 dose_change/dietary_change |
| 16 | forbidden_terms_registry 缺 4 个术语 |
| 17 | 无 CI 索引重建/验证步骤 |
| 18 | 无文章过期测试 |
| 19 | KNOWN_TERMS 缺失重要查询词 |

---

## I. Recommended KB Iteration

| 阶段 | 重点 | 预估时间 |
|------|------|---------|
| **Phase 0** | 修 P0（材料类型对齐 + 危险术语） | 1 天 |
| **Phase 1** | travel_care KB（4 篇文章 + 来源 + 路由 + eval） | 3 天 |
| **Phase 2** | product_fit KB（2 篇文章 + eval）+ glossary | 2 天 |
| **Phase 3** | 检索质量测试 + CI 索引验证 | 1 天 |
| **Phase 4** | P1 地区（HK → SG → JP） | 5-7 天 |
| **Phase 5** | mixed_materials 文章 + 地区规则 | 2 天 |

---

## J. Files Created

```
docs/kb_audit/
├── KB_CURRENT_MAP.md           — KB 结构总地图
├── KB_COVERAGE_MATRIX.md       — 用户流程覆盖矩阵
├── KB_SOURCES_AUDIT.md         — 来源质量审计
├── KB_ONTOLOGY_ALIGNMENT.md    — Ontology 对齐分析
├── KB_RETRIEVAL_AUDIT.md       — 检索行为审计
├── KB_SAFETY_AUDIT.md          — 安全审计
├── KB_TEST_COVERAGE_AUDIT.md   — 测试覆盖审计
├── KB_NEXT_ITERATION_PLAN.md   — 下一轮迭代计划
└── KB_AUDIT_SUMMARY.md         — 本汇总报告
```

---

## 你最关心的 5 个问题的直接回答

### 1. travel_care / product_fit 到底有没有真实 KB 支撑？

**travel_care: 完全没有。** 无 domain、无文章、无路由、无来源、无 eval、无测试。示例是纯占位符。

**product_fit: 半断裂。** 最接近的文章 `prescription-diet.md` 明确禁止推荐品牌，但示例期望推荐"肾脏支持处方粮"——两者矛盾。

### 2. sources.yaml 是否能追溯每篇文章？

**能。** 12 个来源全部被至少 1 篇文章引用，无孤儿来源，无断链。但 2 个中国来源的 URL 只指向首页而非具体文档。

### 3. ontology.yaml 是否和 material_ops.py 对齐？

**不对齐。** 存在 3 处关键命名不匹配（claim_document≠claim_form, medical_report≠medical_record, clinic_communication≠chat_record），会导致路由失败。此外 routing 期望 3 个 material_ops 无法产生的类型。

### 4. query_knowledge_base.py 对真实用户问题的命中效果？

**账单/保险/急症类问题命中良好。** travel_care 问题无匹配，product_fit 问题弱匹配。KNOWN_TERMS 缺失多个重要查询词（疫苗、手术、麻醉等）。

### 5. 有无危险表述或内部规则混入用户可见 KB？

**无危险表述。** 3 处内部术语碰撞（`置信度`×2, `diagnosis_or_assessment`×1），属于 P1 修复项，不是安全危机。
