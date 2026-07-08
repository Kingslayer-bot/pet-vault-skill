# KB Current Map — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08
**Project root**: `remote_repo/pet-vault-skill`

---

## 1. Complete KB Tree

```
kb/
├── ontology.yaml                    (45 lines — domains, jurisdictions, languages, currencies, boundaries)
├── sources.yaml                     (157 lines — 12 sources)
├── articles/
│   ├── billing/
│   │   ├── billing-line-items-cn.md          (49 lines)
│   │   ├── billing-line-items-us.md          (49 lines)
│   │   └── payment-discount-refund.md        (49 lines)
│   ├── insurance/
│   │   ├── claim-packet-cn.md                (52 lines)
│   │   ├── claim-packet-us.md                (49 lines)
│   │   ├── insurance-terms-cn.md             (51 lines)
│   │   ├── insurance-terms-us.md             (51 lines)
│   │   ├── policy-limits-and-deductibles.md  (49 lines)
│   │   └── rejection-letter-analysis.md      (50 lines)
│   ├── jurisdiction/
│   │   ├── cn-vet-records.md                 (48 lines)
│   │   └── us-vet-records.md                 (47 lines)
│   ├── medical/
│   │   ├── imaging-report-basics.md          (46 lines)
│   │   ├── lab-report-basics.md              (47 lines)
│   │   ├── medication-basics.md              (47 lines)
│   │   └── prescription-diet.md              (48 lines)
│   └── safety/
│       ├── emergency-boundary.md             (50 lines)
│       └── toxin-boundary.md                 (50 lines)
├── rules/
│   ├── billing_validation.yaml               (16 lines)
│   ├── insurance_guardrails.yaml             (18 lines)
│   ├── medical_safety.yaml                   (16 lines)
│   ├── pdf_policy.yaml                       (19 lines)
│   ├── privacy.yaml                          (18 lines)
│   └── routing.yaml                          (43 lines)
├── eval/
│   ├── billing_cases.yaml                    (12 lines, 4 cases)
│   ├── insurance_cases.yaml                  (9 lines)
│   ├── medical_safety_cases.yaml             (8 lines, 4 cases)
│   ├── pdf_cases.yaml                        (4 lines, 2 cases)
│   └── route_cases.yaml                      (15 lines, 4 cases)
└── index/
    ├── .gitkeep                              (1 byte)
    └── kb.sqlite                             (61,440 bytes, built 2026-07-07)
```

**Totals**: 17 articles, 6 rules, 5 eval files, 1 ontology, 1 sources, 1 SQLite index

---

## 2. Article Inventory

| # | File | id | Title | Domain | Region | Source Tier | Risk Level |
|---|------|----|-------|--------|--------|-------------|------------|
| 1 | billing/billing-line-items-cn.md | billing-line-items-cn | 中国宠物医疗账单项目解释 | billing | CN | internal_template | medium |
| 2 | billing/billing-line-items-us.md | billing-line-items-us | US veterinary invoice line items | billing | US | internal_template | medium |
| 3 | billing/payment-discount-refund.md | payment-discount-refund | 付款、折扣和退款不能混入医疗费用 | billing | global | internal_template | high |
| 4 | insurance/claim-packet-cn.md | claim-packet-cn | 中国宠物保险理赔材料包 | insurance | CN | insurer_policy | high |
| 5 | insurance/claim-packet-us.md | claim-packet-us | 美国宠物保险理赔材料包 | insurance | US | regulator | medium |
| 6 | insurance/insurance-terms-cn.md | insurance-terms-cn | 中国宠物保险常见条款 | insurance | CN | insurer_policy | high |
| 7 | insurance/insurance-terms-us.md | insurance-terms-us | 美国宠物保险常见术语 | insurance | US | regulator | medium |
| 8 | insurance/policy-limits-and-deductibles.md | policy-limits-and-deductibles | 免赔额、赔付比例和限额如何影响估算 | insurance | global | regulator | medium |
| 9 | insurance/rejection-letter-analysis.md | rejection-letter-analysis | 拒赔信分析边界 | insurance | global | regulator | high |
| 10 | jurisdiction/cn-vet-records.md | cn-vet-records | 中国动物诊疗病历、处方和理赔材料 | jurisdiction | CN | government | medium |
| 11 | jurisdiction/us-vet-records.md | us-vet-records | 美国兽医记录和理赔材料索取 | jurisdiction | US | veterinary_association | medium |
| 12 | medical/imaging-report-basics.md | imaging-report-basics | 影像报告基础术语 | medical | global | veterinary_reference | medium |
| 13 | medical/lab-report-basics.md | lab-report-basics | 化验报告基础术语 | medical | global | veterinary_reference | medium |
| 14 | medical/medication-basics.md | medication-basics | 用药记录基础解释 | medical | global | veterinary_reference | high |
| 15 | medical/prescription-diet.md | prescription-diet | 处方粮和营养建议边界 | medical | global | veterinary_association | medium |
| 16 | safety/emergency-boundary.md | emergency-boundary | 急症安全边界 | safety | global | veterinary_reference | high |
| 17 | safety/toxin-boundary.md | toxin-boundary | 中毒与误食安全边界 | safety | global | professional_public_education | high |

