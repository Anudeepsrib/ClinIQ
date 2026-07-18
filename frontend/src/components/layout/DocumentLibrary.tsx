"use client";

import { ChangeEvent, useCallback, useEffect, useState } from "react";
import { FileClock, FileText, Trash2, Upload } from "lucide-react";

import {
    apiBaseUrl,
    getAuthHeaders,
    parseError,
    useChatStore,
} from "@/store/chatStore";

interface DocumentInfo {
    doc_id: string;
    filename: string;
    department: string;
    chunk_count: number;
    version: number;
    ingested_by: string;
    ingested_at: string;
    status: string;
}

interface IngestJob {
    job_id: string;
    filename: string;
    modality: string;
    status: "queued" | "processing" | "completed" | "failed";
    error?: string;
    result?: { change_type: string; chunk_count: number; version: number };
}

const delay = (milliseconds: number) => new Promise((resolve) => setTimeout(resolve, milliseconds));

export function DocumentLibrary() {
    const user = useChatStore((state) => state.user);
    const [departments, setDepartments] = useState<string[]>([]);
    const [department, setDepartment] = useState("");
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [history, setHistory] = useState<Record<string, DocumentInfo[]>>({});
    const [status, setStatus] = useState("");

    const loadDocuments = useCallback(async (selectedDepartment: string) => {
        if (!selectedDepartment) return;
        const res = await fetch(
            `${apiBaseUrl}/api/v1/documents/${encodeURIComponent(selectedDepartment)}`,
            { headers: getAuthHeaders() },
        );
        if (res.ok) setDocuments(await res.json());
    }, []);

    useEffect(() => {
        if (!user) return;
        void (async () => {
            const res = await fetch(`${apiBaseUrl}/api/v1/departments`, { headers: getAuthHeaders() });
            if (!res.ok) return;
            const data = await res.json();
            const available = data.departments || [];
            setDepartments(available);
            const first = available[0] || "";
            setDepartment(first);
            await loadDocuments(first);
        })();
    }, [loadDocuments, user]);

    const selectDepartment = (selectedDepartment: string) => {
        setDepartment(selectedDepartment);
        setHistory({});
        void loadDocuments(selectedDepartment);
    };

    const pollJob = async (jobId: string): Promise<IngestJob> => {
        for (let attempt = 0; attempt < 120; attempt += 1) {
            const res = await fetch(`${apiBaseUrl}/api/v1/ingest/jobs/${jobId}`, {
                headers: getAuthHeaders(),
            });
            if (!res.ok) throw new Error(await parseError(res));
            const job: IngestJob = await res.json();
            setStatus(`${job.filename}: ${job.status} (${job.modality})`);
            if (job.status === "completed") return job;
            if (job.status === "failed") throw new Error(job.error || "Ingestion failed");
            await delay(1000);
        }
        throw new Error("Ingestion status timed out");
    };

    const upload = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !department) return;
        setStatus(`${file.name}: uploading`);
        const body = new FormData();
        body.append("file", file);
        body.append("department", department);
        try {
            const res = await fetch(`${apiBaseUrl}/api/v1/ingest/jobs`, {
                method: "POST",
                headers: getAuthHeaders(),
                body,
            });
            if (!res.ok) throw new Error(await parseError(res));
            const queued: IngestJob = await res.json();
            const completed = await pollJob(queued.job_id);
            setStatus(
                `${completed.filename}: ${completed.result?.change_type} · ${completed.result?.chunk_count} chunks · v${completed.result?.version}`,
            );
            await loadDocuments(department);
        } catch (error) {
            setStatus(error instanceof Error ? error.message : "Upload failed");
        } finally {
            event.target.value = "";
        }
    };

    const loadHistory = async (document: DocumentInfo) => {
        const res = await fetch(
            `${apiBaseUrl}/api/v1/documents/${encodeURIComponent(department)}/${encodeURIComponent(document.filename)}/history`,
            { headers: getAuthHeaders() },
        );
        if (res.ok) {
            const data = await res.json();
            setHistory((current) => ({ ...current, [document.doc_id]: data.history }));
        }
    };

    const removeDocument = async (document: DocumentInfo) => {
        if (!window.confirm(`Delete ${document.filename} from ${department}?`)) return;
        const res = await fetch(
            `${apiBaseUrl}/api/v1/documents/${encodeURIComponent(department)}/${encodeURIComponent(document.filename)}`,
            { method: "DELETE", headers: getAuthHeaders() },
        );
        if (res.ok) await loadDocuments(department);
    };

    return (
        <details className="border-t border-slate-200 p-4">
            <summary className="cursor-pointer text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
                Document Library
            </summary>

            <div className="mt-4 space-y-3">
                <select
                    value={department}
                    onChange={(event) => selectDepartment(event.target.value)}
                    className="w-full border border-slate-300 bg-white p-2 text-xs text-slate-800"
                    aria-label="Document department"
                >
                    {departments.map((item) => <option key={item}>{item}</option>)}
                </select>

                <label className="flex cursor-pointer items-center justify-center gap-2 border border-dashed border-gold-500 p-3 text-xs font-bold text-slate-700 hover:bg-gold-500/10">
                    <Upload className="h-4 w-4" />
                    Upload policy
                    <input
                        type="file"
                        className="sr-only"
                        accept=".pdf,.docx,.xlsx,.xls,.png,.jpg,.jpeg,.tiff,.bmp,.dcm,.mp3,.wav,.m4a,.flac,.ogg,.mp4,.mov,.avi,.webm"
                        onChange={upload}
                    />
                </label>

                {status && <p aria-live="polite" className="text-[10px] text-slate-500">{status}</p>}

                <div className="space-y-2">
                    {documents.map((document) => (
                        <article key={document.doc_id} className="border border-slate-200 p-2 text-xs">
                            <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                    <p className="truncate font-medium text-slate-800 flex items-center gap-1">
                                        <FileText className="h-3 w-3 shrink-0" /> {document.filename}
                                    </p>
                                    <p className="mt-1 text-[10px] text-slate-400">
                                        v{document.version} · {document.chunk_count} chunks
                                    </p>
                                </div>
                                <div className="flex gap-1">
                                    <button
                                        type="button"
                                        onClick={() => void loadHistory(document)}
                                        className="p-1 text-slate-400 hover:text-gold-600"
                                        title="Load version history"
                                    >
                                        <FileClock className="h-3 w-3" />
                                    </button>
                                    {user?.role === "admin" && (
                                        <button
                                            type="button"
                                            onClick={() => void removeDocument(document)}
                                            className="p-1 text-slate-400 hover:text-red-600"
                                            title="Delete document"
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {history[document.doc_id] && (
                                <ul className="mt-2 border-t border-slate-100 pt-2 text-[10px] text-slate-500">
                                    {history[document.doc_id].map((version) => (
                                        <li key={`${version.doc_id}-${version.version}`}>
                                            v{version.version} · {version.status} · {version.ingested_by}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </article>
                    ))}
                    {!documents.length && <p className="text-[10px] text-slate-400">No active documents.</p>}
                </div>
            </div>
        </details>
    );
}
