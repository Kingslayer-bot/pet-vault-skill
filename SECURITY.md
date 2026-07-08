# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it privately via email to the repository maintainer. Do not open a public issue.

## Safety Boundaries

PetVault enforces safety through multiple layers:

1. **Forbidden terms registry** (`.agents/forbidden_terms_registry.yaml`) — canonical list of internal terms that must never appear in user output
2. **Prompt boundaries** (`.agents/prompt_boundaries.yaml`) — defines user-visible vs internal content rules
3. **Medical safety rules** (`kb/rules/medical_safety.yaml`) — forbids diagnosis, prescribing, and emergency downplaying
4. **Insurance guardrails** (`kb/rules/insurance_guardrails.yaml`) — forbids coverage guarantees and legal advice
5. **Report sanitizer** (`scripts/report_sanitizer.py`) — strips internal terms from output

## What PetVault Does NOT Do

- Does not diagnose pets or replace veterinary judgment
- Does not promise insurance coverage or claim outcomes
- Does not recommend specific products or brands
- Does not provide legal advice
- Does not store data in the cloud (local-first architecture)
