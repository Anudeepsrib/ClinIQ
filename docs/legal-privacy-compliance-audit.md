# Legal, Privacy, and Compliance Technical Audit

This report is technical compliance hardening, not legal advice. It reflects the repository state reviewed on 2026-09-28; deployment practices and provider settings were not available.

### 1. COPPA and collection of data from children

**Found**
- There is no public signup, OAuth, magic-link, newsletter, waitlist, contact, public profile, or avatar flow. `POST /api/v1/auth/register` in `app/api/routes.py` requires `AdminUser`; the login describes assigned/admin-provisioned staff access.
- The application is an internal hospital policy reference tool for workforce roles. The repository contains no evidence that it is directed to children or knowingly collects data from children under 13.
- Authenticated users can submit queries, feedback, and documents; these are not public child-directed collection points.

**Changed**
- Verified the Next.js login describes administrator-provisioned access.
- Verified the registration dependency is server-side, so a direct API request cannot bypass administrator authorization.

**You still need to**
- Confirm with counsel and product owners that production use is workforce-only and not directed to children. If minors will use it, decide whether to prohibit under-13 use or implement a counsel-approved age/parental-consent flow before collecting data.

### 2. Remote fonts and third-party resources

**Found**
- `frontend/src/app/layout.tsx` used `next/font/google`, which fetches Google font assets at build time and bundles them rather than causing a browser request.
- No other browser-loaded remote fonts, scripts, CSS, pixels, SDKs, or widgets were found.

**Changed**
- Removed `next/font/google`; the Next.js client now uses system font stacks.
- Removed the redundant FastAPI-served static client and its remote browser dependencies. The backend root now returns a small API descriptor.

**You still need to**
- None.

### 3. Analytics, session replay, heatmaps, and behavioral tracking

**Found**
- No PostHog, Hotjar, FullStory, LogRocket, Clarity, Mixpanel, Amplitude, Google Analytics, Meta Pixel, Sentry Replay, Heap, Segment, Mouseflow, heatmap, keystroke, or client event SDK was found.
- LangSmith is server-side observability, not browser analytics. It is disabled by default (`ENABLE_EXTERNAL_TRACING=false`), initializes lazily in `app/observability/tracing.py`, hashes usernames for metadata, and receives PII-masked questions/feedback through `app/api/routes.py`.

**Changed**
- No new consent banner was added because no non-essential browser tracker exists. Existing server-side external tracing remains an explicit deployment configuration rather than a user-consent mechanism.

**You still need to**
- Decide with privacy/legal and hospital governance whether LangSmith processing is permitted, on what basis, and under what contract/BAA, retention, access, and data-residency controls before enabling it.

### 4. Marketing email and CAN-SPAM controls

**Found**
- No email provider, SMTP client, template, newsletter, lifecycle campaign, or outbound email path exists in the repository.

**Changed**
- None; unsubscribe and suppression infrastructure would be unused speculative code.

**You still need to**
- None unless email functionality is added; audit and classify it before launch.

### 5. Subscriptions and automatic renewal disclosures

**Found**
- No pricing, checkout, payment processor, paywall, trial, subscription API, recurring billing, upgrade, renewal, or cancellation flow exists.

**Changed**
- None.

**You still need to**
- None unless paid or recurring plans are added; review the complete purchase and cancellation flow before launch.

### 6. User uploads, copyright complaints, and DMCA process

**Found**
- Authenticated users upload documents/media at `POST /api/v1/ingest` and `/ingest/jobs`; `frontend/src/components/layout/DocumentLibrary.tsx` exposes the UI. Uploads are department-scoped and not publicly published. Admins can soft-delete documents through `DELETE /api/v1/documents/{department}/{filename}`.
- No copyright policy, complaint channel, designated agent information, or repeat-infringer language previously existed.

**Changed**
- Added a public copyright/takedown page to the Next.js application, linked before login and in the authenticated footer. It includes authorized-use, notice, removal, and repeat-infringer language plus an explicit contact placeholder and safe-harbor disclaimer.
- Existing admin deletion is the technical removal hook. Upload authentication, RBAC, filename, MIME/extension, and size controls remain in `app/api/routes.py` and `app/security/uploads.py`.

