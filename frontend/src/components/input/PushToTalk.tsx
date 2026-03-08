"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Mic } from "lucide-react";

interface PushToTalkProps {
    onRecordingComplete?: (blob: Blob) => void;
}

export function PushToTalk({ onRecordingComplete }: PushToTalkProps) {
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorderRef.current.onstop = () => {
                const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
                onRecordingComplete?.(audioBlob);

                // Cleanup all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Microphone access denied:", err);
        }
    }, [onRecordingComplete]);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current?.state === "recording") {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    }, []);

    // Keyboard accessibility (Spacebar to hold-to-talk)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === "Space" && !e.repeat && document.activeElement === document.body) {
                e.preventDefault();
                startRecording();
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            if (e.code === "Space") {
                e.preventDefault();
                stopRecording();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        window.addEventListener("keyup", handleKeyUp);

        return () => {
            window.removeEventListener("keydown", handleKeyDown);
            window.removeEventListener("keyup", handleKeyUp);

            // Cleanup incase unmounted while recording
            if (mediaRecorderRef.current?.state === "recording") {
                mediaRecorderRef.current.stop();
            }
        };
    }, []);

    return (
        <div className="relative flex items-center justify-center">
            {/* Active Pulse Ring */}
            {isRecording && (
                <span className="absolute inline-flex h-full w-full rounded-full bg-crimson-500 opacity-75 animate-ping" />
            )}

            <button
                type="button"
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onMouseLeave={stopRecording}
                onTouchStart={startRecording}
                onTouchEnd={stopRecording}
                className={`relative z-10 w-10 h-10 flex items-center justify-center rounded-none shadow-sm transition-colors border ${isRecording
                    ? "bg-crimson-600 border-crimson-700 text-white"
                    : "bg-white border-slate-200 text-slate-500 hover:text-black hover:bg-slate-50"
                    }`}
                aria-label="Push to Talk"
            >
                <Mic className={`w-5 h-5 ${isRecording ? "animate-pulse" : ""}`} />
            </button>
        </div>
    );
}
