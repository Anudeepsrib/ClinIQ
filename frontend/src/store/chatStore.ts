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

        // Mock bot response logic
        if (role === "user") {
            set({ isLoading: true });

            setTimeout(() => {
                const userQuery = content.toLowerCase();
                let botResponse: Message = {
                    id: (Date.now() + 1).toString(),
                    role: "bot",
                    content: "I did not understand. Could you rephrase your clinical query?",
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                };

                // Scenario 1: Clarification needed
                if (userQuery.includes("lab") || userQuery.includes("results")) {
                    botResponse = {
                        ...botResponse,
                        content: "I need a specific patient context to retrieve lab vitals. Which active patient are you inquiring about?",
                        options: ["Patterson, Emily (Bed 4)", "Rodriguez, Luis (Bed 12)", "Search Global Directory"],
                    };
                }

                // Scenario 2: Selecting patient context after clarification
                else if (userQuery.includes("patterson")) {
                    set({ activeFocus: { name: "Emily Patterson", room: "Bed 4 - ICU", id: "MRN-10924", status: "CRITICAL" } });
                    botResponse = {
                        ...botResponse,
                        content: "Retrieving lab vitals for Emily Patterson... CBC shows elevated WBC count. [MASK]",
                        source: "EMR Integration v2.1",
                        confidence: "High",
                        masked: true, // Trigger InlineMasking for RBAC
                    };
                }

                // Scenario 3: Standard Retrieval
                else if (userQuery.includes("heparin") || userQuery.includes("dosage")) {
                    botResponse = {
                        ...botResponse,
                        content: "The standard adult dosage protocol for Heparin (IV) is a bolus of 80 units/kg followed by an infusion of 18 units/kg/hr. Please re-verify against patient weight.",
                        source: "Clinical Guidelines 2025",
                        confidence: "High",
                    };
                }

                set((state) => ({
                    messages: [...state.messages, botResponse],
                    isLoading: false,
                }));

            }, 1500);
        }
    },
}));
