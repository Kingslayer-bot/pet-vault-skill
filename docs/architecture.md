# PetVault Architecture

## Overview

PetVault is a local-first pet medical record management system that:
1. Ingests pet medical documents (invoices, lab reports, prescriptions, insurance policies)
2. Classifies and organizes materials
3. Generates user-facing reports (Markdown → LaTeX → PDF)
4. Maintains a local SQLite vault for long-term storage

## Repository Structure

```
remote_repo/                    # Git repository root
├── AGENTS.md                   # Agent governance instructions
├── README.md / README.zh-CN.md # Project documentation
├── VERSION                     # Version tracking
├── LICENSE
├── .github/workflows/ci.yml   # CI pipeline
├── .gitignore
├── docs/                       # Engineering documentation
│   ├── architecture.md         # This file
│   └── pdf_pipeline.md         # PDF rendering pipeline
├── pet-vault-skill/            # Skill package
│   ├── SKILL.md                # Skill definition (entry point)
│   ├── scripts/                # Python scripts (core logic)
│   ├── tests/                  # Test suite
│   ├── prompts/                # Agent prompt files (13 agents)
│   ├── kb/                     # Knowledge base (articles, rules, ontology)
│   ├── config/                 # Configuration files
│   ├── schemas/                # JSON schemas
│   ├── templates/              # LaTeX templates
│   ├── adapters/               # External system adapters
│   ├── agents/                 # OpenAI agent config
│   ├── internal/               # Internal documentation
│   ├── references/             # Reference documents
│   └── .agents/                # Agent governance (pipeline registry, eval cases)
└── work/                       # Working artifacts (git-ignored)
```

## Core Pipeline

```
User Request + Materials
    │
    ▼
petvault_dispatch.py            # Route: emergency / forbidden / report / knowledge
    │
    ▼
run_pipeline.py                 # Orchestrator entry point
    │
    ├── 1. ingest_materials()   # Read, classify, index materials
    ├── 2. resolve_report_type() # Auto-select report type
    ├── 3. build_report_markdown() # Generate report.md
    ├── 4. sanitize_report_markdown() # Remove internal terms
    ├── 5. render_latex()       # Markdown → LaTeX
    ├── 6. compile_pdf()        # LaTeX → PDF (xelatex/latexmk)
    ├── 7. inspect_report()     # QA checks
    ├── 8. build_user_manifest() # Create user-safe manifest
    └── 9. update_local_db()    # Write to SQLite vault
```

## Agent System

13 agent roles are organized into 4 logical pipelines:

1. **Intake Pipeline** — Material Organizer, Pet Profile Inference
2. **Domain Analysis Pipeline** — Bill Analysis, Insurance Check, Timeline, Chronic Review, Family Summary
3. **Report Pipeline** — Report Composer, LaTeX Renderer, Quality Inspector, SOAP Draft, Client Summary
4. **Safety & Routing Pipeline** — Orchestrator, Safety Guard

See `.agents/pipeline_registry.yaml` for the complete mapping.

## Output Leakage Prevention

**P0 Rule**: User-facing output must never contain internal classification codes, status codes, metadata, or developer terms.

Enforcement chain:
1. `.agents/forbidden_terms_registry.yaml` — canonical forbidden terms list
2. `scripts/report_sanitizer.py` — sanitizes report.md before writing
3. `scripts/report_sanitizer.py:build_user_manifest()` — strips internal fields from manifest
4. `tests/test_internal_leakage.py` — verifies no leakage in all report types

## Knowledge Base

```
kb/
├── articles/           # Curated knowledge cards
│   ├── billing/        # Billing terminology and patterns
│   ├── insurance/      # Insurance terms, claim packets
│   ├── medical/        # Medical report basics, prescriptions
│   ├── safety/         # Emergency boundaries, toxin info
│   └── jurisdiction/   # Regional regulations (US, CN)
├── rules/              # YAML rule files
│   ├── routing.yaml
│   ├── billing_validation.yaml
│   ├── insurance_guardrails.yaml
│   ├── medical_safety.yaml
│   ├── pdf_policy.yaml
│   └── privacy.yaml
├── ontology.yaml       # Domain taxonomy
└── sources.yaml        # Source metadata
```

## Data Flow

```
Input: raw files (PNG, MD, TXT, PDF)
    │
    ▼
vault/raw/<type>/           # Original files copied here
vault/cleaned/markdown/     # Normalized markdown
vault/structured/           # materials_index.json, pets, visits, bills, claims
vault/pet_vault.sqlite3     # SQLite database
    │
    ▼
Output: report directory
    report.md               # Sanitized user report
    report.tex              # LaTeX source
    report.pdf              # Compiled PDF
    manifest.json           # Internal manifest (with routing)
    user_manifest.json      # User-safe manifest (no routing)
    qa_result.json          # QA check results
    build.log               # PDF compilation log
```
