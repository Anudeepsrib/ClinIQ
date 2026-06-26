# ClinIQ Frontend

This is the Next.js interface for ClinIQ, a focused hospital policy RAG reference app.

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

## Verification

```bash
npm run lint
npm run build
```
