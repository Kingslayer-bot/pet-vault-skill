# Pet Vault Skill

[中文说明](README.zh-CN.md)

`pet-vault-skill` is the local-first engine behind **PetVault AI**. Under `PRD V1.1`, PetVault AI spans a consumer-side report explanation workflow, a hospital-side extension path, and a local archive plus PDF-ready report engine. The first complete version in this repository focuses on the engine and the consumer-side workflow, while reserving structure for hospital-side SOAP drafts and clinic-to-client explanation materials.

## Current Positioning

- Implemented and runnable: local ingestion, material indexing, baseline classification, Markdown report generation, LaTeX rendering, and SQLite persistence.
- Implemented and tested: `general`, `medical_summary`, `bill_explain`, `claim_check`, `timeline`, `chronic_review`, and `clinic_client_summary` outputs.
- Implemented: automatic report-type routing from request text and material type, with first-pass PDF-oriented handling for bill, payment, invoice, insurance, and claim requests.
- Implemented: a small curated local knowledge base for knowledge-only questions about billing vocabulary, claim packets, nutrition boundaries, and emergency escalation.
- Explicitly reserved, not fully implemented: OCR, image body extraction, follow-up Q&A loop, B-side voice-to-SOAP flow, and a full hospital admin platform.

## Goals

- Help caregivers understand veterinary reports, bills, prescriptions, and visit records.
- Help caregivers prepare referral packets and claim-material packages.
- Separate raw files, cleaned text, structured indexes, SQLite data, and report outputs.
- Reserve structured interfaces for future hospital-side SOAP drafts and client-facing explanation materials.

## Local-First Principle

The project borrows the local-first direction from EinVault but does not fork or depend on it in Phase 1. This version focuses on a stable local vault, report pipeline, and SQLite-backed archive first.

## Phase 1 Features

- Initialize `~/PetVault/vault` and `~/PetVault/reports`.
- Read `.txt`, `.md`, `.csv`, `.json`, and `.tex` inputs as real text sources.
- Preserve `.pdf`, `.docx`, and image inputs as indexed placeholders when body text is not parsed in Phase 1.
- Extract `pet_name`, `clinic`, `date`, `confidence`, and `status` into the material index.
- Generate caregiver-facing `report.md`.
- Generate `report.tex` using the required LaTeX baseline.
- Optionally compile `report.pdf` when local `xelatex` or `latexmk` is available.
- Generate `manifest.json`, `qa_result.json`, and `build.log`.
- Persist data into `pet_vault.sqlite3`.

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

`--report-type` defaults to `auto`. Use `--skip-pdf-compile` only for fast tests or machines without a local TeX engine.

Knowledge-only query:

```bash
python pet-vault-skill/scripts/query_knowledge_base.py "What materials do pet insurance claims usually need?"
```

## Safety Boundaries

- Do not replace veterinary diagnosis.
- Do not make treatment decisions.
- Do not judge whether a clinic overcharged.
- Do not promise insurance reimbursement.
- Do not invent pet, clinic, policy, or diagnosis facts.
- Mark uncertain fields explicitly.
- Keep B-side drafts under human review.

## Validation

```bash
python pet-vault-skill/tests/test_pet_vault_skill.py
python -m compileall -q pet-vault-skill/scripts pet-vault-skill/adapters pet-vault-skill/tests
```

## License

MIT License.
