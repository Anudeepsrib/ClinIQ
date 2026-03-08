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
        <div className="w-full max-w-4xl mx-auto bg-white border-t-4 border-t-gold-500 border border-slate-200 p-4 shadow-xl focus-within:border-gold-500 focus-within:ring-1 focus-within:ring-gold-500 transition-all">
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a clinical query or protocol request..."
                    className="w-full min-h-[60px] max-h-[200px] resize-none border-none focus:ring-0 text-sm bg-transparent !outline-none text-black placeholder:text-slate-400"
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
                        className="group flex items-center justify-center bg-gold-500 hover:bg-gold-400 disabled:bg-slate-200 text-black p-3 transition-all shadow-md active:scale-95"
                        title="Send Query (Enter)"
                    >
                        <Send className="w-4 h-4 translate-y-px group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            </form>
        </div>
    );
}
