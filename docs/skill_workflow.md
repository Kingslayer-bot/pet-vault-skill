# PetVault Skill 工作流评估

## 当前工作流地图

```text
request_text + input materials
  ↓
dispatch / safety (petvault_dispatch.py) — DETERMINISTIC
  ↓
run_pipeline (petvault_core.py) — DETERMINISTIC
  ↓
ingest materials (petvault_core.py) — DETERMINISTIC
  ↓
report type resolution (petvault_core.py) — DETERMINISTIC
  ↓
domain-specific extraction / billing analysis (petvault_core.py) — DETERMINISTIC
  ↓
report markdown composition (petvault_core.py) — DETERMINISTIC
  ↓
report sanitizer (report_sanitizer.py) — DETERMINISTIC
  ↓
LaTeX rendering (latex_ops.py) — DETERMINISTIC
  ↓
PDF compilation (petvault_core.py) — DETERMINISTIC (external tool)
  ↓
QA inspection (petvault_core.py) — DETERMINISTIC
  ↓
manifest / user_manifest (manifest_ops.py) — DETERMINISTIC
  ↓
SQLite vault update (petvault_core.py) — DETERMINISTIC
```

## 阶段分析

| 阶段 | 当前函数/文件 | 确定性/Agent | 用户可见风险 | 测试覆盖 | 建议 |
|------|--------------|-------------|-------------|---------|------|
| dispatch/safety | `petvault_dispatch.py` | 确定性 | P0-泄漏 | ✅ 完整 | 保持 |
| ingest materials | `petvault_core.py:ingest_materials` | 确定性 | 低 | ✅ 完整 | 可提取 |
| report type resolution | `petvault_core.py:auto_select_report_type` | 确定性 | 低 | ✅ 完整 | 可提取 |
| billing analysis | `petvault_core.py:build_bill_items` | 确定性 | P1-金额 | ⚠️ 部分 | **本轮提取** |
| report composition | `petvault_core.py:build_report_markdown` | 确定性 | P0-泄漏 | ✅ 完整 | 保持 |
| sanitizer | `report_sanitizer.py` | 确定性 | P0-泄漏 | ✅ 完整 | **统一注册表** |
| LaTeX rendering | `latex_ops.py` | 确定性 | P1-格式 | ✅ 完整 | 已提取 |
| PDF compilation | `petvault_core.py:compile_pdf` | 确定性 | 低 | ✅ 完整 | 可提取 |
| QA inspection | `petvault_core.py:inspect_report` | 确定性 | 低 | ✅ 完整 | 可提取 |
| manifest | `manifest_ops.py` | 确定性 | P0-泄漏 | ✅ 完整 | 已提取 |
| vault update | `petvault_core.py:update_local_db` | 确定性 | 低 | ✅ 完整 | 可提取 |

## 关键发现

1. **所有阶段都是确定性 Python** — 没有 LLM/agent 逻辑在管线中
2. **P0 泄漏风险已修复** — sanitizer 和 manifest 分离
3. **billing 模块是最大的提取候选** — 包含金额解析、分类、合计等纯函数
4. **禁止词重复** — 3 处独立维护，需统一
5. **eval_cases 未连接** — YAML 文件存在但未被测试读取