**You still need to**
- Choose and publish the operator's copyright contact at `[INSERT DESIGNATED COPYRIGHT CONTACT]` in `frontend/src/app/copyright/page.tsx`.
- If relying on U.S. DMCA safe harbor, register a designated agent using the U.S. Copyright Office's current online process, pay the then-current fee, publish matching details, renew within the Office's required cycle, and update both records whenever details change. Counsel should confirm applicability and the operational notice/counter-notice/repeat-infringer process.

### 7. Privacy policy and Terms of Service

**Found**
- No public Privacy Policy or Terms existed. Code-derived recipients/processors are Google Gemini, OpenAI, Azure AI Search, LangSmith, and optionally remote Chroma; local Ollama/vLLM and local SQLite/Chroma are alternatives. Hosting is configurable (Render, Docker, or Kubernetes) and cannot be identified as the production operator from source.

**Changed**
- Added unauthenticated Privacy, Terms, and Copyright pages to the Next.js client and linked them on login and in the authenticated footer.
- The privacy baseline names only code-supported processing and expressly leaves operator, rights contact, retention, lawful basis, transfers, and sale/sharing facts unresolved.
- Removed the redundant static client; Next.js statically generates all three policy routes.

**You still need to**
- Have counsel replace the technical baselines with operator- and jurisdiction-specific policies; fill in controller/operator/contact, data categories, purposes, lawful bases, retention, rights, transfers, sale/sharing, security, effective date, change process, and complaint/escalation details.
- Confirm which optional providers and hosting path production actually uses and execute required vendor agreements/BAAs/DPAs.

### 8. Cookies and consent

**Found**
- No cookies, advertising IDs, analytics storage, or consent state exists. The Next.js client stored only the authentication JWT in `localStorage`. This is a strictly necessary authentication value, not a tracking identifier.

**Changed**
- Moved the JWT to `sessionStorage` in `frontend/src/store/chatStore.ts`, reducing persistence after the browser session. Logout removes it. No cookie banner was added because no non-essential browser storage exists.

**You still need to**
- Decide whether production should use a server-set `HttpOnly`, `Secure`, `SameSite` session cookie instead of browser-readable bearer storage; that change requires coordinated API authentication and CSRF design.

### 9. Secrets, credentials, and personal data exposure

**Found**
- Repository-wide signature searches found placeholders but no current high-confidence private key/token. `.env*` files are ignored except examples; examples contain blank/placeholding server-side variables. Helm supports an external secret, and production configuration rejects weak JWT secrets.
- Git history contains commits touching `.env`; current deletion cannot establish that prior values were non-secret. Logging has a root redaction filter and route errors use `redact_text`, but some operational logs contain usernames, session IDs, filenames, provider names, and departments.
- `NEXT_PUBLIC_API_URL` is intentionally public configuration; no provider secret is placed in a browser environment variable.

**Changed**
- Removed third-party browser scripts, narrowed CSP sources, and reduced bearer-token persistence. Existing `.gitignore`, placeholder configuration, production validation, redaction, and disabled-by-default tracing were verified.

**You still need to**
- Treat any credentials ever stored in historical `.env` commits as exposed: identify and rotate them, review Git/provider secret-scanning results, and decide with repository owners whether history rewriting is appropriate.
- Define approved production log fields, access, retention, and deletion; decide whether usernames, filenames, session IDs, and department metadata require additional pseudonymization.

