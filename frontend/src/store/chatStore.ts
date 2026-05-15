import { create } from "zustand";

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

interface ActiveFocus {
    name: string;
    room: string;
    id: string;
    status: string;
}

interface ChatState {
    messages: Message[];
    activeFocus: ActiveFocus | null;
    isLoading: boolean;
    llmProvider: "azure_openai" | "ollama" | "vllm";
    addMessage: (content: string, role?: "user" | "bot") => void;
    copilotQuickHelp: (question: string, context?: string, department?: string) => void;
    setFocus: (focus: ActiveFocus | null) => void;
    setLlmProvider: (provider: "azure_openai" | "ollama" | "vllm") => void;
}

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getJsonHeaders(): HeadersInit {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (typeof window !== "undefined") {
        const token = window.localStorage.getItem("cliniq_token");
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }
    }
    return headers;
}

async function parseError(res: Response): Promise<string> {
    try {
        const data = await res.json();
        if (typeof data.detail === "string") return data.detail;
    } catch {
        // Keep the generic status message below.
    }
    return `Request failed (${res.status})`;
}

export const useChatStore = create<ChatState>((set, get) => ({
    messages: [],
    activeFocus: null,
    isLoading: false,
    llmProvider: "azure_openai",

    setFocus: (focus) => set({ activeFocus: focus }),
    
    setLlmProvider: (provider) => set({ llmProvider: provider }),

    addMessage: (content, role = "user") => {
        const newMessage: Message = {
            id: Date.now().toString(),
            role,
            content,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        set((state) => ({ messages: [...state.messages, newMessage] }));

        // Bot response logic via API fetch
        if (role === "user") {
            set({ isLoading: true });

            (async () => {
                try {
                    const res = await fetch(`${apiBaseUrl}/api/v1/query`, {
                        method: "POST",
                        headers: getJsonHeaders(),
                        body: JSON.stringify({ question: content })
                    });

                    if (!res.ok) throw new Error(await parseError(res));

                    const data = await res.json();

                    const botResponse: Message = {
                        id: (Date.now() + 1).toString(),
                        role: "bot",
                        content: data.answer,
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        options: data.options?.length > 0 ? data.options : undefined,
                        source: data.sources?.length > 0 ? data.sources[0].source : undefined,
                        confidence: data.confidence_score > 0.9 ? "High" : (data.confidence_score > 0.7 ? "Medium" : "Low"),
                        masked: data.masked || false,
                    };

                    // Specific UI Focus toggle for the demo scenario layout showcase
                    if (content.toLowerCase().includes("patterson")) {
                        set({ activeFocus: { name: "Emily Patterson", room: "Bed 4 - ICU", id: "MRN-10924", status: "CRITICAL" } });
                    }

                    set((state) => ({
                        messages: [...state.messages, botResponse],
                        isLoading: false,
                    }));
                } catch (error) {
                    const message = error instanceof Error ? error.message : "Unknown API error";
                    set((state) => ({
                        messages: [...state.messages, {
                            id: (Date.now() + 1).toString(),
                            role: "bot",
                            content: `Unable to reach ClinIQ API. ${message}`,
                            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        }],
                        isLoading: false,
                    }));
                }
            })();
        }
    },

    copilotQuickHelp: (question, context, department) => {
        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: `🩺 [Copilot Health] ${question}`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        set((state) => ({ messages: [...state.messages, userMsg], isLoading: true }));

        (async () => {
            try {
                const res = await fetch(`${apiBaseUrl}/api/v1/copilot/quick-help`, {
                    method: "POST",
                    headers: getJsonHeaders(),
                    body: JSON.stringify({ 
                        question, 
                        context, 
                        department,
                        provider: get().llmProvider // Send the selected provider
                    }),
                });

                if (!res.ok) throw new Error(await parseError(res));

                const data = await res.json();

                const botResponse: Message = {
                    id: (Date.now() + 1).toString(),
                    role: "bot",
                    content: data.answer + (data.disclaimer ? `\n\n⚠️ ${data.disclaimer}` : ""),
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    source: data.sources?.[0]?.title || "Microsoft Copilot Health",
                    confidence: data.confidence === "high" ? "High" : (data.confidence === "medium" ? "Medium" : "Low"),
                };

                set((state) => ({
                    messages: [...state.messages, botResponse],
                    isLoading: false,
                }));
            } catch (error) {
                const message = error instanceof Error ? error.message : "Please try again or use the standard query.";
                set((state) => ({
                    messages: [...state.messages, {
                        id: (Date.now() + 1).toString(),
                        role: "bot",
                        content: `Unable to reach Copilot Health. ${message}`,
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    }],
                    isLoading: false,
                }));
            }
        })();
    },
}));
