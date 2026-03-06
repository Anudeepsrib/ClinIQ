import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const interDisplay = Inter({
  variable: "--font-inter-display",
  subsets: ["latin"],
  display: "swap",
  weight: ["600", "700", "800"],
});

const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
  display: "swap",
});

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
    <html lang="en">
      <body
        className={`${inter.variable} ${interDisplay.variable} ${robotoMono.variable} antialiased bg-background text-foreground min-h-screen flex flex-col`}
      >
        {/* Global Header */}
        <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-white shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-6 h-6 bg-red-600 rotate-45" /> {/* Placeholder Sharp Logo */}
            <h1 className="font-display font-bold text-navy-900 tracking-tight">
              City General Hospital
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm font-mono text-slate-500">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-none bg-cyan-500 animate-pulse" />
              Secure Session
            </span>
            <span className="px-2 py-1 bg-navy-900 text-white font-bold text-xs uppercase tracking-wider">
              Dr. House (Cardiology)
            </span>
          </div>
        </header>

        {/* Main 70/30 Layout Structure */}
        <main className="flex-1 flex overflow-hidden">
          {children}
        </main>

        <footer className="h-8 border-t border-border flex items-center justify-center bg-slate-50 text-[10px] text-slate-400 font-mono uppercase tracking-widest shrink-0">
          AI-assisted retrieval. Do not replace clinical judgment or direct patient assessment.
        </footer>
      </body>
    </html>
  );
}
