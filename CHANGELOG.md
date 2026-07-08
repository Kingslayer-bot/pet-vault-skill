# Changelog

All notable changes to PetVault skill will be documented in this file.

## [Unreleased]

### Architecture & Engineering

- **Modular extraction:** Extract `billing_ops.py`, `material_ops.py`, `latex_ops.py`, `manifest_ops.py`, `pdf_ops.py`, `bill_render_ops.py` from monolithic `petvault_core.py`
- **Unified forbidden terms registry:** Single source of truth in `.agents/forbidden_terms_registry.yaml` loaded via `agent_registry_loader.py`
- **Report sanitizer:** `report_sanitizer.py` ensures no internal terms in user-facing output
- **Reconstructed bill section:** Bill reports now include a clean, re-rendered bill table instead of raw invoice image embedding
- **Golden text snapshot tests:** Tests compare normalized text for report quality verification

### Safety & Quality

- **Internal leakage prevention:** 38 forbidden terms tracked and tested across all report types
- **PDF QA pipeline:** `pdf_ops.py` provides modular PDF compilation and quality inspection
- **Eval cases connected:** 5 eval case files (`internal_leakage`, `pdf_render`, `billing_report`, `skill_workflow`, `report_artifact`) now have automated tests
- **User-visible safety:** All output paths (report.md, report.tex, user_manifest.json, examples, golden snapshots) verified free of internal terms

### Documentation

- **SKILL.md updated:** 4-pipeline architecture, examples, eval cases, safety boundaries, reconstructed bill rendering
- **AGENTS.md created:** Contributor/coding agent guide with code quality standards
- **Docs directory:** `docs/architecture.md`, `docs/pdf_pipeline.md`, `docs/skill_workflow.md`

### Examples & Eval Cases

- **6 user flow examples:** `bill_explain`, `knowledge_query`, `emergency_guardrail`, `insurance_boundary`, `travel_care`, `product_fit`
- **5 eval case files:** All connected to automated tests
- **Golden fixtures:** `tests/golden/` for snapshot testing

### Testing

- **Test count:** 181 tests (up from 114)
- **New test files:** 13 new test files covering all new modules and eval cases
- **All tests pass:** 0 failures, 0 errors

---

## [0.1.1] - 2026-07-06

### Initial Release

- PetVault skill v0.1.1 release
- Unified dispatch with emergency/knowledge/report routing
- Local knowledge hub with KB articles, rules, eval cases
- Bill explanation, timeline, claim check report types
- LaTeX rendering and PDF compilation
- 114 tests passing
