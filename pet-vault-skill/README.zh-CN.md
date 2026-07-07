# Pet Vault Skill / 宠物资料整理 Skill

[English](README.md)

`pet-vault-skill` 是 **PetVault AI** 的本地优先底层引擎。按照 `PRD V1.1`，PetVault AI 的总体产品形态是：`C 端宠物医疗报告解读工具 + B 端兽医院智能管理扩展 + 本地资料库与 PDF 报告生成引擎`。本仓库当前的第一版完整 skill 以本地资料整理、报告解读、账单解释、健康时间线、理赔材料检查和 PDF 就绪输出为主，同时为 B 端语音转病历和客户解释材料生成保留结构。

## 当前版本定位

- 已实现并可运行：本地资料导入、材料索引、基础分类、Markdown 报告、LaTeX 渲染、SQLite 落库。
- 已实现并经过测试：`general`、`medical_summary`、`bill_explain`、`claim_check`、`timeline`、`chronic_review`、`clinic_client_summary` 七类输出。
- 已实现：根据用户原话和材料类型自动选择报告类型；账单、付费、发票、保险、理赔类请求可首轮按 PDF 交付策略执行。
- 已实现：用于知识性问询的小型本地知识库，覆盖账单项目、理赔材料包、营养/处方粮边界和紧急风险分流。
- 明确保留但未完整实现：OCR、图片正文抽取、AI 追问闭环、B 端语音转病历、完整医院后台。

## 目标

- 帮助宠物主理解兽医报告、账单、处方和就诊资料。
- 帮助宠物主整理跨院就诊资料包和理赔材料包。
- 把原始材料、清洗文本、结构化索引、SQLite 数据库和报告输出分开保存。
- 为后续 B 端 SOAP 草稿与客户解释材料保留结构化接口。

## Local-First 原则

本项目参考 EinVault 的 local-first 思路，但不直接依赖或 fork EinVault。本版本先把稳定的本地资料库、报告生成和 SQLite 存储做完整；后续版本再考虑更深的 EinVault / Paperless-ngx 适配。

## 当前 Phase 1 能力

- 初始化 `~/PetVault/vault` 和 `~/PetVault/reports`。
- 对 `.txt`、`.md`、`.csv`、`.json`、`.tex` 做真实文本读取。
- 对 `.pdf`、`.docx`、图片等非文本材料保留原件、建立索引，并标记正文待确认。
- 提取 `pet_name`、`clinic`、`date`、`confidence`、`status` 等材料索引字段。
- 生成用户可读 `report.md`。
- 生成继承指定 LaTeX 风格的 `report.tex`。
- 在本机安装 `xelatex` 或 `latexmk` 时可选编译 `report.pdf`。
- 生成 `manifest.json`、`qa_result.json`、`build.log`。
- 写入本地 SQLite 数据库 `pet_vault.sqlite3`。

## 快速开始

```bash
python pet-vault-skill/scripts/run_pipeline.py ^
  --input path/to/materials ^
  --output path/to/PetVault/reports/2026-07-06_Mimi_claim_check ^
  --vault path/to/PetVault/vault ^
  --request "帮我检查理赔材料够不够" ^
  --pet-name Mimi ^
  --pdf-policy required
```

`--report-type` 默认是 `auto`。如果本机具备 LaTeX 环境，可以使用 `--pdf-policy required` 要求生成 `report.pdf`；如果只是快速测试或本机没有 TeX 引擎，可以加 `--skip-pdf-compile`，脚本会在 `build.log` 中写明跳过原因。

知识性问询：

```bash
python pet-vault-skill/scripts/query_knowledge_base.py "理赔需要哪些材料"
```

## 报告类型

| 类型 | 适用场景 |
| --- | --- |
| `general` | 多种材料的综合整理报告 |
| `medical_summary` | 兽医报告简明解读 |
| `bill_explain` | 账单、发票、费用明细解释 |
| `claim_check` | 保单和理赔材料完整性检查 |
| `timeline` | 跨院就诊或新医院资料包 |
| `chronic_review` | 慢病或中老年宠物月度复盘 |
| `clinic_client_summary` | B 端客户解释材料草稿 |

## 输出文件

每次运行会输出：

```text
report.md
report.tex
report.pdf            # 仅在本机 TeX 环境可用且编译成功时存在
manifest.json
qa_result.json
build.log
```

长期资料写入：

```text
PetVault/vault/
├── pet_vault.sqlite3
├── raw/
├── cleaned/
├── structured/
└── attachments/
```

## 安全边界

- 不替代兽医诊断。
- 不直接给出治疗决策。
- 不判断医院是否乱收费。
- 不承诺保险一定理赔。
- 不凭空补写宠物、医院、保单或诊断信息。
- 对不确定信息明确标注“待确认”或“资料不足”。
- B 端草稿必须保留人工审核前提。

## 验证

```bash
python pet-vault-skill/tests/test_pet_vault_skill.py
python -m compileall -q pet-vault-skill/scripts pet-vault-skill/adapters pet-vault-skill/tests
```

## 开源协议

本项目采用 MIT License 开源。
