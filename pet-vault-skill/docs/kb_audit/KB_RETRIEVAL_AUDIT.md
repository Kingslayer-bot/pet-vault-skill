# KB Retrieval Audit — PetVault Knowledge Base Audit

**Audit date**: 2026-07-08

---

## 1. Retrieval Architecture

`query_knowledge_base.py` uses a two-tier search:

1. **SQLite FTS5** (primary): `kb/index/kb.sqlite` with virtual table `kb_fts` — indexes `title` and `body` columns. Supports `domain`, `jurisdiction`, `language` filters.
2. **Markdown fallback** (secondary): `rglob("*.md")` from `kb/articles/`, keyword counting/scoring against `title+domain+body` (x3 weight), title match bonus (+4), domain exact match bonus (+2).

**KNOWN_TERMS** for Chinese token extraction (24 terms): 理赔, 报销, 材料, 保单, 保险, 等待期, 既往症, 账单, 发票, 费用, 付款, 折扣, 退款, 检查, 化验, 处方, 营养, 处方粮, 中毒, 毒物, 急诊, 百合, 巧克力.

---

## 2. Sample Query Analysis

Based on the KB structure, FTS5 indexing, and article content:

| Query | Expected Match | Likely Top Result | Assessment |
|-------|---------------|-------------------|------------|
| 为什么账单里有 exam fee？ | billing-line-items-cn/us | billing-line-items-cn (contains exam in bill_categories) | **OK** — will match |
| 疫苗费用为什么会出现在账单里？ | billing-line-items-cn | billing-line-items-cn (contains 疫苗 in body) | **Partial** — "疫苗" not in KNOWN_TERMS; may rely on FTS5 Chinese tokenization |
| 保险是不是一定能理赔？ | insurance articles + guardrails | insurance-terms-cn or claim-packet-cn | **OK** — will match, and guardrails block dangerous response |
| 猫出差期间饮水怎么安排？ | travel_care | **NO MATCH** — no travel articles exist | **FAIL** — will return empty or irrelevant results |
| 自动喂食机适合胆小猫吗？ | product_fit | prescription-diet.md (weak match on 营养/处方粮) | **Weak** — not the right article |
| 宠物呼吸困难怎么办？ | emergency-boundary | emergency-boundary.md (contains 呼吸困难) | **OK** — will match |
| 宠物账单里的 lab work 是什么？ | lab-report-basics | lab-report-basics.md (contains 化验/lab) | **OK** — will match |

---

## 3. Retrieval Quality Issues

### 3.1 KNOWN_TERMS Gaps

The 24 hardcoded Chinese terms miss important query patterns:

| Missing Term | Impact |
|-------------|--------|
| 疫苗 (vaccine) | travel_care queries about vaccination requirements won't tokenize properly |
| 急诊 (emergency) — actually present | OK |
| 处方粮 (prescription diet) — actually present | OK |
| 手术 (surgery) | billing queries about surgery fees may not tokenize |
| 麻醉 (anesthesia) | billing queries about anesthesia fees |
| 住院 (hospitalization) | billing queries about hospitalization |
| 影像 (imaging) | medical queries about imaging reports |
| 免赔额 (deductible) | insurance queries about deductibles |
| 赔付比例 (reimbursement rate) | insurance queries |
| 等待期 (waiting period) — actually present | OK |

### 3.2 FTS5 Limitations

- FTS5 indexes `title` and `body` but NOT `domain`, `jurisdiction`, or `language` (those are UNINDEXED columns used for post-filter)
- Chinese tokenization quality depends on SQLite build — may not segment Chinese well
- No synonym expansion (e.g., "猫" won't match "feline")
- No fuzzy matching for typos

### 3.3 No Retrieval Quality Tests

Current test coverage:
- `test_pet_vault_skill.py`: One test checks that "理赔需要哪些材料" returns ≥1 match
- `test_local_knowledge_hub.py`: Tests filter combinations (domain/jurisdiction/language)
- **No test validates**: relevance ranking, top-result accuracy, multi-result ordering, cross-domain queries

---

## 4. Index Status

| Aspect | Status |
|--------|--------|
| Index file | `kb/index/kb.sqlite` (61,440 bytes) |
| Built | 2026-07-07 14:06:26 |
| Articles last reviewed | 2026-07-07 |
| In sync | YES — same date as articles |
| Build script | `build_kb_index.py` — full rebuild (DROP + CREATE + INSERT) |
| CI validation | **None** — no CI job rebuilds or validates index |
| Staleness test | **None** — no test checks index freshness |

---

## 5. Recommendations

| Priority | Action |
|----------|--------|
| P0 | Add retrieval quality test: at least 5 queries with expected top-1 article_id |
| P1 | Expand KNOWN_TERMS to cover all bill_categories and insurance terms |
| P1 | Add CI step to rebuild index and validate article-index consistency |
| P2 | Add cross-language query test (Chinese query matching English article content) |
| P2 | Consider adding synonym table for common pet terms |
| P2 | Add index freshness test (compare sqlite mtime vs article mtime) |
