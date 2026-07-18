import { create } from "zustand";

export type LlmProvider = "google_gemma" | "azure_openai" | "ollama" | "vllm";
export type ChatMode = "rag" | "quick_help";

export interface AuthUser {
    id: number;
    username: string;
    full_name: string;
    role: string;
    departments: string[];
    is_active: boolean;
    created_at: string;
}

export interface Message {
    id: string;
    role: "user" | "bot";
    content: string;
    timestamp: string;
    source?: string;
    confidence?: "High" | "Medium" | "Low";
    options?: string[];
    masked?: boolean;
    runId?: string;
    feedbackEnabled?: boolean;
    feedbackStatus?: "sending" | "sent" | "error";
}

export interface SessionSummary {
    session_id: string;
    title: string;
    created_at: string;
    message_count: number;
    department: string;
}

interface StoredMessage {
    role: "user" | "bot";
    content: string;
    session_id: string;
    timestamp: string;
    msg_index: number;
}

interface ChatState {
    user: AuthUser | null;
    authReady: boolean;
    messages: Message[];
    isLoading: boolean;
    llmProvider: LlmProvider;
    chatMode: ChatMode;
    chatHistoryEnabled: boolean;
    sessions: SessionSummary[];
    activeSessionId: string | null;
    searchResults: StoredMessage[];
    initializeAuth: () => Promise<void>;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
    addMessage: (content: string, role?: "user" | "bot") => void;
    copilotQuickHelp: (question: string, context?: string, department?: string) => void;
    setLlmProvider: (provider: LlmProvider) => void;
    setChatMode: (mode: ChatMode) => void;
    newChat: (department?: string) => Promise<void>;
    loadSessions: () => Promise<void>;
    openSession: (sessionId: string) => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
    searchHistory: (query: string) => Promise<void>;
    clearSearch: () => void;
    submitFeedback: (messageId: string, runId: string, score: number, comment?: string) => Promise<void>;
}

export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function token(): string | null {
    return typeof window === "undefined" ? null : window.localStorage.getItem("cliniq_token");
}

