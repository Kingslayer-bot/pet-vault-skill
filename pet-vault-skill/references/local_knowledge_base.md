# Local Knowledge Base Design

Use this reference when the user asks a knowledge-only question or when improving the PetVault local knowledge layer.

## Routing

- Knowledge-only question: no uploaded material, no request to organize, archive, explain a specific bill/report, check a claim packet, or generate PDF. Use `scripts/query_knowledge_base.py`, answer briefly, cite local `article_id` and source URL, and do not create a vault report.
- Purposeful report request: uploaded files, paths, images, invoices, bills, payment, insurance, claim, referral packet, or explicit PDF/archive wording. Run the report pipeline and attach or link `report.pdf` when available.
- Ambiguous request: ask one confirmation question. Do not default silently to `general` when the user likely expects a bill, claim, or timeline deliverable.

## Initial Crawl Scope

Prioritize low-risk, user-education sources:

- Pet insurance concepts: claim packets, invoices, medical records, waiting period, deductible, reimbursement, exclusions, pre-existing condition language.
- Billing vocabulary: examination, lab, imaging, sedation, injection, prescription, food, service fee, payment, discount, balance.
- Medical-record vocabulary: CBC, chemistry, electrolytes, urinalysis, radiology, ultrasound, prescription, SOAP note, discharge summary.
- Nutrition and prescription-food questions: diet history, body condition score, feeding instructions, when to ask the veterinarian.
- Emergency escalation pages: toxin ingestion, drug/food/device safety alerts, recall routing.

Avoid crawling or using:

- Forum anecdotes as authority.
- Unverified dosage tables, diagnosis checklists, or home treatment recipes.
- Insurer marketing pages as policy truth unless the user uploads that exact policy.

## Storage Form

Use three layers:

- `kb/articles/*.md`: curated Markdown articles with frontmatter fields `article_id`, `title`, `topic`, `jurisdiction`, `risk_level`, `source_url`, and `updated_at`.
- `kb/sources.yaml`: crawl allowlist with scope and boundary notes.
- SQLite/FTS index: optional generated index for speed. It should be rebuildable from Markdown and should not become the source of truth.

Long-term PetVault facts belong in the vault SQLite database, not in KB articles. Reports are snapshots, not knowledge-base entries.

## Answer Contract

- Knowledge answers must say when a point is general education rather than pet-specific advice.
- Insurance answers must say when policy terms are missing and must not promise reimbursement.
- Medical answers must explain terminology and questions to ask, not diagnose or prescribe.
- Emergency answers must route to a veterinarian, poison-control service, or local emergency clinic.
