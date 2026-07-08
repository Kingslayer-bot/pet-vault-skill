# KB Sources Audit — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## 1. Sources Inventory (12 total)

| # | Source ID | Title | URL | Domain(s) | Region | Tier | Lang | URL Quality | Articles Using It |
|---|---------|-------|-----|-----------|--------|------|------|-------------|-------------------|
| 1 | naic-pet-insurance-model-act | NAIC Pet Insurance Model Act | https://content.naic.org/sites/default/files/model-law-633.pdf | insurance, jurisdiction | US | 1 | en | Direct PDF | claim-packet-us, insurance-terms-us, policy-limits, rejection-letter, us-vet-records |
| 2 | naphia-industry-data | North American Pet Health Insurance Association | https://naphia.org/ | insurance | US | 2 | en | Homepage | insurance-terms-us |
| 3 | avma-owner-records-ethics | AVMA owner and ethics resources | https://www.avma.org/.../principles-veterinary-medical-ethics-avma | medical, jurisdiction | US | 1 | en | Specific page | us-vet-records |
| 4 | fda-animal-veterinary | FDA Animal and Veterinary | https://www.fda.gov/animal-veterinary | medical, nutrition, safety | US | 1 | en | Section page | medication-basics, prescription-diet, toxin-boundary |
| 5 | aspca-poison-control | ASPCA Animal Poison Control Center | https://www.aspca.org/pet-care/aspca-poison-control | safety | US | 3 | en | Info page | emergency-boundary, toxin-boundary |
| 6 | wsava-nutrition-guidelines | WSAVA Global Nutrition Guidelines | https://wsava.org/global-guidelines/global-nutrition-guidelines/ | nutrition, medical | global | 1 | en | Guidelines page | prescription-diet |
| 7 | merck-veterinary-manual | Merck Veterinary Manual | https://www.merckvetmanual.com/ | medical | global | 3 | en | Homepage | imaging-report, lab-report, medication-basics, emergency-boundary |
| 8 | cornell-feline-health-center | Cornell Feline Health Center | https://www.vet.cornell.edu/.../cornell-feline-health-center | medical | US | 1 | en | Center page | lab-report-basics |
| 9 | moa-vet-records-cn | 农业农村部动物诊疗病历与兽医处方规范 | https://xmsyj.moa.gov.cn/.../6442774.htm | jurisdiction, medical | CN | 1 | zh | Gov page | claim-packet-cn, cn-vet-records |
| 10 | nfra-pet-insurance-risk-cn | 国家金融监督管理总局风险提示 | https://www.nfra.gov.cn/ | insurance | CN | 1 | zh | **Homepage only** | claim-packet-cn, insurance-terms-cn, cn-vet-records, rejection-letter |
| 11 | pingan-pet-insurance-terms-cn | 平安公开宠物险产品页面 | https://www.pingan.com/ | insurance | CN | 2 | zh | **Homepage only** | claim-packet-cn, insurance-terms-cn, policy-limits |
| 12 | internal-anonymized-billing-taxonomy | PetVault anonymized billing taxonomy | local-guidance | billing | global | 4 | zh | Internal | billing-line-items-cn, billing-line-items-us, payment-discount-refund |

---

## 2. Source Quality Issues

### Missing Specific URLs (P1)

| Source ID | Problem | Impact |
|-----------|---------|--------|
| nfra-pet-insurance-risk-cn | URL points to `https://www.nfra.gov.cn/` (homepage), not the specific risk advisory document | Cannot verify source content; URL may return different content over time |
| pingan-pet-insurance-terms-cn | URL points to `https://www.pingan.com/` (corporate homepage), not specific pet insurance product page | Product pages change frequently; homepage link is not traceable |

### Orphaned Sources

**None.** All 12 sources are referenced by at least one article.

### Articles Referencing Nonexistent Sources

**None.** All `sources:` fields in article frontmatter reference valid source IDs.

### Duplicate Sources

**None found.** Each source ID is unique.

### Source Region Distribution

| Region | Count | Gap |
|--------|-------|-----|
| US | 6 | Adequate for P0 |
| CN | 3 | Adequate for P0 |
| global | 2 | Adequate |
| internal | 1 | N/A |
| **HK** | **0** | **No HK sources for P1 jurisdiction** |
| **SG** | **0** | **No SG sources for P1 jurisdiction** |
| **JP** | **0** | **No JP sources for P1 jurisdiction** |

### Source Tier Distribution

| Tier | Count | Sources |
|------|-------|---------|
| Tier 1 (regulator/gov) | 6 | naic, avma, fda, wsava, cornell, moa, nfra |
| Tier 2 (industry/insurer) | 2 | naphia, pingan |
| Tier 3 (reference/nonprofit) | 2 | aspca, merck |
| Tier 4 (internal) | 1 | internal-anonymized-billing-taxonomy |

### Missing Source Types

| Missing Type | Needed For |
|-------------|-----------|
| HK veterinary authority | HK jurisdiction articles |
| SG animal & veterinary service | SG jurisdiction articles |
| JP veterinary medical association | JP jurisdiction articles |
| CN poison control / emergency vet | CN safety articles (currently only ASPCA US) |
| Travel/airline regulations source | travel_care articles |
| Pet product safety source | product_fit articles |

---

## 3. Source Metadata Completeness

Every source has: `id`, `title`, `url`, `domain`, `region`, `tier`, `language`, `allowed_use`, `forbidden_use`, `needs_verification`, `last_reviewed`.

**Missing fields**: None. All sources have complete metadata.

**Date uniformity**: All sources have `last_reviewed: 2026-07-07`. This is suspicious — either all were reviewed on the same day (possible for initial creation) or dates were batch-set without actual review.

---

## 4. Recommendations

| Priority | Action |
|----------|--------|
| P0 | Fix nfra-pet-insurance-risk-cn URL to specific risk advisory document |
| P0 | Fix pingan-pet-insurance-terms-cn URL to specific pet insurance product page |
| P1 | Add HK/SG/JP sources before creating P1 jurisdiction articles |
| P1 | Add CN emergency contact source (中国畜牧兽医学会 or local animal emergency) |
| P2 | Add travel-related regulatory sources (USDA APHIS, CN customs) for travel_care |
| P2 | Stagger `last_reviewed` dates to reflect actual review cadence |
