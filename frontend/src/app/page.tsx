"use client";

import Image from "next/image";
import { ContextDrawer } from "@/components/layout/ContextDrawer";
import { ChatStream } from "@/components/chat/ChatStream";

export default function Home() {
  // Enforce 80/20 Asymmetric Enterprise Layout
  const isEnterprise = true;

  return (
    <div className="flex flex-col h-screen w-full">
      {/* Global Header */}
      <header className="h-20 border-b border-border flex items-center justify-between px-8 bg-gradient-to-r from-black to-slate-900 border-b-gold-500/20 text-white shrink-0 z-10 shadow-sm">
        <div className="flex items-center gap-5">
          <div className="p-1 bg-white/5 rounded-md border border-white/10 shadow-inner">
            <Image src="/logo.png" alt="Clinical Assistant Logo" width={56} height={56} className="drop-shadow-md" />
          </div>
          <div className="flex flex-col">
            <h1 className="font-display font-bold text-xl text-white tracking-tight leading-none">
              City General Hospital
            </h1>
            <span className="text-[10px] font-mono text-gold-500 uppercase tracking-widest mt-1">Enterprise Clinical System</span>
          </div>
        </div>

        <div className="flex items-center gap-6 text-sm font-mono text-slate-300">


          <div className="flex items-center gap-3 border-l border-slate-700 pl-6 h-8">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-none bg-gold-400 opacity-75"></span>
              <span className="relative inline-flex rounded-none h-2.5 w-2.5 bg-gold-500"></span>
            </span>
            <span className="text-gold-500 font-bold uppercase tracking-wider text-[11px]">Secure</span>
          </div>

          <div className="flex flex-col items-end border-l border-slate-700 pl-6">
            <span className="text-[11px] text-slate-400 uppercase tracking-widest leading-none mb-1">Active Session</span>
            <span className="font-bold text-xs uppercase tracking-wider text-white leading-none">
              Dr. House (Cardiology)
            </span>
          </div>
        </div>
      </header>

      {/* Main Layout Structure */}
      <main className="flex-1 flex overflow-hidden">
        {/* Collapsible Context Drawer */}
        <ContextDrawer isEnterprise={isEnterprise} />

        {/* Primary Chat Stream */}
        <section className="flex-1 flex flex-col bg-slate-50 relative border-l border-border h-full overflow-hidden">
          <ChatStream />
        </section>
      </main>

      <footer className="h-8 border-t border-border flex items-center justify-center bg-slate-50 text-[10px] text-slate-400 font-mono uppercase tracking-widest shrink-0">
        AI-assisted retrieval. Do not replace clinical judgment or direct patient assessment.
      </footer>
    </div>
  );
}
