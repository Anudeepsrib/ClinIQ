import Link from "next/link";

export default function TermsPage() {
  return <main className="mx-auto max-w-3xl p-8 prose">
    <h1>Terms of Use</h1>
    <p>ClinIQ is a policy-reference tool for authorized workforce users. It does not provide medical advice, diagnosis, treatment, or a substitute for current institutional policy and professional judgment.</p>
    <p>Users must protect credentials, follow organizational access rules, verify answers against authoritative sources, and upload only content they are authorized to use. Access may be suspended or content removed for security, privacy, copyright, or policy reasons.</p>
    <p>The deploying organization must replace this technical baseline with terms reviewed for its operator, users, jurisdiction, warranties, acceptable use, dispute process, and other business requirements.</p>
    <p><Link href="/">Return to ClinIQ</Link></p>
  </main>;
}
