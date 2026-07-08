# KB Coverage Matrix — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## 1. User Flow Coverage Matrix

| User Flow | Required KB Knowledge | Current KB Support | Evidence Files | Gaps | Risk |
|-----------|---------------------|-------------------|----------------|------|------|
| **bill_explain** | Billing line item taxonomy, charge/payment/discount separation, currency handling | billing-line-items-cn.md, billing-line-items-us.md, payment-discount-refund.md, billing_validation.yaml | 3 articles + 1 rule + 4 eval cases + 1 example | US billing example missing; HK/SG/JP billing missing | **Strong** |
| **knowledge_query** | Broad KB coverage for term explanation, claim materials, medical terms, insurance concepts | 17 articles across 5 domains, FTS5 index | All articles searchable via query_knowledge_base.py | No retrieval quality tests; no relevance ranking validation | **Strong** |
| **emergency_guardrail** | Toxin identification, emergency symptoms, red flags, escalation contacts | emergency-boundary.md, toxin-boundary.md, medical_safety.yaml | 2 articles + 1 rule + 12 eval cases + 1 example | Emergency contacts US-only (ASPCA); no CN/HK/SG/JP contacts | **Strong** |
| **insurance_boundary** | Claim material check, forbidden guarantee language, policy term explanation | 6 insurance articles, insurance_guardrails.yaml | 6 articles + 1 rule + insurance_cases eval + 1 example | No jurisdiction-specific guardrails for CN vs US | **Strong** |
| **travel_care** | Airline pet policies, health certificates, quarantine regulations, carrier requirements | **NONE** | 1 example (orphaned) | No domain in ontology, no articles, no routing rule, no sources, no eval cases | **Missing** |
| **product_fit** | Senior pet nutrition, prescription diet guidance, age-specific considerations | prescription-diet.md (partial) | 1 example (semi-orphaned) | No dedicated article; existing article FORBIDS brand/type recommendations that example expects | **Weak** |
| **mixed_materials** | Multi-type material routing, combined report generation | routing.yaml (mixed_materials_routing) | 1 eval case in skill_workflow_cases.yaml | No KB content for mixed-material explanation; routing only | **Partial** |
| **empty_or_weak_input** | Fallback behavior, clarification prompts | routing.yaml (fallback) | 1 eval case in skill_workflow_cases.yaml | No KB content; purely code-level handling | **Partial** |

---

## 2. Coverage Risk Labels

- **Strong**: KB articles + rules + eval cases + examples all present and aligned
- **Partial**: Some KB support exists but significant gaps remain
- **Weak**: Minimal KB support; closest article has conflicting safety boundaries
- **Missing**: No KB content exists for this flow

---

## 3. Domain Coverage by User Flow

| Domain | bill_explain | knowledge_query | emergency_guardrail | insurance_boundary | travel_care | product_fit |
|--------|-------------|-----------------|--------------------|--------------------|-------------|-------------|
| billing | **Primary** | Supported | -- | -- | -- | -- |
| insurance | -- | Supported | -- | **Primary** | -- | -- |
| medical | -- | Supported | -- | -- | -- | Partial |
| safety | -- | -- | **Primary** | -- | -- | -- |
| jurisdiction | -- | Supported | -- | Supported | -- | -- |
| nutrition | -- | -- | -- | -- | -- | Partial |
| travel | -- | -- | -- | -- | **MISSING** | -- |

---

## 4. Article-to-Flow Reference Map

| KB Article | bill_explain | knowledge_query | emergency | insurance | travel | product |
|-----------|-------------|-----------------|-----------|-----------|--------|---------|
| billing-line-items-cn | PRIMARY | searchable | -- | -- | -- | -- |
| billing-line-items-us | (no example) | searchable | -- | -- | -- | -- |
| payment-discount-refund | PRIMARY | searchable | -- | -- | -- | -- |
| claim-packet-cn | -- | PRIMARY | -- | -- | -- | -- |
| claim-packet-us | -- | PRIMARY | -- | -- | -- | -- |
| insurance-terms-cn | -- | searchable | -- | supported | -- | -- |
| insurance-terms-us | -- | searchable | -- | supported | -- | -- |
| policy-limits-and-deductibles | -- | searchable | -- | supported | -- | -- |
| rejection-letter-analysis | -- | searchable | -- | supported | -- | -- |
| cn-vet-records | -- | searchable | -- | -- | -- | -- |
| us-vet-records | -- | searchable | -- | -- | -- | -- |
| imaging-report-basics | -- | searchable | -- | -- | -- | -- |
| lab-report-basics | -- | searchable | -- | -- | -- | -- |
| medication-basics | -- | searchable | -- | -- | -- | -- |
| prescription-diet | -- | searchable | -- | -- | -- | PARTIAL |
| emergency-boundary | -- | searchable | PRIMARY | -- | -- | -- |
| toxin-boundary | -- | searchable | PRIMARY | -- | -- | -- |

---

## 5. Eval Case Coverage by Flow

| Flow | .agents/eval_cases/ | kb/eval/ | Test files |
|------|-------------------|----------|------------|
| bill_explain | report_artifact_cases (6), billing_report_cases (3) | billing_cases (4), pdf_cases (2) | test_billing_report_eval_cases, test_report_golden_snapshots, test_bill_render_ops |
| knowledge_query | skill_workflow_cases (1) | route_cases (1) | test_skill_workflow_cases, test_pet_vault_skill |
| emergency_guardrail | emergency_routing_cases (12) | medical_safety_cases (4) | test_subagent_workflow, test_skill_workflow_cases |
| insurance_boundary | skill_workflow_cases (2 forbidden) | insurance_cases (5+2) | test_subagent_workflow, test_local_knowledge_hub |
| **travel_care** | **NONE** | **NONE** | **NONE** |
| **product_fit** | **NONE** | **NONE** | **NONE** |
| mixed_materials | skill_workflow_cases (1 routing) | route_cases (0) | test_skill_workflow_cases (routing only) |
| empty_input | skill_workflow_cases (1) | -- | test_skill_workflow_cases |

---

## 6. Critical Findings

1. **travel_care is completely unsupported by KB** — no domain, no articles, no routing, no sources, no eval, no tests. The example is a pure placeholder.
2. **product_fit is semi-broken** — the closest article (prescription-diet.md) explicitly forbids the kind of recommendation the example expects.
3. **kb/eval/ is dead code** — 5 files with ~14 eval cases are never loaded by any script or test. Active eval is in `.agents/eval_cases/`.
4. **11 of 17 articles lack dedicated example flows** — they are discoverable via FTS but have no demonstrated usage path.
5. **No retrieval quality tests** — only one test checks that query_knowledge_base.py returns at least 1 match. No relevance ranking validation.
