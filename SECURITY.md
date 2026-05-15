# Security Policy

## Reporting Vulnerabilities

Please report suspected vulnerabilities privately to the repository owner before opening a public issue. Include the affected commit, reproduction steps, impact, and any suggested mitigation.

## Secret Handling

Do not commit `.env`, API keys, JWT secrets, local databases, vector stores, logs, or trace exports. Use `.env.example` for placeholders only. If a secret was ever committed, rotate it in the upstream provider and treat the old value as compromised.

## PHI Warning

This repository is a local demo/reference implementation. Do not ingest real PHI, patient records, clinical notes, images, or identifiers unless your organization has completed a formal compliance, privacy, and security review.

## Compliance Scope

ClinIQ includes HIPAA-aware controls such as RBAC, department scoping, PHI masking, safer logging, disabled-by-default external tracing, and upload validation. These controls do not make the project certified HIPAA-compliant production software.

## Recommended Production Controls

- Store secrets in a managed vault or Kubernetes Secret backed by an approved secret manager.
- Enforce HTTPS, explicit CORS origins, strong JWT secrets, short token lifetimes, and audited user provisioning.
- Disable external tracing unless a business associate agreement and PHI-safe trace policy are in place.
- Run dependency, container, IaC, and secret scans in CI.
- Perform threat modeling, clinical safety review, and incident-response planning before using real clinical workflows.
