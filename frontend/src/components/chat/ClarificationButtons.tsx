import { useChatStore } from "@/store/chatStore";

export function ClarificationButtons({
    options,
    onSelect
}: {
    options: string[],
    onSelect: (option: string) => void
}) {
    const { isLoading } = useChatStore();

    return (
        <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-100">
            {options.map((option) => (
                <button
                    key={option}
                    disabled={isLoading}
                    onClick={() => onSelect(option)}
                    className="text-xs font-mono font-bold uppercase tracking-wider px-3 py-1.5 border border-slate-200 bg-white text-navy-800 hover:bg-cyan-50 hover:border-cyan-500 hover:text-cyan-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-left"
                >
                    {option}
                </button>
            ))}
        </div>
    );
}
