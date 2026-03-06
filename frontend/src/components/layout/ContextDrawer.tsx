"use client";

import { useChatStore } from "@/store/chatStore";
import { FolderOpen, FileText, UserPlus, FileClock, ShieldAlert } from "lucide-react";

export function ContextDrawer() {
    const activeFocus = useChatStore((state) => state.activeFocus);

    return (
        <aside className="w-[30%] min-w-[280px] max-w-[400px] bg-white flex flex-col h-full border-r border-border shrink-0">
            {/* Drawer Header */}
            <div className="h-14 border-b border-border flex items-center px-4 shrink-0 bg-slate-50">
                <FolderOpen className="w-4 h-4 text-navy-700 mr-2" />
                <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-navy-800">
                    Context Drawer
                </h2>
            </div>

            {/* Active Focus Section */}
            <div className="p-4 border-b border-border">
                <h3 className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-3">
                    Active Focus
                </h3>

                {activeFocus ? (
                    <div className="bg-slate-50 border border-border p-3 rounded-none relative overflow-hidden group">
                        {/* Strict geometric accent mark */}
                        <div className="absolute top-0 left-0 w-1 h-full bg-gold-500" />

                        <div className="flex items-start justify-between">
                            <div>
                                <p className="font-display font-bold text-sm text-navy-900 leading-tight">
                                    {activeFocus.name}
                                </p>
                                <p className="text-xs text-slate-500 mt-1 font-mono">
                                    Room: {activeFocus.room} | ID: {activeFocus.id}
                                </p>
                            </div>
                            <span className="bg-red-50 text-red-600 text-[10px] font-bold px-1.5 py-0.5 border border-red-200 uppercase">
                                {activeFocus.status}
                            </span>
                        </div>
                    </div>
                ) : (
                    <div className="border border-dashed border-slate-300 p-4 text-center bg-slate-50/50">
                        <UserPlus className="w-5 h-5 text-slate-400 mx-auto mb-2" />
                        <p className="text-xs text-slate-500 font-mono">No Patient Selected</p>
                    </div>
                )}
            </div>

            {/* Recent Threads / Audits */}
            <div className="p-4 flex-1 overflow-y-auto">
                <h3 className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-3 flex items-center justify-between">
                    <span>Recent Threads</span>
                    <FileClock className="w-3 h-3" />
                </h3>

                <ul className="space-y-2">
                    {[
                        { id: "1", title: "Heparin IV Dosages", time: "10:42 AM", secure: false },
                        { id: "2", title: "Shift Handoff Protocol", time: "09:15 AM", secure: false },
                        { id: "3", title: "Patient Vitals (Masked)", time: "Yesterday", secure: true },
                    ].map((thread) => (
                        <li
                            key={thread.id}
                            className="group flex flex-col p-2 border border-transparent hover:border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors"
                        >
                            <div className="flex items-center justify-between mb-1">
                                <span className="flex items-center text-xs font-medium text-navy-800 group-hover:text-cyan-600 transition-colors">
                                    <FileText className="w-3 h-3 mr-1.5 opacity-70" />
                                    {thread.title}
                                </span>
                                {thread.secure && <ShieldAlert className="w-3 h-3 text-red-500" />}
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono ml-4.5">
                                {thread.time}
                            </span>
                        </li>
                    ))}
                </ul>
            </div>
        </aside>
    );
}
