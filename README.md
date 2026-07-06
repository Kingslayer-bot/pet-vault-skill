# PetVault AI / pet-vault-skill

This repository contains the first open-source version of `pet-vault-skill`, the local-first engine behind **PetVault AI**.

本仓库包含 `pet-vault-skill` 的第一版开源内容。它是 **PetVault AI** 的本地优先底层引擎，用于整理宠物医疗资料、生成解释性 Markdown/LaTeX 报告，并为后续 C 端与 B 端扩展保留结构。

## Repository Layout / 仓库结构

```text
pet-vault-skill/
  SKILL.md
  README.md
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

## Product Scope / 产品范围

`PetVault AI` in `PRD V1.1` is defined as a three-layer product:

- `C side`: report explanation, bill explanation, health timeline, claim material check, PDF-ready export
- `B side`: SOAP draft demo structure, clinic-to-client explanation draft structure
- `Engine`: local material ingestion, structured vault, Markdown/LaTeX/PDF pipeline

当前仓库中的可运行实现仍以 `Engine + C 端主链路` 为主。B 端部分只保留 prompt、schema、模板和目录结构，不宣称已经做成完整医院后台或完整语音转病历链路。

## Current Version / 当前版本

- Repository version: `0.1.1`
- Product baseline: `PetVault AI PRD V1.1`
- License: `MIT`

## Verified Scope / 已验证能力

- local `vault/raw`, `vault/cleaned`, `vault/structured`, and SQLite storage
- text-first material ingestion for `.txt`, `.md`, `.csv`, `.json`, `.tex`
- placeholder indexing for `.pdf`, `.docx`, and images when body text is not parsed in Phase 1
- material classification with `pet_name`, `clinic`, `date`, `confidence`, and `status`
- caregiver-facing `report.md`
- LaTeX `report.tex` using the required CTeX baseline
- `manifest.json`, `qa_result.json`, and `build.log`
- optional PDF compilation when local `xelatex` or `latexmk` is available
- behavior tests for local storage, safety boundaries, report types, and harness-driven checks

已验证范围说明：当前版本对文本类材料有真实读取能力；对 PDF、DOCX、图片等非文本材料，第一版默认保留原件、建立索引并提示正文待确认，而不是承诺完整 OCR。

## Quick Start / 快速开始

```bash
python pet-vault-skill/scripts/run_pipeline.py \
  --input path/to/materials \
  --output path/to/PetVault/reports/2026-07-06_Mimi_claim_check \
  --vault path/to/PetVault/vault \
  --report-type claim_check \
  --pet-name Mimi \
  --skip-pdf-compile
```

More detailed bilingual usage is in [`pet-vault-skill/README.md`](pet-vault-skill/README.md).

更详细的双语说明、边界和报告类型说明见 [`pet-vault-skill/README.md`](pet-vault-skill/README.md)。

## Validation / 验证

Fast checks:

```bash
python pet-vault-skill/tests/test_pet_vault_skill.py
python -m compileall -q pet-vault-skill/scripts pet-vault-skill/adapters pet-vault-skill/tests
```

GitHub CI runs the same repository-local checks from a clean checkout.

维护者可选检查：如果本机具备 Codex skill 校验脚本，可额外运行 `quick_validate.py`，但这不是开源仓库的硬依赖。

## Push Target / 推送仓库

Target repository: [Kingslayer-bot/pet-vault-skill](https://github.com/Kingslayer-bot/pet-vault-skill)

## License / 许可证

MIT License. See [`LICENSE`](LICENSE).
