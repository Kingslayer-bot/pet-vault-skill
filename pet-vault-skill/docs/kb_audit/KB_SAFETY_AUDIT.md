# KB Safety Audit — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## 1. Overall Safety Rating: **STRONG**

The knowledge base is well-designed with defense-in-depth safety architecture. No dangerous overclaims, no diagnosis replacement, no insurance guarantees found in any KB article body text.

---

## 2. Dangerous Term Search Results

### Chinese Dangerous Terms

| Term | Found? | Context | Risk |
|------|--------|---------|------|
| 确诊 | NO | — | — |
| 一定可以理赔 | NO | — | — |
| 医院乱收费 | NO | — | — |
| 建议立即治疗 | NO | — | — |
| 保证 | NO | — | — |
| 法律责任 | NO | — | — |
| 欺诈 | YES | sources.yaml:128 — source metadata describing allowed_use of anti-fraud reference | SAFE |
| 药物剂量 | NO | — | — |
| 替代兽医 | YES | medication-basics.md:25 — "不能改剂量、停药或替代兽医处方" (boundary statement) | SAFE |

### English Dangerous Terms

| Term | Found? | Context | Risk |
|------|--------|---------|------|
| diagnosis | YES | Multiple articles — all in `forbidden_outputs` declarations or boundary statements | SAFE |
| guaranteed | NO | — | — |
| definitely covered | NO | — | — |
| malpractice | NO | — | — |
| fraud | YES | ontology.yaml:44 — boundary statement | SAFE |
| guaranteed reimbursement | NO | — | — |
| recommend treatment | NO | — | — |
| dose | YES | toxin-boundary.md, emergency-boundary.md — in `allowed_outputs` for triage info gathering | SAFE |
| dosage | NO | — | — |

### Insurance Overclaim Patterns

| Term | Found? | Context | Risk |
|------|--------|---------|------|
| 一定能赔 | YES | insurance_guardrails.yaml:2 — listed as **forbidden claim** | SAFE |
| 一定不能赔 | YES | insurance_guardrails.yaml:3 — listed as **forbidden claim** | SAFE |
| guarantee_coverage | YES | insurance_guardrails.yaml:4 — listed as **forbidden claim** | SAFE |
| 一定能报 | NO | — | — |
| 肯定能赔 | NO | — | — |
| 100% | NO | — | — |
| always covered | NO | — | — |

### Medical Diagnosis Replacement Patterns

| Term | Found? | Risk |
|------|--------|------|
| 诊断为 | NO | — |
| 确诊为 | NO | — |
| 患有 | NO | — |
| 应该用药 | NO | — |
| 建议服用 | NO | — |

---

## 3. Internal Term Leakage

### Found in KB Files

| Term | File | Line | Context | Risk |
|------|------|------|---------|------|
| 置信度 | billing-line-items-us.md | 49 | "低置信度项目需要人工复核" | **P1** — natural language use collides with forbidden_terms_registry |
| 置信度 | policy-limits-and-deductibles.md | 49 | "估算置信度必须降低" | **P1** — same collision |
| diagnosis_or_assessment | claim-packet-us.md | 26 | internal-code-style name in user-facing body | **P1** — should be translated |
| routing | sources.yaml | 50 | in `allowed_use` metadata field | LOW — metadata, not body |

### NOT Found in KB (properly excluded)

dispatch, classification, extracted, indexed_only, trace, PRD, Harness, HMW, POV, pipeline, agent_registry, confidence (as metadata label), debug, intent

---

## 4. Rule File Assessments

### medical_safety.yaml — Adequate

**Present**: 5 forbidden actions (diagnose, prescribe, stop_medication, no_vet_for_red_flag, downplay_emergency), 8 red_flags (toxin, breathing, seizure, urinate, vomiting, trauma, collapse, foreign_body)

**Gaps**: Missing `recommend_dietary_change` and `dose_change` (only in individual article frontmatter). No species-specific red flags. No severity escalation rules.

### insurance_guardrails.yaml — Strong

**Present**: 10 forbidden claims (一定能赔, 一定不能赔, guarantee_coverage, deny_coverage_definitively, legal_judgment, recommend_insurance_product, help_falsify_records, help_hide_preexisting_condition, incomplete_material_assessment, judge_without_policy), 5 allowed claims

**Gaps**: Missing `help_appeal_without_evidence`. No jurisdiction-specific guardrails.

### forbidden_terms_registry.yaml — Adequate

**Present**: 6 categories (internal_type_codes: 11, internal_status_codes: 4, internal_metadata_keywords: 10, developer_terms: 7, forbidden_tags: 3, routing_reason_prefixes: 3)

**Gaps**: Missing `indexed_with_manual_transcription` (present in prompt_boundaries.yaml but absent from registry). Missing `pipeline`, `agent_registry`, `qa_result`, `pdf_policy`. `all_forbidden: []` is empty (computed at load time but misleading if read directly).

---

## 5. Safety Boundary Quality

| Article | Domain | Forbidden Outputs | Contains Actual Advice? |
|---------|--------|-------------------|------------------------|
| medication-basics | medical | diagnose, prescribe, dose_change, stop_medication | NO |
| imaging-report-basics | medical | diagnose, prescribe, no_vet_for_red_flag | NO |
| lab-report-basics | medical | diagnose, prescribe, stop_medication | NO |
| prescription-diet | medical | recommend_brand, override_vet_diet_plan, diagnose | NO |
| toxin-boundary | safety | home_treatment_dosing, delay_vet_care, diagnose | NO |
| emergency-boundary | safety | diagnose, downplay_emergency, delay_vet_care | NO |
| billing-line-items-cn | billing | price_fairness_judgment, diagnosis_from_bill | NO |
| billing-line-items-us | billing | price_fairness_judgment, diagnosis_from_bill | NO |
| claim-packet-us | insurance | guarantee_coverage, deny_coverage, legal_advice | NO |
| claim-packet-cn | insurance | guarantee_coverage, deny_coverage, help_falsify_records | NO |
| cn-vet-records | jurisdiction | legal_advice, falsify_record | NO |
| us-vet-records | jurisdiction | legal_advice, accuse_clinic | NO |

**All 17 articles** properly declare forbidden_outputs and contain no dangerous advice.

---

## 6. Recommendations

| Priority | Action |
|----------|--------|
| P0 | Rewrite `置信度` in billing-line-items-us.md:49 and policy-limits-and-deductibles.md:49 to avoid forbidden_terms collision |
| P0 | Rewrite `diagnosis_or_assessment` in claim-packet-us.md:26 to natural language |
| P1 | Add `dose_change`, `recommend_dietary_change` to medical_safety.yaml global forbidden list |
| P1 | Add missing terms to forbidden_terms_registry.yaml (`indexed_with_manual_transcription`, `pipeline`, `agent_registry`) |
| P2 | Add species-specific red flags to medical_safety.yaml |
| P2 | Add jurisdiction-specific insurance guardrails for CN vs US |
