# KB Ontology Alignment — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## 1. Ontology Structure

```yaml
domains:        [billing, insurance, medical, nutrition, safety, jurisdiction]
jurisdictions:  p0: [US, CN]  |  p1: [HK, SG, JP]  |  global: [global]
languages:      p0: [zh, en]  |  p1: [zh-Hant, ja, ko, th]
currencies:     p0: [USD, CNY, RMB]  |  p1: [HKD, SGD, JPY]
bill_categories: exam, emergency_fee, diagnostic, imaging, hospitalization,
                 iv_fluids, anesthesia, surgery, medication, injection,
                 prescription_diet, disposal_fee, admin_fee, tax,
                 payment, discount, refund, unknown
boundaries:
  billing:    "Separate charge, payment, discount, refund, and tax."
  insurance:  "Conditional precheck only. No coverage guarantees..."
  medical:    "Explain terms and red flags only. No diagnosis..."
```

---

## 2. Material Type Alignment (CRITICAL)

### material_ops.py vs routing.yaml vs pdf_policy.yaml

| material_ops.py | routing.yaml | pdf_policy.yaml | Aligned? |
|----------------|-------------|----------------|----------|
| `invoice` | `invoice` | `invoice` | OK |
| `bill` | — | — | **MISSING from routing/pdf_policy** |
| `insurance_policy` | `insurance_policy` | `insurance_policy` | OK |
| `claim_document` | `claim_form` | `claim_form` | **MISMATCH** |
| `lab_report` | `lab_report` | `lab_report` | OK |
| `medical_report` | `medical_record` | `medical_record` | **MISMATCH** |
| `prescription` | — | — | **MISSING from routing/pdf_policy** |
| `appointment` | — | — | **MISSING from routing/pdf_policy** |
| `clinic_communication` | `chat_record` | — | **MISMATCH** |
| `pet_profile` | — | — | **MISSING from routing/pdf_policy** |
| — | `payment_record` | `payment_record` | **NOT in material_ops** |
| — | `rejection_letter` | `rejection_letter` | **NOT in material_ops** |
| — | `imaging_report` | `imaging_report` | **NOT in material_ops** |
| — | `chat_record` | — | **NOT in material_ops** (alias of clinic_communication) |
| — | — | `timeline` | **NOT in material_ops or routing** |

### Impact of Mismatches

| Mismatch | Runtime Effect |
|----------|---------------|
| `claim_document` vs `claim_form` | Classified claim_document will NOT match insurance_precheck routing trigger |
| `medical_report` vs `medical_record` | Classified medical_report will NOT match timeline_update routing trigger |
| `clinic_communication` vs `chat_record` | Classified clinic_communication will NOT match routing trigger |
| `bill` missing from routing | Classified bill materials may not trigger bill_report route |
| `payment_record` not in material_ops | Routing expects it but classifier can never produce it |
| `rejection_letter` not in material_ops | Routing expects it but classifier can never produce it |

---

## 3. Domain Alignment Across All Layers

| Domain | Ontology | material_ops | Rules | Articles | Eval (.agents/) | Eval (kb/eval/) | Examples |
|--------|----------|--------------|-------|----------|-----------------|-----------------|----------|
| billing | YES | YES | YES | YES (3) | YES | YES | YES |
| insurance | YES | YES | YES | YES (6) | YES | YES | YES |
| medical | YES | YES | YES | YES (4) | YES | YES | NO |
| nutrition | YES | **NO** | **NO** | YES (1) | **NO** | **NO** | YES (product_fit) |
| safety | YES | NO | YES | YES (2) | YES | YES | YES |
| jurisdiction | YES | NO | NO | YES (2) | **NO** | **NO** | NO |
| travel | **NO** | NO | NO | **NO** | **NO** | **NO** | YES (orphaned) |

---

## 4. Concept Coverage: ontology vs material_ops vs rules vs eval

| Concept | ontology | material_ops | rules | eval | User-visible label? |
|---------|----------|-------------|-------|------|-------------------|
| invoice | bill_categories | MATERIAL_LABELS | routing, pdf_policy | billing_cases | 发票/收据 |
| bill | bill_categories | MATERIAL_LABELS | **MISSING** | billing_cases | 账单/费用明细 |
| insurance_policy | — | MATERIAL_LABELS | routing, pdf_policy | insurance_cases | 保单/保险合同 |
| claim_document | — | MATERIAL_LABELS | **claim_form** (mismatch) | — | 理赔材料 |
| lab_report | — | MATERIAL_LABELS | routing, pdf_policy | — | 化验报告 |
| medical_report | — | MATERIAL_LABELS | **medical_record** (mismatch) | — | 检查报告 |
| prescription | — | MATERIAL_LABELS | **MISSING** | — | 处方/用药 |
| appointment | — | MATERIAL_LABELS | **MISSING** | — | 预约/复诊 |
| clinic_communication | — | MATERIAL_LABELS | **chat_record** (mismatch) | — | 沟通记录 |
| pet_profile | — | MATERIAL_LABELS | **MISSING** | — | 宠物信息 |
| exam | bill_categories | — | — | — | 检查费 |
| emergency_fee | bill_categories | — | — | — | 急诊费 |
| diagnostic | bill_categories | — | — | — | 诊断费 |
| imaging | bill_categories | — | — | — | 影像费 |
| surgery | bill_categories | — | — | — | 手术费 |
| medication | bill_categories | — | — | — | 药费 |
| payment | bill_categories | — | billing_validation | billing_cases | 付款 |
| discount | bill_categories | — | billing_validation | billing_cases | 折扣 |
| refund | bill_categories | — | billing_validation | billing_cases | 退款 |

---

## 5. Mismatches Summary

### P0 — Critical (will cause routing failures)

1. `claim_document` (material_ops) ≠ `claim_form` (routing/pdf_policy)
2. `medical_report` (material_ops) ≠ `medical_record` (routing/pdf_policy)
3. `clinic_communication` (material_ops) ≠ `chat_record` (routing)
4. `bill` (material_ops) not in routing triggers
5. `payment_record`, `rejection_letter`, `imaging_report` in routing but not in material_ops

### P1 — Missing ontology domains

6. No `travel` domain (needed for travel_care)
7. `nutrition` domain exists but has no rules, no material_ops mapping, no eval

### P2 — Consistency issues

8. `RMB` and `CNY` both listed as separate P0 currencies (same currency)
9. `clinic_communication` missing from `EXPLICIT_TYPE_ALIASES` in material_ops.py
10. `bill_categories` in ontology has 18 items but no test validates all are handled
