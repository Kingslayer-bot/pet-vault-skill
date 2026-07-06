---
name: pet-vault-skill
description: Use when organizing pet medical bills, veterinary reports, invoices, visit records, prescriptions, lab reports, insurance policies, claim documents, medication notes, companion profiles, or clinic-side explanation drafts into a local PetVault archive and a printable Markdown/LaTeX/PDF report.
---

# Pet Vault Skill

## Overview

Use this skill to power the local-first engine layer of PetVault AI. The current runnable version focuses on caregiver-facing report explanation, bill explanation, timeline, claim check, and PDF-ready export, while also reserving B-side demo structures for SOAP draft generation and clinic-to-client explanation materials. OCR, image-body extraction, follow-up Q&A, and hospital-side voice workflows are not fully implemented in this version.

## Core Rules

- Keep reports user-facing. Do not expose internal terms such as PRD, Harness, HMW, POV, product requirement document, or developer validation.
- Base every factual claim on uploaded materials or explicit user-provided context.
- Mark uncertain information with explicit uncertainty labels in the user's language.
- Explain and organize bills, timelines, materials, and risks; do not replace veterinary diagnosis or treatment decisions.
- Check insurance material completeness and risk points; do not promise claim outcomes.
- Store long-term data under `~/PetVault/vault/` and per-run report outputs under `~/PetVault/reports/`.
- Preserve Markdown, LaTeX, manifest, QA result, and build log alongside any PDF.

## Quick Start

Use the bundled Phase 1 runner when the user provides local files or asks for a printable report:

```bash
python scripts/run_pipeline.py --input path/to/materials --output ~/PetVault/reports/2026-07-06_Mimi_claim_check --vault ~/PetVault/vault --report-type claim_check --pet-name Mimi
```

Use `--skip-pdf-compile` when XeLaTeX or latexmk is unavailable. The runner still creates `report.md`, `report.tex`, `manifest.json`, `qa_result.json`, and a SQLite vault.

## Workflow

1. Clarify the report type if the user's request is ambiguous: `general`, `medical_summary`, `bill_explain`, `claim_check`, `timeline`, `chronic_review`, or `clinic_client_summary`.
2. Run material organization first. Do not let later analysis agents re-parse raw files independently.
3. Create `materials_index.json` with source file, material type, date, pet name, confidence, and extracted text path.
4. Analyze in parallel only after the material index exists:
   - bill explanation
   - visit timeline
   - insurance material check
   - chronic-care review
   - family summary
5. Compose `report.md` with source list first, user-readable conclusions before details, and missing/uncertain data called out.
6. Render LaTeX with the bundled templates. Use the reference style: `ctexart`, A4, 11pt, `fontset=windows`, 2.35 cm side margins, 2.15/2.20 cm vertical margins, and `\linespread{1.28}`.
7. Compile PDF when a TeX engine is available, then inspect for missing file, empty file, obvious compile errors, forbidden report terms, and layout risk notes.
8. Write structured data and report metadata into the SQLite vault.

## Report Types

| Type | Use For | Required Sections |
| --- | --- | --- |
| `general` | Mixed materials | pet profile, source list, visit summary, bill explanation, claim check, next actions |
| `medical_summary` | Veterinary report explanation | one-line summary, key findings, plain-language explanation, questions for the veterinarian, uncertainty notes |
| `bill_explain` | Bills, invoices, receipts | bill overview, cost categories, high-value items, added items, questions for the clinic |
| `claim_check` | Policies and claim packages | expense summary, existing materials, missing materials, risk reminders, no outcome promise |
| `timeline` | Referral or new clinic handoff | pet profile, medical history, recent timeline, key tests, current medication, clinic-facing summary |
| `chronic_review` | Older pets or chronic illness | monthly overview, visits, labs, medication changes, expense categories, next month actions |
| `clinic_client_summary` | B-side caregiver explanation draft | report summary, key findings, fee notes, follow-up reminders, requires clinician review |

## Local Structure