| Area | Status | Files Changed | Technical Fix | Manual Action Required |
|---|---|---|---|---|
| COPPA | Requires legal review | `frontend/src/components/auth/LoginScreen.tsx` | Verified server-side admin provisioning | Confirm workforce-only audience |
| Remote resources | Fixed | `frontend/src/app/layout.tsx`, `frontend/src/app/globals.css`, `main.py` | Removed remote fonts and the redundant static client | No |
| Tracking | Requires legal review | None | Verified no browser tracking; server tracing stays off by default | Approve contracts/basis before LangSmith enablement |
| Marketing email | No issue found | None | Not applicable | No |
| Subscriptions | No issue found | None | Not applicable | No |
| Copyright/DMCA | Partially fixed | Copyright pages | Public policy and existing admin removal hook | Insert contact; register/maintain agent if applicable |
| Privacy/Terms | Partially fixed | Policy pages, login/footer links, tests | Public technical baselines | Counsel review and deployment facts |
| Cookies/storage | Partially fixed | `frontend/src/store/chatStore.ts` | Session-scoped necessary auth storage | Decide HttpOnly-cookie architecture |
| Secrets/exposure | Requires manual action | `main.py` and browser files | CSP/resource/token-persistence hardening; existing redaction verified | Rotate historical secrets; review logs/history |

### Third-Party Data Flow Inventory

| Provider | Purpose | Data Sent | Trigger / Timing | Consent Dependency | Files |
|---|---|---|---|---|---|
| Google Gemini | LLM and multimodal embeddings | PII-masked query text; uploaded/chunked document or media content for embeddings | Authenticated query/ingest when configured | Organizational approval/legal basis; no browser consent SDK | `app/chat/llm_provider.py`, `app/retrieval/gemini_embeddings.py` |
| OpenAI | Optional LLM/embeddings | PII-masked query text; text chunks | Authenticated query/ingest when selected | Organizational approval/legal basis | same provider files |
| Azure AI Search | Search/vector storage | document chunks, vectors, filenames, department metadata | Authenticated ingest/search when enabled | Organizational approval/contract | `app/retrieval/azure_search_store.py` |
| LangSmith | Server observability/feedback | masked trace content, hashed user ID, role, departments, feedback | Only when explicitly enabled | Governance approval; deployment must determine basis | `app/observability/tracing.py`, `app/api/routes.py` |
| Chroma service | Optional chat history/vector store | masked chat content, user ID, session ID, department | Only when chat history and remote host are configured | Organizational approval/retention policy | `app/chat/chat_history_store.py` |
| Render/Kubernetes operator | Hosting (optional) | application traffic and configured persistent data/logs | Deployment-dependent | Operator must disclose actual host | `render.yaml`, `deploy/helm/cliniq/` |

### Remaining Manual Actions

1. Confirm workforce-only audience and COPPA posture with counsel/product owners.
2. Approve each enabled AI/search/tracing/storage/hosting provider, contracts/BAAs/DPAs, permitted data, retention, access, residency, and incident response.
3. Replace the policy baselines with counsel-approved operator/jurisdiction facts and contact details.
4. Insert the designated copyright contact in both copyright pages; if applicable, register, publish, maintain, and timely renew the U.S. Copyright Office designated agent and operate notice/counter-notice/repeat-infringer procedures.
5. Decide whether to migrate browser bearer authentication to `HttpOnly`, `Secure`, `SameSite` cookies with CSRF protection.
6. Rotate any secrets ever committed in `.env`, review secret-scanning results/history, and decide whether to rewrite repository history.
7. Approve production logging fields and retention, including usernames, filenames, session IDs, and departments.

### Verification Results

- Tests: new FastAPI policy-page/no-remote-dependency tests were added, but `pytest` could not run because neither available Python runtime has the repository test dependencies. Python bytecode compilation passed for `app`, `main.py`, and `tests`.
- Build: Next.js production build passed and statically generated `/privacy`, `/terms`, and `/copyright`.
- Lint/type-check: Next.js TypeScript checking passed during build. ESLint initially found three internal-link errors; these were corrected with `next/link` and lint was rerun.
- Searches: repository-wide remote-resource, analytics, email, subscription/payment, browser storage, credential-signature, log, upload, registration, policy, and provider searches; Git path history for `.env`.
- Unresolved: legal/business/deployment facts in Remaining Manual Actions. No claim of legal compliance or DMCA safe harbor is made.
