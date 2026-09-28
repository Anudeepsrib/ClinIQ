import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clinical Assistant | Enterprise RAG",
  description: "Secure, Role-Based Medical Knowledge Retrieval",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className="antialiased bg-background text-foreground min-h-screen flex flex-col font-sans"
      >
        {children}
      </body>
    </html>
  );
}