```text
~/PetVault/
+-- vault/
|   +-- pet_vault.sqlite3
|   +-- raw/
|   +-- cleaned/
|   +-- structured/
|   +-- attachments/
+-- reports/
    +-- YYYY-MM-DD_pet_report/
        +-- report.md
        +-- report.tex
        +-- report.pdf
        +-- manifest.json
        +-- qa_result.json
        +-- build.log
```

## Bundled Resources

- `scripts/run_pipeline.py`: end-to-end Phase 1 pipeline.
- `scripts/init_vault.py`: create local vault directories and SQLite tables.
- `scripts/ingest_materials.py`: copy source materials, extract text where possible, and build a material index.
- `scripts/classify_materials.py`: classify bills, invoices, prescriptions, lab reports, policies, claim documents, visits, medication notes, and pet profiles.
- `scripts/normalize_markdown.py`: normalize raw text into stable Markdown.
- `scripts/latex_escape.py`: escape LaTeX-sensitive text.
- `scripts/markdown_to_latex.py`: convert generated Markdown into report LaTeX.
- `scripts/build_report.py`: compose the caregiver-facing Markdown report, manifest, QA result, and SQLite report index.
- `scripts/build_report.py`: compose the caregiver-facing Markdown report, plus B-side demo summaries when requested.
- `scripts/compile_pdf.py`: compile with XeLaTeX or latexmk when available.
- `scripts/inspect_pdf_layout.py`: check generated report artifacts and obvious layout risks.
- `config/*.yaml`: agent roles, material types, safety rules, report checks, and LaTeX layout constraints.
- `schemas/*.json`: JSON schemas for generated indexes and QA data.
- `templates/*.tex.j2`: LaTeX report templates.
- `references/petvault_ai_prd_v1_1.md`: product-level scope and V1.1 alignment notes for C-side, B-side, and engine boundaries.

## Agent Roles

- Orchestrator Agent: understand the request, choose the report type, run material organization first, then coordinate analysis, rendering, QA, and writes.
- Material Organizer Agent: classify, rename, extract, clean, index, and store materials.
- Pet Profile Inference Agent: infer pet identity and scenario only for internal report selection; never label the caregiver.
- Bill Analysis Agent: categorize bill items and explain possible relationship to care actions without judging clinic pricing.
- Appointment Timeline Agent: merge appointments, visits, tests, prescriptions, bills, and follow-ups by date.
- Insurance Check Agent: list existing and missing claim materials and risk points without promising results.
- Chronic Care Review Agent: summarize recurring visits, labs, medication, prescription food, care products, and monthly spending.
- Family Summary Agent: produce restrained summaries for family decisions.
- Clinic SOAP Draft Agent: prepare a structured SOAP-style draft from clinician notes or audio transcripts, but never treat it as final without review.
- Clinic Client Summary Agent: prepare a client-facing explanation draft for the clinic side.
- Report Composer Agent: combine outputs into `report.md`.
- LaTeX Renderer Agent: convert Markdown to LaTeX, compile, and log build status.
- Quality Inspector Agent: verify sources, caution boundaries, forbidden terms, files, and readable output.

## Quality Gate

Before finishing, verify:

- `SKILL.md` validates with `quick_validate.py`.
- `report.md` lists used materials and avoids internal developer terms.
- Facts, organized findings, suggestions, missing data, and uncertain fields are separated.
- Medical content does not replace veterinary judgment.
- Claim content does not promise reimbursement.
- B-side drafts remain drafts and require clinician confirmation before archival use.
- `manifest.json`, `qa_result.json`, `materials_index.json`, and `pet_vault.sqlite3` exist.
- `report.tex` follows the bundled LaTeX layout.
- PDF compile or skip status is recorded in `build.log`.

## Common Mistakes

- Starting parallel analysis before a single material index exists. Always index first.
- Filling missing pet, clinic, policy, or diagnosis information from assumptions. Mark it as missing.
- Treating bill explanation as a price fairness judgment. Explain categories and ask-for-confirmation items instead.
- Producing only a PDF. Keep the Markdown, LaTeX, manifest, QA result, and vault data.

