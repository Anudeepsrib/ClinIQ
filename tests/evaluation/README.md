# ClinIQ Evaluation Artifacts

This folder contains deterministic, synthetic assets for evaluating ClinIQ as a hospital policy RAG reference app.

The artifacts do not contain real patient information and should not be treated as production policies.

## Artifacts

- `policy_corpus/` - synthetic policy documents and a manifest.
- `retrieval_eval_dataset.jsonl` - persona-specific retrieval questions with expected source documents and terms.
- `rbac_test_matrix.json` - nurse, admin, and compliance reviewer access expectations.
- `phi_masking_examples.json` - PHI-like strings and expected masking behavior.
- `evaluate.py` - optional RAGAS-style evaluator that can load the JSONL dataset.
- `generate_test_set.py` - optional generator for larger RAGAS datasets.

## What The Pack Proves

The pack is meant to verify that ClinIQ's product claims stay narrow and testable:

- Retrieval should find the right policy document.
- Answers should be grounded in retrieved policy context.
- RBAC should respect role and department boundaries.
- PHI-like values should be masked before graph/model paths where feasible.
- Demo personas should be nurse, admin, and compliance reviewer.

## What It Does Not Prove

The pack does not prove clinical safety, legal compliance, HIPAA compliance, production readiness, or deployment security. Those require organization-specific review and controls outside this repository.

## Running Tests

From the repo root:

```bash
python -m pytest tests/test_policy_eval_artifacts.py tests/test_rag_safety.py tests/test_rbac_matrix.py tests/test_phi_masking_examples.py
```

For the full backend suite:

```bash
python -m pytest
```
