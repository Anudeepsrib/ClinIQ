# ClinIQ Architecture Notes

ClinIQ is designed as a narrow hospital policy RAG reference app. The architecture is intentionally organized around evidence retrieval, access boundaries, PHI masking, conservative generation, and testable evaluation artifacts.

## Product Boundary

ClinIQ answers questions against hospital policy-style documents. It is not an EHR, care coordination system, patient engagement platform, or certified clinical decision support system. Its controls are examples that require organization-specific review before real PHI or live hospital use.

## Request Flow

1. A staff user authenticates with JWT-backed auth.
2. RBAC resolves the user's role and department scope.
3. Incoming question text is anonymized before graph invocation.
4. The LangGraph pipeline checks ambiguity, retrieves department-scoped documents, grades relevance, generates a cited answer, and checks groundedness.
5. If retrieval or model configuration is unavailable, the app returns a conservative fallback rather than inventing an answer.
6. Optional chat history and external tracing stay disabled by default to reduce PHI egress risk.

## Retrieval Boundary

The intended retrieval store is Azure AI Search with one index per department. This creates a simple implementation boundary:

- Nurse personas search nursing, emergency, and general policy documents.
- Admin personas can search all configured departments.
- Compliance reviewer personas map to reviewer-style access over administration and general policy documents unless a deployment adds a dedicated compliance department.

The committed synthetic corpus under `tests/evaluation/policy_corpus` is not runtime hospital data. It exists so reviewers can inspect expected retrieval and grounding behavior without PHI.

## Grounding Boundary

Generation is expected to use retrieved context only. The system prompt requires:

- Source citations with `[Ref X]` notation.
- No outside knowledge.
- No diagnosis, treatment, or patient-specific clinical decisioning.
- Explicit fallback when the answer is absent from accessible policy documents.

The hallucination check is a second pass. It fails closed when no answer or no supporting documents are available.

## Security Boundary

Implemented controls include:

- JWT auth with role hierarchy.
- Department-scoped query and document access.
- PHI-like masking before graph/model paths where feasible.
- Upload filename and metadata validation.
- Conservative production settings validation.
- External tracing disabled by default.

These controls are not a compliance certification. Real deployments still need identity integration, audit retention, encryption and key management, monitoring, incident response, legal review, clinical safety review, and data governance.

## Evaluation Boundary

The evaluation pack provides lightweight, deterministic review assets:

- Synthetic policy corpus.
- Retrieval dataset with expected documents and answer terms.
- Groundedness tests that enforce policy-only behavior.
- RBAC matrix for nurse, admin, and compliance reviewer personas.
- PHI masking examples.

These artifacts are meant to make the app inspectable. They do not replace a production validation plan.

## CareOS Boundary

CareOS should be described as a broader healthcare operating or care workflow platform if it appears in the portfolio. ClinIQ is the smaller evidence retrieval reference. Keeping this separation makes ClinIQ more credible because its claims are concrete, testable, and tied to the repo.
