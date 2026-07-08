# kb/eval/ — DEPRECATED

This directory contains legacy eval case files that are **not loaded by any script or test**.

The active eval case system lives in `.agents/eval_cases/`.

## Migration Status

| kb/eval/ file | Status | Active equivalent |
|---------------|--------|-------------------|
| billing_cases.yaml | Covered | `tests/test_local_knowledge_hub.py` (amount/currency/kind parsing) |
| insurance_cases.yaml | Covered | `.agents/eval_cases/skill_workflow_cases.yaml` (forbidden insurance) |
| medical_safety_cases.yaml | Covered | `.agents/eval_cases/emergency_routing_cases.yaml` |
| pdf_cases.yaml | Covered | `.agents/eval_cases/pdf_render_cases.yaml` |
| route_cases.yaml | Covered | `.agents/eval_cases/skill_workflow_cases.yaml` (routing) |

## What to do

- **Do not add new eval cases here.** Use `.agents/eval_cases/` instead.
- These files may be removed in a future cleanup.
- If you need to test KB behavior, add test cases to `tests/test_kb_retrieval_quality.py` or `.agents/eval_cases/`.
