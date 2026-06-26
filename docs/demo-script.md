# ClinIQ Persona Demo Script

This demo uses synthetic policy examples and avoids live patient data. It is written for a portfolio walkthrough, evaluator review, or short product demo.

## Setup

1. Start the backend and frontend from the README quick start.
2. Use development-only users or seed local users through the admin API.
3. Keep `ENABLE_EXTERNAL_TRACING=false` unless tracing has been approved for the demo.
4. Use questions from `tests/evaluation/retrieval_eval_dataset.jsonl`.

## Persona 1: Nurse

Persona: Maya Patel, charge nurse.

Role mapping: `nurse`.

Departments: `nursing`, `emergency`, `general`.

Goal: Find isolation-room hand hygiene and escalation policy quickly during a shift.

Demo steps:

1. Sign in as the nurse persona.
2. Confirm the department filter shows nursing-accessible departments, not administration-only access.
3. Ask: "What hand hygiene steps are required before entering an isolation room?"
4. Expected response: cites the nursing infection-control policy, mentions "foam in/foam out", PPE availability, isolation cart check, and nurse manager escalation for missing supplies.
5. Ask an out-of-scope administration question: "Who approves emergency policy exceptions?"
6. Expected response: access is denied or the answer is absent because the nurse does not have administration scope.

Talk track:

"ClinIQ is not trying to run the nurse's workflow. It is a policy reference surface. The value is fast, cited policy lookup with the same department boundaries the hospital would expect."

## Persona 2: Admin

Persona: Jordan Lee, hospital operations administrator.

Role mapping: `admin`.

Departments: all configured departments.

Goal: Review policy lifecycle rules and maintain access.

Demo steps:

1. Sign in as the admin persona.
2. Open the admin panel.
3. Show department stats and user management.
4. Ask: "Who can approve emergency policy changes and when must they be reviewed?"
5. Expected response: cites the administration policy lifecycle document, identifies interim approval by the department director and policy office, and includes the five-business-day review requirement.
6. Show that admin can query nursing, administration, compliance-style, and radiology policy examples.

Talk track:

"Admin access is intentionally broader, but the app still frames answers as policy reference, not legal or compliance certification."

## Persona 3: Compliance Reviewer

Persona: Elena Chen, compliance reviewer.

Role mapping: `researcher`.

Departments: `administration`, `general`.

Goal: Verify minimum necessary disclosure behavior and PHI masking examples.

Demo steps:

1. Sign in as the compliance reviewer persona.
2. Ask: "What is the minimum necessary rule for sharing patient details in an audit packet?"
3. Expected response: cites the synthetic PHI minimum necessary policy and says direct identifiers should be excluded unless the approved audit request requires them.
4. Ask: "Can I include John Doe, 555-123-4567, and jane.patient@example.com in a review note?"
5. Expected behavior: query text is anonymized before graph invocation; PHI-like values are masked with typed placeholders.
6. Point to `tests/evaluation/phi_masking_examples.json` and the passing PHI masking tests.

Talk track:

"This is why the repo says HIPAA-aware patterns, not HIPAA-compliant software. The demo proves masking and access checks in a bounded path, while production compliance remains an organizational process."

## Close

End with the ClinIQ/CareOS distinction:

"ClinIQ is a narrow RAG reference app for hospital policy. CareOS can be the broader platform story. ClinIQ's strength is that its claims are specific enough to test."
