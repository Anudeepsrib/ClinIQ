"use client";

import React from "react";
import { motion } from "framer-motion";
import { Cloud, HardDrive, Cpu } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export const ModelSwitcher: React.FC = () => {
  const { llmProvider, setLlmProvider } = useChatStore();

  const providers = [
    { id: "azure_openai", label: "Cloud", icon: Cloud, desc: "GPT-4o (Azure)" },
    { id: "ollama", label: "Local", icon: HardDrive, desc: "Gemma 4 (Ollama)" },
    { id: "vllm", label: "PRO", icon: Cpu, desc: "Gemma 4 (vLLM)" },
  ] as const;

  return (
    <div className="flex flex-col gap-2 p-4 bg-white/5 border-b border-white/10">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">
          Active Clinical Intelligence
        </span>
        <div className="flex items-center gap-1 bg-black/40 p-1 rounded-lg border border-white/5 shadow-inner">
          {providers.map((p) => (
            <button
              key={p.id}
              onClick={() => setLlmProvider(p.id)}
              className={`relative flex items-center gap-2 px-3 py-1.5 rounded-md text-[11px] font-bold transition-all duration-300 ${
                llmProvider === p.id
                  ? "text-white"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {llmProvider === p.id && (
                <motion.div
                  layoutId="active-provider"
                  className="absolute inset-0 bg-gradient-to-r from-gold-600/20 to-gold-500/10 border border-gold-500/30 rounded-md shadow-[0_0_15px_rgba(234,179,8,0.1)]"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <p.icon size={12} className={llmProvider === p.id ? "text-gold-500" : ""} />
              <span className="relative z-10 uppercase tracking-wider">{p.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-2 px-1">
        <div className={`h-1 w-1 rounded-full animate-pulse ${llmProvider === "azure_openai" ? "bg-blue-400" : "bg-gold-500"}`} />
        <span className="text-[9px] text-slate-500 font-mono">
          SYSTEM: {providers.find(p => p.id === llmProvider)?.desc}
        </span>
      </div>
    </div>
  );
};
