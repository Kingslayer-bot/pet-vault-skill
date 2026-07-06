# PetVault AI PRD V1.1 Alignment Notes

## Product Shape

PetVault AI V1.1 is defined as:

- C-side pet medical report explanation
- B-side veterinary workflow support
- local-first material vault and PDF report engine

## Runnable Scope In This Repository

This repository keeps the main executable scope centered on the engine and the C-side report workflow:

- report upload and classification
- medical summary
- bill explanation
- health timeline
- claim material check
- PDF-ready report output
- local SQLite-backed PetVault archive

## Reserved B-Side Demo Scope

The following structures are included for forward compatibility, but are not implemented as a full hospital platform in this version:

- SOAP draft schema and prompt
- clinic client summary prompt and template
- agent role definitions for clinic-side workflows

## Safety Boundaries

- Do not replace veterinary diagnosis.
- Do not make treatment decisions.
- Do not judge whether a clinic overcharged.
- Do not promise insurance reimbursement.
- Mark uncertainty clearly.
- Require human review for B-side drafts.
