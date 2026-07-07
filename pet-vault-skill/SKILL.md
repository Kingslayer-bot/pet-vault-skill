---
name: pet-vault-skill
description: Use when organizing pet medical bills, payments, invoices, veterinary reports, visit records, prescriptions, lab reports, insurance policies, claim documents, medication notes, companion profiles, or clinic-side explanation drafts into a local PetVault archive and printable Markdown/LaTeX/PDF report. Also use for local knowledge-base answers about pet billing vocabulary, claim-material checklists, and record terminology when no user material needs a report.
---

# Pet Vault Skill

## Overview

Use this skill to power the local-first engine layer of PetVault AI. The current runnable version focuses on caregiver-facing report explanation, bill explanation, timeline, claim check, and PDF-ready export, while also reserving B-side demo structures for SOAP draft generation and clinic-to-client explanation materials. OCR, image-body extraction, follow-up Q&A, and hospital-side voice workflows are not fully implemented in this version.

## Core Rules

- For bill, payment, invoice, insurance, reimbursement, or claim-package requests with user material, run the report workflow on the first response and provide the PDF path or attachment when compilation succeeds.
- Keep chat responses short: one result sentence, the report path/PDF status, and at most three user-confirmation items. Put detailed explanation in `report.md` and `report.pdf`, not in the chat.
- Keep reports user-facing. Do not expose internal terms such as PRD, Harness, HMW, POV, product requirement document, or developer validation.
- Do not narrate internal agent roles, pipeline steps, QA implementation, database internals, or retry details to the user unless they explicitly ask for debugging information.
- Base every factual claim on uploaded materials or explicit user-provided context.
- Mark uncertain information with explicit uncertainty labels in the user's language.
- Explain and organize bills, timelines, materials, and risks; do not replace veterinary diagnosis or treatment decisions.
- Check insurance material completeness and risk points; do not promise claim outcomes.
- Use the local KB for knowledge-only questions. Do not create vault/report files for pure knowledge questions without materials or report intent.
- Store long-term data under `~/PetVault/vault/` and per-run report outputs under `~/PetVault/reports/`.
- Preserve Markdown, LaTeX, manifest, QA result, and build log alongside any PDF.

## Quick Start

Use the bundled Phase 1 runner when the user provides local files or asks for a printable report. `--report-type auto` is the default and uses `--request` plus material types to select `bill_explain`, `claim_check`, `timeline`, and other report types:

```bash
python scripts/run_pipeline.py --input path/to/materials --output ~/PetVault/reports/2026-07-06_Mimi_bill_explain --vault ~/PetVault/vault --request "帮我解释这张账单" --pet-name Mimi --pdf-policy required
```

Use `--pdf-policy required` for user-facing bill, payment, invoice, insurance, and claim-package deliverables when a PDF must be attached. Use `--skip-pdf-compile` only for fast validation or when a TeX engine is unavailable; the runner still creates `report.md`, `report.tex`, `manifest.json`, `qa_result.json`, and a SQLite vault.

For knowledge-only questions without user materials:

```bash
python scripts/query_knowledge_base.py "理赔需要哪些材料" --limit 3
```

## Workflow

1. Route the request:
   - Knowledge-only, no user material, no report/PDF/archive intent: query the local KB and answer briefly.
   - Bill, payment, invoice, insurance, reimbursement, claim, or uploaded-material request: run the report workflow immediately.
   - Ambiguous material request: ask one confirmation question rather than silently guessing.
2. Run material organization first. Do not let later analysis agents re-parse raw files independently.
3. Create `materials_index.json` with source file, material type, date, pet name, confidence, and extracted text path. Respect explicit `Material type:` hints and do not treat "policy not visible" as a policy document.
4. Select `report_type` automatically when possible: `bill_explain`, `claim_check`, `timeline`, `medical_summary`, `chronic_review`, `clinic_client_summary`, or `general`. Save the selected type and routing reason in `manifest.json`; do not expose routing internals in chat.
5. Analyze in parallel only after the material index exists:
   - bill explanation
   - visit timeline
   - insurance material check
   - chronic-care review
   - family summary
6. Compose `report.md` with source list first, user-readable conclusions before details, and missing/uncertain data called out.
7. Render LaTeX with the bundled templates. Use the reference style: `ctexart`, A4, 11pt, `fontset=windows`, 2.35 cm side margins, 2.15/2.20 cm vertical margins, and `\linespread{1.28}`.
8. Compile PDF when a TeX engine is available. With `--pdf-policy required`, missing `report.pdf` is a blocking QA issue.
9. Inspect for missing files, empty PDF, obvious compile errors, forbidden report terms, billing extraction gaps, and layout risk notes.
10. Write structured data and report metadata into the SQLite vault after QA, including `pdf_status` and `qa_status`.

## Chat Output Policy

For report requests, the user-visible answer should be compact:

- State the report type and whether PDF compilation succeeded.
- Link or attach `report.pdf`; if missing, link `report.md`/`report.tex` and state the blocker.
- List at most three urgent missing/uncertain items.

Do not paste the full report into chat unless the user explicitly asks. Do not expose implementation details such as material index creation, SQLite probes, LaTeX retries, agent names, or QA internals.

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

The skill also contains a small local knowledge base:

```text
kb/
+-- articles/
|   +-- claim-packet-us.md
|   +-- billing-line-items.md
|   +-- nutrition-prescription-food.md
|   +-- toxin-emergency-boundary.md
+-- sources.yaml
```

Read `references/local_knowledge_base.md` when extending crawl targets, schemas, or KB routing. Keep authoritative source URLs, retrieval/update dates, jurisdiction, topic, and risk level with each article. Use Markdown as the source of truth; any SQLite/FTS index must be rebuildable.

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
- `scripts/query_knowledge_base.py`: search curated local KB articles for knowledge-only questions.
- `scripts/quick_validate.py`: validate the skill package, required resources, and CLI entrypoints.
- `config/*.yaml`: agent roles, material types, safety rules, report checks, and LaTeX layout constraints.
- `schemas/*.json`: JSON schemas for generated indexes and QA data.
- `templates/*.tex.j2`: LaTeX report templates.
- `kb/articles/*.md` and `kb/sources.yaml`: curated local knowledge base and crawl allowlist.
- `references/local_knowledge_base.md`: KB routing, crawl scope, and storage guidance.
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
- For `--pdf-policy required`, missing `report.pdf` blocks QA.
- `manifest.json` report type, `materials_index.json`, and SQLite records agree for the final report.
- Knowledge-only answers cite local KB `article_id`/source URL and do not create report artifacts.

## Common Mistakes

- Starting parallel analysis before a single material index exists. Always index first.
- Filling missing pet, clinic, policy, or diagnosis information from assumptions. Mark it as missing.
- Treating bill explanation as a price fairness judgment. Explain categories and ask-for-confirmation items instead.
- Producing only a PDF. Keep the Markdown, LaTeX, manifest, QA result, and vault data.
- Dumping full bill explanations into chat when a report PDF should carry the detail.
- Letting a generic insurance word in a bill transcription override explicit invoice/bill evidence.
