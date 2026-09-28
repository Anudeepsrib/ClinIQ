import Link from "next/link";

export default function CopyrightPage() {
  return <main className="mx-auto max-w-3xl p-8 prose">
    <h1>Copyright and Takedown Policy</h1>
    <p>Only upload material you own or are authorized to use. Copyright complaints should identify the protected work, the material and its location, the complainant&apos;s contact information, a good-faith statement, an accuracy-and-authority statement under penalty of perjury, and a physical or electronic signature.</p>
    <p>Send notices to <strong>[INSERT DESIGNATED COPYRIGHT CONTACT]</strong>. The operator may restrict or remove reported material and terminate repeat infringers where appropriate.</p>
    <p>This page does not itself create DMCA safe-harbor protection. The operator must publish matching contact details and, if relying on the U.S. DMCA process, register and maintain a designated agent with the U.S. Copyright Office.</p>
    <p><Link href="/">Return to ClinIQ</Link></p>
  </main>;
}
