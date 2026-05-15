# Security Hardening Notes

## CORS

CORS is driven by `CORS_ALLOWED_ORIGINS`. Development defaults are localhost-only. Production rejects wildcard origins when credentials are enabled.

## JWT Secret

`JWT_SECRET_KEY` must be generated per deployment. Production startup rejects weak, placeholder, or short JWT secrets. Demo admin seeding is disabled by default and must never be enabled in production.

## PHI Logging

Application logging uses a redaction filter for common secret and PHI-like patterns. Query text is anonymized before graph invocation, chat history storage, and external model/tracing paths where feasible.

## Tracing

`ENABLE_EXTERNAL_TRACING=false` by default. When disabled, LangChain tracing environment variables are forced off so prompts and retrieved context are not sent to LangSmith by accident.

## Upload Safety

Document ingestion validates file size, extension, MIME type, and filename safety. Filenames with path separators or traversal are rejected. Parsed documents are handled in memory; runtime DBs, vector stores, and temp files are ignored by Git.

## RAG Prompt Injection

The generation prompt treats retrieved documents as untrusted content and instructs the model not to follow document-embedded instructions. The hallucination checker fails closed if verification cannot run. The assistant should cite sources and avoid diagnosis or treatment advice.

## Remaining Production Work

Before real PHI use, add organization-approved identity management, audit log retention, encrypted persistent storage, KMS-backed secrets, container and IaC scanning, monitoring, backup/restore, legal review, and clinical safety validation.
