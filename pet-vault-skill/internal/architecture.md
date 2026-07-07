# PetVault Agent Architecture (Internal)

This document defines internal agent roles. Do not expose to end users.

## Agent Roles

- Orchestrator Agent: understand the request, choose the report type, run material organization first, then coordinate analysis, rendering, QA, and writes.
- Material Organizer Agent: classify, rename, extract, clean, index, and store materials.
- Pet Profile Inference Agent: infer pet identity and scenario only for internal report selection; never label the caregiver.
- Bill Analysis Agent: categorize bill items and explain possible relationship to care actions without judging clinic pricing.
- Appointment Timeline Agent: merge appointments, visits, tests, prescriptions, bills, and follow-ups by date.
- Insurance Check Agent: list existing and missing claim materials and risk points without promising results.
- Chronic Care Review Agent: summarize recurring visits, labs, medication, prescription food, care products, and monthly spending.
- Family Summary Agent: produce restrained summaries for family decisions.
- Clinic SOAP Draft Agent: prepare a structured SOAP-style draft from clinician notes or audio transcripts, but never treat it as final without review.
- Clinic Client Summary Agent: prepare a client-facing explanation draft for the clinic side.
- Report Composer Agent: combine outputs into `report.md`.
- LaTeX Renderer Agent: convert Markdown to LaTeX, compile, and log build status.
- Quality Inspector Agent: verify sources, caution boundaries, forbidden terms, files, and readable output.
