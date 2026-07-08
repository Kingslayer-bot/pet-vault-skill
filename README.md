# PetVault AI / pet-vault-skill

[中文说明](README.zh-CN.md)

This repository contains the first open-source version of `pet-vault-skill`, the local-first engine behind **PetVault AI** — a workflow for organizing pet medical records, explaining veterinary reports and bills, and generating Markdown, LaTeX, and PDF care summaries.

## Repository Layout

```text
pet-vault-skill/
  SKILL.md              — Skill definition and agent instructions
  scripts/              — Core Python modules
  kb/                   — Knowledge base (articles, rules, sources, index)
  .agents/              — Agent governance (eval cases, forbidden terms, pipelines)
  config/               — Material types, safety rules, report harness
  templates/            — LaTeX report templates
  schemas/              — JSON schemas for manifests and QA
  tests/                — 241 unit tests
  examples/             — 6 user flow examples
  prompts/              — Agent prompt files
  docs/                 — Architecture docs, KB audit reports
.github/workflows/      — CI pipeline
```

## Five Core User Scenarios

| Scenario | Status | Description |
|----------|--------|-------------|
| Bill Explanation | Strong | Invoice/bill item categorization, currency handling (USD/CNY/HKD/SGD/JPY) |
| Insurance Boundary | Strong | Claim material check, policy term explanation, no coverage guarantees |
| Emergency Guardrail | Strong | Toxin/symptom detection, regional emergency contacts (US/CN/HK/SG/JP) |
| Travel Care | Strong | Pet airline requirements, health certificates, travel checklists |
| Product Fit | Strong | Senior pet nutrition, prescription diet boundaries, safe guidance |

## Regional Coverage

| Region | Billing | Insurance | Jurisdiction | Safety | Status |
|--------|---------|-----------|-------------|--------|--------|
| US | billing-line-items-us | insurance-terms-us, claim-packet-us | us-vet-records | ASPCA | P0 |
| CN | billing-line-items-cn | insurance-terms-cn, claim-packet-cn | cn-vet-records | Local hotline | P0 |
| HK | billing-line-items-hk | insurance-terms-hk | hk-vet-records | AFCD 2708 8885 | P1 |
| SG | billing-line-items-sg | insurance-terms-sg | sg-vet-records | AVS 1800-476-1600 | P1 |
| JP | billing-line-items-jp | insurance-terms-jp | jp-vet-records | 動物愛護センター | P1 |
| global | payment-discount-refund | policy-limits, rejection-letter | — | Emergency boundary | — |

## Quick Start

```bash
# Generate a report from uploaded materials
python pet-vault-skill/scripts/run_pipeline.py \
  --input path/to/materials \
  --output ~/PetVault/reports/2026-07-06_Mimi_bill_explain \
  --vault ~/PetVault/vault \
  --request "帮我解释这张账单" \
  --pet-name Mimi \
  --pdf-policy required

# Query the knowledge base
python pet-vault-skill/scripts/query_knowledge_base.py "等待期是什么意思" \
  --domain insurance --jurisdiction US --language zh --limit 3

# Validate KB structure
python pet-vault-skill/scripts/validate_kb.py pet-vault-skill

# Build KB index
python pet-vault-skill/scripts/build_kb_index.py pet-vault-skill
```

## Validation

```bash
# Run all tests
python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v

# Compile check
python -m compileall -q pet-vault-skill/scripts pet-vault-skill/adapters pet-vault-skill/tests
```

GitHub CI runs the same checks from a clean checkout.

## Knowledge Base

- **32 articles** across 7 domains (billing, insurance, medical, nutrition, safety, jurisdiction, travel)
- **20 sources** (US/CN/HK/SG/JP/global, tier 1-4)
- **53 eval cases** in `.agents/eval_cases/`
- **40 KNOWN_TERMS** for Chinese query matching
- Safety boundaries: no diagnosis, no coverage guarantees, no brand recommendations

## License

MIT License. See [`LICENSE`](LICENSE).
