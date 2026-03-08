"use client";

import { useChatStore } from "@/store/chatStore";
import { FolderOpen, FileText, UserPlus, FileClock, ShieldAlert } from "lucide-react";

export function ContextDrawer({ isEnterprise = true }: { isEnterprise?: boolean }) {
    const activeFocus = useChatStore((state) => state.activeFocus);

    return (
        <aside className={`min-w-[280px] max-w-[400px] bg-white flex flex-col h-full border-r border-border shrink-0 transition-all duration-300 ${isEnterprise ? 'w-[20%]' : 'w-[30%]'}`}>
            {/* Drawer Header */}
            <div className="h-14 border-b border-border flex items-center px-5 shrink-0 bg-black text-white">
                <FolderOpen className="w-4 h-4 text-gold-500 mr-2" />
                <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-white">
                    Patient Context
                </h2>
            </div>

            {/* Active Focus Section */}
            <div className="p-4 border-b border-border">
                <h3 className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-3">
                    Active Focus
                </h3>

                {activeFocus ? (
                    <div className="bg-gradient-to-br from-gold-500/10 to-transparent border-l-4 border-l-gold-500 border-y border-r border-slate-200 p-4 rounded-none relative overflow-hidden group hover:from-gold-500/20 transition-all shadow-sm">

                        <div className="flex items-start justify-between">
                            <div>
                                <p className="font-display font-bold text-[15px] text-black leading-tight tracking-tight">
                                    {activeFocus.name}
                                </p>
                                <p className="text-[11px] text-slate-500 mt-1.5 font-mono">
                                    RM: {activeFocus.room} &nbsp;|&nbsp; ID: {activeFocus.id}
                                </p>
                            </div>
                            <span className="bg-crimson-600 text-white shadow-sm text-[10px] font-bold px-2 py-0.5 border border-crimson-700 uppercase tracking-wider">
                                {activeFocus.status}
                            </span>
                        </div>
                    </div>
                ) : (
                    <div className="border border-dashed border-slate-300 p-6 text-center bg-slate-50">
                        <UserPlus className="w-5 h-5 text-slate-400 mx-auto mb-2 opacity-50" />
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
                                <span className="flex items-center text-xs font-medium text-slate-800 group-hover:text-gold-600 transition-colors">
                                    <FileText className="w-3 h-3 mr-1.5 opacity-70" />
                                    {thread.title}
                                </span>
                                {thread.secure && <ShieldAlert className="w-3 h-3 text-crimson-500" />}
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
