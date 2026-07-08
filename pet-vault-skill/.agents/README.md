# PetVault Agent & Pipeline Registry

This directory defines the agent system architecture for PetVault.

## Structure

```
.agents/
├── README.md                          # This file
├── pipeline_registry.yaml             # Maps 13 agents → 4 pipelines
├── prompt_boundaries.yaml             # User-visible vs internal content rules
├── forbidden_terms_registry.yaml      # Master forbidden terms list (sanitizer source)
├── pipelines/
│   ├── intake_pipeline.yaml           # Material Organizer + Pet Profile Inference
│   ├── domain_analysis_pipeline.yaml  # Bill Analysis + Medical + Insurance
│   ├── report_pipeline.yaml           # Report Composer + LaTeX Renderer + QA
│   └── safety_routing_pipeline.yaml   # Orchestrator + Safety Guard
└── eval_cases/
    ├── internal_leakage_cases.yaml    # Golden tests for internal term leakage
    ├── pdf_render_cases.yaml          # PDF rendering golden tests
    ├── emergency_routing_cases.yaml   # Emergency routing golden tests
    └── billing_report_cases.yaml      # Billing report golden tests
```

## Pipeline Design

PetVault uses 4 logical pipelines composed from 13 agent roles:

1. **Intake Pipeline** — Classify, extract, index materials
2. **Domain Analysis Pipeline** — Analyze bills, medical records, insurance
3. **Report Pipeline** — Compose, render, QA the final report
4. **Safety & Routing Pipeline** — Route requests, enforce guardrails

The original 13 agent prompts are preserved in `prompts/` for backward compatibility.
This directory provides the higher-level pipeline view for maintenance and evaluation.
