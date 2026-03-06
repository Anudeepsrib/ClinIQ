"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { PushToTalk } from "./PushToTalk";

export function ChatInput() {
    const [input, setInput] = useState("");
    const { addMessage, isLoading } = useChatStore();

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        addMessage(input);
        setInput("");
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto bg-white border border-border p-3 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.1)] focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500 transition-all">
            <form onSubmit={handleSubmit} className="flex flex-col gap-2">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a clinical query or protocol request..."
                    className="w-full min-h-[60px] max-h-[200px] resize-none border-none focus:ring-0 text-sm bg-transparent !outline-none text-navy-900 placeholder:text-slate-400"
                    rows={1}
                />

                <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-4">
                        <PushToTalk onRecordingComplete={(blob: Blob) => console.log("Audio ready:", blob)} />
                        <span className="text-[10px] font-mono text-slate-400 tracking-wider">
                            Hold the microphone to record.
                        </span>
                    </div>

                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="group flex items-center justify-center bg-navy-900 hover:bg-cyan-600 disabled:bg-slate-200 text-white p-3 rounded-none transition-colors"
                        title="Send Query (Enter)"
                    >
                        <Send className="w-4 h-4 translate-y-px group-hover:translate-x-0.5 transition-transform" />
                    </button>
                </div>
            </form>
        </div>
    );
}
