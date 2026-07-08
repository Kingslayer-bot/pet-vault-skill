# KB Next Iteration Plan — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## P0 — Must Fix (unsafe output or routing failure risk)

| # | Issue | Evidence | Impact | Fix | Effort |
|---|-------|----------|--------|-----|--------|
| 1 | **Material type mismatches** (claim_document≠claim_form, medical_report≠medical_record, clinic_communication≠chat_record) | material_ops.py vs routing.yaml | Routing failures — classified materials won't match triggers | Align names across material_ops, routing, pdf_policy | 2h |
| 2 | **`bill` missing from routing** | material_ops produces `bill` but routing only has `invoice` | bill materials may not trigger bill_report | Add `bill` to routing triggers | 30min |
| 3 | **Missing material types in material_ops** (payment_record, rejection_letter, imaging_report) | routing.yaml expects them | Routing expects types classifier can never produce | Add to MATERIAL_LABELS or remove from routing | 1h |
| 4 | **`置信度` collision** in 2 articles | billing-line-items-us.md:49, policy-limits-and-deductibles.md:49 | Sanitizer may mangle natural language | Rewrite to avoid term (e.g., "识别准确度") | 15min |
| 5 | **`diagnosis_or_assessment` internal-code style** | claim-packet-us.md:26 | Internal naming in user-facing text | Rewrite to "诊断或评估" | 5min |

---

## P1 — Current User Flows Missing KB Support

| # | Issue | Evidence | Impact | Fix | Effort |
|---|-------|----------|--------|-----|--------|
| 6 | **travel_care: zero KB content** | No domain, no articles, no routing, no sources, no eval, no tests | travel_care example completely orphaned; runtime will return empty | See travel_care expansion plan below | 2-3 days |
| 7 | **product_fit: broken example** | prescription-diet.md forbids brand recommendations; example expects them | product_fit example contradicts KB safety boundaries | See product_fit expansion plan below | 1-2 days |
| 8 | **Emergency contacts US-only** | emergency-boundary.md only lists ASPCA (US) | CN/HK/SG/JP users get US-only emergency info | Add CN emergency contacts to emergency-boundary.md | 2h |
| 9 | **No retrieval quality tests** | Only 1 query tested | Cannot verify KB actually serves user queries | Add 5+ query tests with expected results | 2h |
| 10 | **kb/eval/ dead code** | 5 files never loaded by any script or test | Confusing; wasted maintenance effort | Either wire into test suite or delete | 1h |

---

## P2 — Structure, Source, Maintainability

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 11 | Source URLs for nfra/pingan point to homepages | Update to specific document URLs | 30min |
| 12 | No HK/SG/JP sources | Add sources before creating P1 articles | 1 day |
| 13 | `clinic_communication` missing from EXPLICIT_TYPE_ALIASES | Add alias entry | 5min |
| 14 | CNY/RMB duplicate in ontology | Document as intentional alias or deduplicate | 15min |
| 15 | medical_safety.yaml missing dose_change/dietary_change | Add to global forbidden list | 15min |
| 16 | forbidden_terms_registry.yaml missing terms | Add indexed_with_manual_transcription, pipeline, agent_registry | 15min |
| 17 | No CI step for index rebuild/validation | Add build_kb_index.py to CI | 1h |
| 18 | No article expiration test | Add test checking expires_at field | 30min |
| 19 | KNOWN_TERMS gaps in query_knowledge_base.py | Add 疫苗, 手术, 麻醉, 住院, 影像, 免赔额, 赔付比例 | 15min |

---

## travel_care KB Expansion Plan

### New Domain

Add `travel` to ontology.yaml domains list.

### New Articles (minimum viable)

| Article | Domain | Region | Sources Needed |
|---------|--------|--------|---------------|
| pet-airline-requirements-us.md | travel | US | USDA APHIS, airline policies |
| pet-airline-requirements-cn.md | travel | CN | 中国海关, 航空公司政策 |
| pet-health-certificate.md | travel | global | USDA, MOA |
| pet-quarantine-rules.md | travel | global | Regional quarantine authorities |

### New Sources

| Source ID | Title | Region |
|-----------|-------|--------|
| usda-aphis-pet-travel | USDA APHIS Pet Travel | US |
| cn-customs-pet-import | 中国海关总署宠物出入境 | CN |

### New Routing Rule

Add `travel_care` route in routing.yaml with triggers: 飞机, 航班, 出差, 旅行, travel, flight, airline, carrier.

### New Eval Cases

- travel_health_certificate_us
- travel_health_certificate_cn
- travel_airline_carrier_requirements
- travel_quarantine_rules

---

## product_fit KB Expansion Plan

### New Article

| Article | Domain | Region | Sources Needed |
|---------|--------|--------|---------------|
| senior-pet-nutrition.md | nutrition | global | WSAVA, AAFCO, Merck |
| age-specific-diet-guide.md | nutrition | global | WSAVA, veterinary nutritionists |

### Key Design Decision

The new articles must:
- Explain nutritional needs by life stage (kitten, adult, senior)
- Explain prescription diet categories (kidney, joint, weight, dental)
- **FORBID**: recommending specific brands, overriding vet diet plans, diagnosing conditions
- **ALLOW**: explaining what "senior formula" means, listing common prescription diet categories, suggesting questions for the vet

### New Eval Cases

- product_fit_senior_cat_nutrition
- product_fit_prescription_diet_explanation
- product_fit_brand_recommendation_refusal

---

## mixed_materials KB Expansion Plan

### Current Status

The routing rule handles mixed materials but there's no KB content explaining how to handle them.

### New Article

| Article | Domain | Region | Sources Needed |
|---------|--------|--------|---------------|
| mixed-material-guide.md | billing | global | Internal |

### Content

- How to handle a submission with both bill + insurance policy
- How to handle bill + medical report
- Priority rules when multiple material types conflict

---

## Glossary Expansion Plan

### Current State

No dedicated glossary exists. Bill categories are in ontology.yaml (18 items) but not user-facing.

### Recommended

Create `kb/articles/reference/glossary.md` covering:
- All 18 bill_categories with user-friendly explanations
- Common insurance terms (deductible, waiting period, pre-existing condition)
- Common medical terms (ALT, BUN, creatinine, CBC)
- Common prescription terms (Rx diet, therapeutic diet)

---

## Regional Rules Expansion Plan

### Current State

Only US and CN have jurisdiction articles. HK/SG/JP have zero content.

### Recommended (P1 priority order)

1. HK: billing line items, insurance terms, vet record laws
2. SG: billing line items, insurance terms, AVS regulations
3. JP: billing line items, insurance terms, JVMA guidelines

Each needs: local sources, local currency examples, local regulatory references.

---

## Implementation Priority

| Phase | Focus | Duration |
|-------|-------|----------|
| Phase 0 | Fix P0 items (material type alignment, dangerous terms) | 1 day |
| Phase 1 | travel_care KB (4 articles + sources + routing + eval) | 3 days |
| Phase 2 | product_fit KB (2 articles + eval) + glossary | 2 days |
| Phase 3 | Retrieval quality tests + CI index validation | 1 day |
| Phase 4 | P1 jurisdictions (HK → SG → JP) | 5-7 days |
| Phase 5 | mixed_materials article + regional rules | 2 days |
