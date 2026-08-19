"use client";

import type { RecorderState } from "@/hooks/use-voice-recorder";

interface VoiceButtonProps {
  state: RecorderState;
  onStart: () => void;
  onStop: () => void;
}

export default function VoiceButton({
  state,
  onStart,
  onStop,
}: VoiceButtonProps) {
  const isRecording = state === "recording";
  const isRequesting = state === "requesting";

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Pulse ring (recording state) */}
      <div className="relative">
        {isRecording && (
          <>
            <div className="absolute inset-0 rounded-full bg-accent/20 animate-pulse-ring" />
            <div
              className="absolute inset-0 rounded-full bg-accent/10 animate-pulse-ring"
              style={{ animationDelay: "0.5s" }}
            />
          </>
        )}
        <button
          id="voice-button"
          onClick={isRecording ? onStop : onStart}
          disabled={isRequesting}
          className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
            isRecording
              ? "bg-accent/20 border-2 border-accent shadow-[0_0_30px_rgba(14,165,233,0.3)]"
              : isRequesting
              ? "bg-bg-elevated border-2 border-border-default opacity-50 cursor-wait"
              : "bg-bg-elevated border-2 border-border-default hover:border-accent/50 hover:bg-accent/5 hover:shadow-[0_0_20px_rgba(14,165,233,0.1)]"
          }`}
          aria-label={isRecording ? "Stop recording" : "Start recording"}
        >
          {isRecording ? (
            /* Stop icon */
            <div className="w-5 h-5 rounded-sm bg-accent" />
          ) : (
            /* Microphone icon */
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={`${
                isRequesting ? "text-text-muted" : "text-text-secondary"
              }`}
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
          )}
        </button>
      </div>

      {/* Label */}
      <span className="text-xs text-text-muted font-medium">
        {isRecording
          ? "Tap to stop"
          : isRequesting
          ? "Requesting microphone..."
          : state === "stopped"
          ? "Audio captured"
          : state === "error"
          ? "Error — tap to retry"
          : "Tap to speak"}
      </span>
    </div>
  );
}
