# KB Test Coverage Audit — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## 1. Test Inventory (17 test files, ~2,123 lines)

| # | Test File | Lines | KB Aspects Covered |
|---|-----------|-------|-------------------|
| 1 | test_kb_structure.py | 147 | sources.yaml validity, ontology.yaml domains, 5 article subdirs, 6 rules, forbidden_outputs, no flat articles |
| 2 | test_local_knowledge_hub.py | 161 | 21 required KB paths, frontmatter (13 fields, source ID cross-ref), safety content guard, routing/pdf_policy rules, amount/currency/kind parsing, KB query filters |
| 3 | test_pet_vault_skill.py | 410 | Required resource existence, 7 report type smoke tests, knowledge_query entrypoint ("理赔需要哪些材料" ≥1 match) |
| 4 | test_subagent_workflow.py | 162 | Prompt routing priorities, emergency dispatch, insurance guardrails (forbidden/allowed claims), prompt file existence |
| 5 | test_eval_cases.py | 110 | Eval case YAML existence + schema, internal leakage sanitizer cases, PDF render LaTeX cases |
| 6 | test_skill_workflow_cases.py | 89 | Emergency/forbidden/knowledge routing via dispatch(), output safety (must_not_include) |
| 7 | test_billing_report_eval_cases.py | 114 | bill_explain_basic sections, charges/payments/discounts, multi-currency, no internal leakage |
| 8 | test_internal_leakage.py | 265 | Sanitizer: type codes, status codes, confidence scores, forbidden tags, developer terms, routing metadata; full pipeline for all 7 report types |
| 9 | test_report_golden_snapshots.py | 114 | Bill section golden snapshot, bill table structure, no internal terms, LaTeX conversion |
| 10 | test_report_artifact_cases.py | 88 | report_artifact_cases.yaml validation + 2 eval cases |
| 11 | test_bill_render_ops.py | 106 | Markdown table rendering, Chinese labels, payment not charge, empty items pending, no internal terms |
| 12 | test_material_ops.py | 124 | Material classification, date/pet/clinic extraction, normalization, no internal labels |
| 13 | test_billing_ops.py | 128 | Currency normalization, money kind classification, money parsing, bill items, format currency |
| 14 | test_agent_registry_loader.py | 76 | Registry file existence, forbidden terms loading, type/status map |
| 15 | test_manifest_ops.py | 103 | Type label translation, deterministic report IDs, user manifest fields |
| 16 | test_latex_ops.py | 121 | LaTeX escaping, inline LaTeX, table detection/conversion, markdown-to-LaTeX, cover titles |
| 17 | test_pdf_ops.py | 115 | PDF compilation, forbidden term detection, required files, PDF status, fee explanation |

---

## 2. KB-Specific Test Coverage

| KB Aspect | Tested? | Test File(s) | Coverage Level |
|-----------|---------|-------------|----------------|
| Article existence | YES | test_kb_structure, test_local_knowledge_hub, test_pet_vault_skill | Strong |
| Article frontmatter schema | YES | test_local_knowledge_hub (13 required fields) | Strong |
| Source ID cross-reference | YES | test_local_knowledge_hub | Strong |
| Source YAML validity | YES | test_kb_structure | Strong |
| Ontology YAML domains | YES | test_kb_structure | Moderate |
| Rules file existence | YES | test_kb_structure (6 files) | Strong |
| Rules content (insurance_guardrails) | YES | test_subagent_workflow | Moderate |
| Rules content (routing) | YES | test_local_knowledge_hub (encoded cases) | Moderate |
| Rules content (medical_safety) | **NO** | — | **Gap** |
| Rules content (billing_validation) | **NO** | — | **Gap** |
| Rules content (privacy) | **NO** | — | **Gap** |
| Rules content (pdf_policy) | YES | test_local_knowledge_hub (encoded cases) | Moderate |
| KB query entrypoint | YES | test_pet_vault_skill (1 query) | **Weak** |
| KB query relevance ranking | **NO** | — | **Gap** |
| KB query multi-result ordering | **NO** | — | **Gap** |
| KB index consistency | **NO** | — | **Gap** |
| Article expiration | **NO** | — | **Gap** |
| Forbidden terms in articles | YES | test_local_knowledge_hub (safety domain guard) | Moderate |
| Internal leakage | YES | test_internal_leakage (comprehensive) | Strong |

---

## 3. User Flow Test Coverage

| Flow | Eval Cases | Tests | Coverage |
|------|-----------|-------|----------|
| bill_explain | report_artifact_cases (6), billing_report_cases (3), skill_workflow_cases (1) | 5 test files | **Strong** |
| knowledge_query | skill_workflow_cases (1), emergency_routing_cases (1) | 2 test files | **Moderate** |
| emergency_guardrail | emergency_routing_cases (12), medical_safety_cases (4), skill_workflow_cases (1) | 2 test files | **Strong** |
| insurance_boundary | skill_workflow_cases (2 forbidden), insurance_cases (5+2) | 2 test files | **Strong** |
| **travel_care** | **NONE** | **NONE** | **Missing** |
| **product_fit** | **NONE** | **NONE** | **Missing** |
| mixed_materials | skill_workflow_cases (1 routing only) | 1 test file | **Weak** |
| empty_input | skill_workflow_cases (1) | 1 test file | **Moderate** |

---

## 4. kb/eval/ vs .agents/eval_cases/

| System | Files | Loaded by Code | Loaded by Tests | Status |
|--------|-------|---------------|-----------------|--------|
| `kb/eval/` | 5 files, ~14 cases | **NO** | **NO** | **Dead code** |
| `.agents/eval_cases/` | 6 files, ~39 cases | YES | YES | Active |

The `kb/eval/` directory appears to be an older or parallel eval system. None of its 5 YAML files are loaded by any Python script or test. The active eval system uses `.agents/eval_cases/` instead.

---

## 5. Coverage Gaps Summary

### Critical Gaps

1. **travel_care**: Zero eval cases, zero tests
2. **product_fit**: Zero eval cases, zero tests
3. **KB retrieval quality**: Only 1 query tested ("理赔需要哪些材料"), no relevance validation
4. **kb/eval/ dead code**: 5 files with ~14 eval cases never consumed

### High Priority Gaps

5. **medical_safety.yaml content**: No test validates forbidden actions or red_flags list
6. **billing_validation.yaml content**: No test validates fail_conditions
7. **privacy.yaml content**: No test at all
8. **KB index consistency**: No test checks kb.sqlite matches article files
9. **Article expiration**: No test checks expires_at field
10. **P1 jurisdictions**: No test validates HK/SG/JP content or behavior

### Medium Priority Gaps

11. **Bill category coverage**: ontology defines 18 categories but no test validates all are handled
12. **Uncertainty labels**: config defines required_uncertainty_labels but no test verifies they appear in reports
13. **Source URL reachability**: No test validates source URLs return valid content
14. **B-side review requirement**: clinic SOAP/client summary review not tested

---

## 6. Recommendations

| Priority | Action |
|----------|--------|
| P0 | Add travel_care eval cases + test |
| P0 | Add product_fit eval cases + test |
| P1 | Add retrieval quality test (5+ queries with expected top-1 article_id) |
| P1 | Add medical_safety.yaml content validation test |
| P1 | Add billing_validation.yaml fail_conditions test |
| P1 | Add privacy.yaml content test |
| P1 | Wire kb/eval/ into test suite OR delete it |
| P2 | Add KB index consistency test |
| P2 | Add article expiration validation test |
| P2 | Add P1 jurisdiction coverage test |
