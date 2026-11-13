/**
 * SAMVAD — useVoiceRecorder Hook
 *
 * Manages browser microphone capture lifecycle:
 *   idle → requesting → recording → stopped
 *
 * Captures raw audio via MediaRecorder while simultaneously using
 * browser SpeechRecognition (webkitSpeechRecognition) when available
 * to provide real-time verbatim speech-to-text feedback in the UI.
 */

"use client";

import { useCallback, useMemo, useRef, useState } from "react";

export type RecorderState =
  | "idle"
  | "requesting"
  | "recording"
  | "stopped"
  | "error";

interface UseVoiceRecorderOptions {
  language?: string;
  onLiveTranscript?: (text: string) => void;
}

interface UseVoiceRecorderReturn {
  state: RecorderState;
  audioBlob: Blob | null;
  error: string | null;
  liveTranscript: string;
  isListening: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  reset: () => void;
}

const LANG_MAP: Record<string, string> = {
  en: "en-US",
  hi: "hi-IN",
  bn: "bn-IN",
  ta: "ta-IN",
  te: "te-IN",
  mr: "mr-IN",
};

export function useVoiceRecorder(
  options?: UseVoiceRecorderOptions
): UseVoiceRecorderReturn {
  const [state, setState] = useState<RecorderState>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [liveTranscript, setLiveTranscript] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  const startRecording = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    setLiveTranscript("");
    setState("requesting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        setState("stopped");

        // Release microphone tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.onerror = () => {
        setError("Audio recording failed.");
        setState("error");
        stream.getTracks().forEach((track) => track.stop());
      };

      // Buffer audio chunks every 250ms
      recorder.start(250);
      setState("recording");

      // Optional real-time speech recognition for instant visual typing feedback
      if (typeof window !== "undefined") {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const win = window as any;
        const SpeechRecognitionAPI =
          win.SpeechRecognition || win.webkitSpeechRecognition;

        if (SpeechRecognitionAPI) {
          try {
            const recognizer = new SpeechRecognitionAPI();
            recognizer.continuous = true;
            recognizer.interimResults = true;
            recognizer.lang =
              (options?.language && LANG_MAP[options.language]) || "en-US";

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            recognizer.onresult = (event: any) => {
              let text = "";
              for (let i = 0; i < event.results.length; i++) {
                text += event.results[i][0].transcript;
              }
              const cleaned = text.trim();
              if (cleaned) {
                setLiveTranscript(cleaned);
                options?.onLiveTranscript?.(cleaned);
              }
            };

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            recognizer.onerror = (ev: any) => {
              if (ev.error !== "no-speech" && ev.error !== "aborted") {
                // Speech recognition error is non-fatal since audio blob is still recorded
                console.warn("Speech recognition notice:", ev.error);
              }
            };

            recognizer.start();
            recognitionRef.current = recognizer;
          } catch {
            // Browser speech recognition initialization failure is non-fatal
          }
        }
      }
    } catch (err) {
      let message = "Unable to access microphone.";
      if (err instanceof DOMException) {
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
          message =
            "Microphone permission denied. Please allow microphone access in your browser address bar.";
        } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
          message = "No microphone found. Please connect a microphone.";
        } else if (err.name === "NotReadableError") {
          message = "Microphone is currently in use by another application.";
        }
      }
      setError(message);
      setState("error");
    }
  }, [options]);

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }
      recognitionRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    setAudioBlob(null);
    setLiveTranscript("");
    setError(null);
    setState("idle");
  }, []);

  return useMemo(
    () => ({
      state,
      audioBlob,
      error,
      liveTranscript,
      isListening: state === "recording",
      startRecording,
      stopRecording,
      reset,
    }),
    [state, audioBlob, error, liveTranscript, startRecording, stopRecording, reset]
  );
}
