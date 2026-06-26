---
doc_id: CMP-PHI-003
title: Minimum Necessary Disclosure For Audit Packets
department: administration
synthetic: true
---

# Minimum Necessary Disclosure For Audit Packets

This synthetic policy is for ClinIQ evaluation only.

## Minimum Necessary Rule

Audit packets must follow the minimum necessary standard. Include policy references, dates, department, role, and deidentified event descriptions when those fields answer the audit question.

Direct identifiers must be excluded unless the approved audit request specifically requires them. Direct identifiers include patient name, phone number, email address, SSN, MRN, account number, and full street address.

Draft audit notes should use typed placeholders or deidentified tokens instead of patient identifiers. Reviewers should not paste raw PHI into model prompts or external tracing tools.

## External Review

External tracing must remain disabled unless PHI egress has been approved by security, privacy, and legal reviewers. Approved exports must document purpose, retention, reviewer, and deletion plan.
