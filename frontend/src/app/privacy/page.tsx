import Link from "next/link";

export default function PrivacyPage() {
  return <main className="mx-auto max-w-3xl p-8 prose">
    <h1>Privacy Notice</h1>
    <p>ClinIQ is an administrator-provisioned hospital policy reference application. It processes account identifiers, roles, department access, queries, feedback, and documents submitted by authorized users.</p>
    <h2>Services used by the application</h2>
    <p>Depending on deployment configuration, data may be processed by Google Gemini, OpenAI, Azure AI Search, LangSmith, or a configured Chroma service. Local Ollama and vLLM options are also supported. External tracing and persistent chat history are disabled by default.</p>
    <p>Do not submit patient information unless your organization has approved the deployment, providers, contracts, access controls, retention, and incident-response process. Contact your deploying organization for access, correction, deletion, retention, and privacy questions.</p>
    <p>This repository does not establish the operator, jurisdiction, retention periods, lawful bases, international-transfer terms, or sale/sharing practices. The deploying organization must complete those disclosures before production use.</p>
    <p><Link href="/">Return to ClinIQ</Link></p>
  </main>;
}
