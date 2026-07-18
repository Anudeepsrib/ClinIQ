"use client";

import Image from "next/image";
import { FormEvent, useState } from "react";
import { LogIn, ShieldCheck } from "lucide-react";

import { useChatStore } from "@/store/chatStore";

export function LoginScreen() {
    const login = useChatStore((state) => state.login);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        setLoading(true);
        setError("");
        try {
            await login(username, password);
        } catch (loginError) {
            setError(loginError instanceof Error ? loginError.message : "Sign in failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-white grid place-items-center p-6">
            <section className="w-full max-w-md border border-slate-700 bg-slate-900 shadow-2xl">
                <div className="border-b border-gold-500/30 p-6 flex items-center gap-4">
                    <Image src="/logo.png" alt="ClinIQ logo" width={52} height={52} />
                    <div>
                        <h1 className="font-display text-2xl font-bold">ClinIQ</h1>
                        <p className="text-xs font-mono uppercase tracking-widest text-gold-500">
                            Hospital Policy Reference
                        </p>
                    </div>
                </div>

                <form onSubmit={submit} className="p-6 space-y-5">
                    <div className="flex items-center gap-2 text-sm text-slate-300">
                        <ShieldCheck className="h-4 w-4 text-gold-500" />
                        Sign in with your assigned staff account.
                    </div>

                    <label className="block text-xs font-mono uppercase tracking-wider text-slate-300">
                        Username
                        <input
                            autoComplete="username"
                            value={username}
                            onChange={(event) => setUsername(event.target.value)}
                            className="mt-2 w-full border border-slate-600 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-gold-500"
                            required
                        />
                    </label>

                    <label className="block text-xs font-mono uppercase tracking-wider text-slate-300">
                        Password
                        <input
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            className="mt-2 w-full border border-slate-600 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-gold-500"
                            required
                        />
                    </label>

                    {error && <p role="alert" className="text-sm text-red-400">{error}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gold-500 px-4 py-3 text-sm font-bold uppercase tracking-wider text-black hover:bg-gold-400 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        <LogIn className="h-4 w-4" />
                        {loading ? "Signing in…" : "Sign in"}
                    </button>
                </form>
            </section>
        </main>
    );
}
