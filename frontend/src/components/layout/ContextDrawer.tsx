"use client";

import { FormEvent, useState } from "react";
import { FileText, FolderOpen, Plus, Search, Trash2 } from "lucide-react";

import { useChatStore } from "@/store/chatStore";
import { DocumentLibrary } from "./DocumentLibrary";

function sessionTime(value: string): string {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString([], { dateStyle: "short", timeStyle: "short" });
}

export function ContextDrawer({ isEnterprise = true }: { isEnterprise?: boolean }) {
    const {
        sessions,
        activeSessionId,
        chatHistoryEnabled,
        searchResults,
        newChat,
        openSession,
        deleteSession,
        searchHistory,
        clearSearch,
    } = useChatStore();
    const [query, setQuery] = useState("");

    const submitSearch = (event: FormEvent) => {
        event.preventDefault();
        void searchHistory(query);
    };

    return (
        <aside className={`min-w-[280px] max-w-[400px] bg-white flex flex-col h-full border-r border-border shrink-0 transition-all duration-300 ${isEnterprise ? "w-[20%]" : "w-[30%]"}`}>
            <div className="h-14 border-b border-border flex items-center justify-between px-4 shrink-0 bg-black text-white">
                <div className="flex items-center">
                    <FolderOpen className="w-4 h-4 text-gold-500 mr-2" />
                    <h2 className="font-mono text-xs font-bold uppercase tracking-widest">Policy Workspace</h2>
                </div>
                <button
                    type="button"
                    onClick={() => void newChat()}
                    className="border border-slate-700 p-1.5 text-slate-300 hover:border-gold-500 hover:text-gold-500"
                    title="New chat"
                >
                    <Plus className="h-3.5 w-3.5" />
                </button>
            </div>

            <section className="p-4 flex-1 overflow-y-auto">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Recent Threads</h3>
                    <span className={`h-2 w-2 ${chatHistoryEnabled ? "bg-emerald-500" : "bg-slate-300"}`} title={chatHistoryEnabled ? "History enabled" : "History disabled"} />
                </div>

                {chatHistoryEnabled ? (
                    <>
                        <form onSubmit={submitSearch} className="mb-3 flex border border-slate-200">
                            <input
                                value={query}
                                onChange={(event) => {
                                    setQuery(event.target.value);
                                    if (!event.target.value) clearSearch();
                                }}
                                className="min-w-0 flex-1 px-2 py-1.5 text-xs outline-none"
                                placeholder="Search history"
                                aria-label="Search chat history"
                            />
                            <button type="submit" className="px-2 text-slate-400 hover:text-gold-600" title="Search">
                                <Search className="h-3.5 w-3.5" />
                            </button>
                        </form>

                        {searchResults.length > 0 && (
                            <div className="mb-4 border-b border-slate-200 pb-3 space-y-1">
                                <p className="text-[9px] font-mono uppercase text-slate-400">Matches</p>
                                {searchResults.map((result) => (
                                    <button
                                        type="button"
                                        key={`${result.session_id}-${result.msg_index}`}
                                        onClick={() => void openSession(result.session_id)}
                                        className="block w-full truncate bg-slate-50 p-2 text-left text-[10px] text-slate-600 hover:bg-gold-500/10"
                                    >
                                        {result.content}
                                    </button>
                                ))}
                            </div>
                        )}

                        <ul className="space-y-2">
                            {sessions.map((session) => (
                                <li
                                    key={session.session_id}
                                    className={`group flex items-start border p-2 transition-colors ${activeSessionId === session.session_id ? "border-gold-500 bg-gold-500/5" : "border-transparent hover:border-slate-200 hover:bg-slate-50"}`}
                                >
                                    <button
                                        type="button"
                                        onClick={() => void openSession(session.session_id)}
                                        className="min-w-0 flex-1 text-left"
                                    >
                                        <span className="flex items-center text-xs font-medium text-slate-800">
                                            <FileText className="w-3 h-3 mr-1.5 shrink-0 opacity-70" />
                                            <span className="truncate">{session.title}</span>
                                        </span>
                                        <span className="mt-1 block text-[9px] text-slate-400 font-mono">
                                            {session.department} · {sessionTime(session.created_at)}
                                        </span>
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => void deleteSession(session.session_id)}
                                        className="p-1 text-slate-300 opacity-0 group-hover:opacity-100 hover:text-red-600"
                                        title="Delete thread"
                                    >
                                        <Trash2 className="h-3 w-3" />
                                    </button>
                                </li>
                            ))}
                        </ul>
                        {!sessions.length && <p className="text-[10px] text-slate-400">Start a chat to create the first thread.</p>}
                    </>
                ) : (
                    <p className="text-[10px] leading-relaxed text-slate-400">
                        Persistent threads are off. Set CHAT_HISTORY_ENABLED=true to enable them.
                    </p>
                )}
            </section>

            <DocumentLibrary />
        </aside>
    );
}
