# PetVault AI / pet-vault-skill

[中文说明](README.zh-CN.md)

This repository contains the first open-source version of `pet-vault-skill`, the local-first engine behind **PetVault AI**.

## Repository Layout

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
  kb/
  templates/
  adapters/
  tests/
.github/workflows/
```

## Product Scope

`PetVault AI` in `PRD V1.1` is defined as a three-layer product:

- `C side`: report explanation, bill explanation, health timeline, claim material check, PDF-ready export
- `B side`: SOAP draft demo structure, clinic-to-client explanation draft structure
- `Engine`: local material ingestion, structured vault, Markdown/LaTeX/PDF pipeline

The runnable implementation in this repository still centers on the `Engine + C-side workflow`. The B-side content in this version is limited to prompts, schemas, templates, and directory structure. It does not claim to be a complete hospital admin platform or a complete voice-to-record workflow.

## Current Version

- Repository version: `0.1.2`
- Product baseline: `PetVault AI PRD V1.1`
- License: `MIT`

## Verified Scope

- local `vault/raw`, `vault/cleaned`, `vault/structured`, and SQLite storage
- text-first material ingestion for `.txt`, `.md`, `.csv`, `.json`, `.tex`
- placeholder indexing for `.pdf`, `.docx`, and images when body text is not parsed in Phase 1
- material classification with `pet_name`, `clinic`, `date`, `confidence`, and `status`
- caregiver-facing `report.md`
- LaTeX `report.tex` using the required CTeX baseline
- `manifest.json`, `qa_result.json`, and `build.log`
- optional PDF compilation when local `xelatex` or `latexmk` is available
- automatic report-type routing from request text and material types
- curated local knowledge-base lookup for knowledge-only billing, claim, and record terminology questions
- behavior tests for local storage, safety boundaries, report types, and harness-driven checks

This first version provides real text ingestion for text-based materials. For PDF, DOCX, and image inputs, Phase 1 preserves the original file, creates an index entry, and marks the body text as pending confirmation rather than promising full OCR.

## Quick Start

```bash
python pet-vault-skill/scripts/run_pipeline.py \
  --input path/to/materials \
  --output path/to/PetVault/reports/2026-07-06_Mimi_claim_check \
  --vault path/to/PetVault/vault \
  --request "Check whether this claim packet has enough material" \
  --pet-name Mimi \
  --pdf-policy required
```

More detailed usage, boundaries, and report-type documentation are in [`pet-vault-skill/README.md`](pet-vault-skill/README.md).

## Validation

Fast checks:

```bash
python pet-vault-skill/tests/test_pet_vault_skill.py
python -m compileall -q pet-vault-skill/scripts pet-vault-skill/adapters pet-vault-skill/tests
```

GitHub CI runs the same repository-local checks from a clean checkout.

Optional maintainer check: if your machine has the Codex skill validator available, you can run `quick_validate.py`, but it is not a hard dependency for the open-source repository.

## Push Target

Target repository: [Kingslayer-bot/pet-vault-skill](https://github.com/Kingslayer-bot/pet-vault-skill)

## License

MIT License. See [`LICENSE`](LICENSE).
