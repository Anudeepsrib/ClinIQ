# ClinIQ Security and Readiness Audit

## Summary

This pass focused on P0/P1 risks that could leak secrets/PHI, prevent local startup, or create unsafe healthcare AI behavior. The repo now starts locally without `.env`, external tracing is disabled by default, Azure/Chroma/OpenAI integrations no longer fail at import time, CORS is explicit, JWT settings are validated, uploads are guarded, generated/local runtime artifacts are removed from the working tree, and README language now says HIPAA-aware controls rather than HIPAA compliance.

## P0 Findings

- Public `.env` contained set secret-like values. Fixed by deleting `.env` from the working tree, expanding `.gitignore`, and replacing `.env.example` with placeholders only. Manual action: rotate anything that was ever committed and purge Git history if this repository was public.
- Backend startup depended on Azure AI Search index creation with empty endpoint/config. Fixed by making Azure Search disabled/lazy unless explicitly configured.
- Default admin seeding used `admin/admin123`. Fixed by disabling demo admin seeding by default and requiring an explicit strong `DEMO_ADMIN_PASSWORD` for local demos.
- External LangSmith tracing defaulted on, risking PHI egress. Fixed with `ENABLE_EXTERNAL_TRACING=false` default and runtime environment enforcement.
- Query and Copilot paths could send raw PHI-like input to model/tracing paths. Fixed by anonymizing query/context text before graph/model invocation and chat history persistence.
- Hallucination verification could fail open or return unverified content. Fixed fail-closed behavior when verification cannot run or no supporting documents exist.

## P1 Findings

- Wildcard CORS with credentials was enabled. Fixed with env-driven localhost defaults and production rejection of wildcard origins with credentials.
- JWT config was weakly typed and accepted production placeholders. Fixed with typed settings, allowed algorithms, expiry bounds, and production validation.
- Upload endpoint lacked size/MIME/filename/path traversal validation. Fixed with upload guards and safe filename sanitization.
- Static UI rendered model markdown without sanitization. Fixed with DOMPurify sanitization and additional HTML escaping.
- Frontend build failed on `PushToTalk` hook typing/dependencies. Fixed.
- Frontend dependency audit found Next/PostCSS/transitive vulnerabilities. Fixed with Next 16.2.6, lockfile refresh, and a PostCSS override; `npm audit` now reports 0 vulnerabilities.
- Python dependency audit found vulnerable `pypdf`, `langchain-openai`, and `ragas`/transitives. Fixed by bumping safe ranges and removing vulnerable optional RAGAS from runtime requirements.
- Error handlers/routes leaked exception strings. Fixed with generic 500 responses and redacted logging.
- Sensitive endpoints were missing focused limits. Added rate limits to login, register, feedback, ingest, query, and Copilot quick help.
- Helm chart created placeholder secrets in-template. Fixed default to external Kubernetes Secret and documented secret-manager usage.

## P2 Findings

- Tracked generated artifacts existed: bytecode, local SQLite DBs, Chroma DB, and temp script. Removed from working tree and expanded ignore rules.
- Dockerfile used incomplete wheel strategy and broad permissions. Fixed deterministic wheel/install flow and non-root runtime ownership.
- Readiness check imported a nonexistent Chroma wrapper. Fixed `/ready` to report optional service configuration safely.
- CI was missing. Added GitHub Actions for backend syntax/lint/tests/audit and frontend install/lint/build/audit.
- Security documentation was missing. Added `SECURITY.md` and `docs/security-hardening.md`.
- Tests did not cover key security controls. Added tests for auth required, wrong department access, PHI masking before graph invocation, upload path traversal rejection, prompt-injection instructions, no-context fallback, and fail-closed hallucination behavior.

## P3 Findings

- README and frontend README/setup text were still scaffold/demo-oriented and overclaimed compliance. Main README setup and disclaimers were rewritten.
- Next.js warned about workspace root inference. Fixed by setting `turbopack.root`.
- Optional evaluation scripts imported vulnerable/uninstalled RAGAS eagerly. Updated to fail with an explicit optional-dependency message.

## Files Changed

- Security/config/backend: `main.py`, `app/core/config.py`, `app/core/logging.py`, `app/api/routes.py`, `app/api/copilot.py`, `app/security/auth.py`, `app/security/rbac.py`, `app/security/pii.py`, `app/security/uploads.py`, `app/security/vault.py`.
- RAG/retrieval/ingestion: `app/retrieval/azure_search_store.py`, `app/retrieval/nodes/*.py`, `app/ingestion/upsert_pipeline.py`, `app/ingestion/document_registry.py`.
- Frontend/static UI: `frontend/package.json`, `frontend/package-lock.json`, `frontend/next.config.ts`, `frontend/src/store/chatStore.ts`, `frontend/src/components/input/*.tsx`, `frontend/.env.example`, `static/index.html`, `static/js/script.js`.
- Deployment/CI/docs: `Dockerfile`, `.dockerignore`, `aks/helm/cliniq/**`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `README.md`, `SECURITY.md`, `docs/security-hardening.md`, `AUDIT_REPORT.md`.
- Dependencies/tests: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `tests/test_security_controls.py`, `tests/test_rag_safety.py`, `tests/evaluation/*.py`.
- Removed from working tree/Git tracking intent: `.env`, `__pycache__/`, tracked `*.pyc`, `data/users.db`, `data/document_registry.db`, `data/vector_db/chroma.sqlite3`, `tmp/verify_gemma.py`.

## Commands Run

- `python -m compileall .` - passed.
- `python -m compileall app main.py tests scripts` - passed.
- `pytest -q` - passed: 14 passed, 30 warnings.
- `pip check` - failed in the current global Python environment due unrelated/conflicting globally installed packages (`camelot-py`, `langchain-chroma`, `llama-index`, `semantic-kernel`, `mcp`, `unstructured-client`). The repository requirements were cleaned, but this shared interpreter is not a clean project virtualenv.
- `pip-audit -r requirements.txt` - passed: no known vulnerabilities found.
- `cd frontend && npm install` - passed.
- `cd frontend && npm run lint` - passed.
- `cd frontend && npm run build` - passed.
- `cd frontend && npm audit` - passed: found 0 vulnerabilities.
- `python -m uvicorn main:app --host 127.0.0.1 --port 8000` with `/health` probe - passed; returned `external_tracing:false`.
- `docker build .` - not completed because Docker Desktop/Linux engine was not running on this machine.

## Tests Added

- Unauthorized query returns 401.
- Department-scoped query rejects unauthorized department access.
- Upload filename path traversal is rejected.
- PHI-like query content is masked before graph invocation.
- Generation prompt treats retrieved documents as untrusted.
- No retrieved context returns a safe fallback.
- Hallucination verification fails closed when it cannot verify an answer.

## Remaining Risks and Manual Actions

- Rotate any API keys/JWT secrets that were ever present in committed `.env`, then run GitHub secret scanning and history cleanup.
- Run `pip check` inside a fresh virtualenv created from `requirements.txt`; the current global interpreter has unrelated package conflicts.
- Start Docker Desktop or another Docker daemon and rerun `docker build .`.
- Do not use real PHI until formal compliance, privacy, legal, security, and clinical safety reviews are complete.
- Wire production identity/user provisioning; demo admin seeding is intentionally disabled by default.
- Configure Azure Search, external tracing, and chat history only with approved secrets, BAAs/contracts, retention policies, and PHI-safe operational controls.
- Re-enable optional RAGAS evaluation only after using a patched non-vulnerable release.
