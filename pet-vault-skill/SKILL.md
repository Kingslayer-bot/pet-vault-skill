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

For unified dispatch routing:

```bash
python scripts/petvault_dispatch.py --request "帮我看下这张账单" --mode auto
```

`--mode` options:

```
--mode auto      Use dispatch to route automatically (default)
--mode report    Force report pipeline
--mode knowledge Force KB query only
--mode emergency Force emergency check
```

Use `--pdf-policy required` for user-facing bill, payment, invoice, insurance, and claim-package deliverables when a PDF must be attached. Use `--skip-pdf-compile` only for fast validation or when a TeX engine is unavailable; the runner still creates `report.md`, `report.tex`, `manifest.json`, `qa_result.json`, and a SQLite vault.

For knowledge-only questions without user materials:

```bash
python scripts/query_knowledge_base.py "理赔需要哪些材料" --limit 3
```

For local knowledge hub validation and search:

```bash
python scripts/validate_kb.py .
python scripts/build_kb_index.py .
python scripts/query_knowledge_base.py "等待期是什么意思" --domain insurance --jurisdiction US --language zh --limit 3
python scripts/validate_billing.py .
python scripts/validate_insurance_output.py .
```

## Local Knowledge Hub Policy

PetVault should be described as a local knowledge hub when explaining product behavior. It connects curated knowledge cards, routing rules, PDF policy, billing validation, insurance guardrails, medical safety boundaries, privacy rules, and evidence-chain schemas.

- Generate PDF by default for bills, payments, invoices, insurance policies, claim forms, rejection letters, medical records, lab reports, imaging reports, and timeline/archive requests. Keep chat concise.
- Use local KB short answers only for pure knowledge questions with no user material and no report/archive intent.
- Trigger emergency boundaries before ordinary KB answers for toxins, poisoning, seizures, breathing difficulty, inability to urinate, persistent vomiting, severe trauma, collapse, bloat, or suspected foreign-body ingestion.
- Keep P0 market support for `US` and `CN`, P0 currencies `USD`, `CNY`, `RMB`, and P1 currency recognition for `HKD`, `SGD`, `JPY`.
- Insurance answers may organize materials, explain terms, list checks, and provide estimates with disclaimers. They must not guarantee coverage, deny coverage definitively, provide legal judgment, recommend insurance products, or help falsify records.
- Medical answers may explain terms and red flags. They must not diagnose, prescribe, downplay emergencies, or advise stopping veterinary care.
- Store user materials in the local vault, never in `kb/`. Redact exports when needed and do not keep raw material text in logs.

## Workflow

1. Route the request via petvault_dispatch:
   - Emergency: return urgent safety response immediately.
   - Knowledge-only with no materials: query the local KB and answer briefly.
   - Has materials or report intent: run the report workflow.
   - Ambiguous: ask one confirmation question.
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

## Safety Boundaries

**Must NOT do:**
- Replace veterinary diagnosis or treatment decisions
- Provide legal judgment or advice
- Promise insurance claim outcomes
- Accuse hospitals of fraud or overcharging
- Expose internal terms in user-facing output
- Embed raw invoice images directly into PDF (use reconstructed bill section instead)

**Must DO:**
- Mark uncertain information with explicit labels
- Base claims only on uploaded materials
- Route emergency symptoms to immediate safety guidance
- Block requests to falsify records
- Sanitize all user-visible output
- Re-render extracted bill data into clean, user-readable tables

## PDF Report Quality

Bill explanation PDFs use **extracted structured data**, not raw image dumps:

1. Extract bill information from uploaded materials
2. Normalize charge/payment/discount/tax categories
3. Render a clean **reconstructed bill section** (账单复刻区)
4. Explain why each major fee exists
5. Show what is paid, what is discount, what is charge, and what needs confirmation

The reconstructed bill section is for understanding only and does not replace original documents.

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
|   +-- billing/
|   |   +-- billing-line-items-us.md
|   |   +-- billing-line-items-cn.md
|   +-- insurance/
|   |   +-- claim-packet-us.md
|   |   +-- claim-packet-cn.md
|   +-- medical/
|   |   +-- prescription-diet.md
|   +-- safety/
|   |   +-- emergency-boundary.md
|   |   +-- toxin-boundary.md
|   +-- jurisdiction/
|       +-- us-vet-records.md
|       +-- cn-vet-records.md
+-- sources.yaml
+-- ontology.yaml
```

Read `references/local_knowledge_base.md` when extending crawl targets, schemas, or KB routing. Keep authoritative source URLs, retrieval/update dates, jurisdiction, topic, and risk level with each article. Use Markdown as the source of truth; any SQLite/FTS index must be rebuildable.

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
- `scripts/compile_pdf.py`: compile with XeLaTeX or latexmk when available.
- `scripts/inspect_pdf_layout.py`: check generated report artifacts and obvious layout risks.
- `scripts/query_knowledge_base.py`: search curated local KB articles for knowledge-only questions.
- `scripts/petvault_dispatch.py`: unified request dispatcher (emergency/knowledge/report routing).
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
- Skipping the unified dispatch step. Always use petvault_dispatch to route emergency/safety queries before any other workflow.
