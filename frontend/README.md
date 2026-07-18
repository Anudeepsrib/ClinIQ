# ClinIQ Frontend

This is the Next.js interface for ClinIQ, a focused hospital policy RAG reference app.

The interface signs in against the FastAPI JWT endpoints and provides policy search, Policy Quick Help, document uploads and version history, optional persistent chat threads, and tracing-backed clinician feedback.

The UI should reinforce the same product boundary as the backend README:

- Ask policy, SOP, coverage, prior authorization, and administrative reference questions.
- Show department scope and source-backed answers.
- Avoid implying that ClinIQ is a care operating system, EHR, clinical decision support product, or compliance-certified platform.

## Development

```bash
npm install
cp .env.example .env.local
npm run dev
```

Windows PowerShell:

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

Use a backend account. For local development, configure `ALLOW_DEMO_ADMIN=true` and a strong `DEMO_ADMIN_PASSWORD` in the root `.env` before starting the backend.

## Verification

```bash
npm run lint
npm run build
```
