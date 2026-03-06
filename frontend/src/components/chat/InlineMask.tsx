import { ShieldAlert } from "lucide-react";

interface InlineMaskProps {
    reason?: string;
}

export function InlineMask({ reason = "Clearance Required" }: InlineMaskProps) {
    return (
        <span
            className="group relative inline-flex items-center text-transparent bg-slate-200 cursor-not-allowed mx-1 px-2 select-none"
            style={{
                backgroundImage: "repeating-linear-gradient(45deg, #e2e8f0 25%, transparent 25%, transparent 75%, #e2e8f0 75%, #e2e8f0), repeating-linear-gradient(45deg, #e2e8f0 25%, #f1f5f9 25%, #f1f5f9 75%, #e2e8f0 75%, #e2e8f0)",
                backgroundPosition: "0 0, 4px 4px",
                backgroundSize: "8px 8px"
            }}
        >
            <span className="opacity-0">▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒</span>

            {/* Strict Square Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-xs bg-navy-900 text-white text-xs p-2 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 flex items-start gap-2 border border-navy-700">
                <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
                <span className="font-mono leading-relaxed">
                    <span className="text-red-400 font-bold block mb-1">REDACTED DATA</span>
                    {reason}
                </span>
            </div>
        </span>
    );
}
