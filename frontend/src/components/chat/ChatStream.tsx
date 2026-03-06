"use client";

import { useRef, useEffect } from "react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "../input/ChatInput";
import { useChatStore } from "@/store/chatStore";

export function ChatStream() {
    const { messages, isLoading } = useChatStore();
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of chat
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    return (
        <div className="flex flex-col h-full bg-white relative">
            <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-400">
                        <h2 className="font-display font-bold text-xl text-navy-800 tracking-tight mb-2">
                            Clinical Knowledge Base
                        </h2>
                        <p className="font-mono text-xs max-w-md text-center leading-relaxed">
                            Ask a question about hospital protocols, resident care plans,
                            or staff procedures.
                            <br />
                            <span className="text-red-500 font-bold mt-2 inline-block">
                                All queries are linked to your identity for auditing.
                            </span>
                        </p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <MessageBubble key={msg.id} message={msg} />
                    ))
                )}

                {isLoading && (
                    <div className="flex space-x-2 p-4 items-center">
                        <div className="w-1.5 h-1.5 bg-gold-500 rounded-none animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-1.5 h-1.5 bg-gold-500 rounded-none animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-1.5 h-1.5 bg-gold-500 rounded-none animate-bounce" style={{ animationDelay: "300ms" }} />
                        <span className="ml-2 text-xs font-mono text-slate-400 uppercase tracking-widest">
                            Retrieving context...
                        </span>
                    </div>
                )}

                <div ref={bottomRef} className="h-4" />
            </div>

            <div className="shrink-0 p-4 border-t border-border bg-slate-50">
                <ChatInput />
            </div>
        </div>
    );
}
