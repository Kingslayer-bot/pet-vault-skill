# PetVault AI / pet-vault-skill

[English](README.md)

本仓库包含 `pet-vault-skill` 的第一版开源内容。它是 **PetVault AI** 的本地优先底层引擎，用于整理宠物医疗资料、生成解释性 Markdown/LaTeX 报告，并为后续 C 端与 B 端扩展保留结构。

## 仓库结构

```text
pet-vault-skill/
  SKILL.md
  README.md
  README.zh-CN.md
  agents/
  config/
  prompts/
  schemas/
  scripts/
  templates/
  adapters/
  tests/
.github/workflows/
```

## 产品范围

`PetVault AI` 在 `PRD V1.1` 中被定义为三层产品：

- `C 端`：报告解读、账单解释、健康时间线、理赔材料检查、PDF 就绪导出
- `B 端`：SOAP 草稿 Demo 结构、医院到宠物主的解释材料草稿结构
- `引擎层`：本地材料导入、结构化资料库、Markdown/LaTeX/PDF 流水线

当前仓库中的可运行实现仍以 `引擎层 + C 端主链路` 为主。B 端部分在本版本中只保留 prompt、schema、模板和目录结构，不宣称已经完成医院后台或完整语音转病历链路。

## 当前版本

- 仓库版本：`0.1.1`
- 产品基线：`PetVault AI PRD V1.1`
- 协议：`MIT`

## 已验证能力

- 本地 `vault/raw`、`vault/cleaned`、`vault/structured` 与 SQLite 存储
- 面向 `.txt`、`.md`、`.csv`、`.json`、`.tex` 的文本优先材料导入
- 当 Phase 1 未解析正文时，对 `.pdf`、`.docx`、图片建立占位索引
- 提取 `pet_name`、`clinic`、`date`、`confidence`、`status` 等材料字段
- 面向宠物主的 `report.md`
- 使用指定 CTeX 基线生成 `report.tex`
- `manifest.json`、`qa_result.json`、`build.log`
- 在本机具备 `xelatex` 或 `latexmk` 时可选编译 PDF
- 覆盖本地存储、安全边界、报告类型与 harness 约束的行为测试

当前第一版对文本类材料提供真实读取能力。对于 PDF、DOCX、图片等输入，Phase 1 默认保留原件、建立索引，并将正文标记为待确认，而不是承诺完整 OCR。

## 快速开始

```bash
python pet-vault-skill/scripts/run_pipeline.py ^
  --input path/to/materials ^
  --output path/to/PetVault/reports/2026-07-06_Mimi_claim_check ^
  --vault path/to/PetVault/vault ^
  --report-type claim_check ^
  --pet-name Mimi ^
  --skip-pdf-compile
```

更详细的用法、边界和报告类型说明见 [`pet-vault-skill/README.zh-CN.md`](pet-vault-skill/README.zh-CN.md)。

## 验证

快速检查：

```bash
python pet-vault-skill/tests/test_pet_vault_skill.py
python -m compileall -q pet-vault-skill/scripts pet-vault-skill/adapters pet-vault-skill/tests
```

GitHub CI 会在干净 checkout 上运行同一套仓库内验证。

维护者可选检查：如果本机具备 Codex skill 校验脚本，也可以额外运行 `quick_validate.py`，但这不是开源仓库的硬依赖。

## 目标仓库

目标仓库：[Kingslayer-bot/pet-vault-skill](https://github.com/Kingslayer-bot/pet-vault-skill)

## 协议

MIT License。见 [`LICENSE`](LICENSE)。
