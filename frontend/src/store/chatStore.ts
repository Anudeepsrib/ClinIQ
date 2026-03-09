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
    addMessage: (content: string, role?: "user" | "bot") => void;
    setFocus: (focus: ActiveFocus | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
    messages: [],
    activeFocus: null,
    isLoading: false,

    setFocus: (focus) => set({ activeFocus: focus }),

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
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; // pointing to prod FastAPI
                    const res = await fetch(`${apiUrl}/api/v1/query`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ question: content })
                    });

                    if (!res.ok) throw new Error("API Error");

                    const data = await res.json();

                    const botResponse: Message = {
                        id: (Date.now() + 1).toString(),
                        role: "bot",
                        content: data.answer,
                        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        options: data.options?.length > 0 ? data.options : undefined,
                        source: data.sources?.length > 0 ? data.sources[0].filename : undefined,
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
                } catch (err) {
                    set((state) => ({
                        messages: [...state.messages, {
                            id: (Date.now() + 1).toString(),
                            role: "bot",
                            content: "Error communicating with the backend API.",
                            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        }],
                        isLoading: false,
                    }));
                }
            })();
        }
    },
}));
