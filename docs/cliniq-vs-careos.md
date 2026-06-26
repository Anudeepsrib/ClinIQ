# ClinIQ Vs CareOS

ClinIQ and CareOS should be positioned as different product stories.

ClinIQ is the focused hospital policy RAG reference app in this repository. It demonstrates how authenticated staff can retrieve institution-specific policy, SOP, coverage, and administrative guidance from department-scoped documents with citations, PHI masking, RBAC checks, and evaluation fixtures.

CareOS should remain the broader healthcare operations or care platform concept. If CareOS includes patient journeys, task orchestration, care team workflows, operational dashboards, EHR-adjacent integrations, or longitudinal care coordination, those belong outside ClinIQ's primary promise.

## Comparison

| Dimension | ClinIQ | CareOS |
| --- | --- | --- |
| Product category | Hospital policy RAG reference app | Healthcare operations or care platform |
| Main user action | Ask a policy question and inspect cited source context | Coordinate workflows, patients, tasks, care programs, or operations |
| Data boundary | Ingested policy documents and department-scoped indexes | Potentially many operational, financial, clinical, and patient-context systems |
| Personas | Nurse, administrator, compliance reviewer, authenticated staff | Care coordinators, clinicians, patients, operations leaders, administrators |
| Core quality bar | Retrieval accuracy, groundedness, citation coverage, RBAC, PHI masking | End-to-end workflow completion, operational KPIs, integration reliability, clinical safety |
| Demo focus | "Can the app answer this policy question from approved documents?" | "Can the platform coordinate and operate the broader care journey?" |
| Compliance language | HIPAA-aware control patterns, not compliance certification | Compliance posture must be separately defined, implemented, and audited |

## Product Boundaries

ClinIQ should say:

- "Hospital policy RAG reference app."
- "Role-scoped retrieval over institutional documents."
- "Source-backed answers with conservative fallback behavior."
- "Synthetic evaluation pack for retrieval, groundedness, RBAC, and PHI masking."

ClinIQ should not say without qualification:

- "Complete healthcare platform."
- "Care operating system."
- "HIPAA-compliant out of the box."
- "Certified clinical decision support."
- "Guaranteed compliant or clinically safe."

## Portfolio Narrative

Use ClinIQ to show depth in one sensitive RAG domain: policy retrieval. Use CareOS, if discussed, to show a broader platform vision. The two can complement each other, but ClinIQ is strongest when it stays narrow, testable, and evidence-backed.