export function getAuthHeaders(): HeadersInit {
    const authToken = token();
    return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

export function getJsonHeaders(): HeadersInit {
    return { ...getAuthHeaders(), "Content-Type": "application/json" };
}

export async function parseError(res: Response): Promise<string> {
    try {
        const data = await res.json();
        if (typeof data.detail === "string") return data.detail;
    } catch {
        // Keep the generic status message below.
    }
    return `Request failed (${res.status})`;
}

async function chatHistoryAvailable(): Promise<boolean> {
    try {
        const res = await fetch(`${apiBaseUrl}/ready`);
        const data = await res.json();
        return res.ok && data.checks?.chat_history === "ready";
    } catch {
        return false;
    }
}

async function createSession(department = "general"): Promise<string | null> {
    const res = await fetch(`${apiBaseUrl}/api/v1/chat/sessions`, {
        method: "POST",
        headers: getJsonHeaders(),
        body: JSON.stringify({ department }),
    });
    if (!res.ok) return null;
    return (await res.json()).session_id;
}

function messageId(): string {
    return globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
}

function displayTime(timestamp?: string): string {
    const date = timestamp ? new Date(timestamp) : new Date();
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function storedMessage(message: StoredMessage): Message {
    return {
        id: `${message.session_id}-${message.msg_index}`,
        role: message.role,
        content: message.content,
        timestamp: displayTime(message.timestamp),
    };
}

export const useChatStore = create<ChatState>((set, get) => ({
    user: null,
    authReady: false,
    messages: [],
    isLoading: false,
    llmProvider: "google_gemma",
    chatMode: "rag",
    chatHistoryEnabled: false,
    sessions: [],
    activeSessionId: null,
    searchResults: [],

    initializeAuth: async () => {
        if (!token()) {
            set({ authReady: true });
            return;
        }
        try {
            const res = await fetch(`${apiBaseUrl}/api/v1/auth/me`, { headers: getAuthHeaders() });
            if (!res.ok) throw new Error(await parseError(res));
            const historyEnabled = await chatHistoryAvailable();
            set({ user: await res.json(), authReady: true, chatHistoryEnabled: historyEnabled });
            if (historyEnabled) await get().loadSessions();
        } catch {
            window.localStorage.removeItem("cliniq_token");
            set({ user: null, authReady: true, chatHistoryEnabled: false });
        }
    },

    login: async (username, password) => {
        const res = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) throw new Error(await parseError(res));
        const data = await res.json();
        window.localStorage.setItem("cliniq_token", data.access_token);
        const historyEnabled = await chatHistoryAvailable();
        set({ user: data.user, chatHistoryEnabled: historyEnabled, authReady: true });
        if (historyEnabled) await get().loadSessions();
    },

    logout: () => {
        window.localStorage.removeItem("cliniq_token");
        set({
            user: null,
            messages: [],
            sessions: [],
            activeSessionId: null,
            searchResults: [],
            chatHistoryEnabled: false,
            chatMode: "rag",
        });
    },

    setLlmProvider: (provider) => set({ llmProvider: provider }),
    setChatMode: (mode) => set({ chatMode: mode }),

    addMessage: (content, role = "user") => {
        const newMessage: Message = {
            id: messageId(),
            role,
            content,
            timestamp: displayTime(),
        };
        set((state) => ({ messages: [...state.messages, newMessage] }));
        if (role !== "user") return;

        set({ isLoading: true });
        void (async () => {
            try {
                let sessionId = get().activeSessionId;
                if (get().chatHistoryEnabled && !sessionId) {
                    sessionId = await createSession(get().user?.departments[0] || "general");
                    set({ activeSessionId: sessionId });
                }

                const res = await fetch(`${apiBaseUrl}/api/v1/query`, {
                    method: "POST",
                    headers: getJsonHeaders(),
                    body: JSON.stringify({
                        question: content,
                        provider: get().llmProvider,
                        session_id: sessionId,
                    }),
                });
                if (!res.ok) throw new Error(await parseError(res));
                const data = await res.json();
                const botResponse: Message = {
                    id: messageId(),
                    role: "bot",
                    content: data.answer,
                    timestamp: displayTime(),
                    options: data.options?.length ? data.options : undefined,
                    source: data.sources?.[0]?.source,
                    confidence: data.confidence_score > 0.9 ? "High" : data.confidence_score > 0.7 ? "Medium" : "Low",
                    masked: data.masked || false,
                    runId: data.run_id || undefined,
                    feedbackEnabled: data.feedback_enabled || false,
                };
                set((state) => ({ messages: [...state.messages, botResponse], isLoading: false }));
                if (get().chatHistoryEnabled) await get().loadSessions();
            } catch (error) {
                const detail = error instanceof Error ? error.message : "Unknown API error";
                set((state) => ({
                    messages: [...state.messages, {
                        id: messageId(),
                        role: "bot",
                        content: `Unable to reach ClinIQ API. ${detail}`,
                        timestamp: displayTime(),
                    }],
                    isLoading: false,
                }));
            }
        })();
    },

    copilotQuickHelp: (question, context, department) => {
        set((state) => ({
            messages: [...state.messages, {
                id: messageId(),
                role: "user",
                content: question,
                timestamp: displayTime(),
            }],
            isLoading: true,
        }));

        void (async () => {
            try {
                let sessionId = get().activeSessionId;
                if (get().chatHistoryEnabled && !sessionId) {
                    sessionId = await createSession(department || get().user?.departments[0] || "general");
                    set({ activeSessionId: sessionId });
                }
                const res = await fetch(`${apiBaseUrl}/api/v1/copilot/quick-help`, {
                    method: "POST",
                    headers: getJsonHeaders(),
                    body: JSON.stringify({
                        question,
                        context,
                        department,
                        provider: get().llmProvider,
                        session_id: sessionId,
                    }),
                });
                if (!res.ok) throw new Error(await parseError(res));
                const data = await res.json();
                set((state) => ({
                    messages: [...state.messages, {
                        id: messageId(),
                        role: "bot",
                        content: data.answer + (data.disclaimer ? `\n\n${data.disclaimer}` : ""),
                        timestamp: displayTime(),
                        source: data.sources?.[0]?.title || "Policy Quick Help",
                        confidence: data.confidence === "high" ? "High" : data.confidence === "medium" ? "Medium" : "Low",
                    }],
                    isLoading: false,
                }));
                if (get().chatHistoryEnabled) await get().loadSessions();
            } catch (error) {
                const detail = error instanceof Error ? error.message : "Please try standard search.";
                set((state) => ({
                    messages: [...state.messages, {
                        id: messageId(),
                        role: "bot",
                        content: `Quick Help is unavailable. ${detail}`,
                        timestamp: displayTime(),
                    }],
                    isLoading: false,
                }));
            }
        })();
    },

    newChat: async (department) => {
        const sessionId = get().chatHistoryEnabled
            ? await createSession(department || get().user?.departments[0] || "general")
            : null;
        set({ messages: [], activeSessionId: sessionId, searchResults: [] });
    },

    loadSessions: async () => {
        const res = await fetch(`${apiBaseUrl}/api/v1/chat/sessions`, { headers: getAuthHeaders() });
        if (res.status === 503) {
            set({ chatHistoryEnabled: false, sessions: [] });
            return;
        }
        if (res.ok) set({ sessions: await res.json() });
    },

    openSession: async (sessionId) => {
        const res = await fetch(`${apiBaseUrl}/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`, {
            headers: getAuthHeaders(),
        });
        if (!res.ok) return;
        const messages: StoredMessage[] = await res.json();
        set({ activeSessionId: sessionId, messages: messages.map(storedMessage), searchResults: [] });
    },

    deleteSession: async (sessionId) => {
        const res = await fetch(`${apiBaseUrl}/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });
        if (!res.ok) return;
        set((state) => ({
            sessions: state.sessions.filter((session) => session.session_id !== sessionId),
            messages: state.activeSessionId === sessionId ? [] : state.messages,
            activeSessionId: state.activeSessionId === sessionId ? null : state.activeSessionId,
        }));
    },

    searchHistory: async (query) => {
        if (!query.trim()) {
            set({ searchResults: [] });
            return;
        }
        const res = await fetch(`${apiBaseUrl}/api/v1/chat/search`, {
            method: "POST",
            headers: getJsonHeaders(),
            body: JSON.stringify({ query, k: 10 }),
        });
        if (res.ok) set({ searchResults: await res.json() });
    },

    clearSearch: () => set({ searchResults: [] }),

    submitFeedback: async (messageIdToUpdate, runId, score, comment) => {
        set((state) => ({
            messages: state.messages.map((message) =>
                message.id === messageIdToUpdate ? { ...message, feedbackStatus: "sending" } : message
            ),
        }));
        const res = await fetch(`${apiBaseUrl}/api/v1/feedback`, {
            method: "POST",
            headers: getJsonHeaders(),
            body: JSON.stringify({ run_id: runId, key: "correctness", score, comment }),
        });
        set((state) => ({
            messages: state.messages.map((message) =>
                message.id === messageIdToUpdate
                    ? { ...message, feedbackStatus: res.ok ? "sent" : "error" }
                    : message
            ),
        }));
    },
}));
