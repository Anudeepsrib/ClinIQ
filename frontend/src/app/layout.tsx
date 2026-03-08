import type { Metadata } from "next";
import "./globals.css";

import { Source_Sans_3, Lexend, Roboto_Mono } from "next/font/google";

const sourceSans = Source_Sans_3({
  variable: "--font-source-sans",
  subsets: ["latin"],
  display: "swap",
});

const lexend = Lexend({
  variable: "--font-lexend",
  subsets: ["latin"],
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
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
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${sourceSans.variable} ${lexend.variable} ${robotoMono.variable} antialiased bg-background text-foreground min-h-screen flex flex-col font-sans`}
      >
        {children}
      </body>
    </html>
  );
}
