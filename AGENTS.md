# AGENTS.md — Coding Agent Instructions for PetVault Skill

This file governs how coding agents (Claude, Codex, Copilot) should work in this repository.

## Source of Truth

The valid Git repository root is `remote_repo/`. The skill package lives at `pet-vault-skill/`.
Do NOT operate on the broken `.git` at the parent directory.

## How to Run Tests

```bash
# From remote_repo/ directory:
python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v
```

Individual test files:
```bash
python -m unittest pet-vault-skill.tests.test_pet_vault_skill -v
python -m unittest pet-vault-skill.tests.test_internal_leakage -v
python -m unittest pet-vault-skill.tests.test_kb_structure -v
python -m unittest pet-vault-skill.tests.test_subagent_workflow -v
python -m unittest pet-vault-skill.tests.test_local_knowledge_hub -v
```

## Where NOT to Write Runtime Artifacts

These directories are git-ignored and should only contain runtime output:
- `work/` — scratch/working files
- `PetVaultRun/` — user data, generated reports, SQLite vaults
- `*.pdf`, `*.sqlite3`, `*.log` — generated artifacts
- `__pycache__/`, `.pytest_cache/` — Python caches

Write source code only in `pet-vault-skill/scripts/`, `pet-vault-skill/tests/`, etc.

## P0 Output Leakage Boundary

**CRITICAL**: User-facing `report.md`, `report.tex`, `report.pdf`, and `user_manifest.json` must NEVER contain:
- Internal type codes: `insurance_policy`, `lab_report`, `medical_report`, `claim_document`, etc.
- Internal status codes: `extracted`, `indexed_only`, `encoding_repaired`
- Metadata: `置信度`, `confidence`, `routing`, `dispatch`, `classification`
- Developer terms: `PRD`, `Harness`, `HMW`, `POV`
- Tags: `[FORBIDDEN]`, `[INTERNAL]`, `[DEBUG]`

The sanitizer (`scripts/report_sanitizer.py`) is the enforcement layer. The canonical forbidden term list is in `.agents/forbidden_terms_registry.yaml`.

## How `.agents/` Should Be Used

`.agents/` contains the agent governance layer:
- `pipeline_registry.yaml` — maps 13 agent roles to 4 logical pipelines
- `prompt_boundaries.yaml` — defines user-visible vs internal content rules
- `forbidden_terms_registry.yaml` — canonical forbidden terms list
- `pipelines/*.yaml` — pipeline definitions
- `eval_cases/*.yaml` — golden test cases for leakage, routing, rendering

When modifying sanitizer logic or adding new internal terms, update `.agents/forbidden_terms_registry.yaml` FIRST, then sync to `report_sanitizer.py` and `test_internal_leakage.py`.

## Safe Refactor Rules

1. **Never delete `petvault_core.py`** — extract modules gradually, keep compatibility imports.
2. **Never remove existing prompts** in `prompts/` — they are part of the agent contract.
3. **Never change user-facing report semantics** except for fixing leakage or formatting.
4. **Extract modules one at a time** — `latex_ops.py` and `manifest_ops.py` are first candidates.
5. **Keep backward compatibility** — when extracting, import the extracted function back into `petvault_core.py`.
6. **Run all 65+ tests after any change** — `python -m unittest discover -s pet-vault-skill/tests -p "test_*.py"`.

## Module Extraction Order (Planned)

| Priority | Target Module | Functions to Extract | Risk |
|----------|--------------|---------------------|------|
| 1 | `latex_ops.py` | `latex_escape`, `_convert_inline_latex`, `markdown_to_latex_body`, `_table_to_longtable`, `render_latex` | Low — pure functions |
| 2 | `manifest_ops.py` | `build_user_manifest`, manifest construction helpers | Low — isolated |
| 3 | `billing_ops.py` | `parse_money_mentions`, `build_bill_items`, `summarize_charge_totals` | Medium |
| 4 | `material_ops.py` | `classify_material`, `extract_*`, `ingest_materials` | Medium |
| 5 | `vault_ops.py` | `init_vault`, `update_local_db`, `json_dump` | Medium |
| 6 | `pdf_ops.py` | `compile_pdf`, `inspect_report` | Medium |
| 7 | `report_ops.py` | `build_report_markdown`, `auto_select_report_type` | High — core logic |

## Git Branch Strategy

- `main` — release-ready, stable
- `fix/*` — bug fixes and structure improvements
- `feat/*` — new features
- Always work on a feature/fix branch, never directly on `main`

## Code Quality Standards

### Google-style Consistency
- Module docstrings required for all scripts
- Function docstrings for public helpers
- Type annotations on function signatures
- Clear, descriptive variable names
- No unused imports
- No broad `except` unless justified
- Stable import order: stdlib → third-party → local

### Karpathy-style Simplicity
- Plain, readable functions
- Minimal abstraction — prefer direct code over clever patterns
- No unnecessary classes — use functions when possible
- No dependency bloat — check existing deps before adding new ones
- Simple data flow — explicit over implicit
- Easy to debug — function length should be reasonable
- Module responsibilities should be clear from the filename

### Deterministic vs Agent Logic
- **Deterministic Python**: All data processing, classification, rendering, sanitization, QA
- **Agent/LLM**: Only for natural-language interpretation at the boundary (e.g., understanding user intent)
- Never mix deterministic logic with LLM calls in the same function
- Keep LLM calls isolated and testable

### Commands to Run Tests
```bash
# All tests
python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v

# Specific module tests
python -m unittest pet-vault-skill.tests.test_agent_registry_loader -v
python -m unittest pet-vault-skill.tests.test_billing_ops -v
python -m unittest pet-vault-skill.tests.test_eval_cases -v
python -m unittest pet-vault-skill.tests.test_internal_leakage -v
python -m unittest pet-vault-skill.tests.test_latex_ops -v
python -m unittest pet-vault-skill.tests.test_manifest_ops -v
```
