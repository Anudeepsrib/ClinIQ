"use client";

import { useChatStore } from "@/store/chatStore";
import { ClarificationButtons } from "./ClarificationButtons";
import { InlineMask } from "./InlineMask";
import { FileText, Clock, ShieldCheck, User } from "lucide-react";

interface Message {
    id: string;
    role: "user" | "bot";
    content: string;
    timestamp: string;
    source?: string;
    confidence?: "High" | "Medium" | "Low";
    options?: string[];
    masked?: boolean;
}

export function MessageBubble({ message }: { message: Message }) {
    const { addMessage } = useChatStore();
    const isBot = message.role === "bot";

    const renderContent = (content: string) => {
        if (!message.masked) return content;

        // Naively split by a special token for the demo, e.g. [MASK] 
        return content.split("[MASK]").map((part, i, arr) => (
            <span key={i}>
                {part}
                {i < arr.length - 1 && <InlineMask reason="Requires 'Attending Physician' clearance for Patient Vitals." />}
            </span>
        ));
    };

    return (
        <div className={`flex flex-col ${isBot ? "items-start" : "items-end"} w-full`}>
            <div
                className={`flex items-start gap-4 max-w-[85%] ${isBot ? "flex-row" : "flex-row-reverse"
                    }`}
            >
                {/* Avatar Square */}
                <div className={`w-8 h-8 shrink-0 flex items-center justify-center border ${isBot
                    ? "bg-navy-900 border-navy-800 text-gold-400"
                    : "bg-slate-100 border-slate-200 text-slate-500"
                    }`}>
                    {isBot ? <ShieldCheck className="w-4 h-4" /> : <User className="w-4 h-4" />}
                </div>

                {/* Message Container */}
                <div className={`flex flex-col gap-2`}>
                    <div className={`p-4 border shadow-sm text-sm leading-relaxed ${isBot
                        ? "bg-white border-slate-200 text-navy-900 shadow-slate-200/50"
                        : "bg-slate-50 border-slate-200 text-navy-800"
                        }`}>
                        <div className="whitespace-pre-wrap font-sans">
                            {renderContent(message.content)}
                        </div>

                        {/* Clarification Buttons */}
                        {message.options && message.options.length > 0 && (
                            <ClarificationButtons
                                options={message.options}
                                onSelect={(opt) => addMessage(opt)}
                            />
                        )}
                    </div>

                    {/* Meta Footer (Only for Bot) */}
                    {isBot && (
                        <div className="flex items-center gap-3 text-[10px] font-mono uppercase tracking-widest text-slate-400 mt-1">
                            <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {message.timestamp}
                            </span>

                            {message.source && (
                                <>
                                    <span className="text-slate-300">|</span>
                                    <span className="flex items-center gap-1 text-navy-600 hover:text-gold-600 cursor-pointer transition-colors">
                                        <FileText className="w-3 h-3" />
                                        Source: {message.source}
                                    </span>
                                </>
                            )}

                            {message.confidence && (
                                <>
                                    <span className="text-slate-300">|</span>
                                    <span className="flex items-center gap-1">
                                        <div className={`w-1.5 h-1.5 rounded-none ${message.confidence === "High" ? "bg-gold-500" :
                                            message.confidence === "Medium" ? "bg-yellow-500" : "bg-red-500"
                                            }`}
                                        />
                                        Conf: {message.confidence}
                                    </span>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