**All articles**: language=zh, species=[dog, cat], last_reviewed=2026-07-07, expires_at=2027-07-07

---

## 3. Rules Inventory

| File | Purpose | Used by code | Used by tests |
|------|---------|-------------|---------------|
| routing.yaml | 5 routes: bill_report, insurance_precheck, knowledge_query, emergency_boundary, timeline_update | petvault_core.py → _get_emergency_terms() | test_kb_structure, test_local_knowledge_hub, kb/eval/route_cases |
| insurance_guardrails.yaml | 10 forbidden_claims, 5 allowed_claims | petvault_core.py → _get_dynamic_forbidden_terms() | test_subagent_workflow, kb/eval/insurance_cases |
| medical_safety.yaml | 5 forbidden actions, 8 red_flags | (not directly imported) | kb/eval/medical_safety_cases |
| billing_validation.yaml | Currencies (USD/CNY/RMB p0, HKD/SGD/JPY p1), separation rules, 5 fail_conditions | (not directly imported) | kb/eval/billing_cases |
| pdf_policy.yaml | PDF required/not_required types, chat output constraints | (not directly imported) | kb/eval/pdf_cases |
| privacy.yaml | Storage model, 8 sensitive fields, log restrictions | (not directly imported) | **NOT tested** |

---

## 4. Sources Inventory

| Source ID | Region | Tier | URL Quality |
|-----------|--------|------|-------------|
| naic-pet-insurance-model-act | US | 1 | Direct PDF — good |
| naphia-industry-data | US | 2 | Homepage — acceptable |
| avma-owner-records-ethics | US | 1 | Specific page — good |
| fda-animal-veterinary | US | 1 | Section page — good |
| aspca-poison-control | US | 3 | Info page — good |
| wsava-nutrition-guidelines | global | 1 | Guidelines page — good |
| merck-veterinary-manual | global | 3 | Homepage — acceptable |
| cornell-feline-health-center | US | 1 | Center page — good |
| moa-vet-records-cn | CN | 1 | Gov page — good |
| nfra-pet-insurance-risk-cn | CN | 1 | **Homepage only — missing specific doc URL** |
| pingan-pet-insurance-terms-cn | CN | 2 | **Homepage only — missing specific product URL** |
| internal-anonymized-billing-taxonomy | global | 4 | local-guidance (internal) |

---

## 5. Code-KB Dependency Graph

```
petvault_core.py
  ├── load_kb_rules() → ALL kb/rules/*.yaml (6 files)
  │   ├── routing.yaml → _get_emergency_terms()
  │   └── insurance_guardrails.yaml → _get_dynamic_forbidden_terms()
  └── load_kb_ontology() → kb/ontology.yaml

query_knowledge_base.py
  ├── load_articles() → ALL kb/articles/**/*.md (17 files via rglob)
  └── search_sqlite() → kb/index/kb.sqlite (FTS5)

build_kb_index.py
  └── imports load_articles() → writes kb/index/kb.sqlite

validate_kb.py
  ├── imports load_articles(), parse_frontmatter()
  ├── reads kb/sources.yaml
  └── validates ALL kb/articles/**/*.md

petvault_dispatch.py
  └── subprocess → query_knowledge_base.py
```

**Orphaned from code**: entire `kb/eval/` directory (5 files) — no script loads them. Active eval cases live in `.agents/eval_cases/`.

---

## 6. Example Flows Inventory

| Flow | Directory | Files | KB Articles Referenced |
|------|-----------|-------|----------------------|
| bill_explain | examples/bill_explain/ | README, request, sample_invoice, expected/report | billing-line-items-cn, payment-discount-refund |
| knowledge_query | examples/knowledge_query/ | README, request, expected/answer | claim-packet-us, claim-packet-cn (via FTS) |
| emergency_guardrail | examples/emergency_guardrail/ | README, request, expected/response | toxin-boundary, emergency-boundary |
| insurance_boundary | examples/insurance_boundary/ | README, request, expected/response | insurance_guardrails.yaml (rules) |
| travel_care | examples/travel_care/ | README, request, expected/response | **NONE — no travel articles exist** |
| product_fit | examples/product_fit/ | README, request, expected/response | prescription-diet.md (partial, but example violates its forbidden_outputs) |
