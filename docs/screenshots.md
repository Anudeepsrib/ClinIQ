# Screenshots

The committed screenshots under `frontend/public/assets` should support the focused policy RAG story. They are demo aids, not evidence of production readiness.

## 01 Initial Interface

Path: `frontend/public/assets/01_Initial_Interface.png`

Use this to introduce ClinIQ as a hospital policy reference app. The recommended talk track is: authenticated staff ask policy questions, select department scope, and inspect cited answers.

## 02 Clarification Requested

Path: `frontend/public/assets/02_Clarification_Requested.png`

Use this to show conservative behavior. When a question is too vague, ClinIQ should ask for a more specific policy, department, procedure, or administrative rule instead of guessing.

## 03 RBAC Inline Masking

Path: `frontend/public/assets/03_RBAC_Inline_Masking.png`

Use this to show the trust boundary. The app demonstrates department-scoped access and PHI-like value masking before sensitive text reaches graph/model paths where feasible.

## 04 Standard Retrieval

Path: `frontend/public/assets/04_Standard_Retrieval.png`

Use this to show the happy path: a specific policy question returns cited source context and a bounded answer.

## Refresh Guidance

When screenshots are refreshed, capture these states:

- Nurse query against nursing policy.
- Admin query against administration policy lifecycle rules.
- Compliance reviewer query with PHI-like values masked.
- Clarification prompt for an ambiguous policy question.

Avoid screenshots that imply ClinIQ is a full care platform, EHR, diagnosis tool, or compliance-certified product.
